"""API v2 de l'organisation ; mêmes services et permissions que l'interface web."""
import json
from datetime import date
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.urls import reverse
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.governance.models import OrganisationVersion, Organe, GroupeCible, PiecePhoenix, MandatOrganisation, ParticipationPhoenix
from apps.governance.phoenix_operations import CONFIG_MODELS, object_version, configure, activate, suspend, readiness, snapshot, CONFIG_FIELDS
from apps.governance.phoenix_workflow import (accessible_dossiers, mandates_for, permitted_transitions, selected_mandate,
    create_dossier, save_version, attach_piece, decide, save_inquiry, set_document_lock, plan_meeting, record_presence, PhoenixConflict)
from apps.norms.models import NormeVersion
from web.phoenix_forms import configuration_form, DossierCreateForm, ActivationForm
from web.organisation_views import preparation_context


def version():
    return get_object_or_404(OrganisationVersion, code='phoenix-2026-10')


def error_response(error):
    messages = error.messages if isinstance(error, ValidationError) else ['Informations invalides ou opération concurrente ; actualiser le dossier.']
    return Response({'errors': messages}, status=409 if isinstance(error, (PhoenixConflict, OperationalError)) else 400)


def dossier_payload(dossier):
    return {'id': dossier.pk, 'norme_id': dossier.norme_id, 'reference': dossier.norme.reference_number,
            'title': dossier.norme.title, 'sc': dossier.gt.sc.code, 'gt': dossier.gt.code,
            'circuit': dossier.circuit.code, 'state': dossier.state, 'revision': dossier.revision,
            'version_id': dossier.document_version_id, 'url': reverse('web:phoenix_dossier', args=[dossier.pk])}


class PhoenixAPIView(APIView):
    permission_classes = [IsAuthenticated]


class ReferenceAPI(PhoenixAPIView):
    def get(self, request):
        preparation_context(request)
        organisation = version()
        return Response({'version': organisation.code, 'status': organisation.status, 'readiness': readiness(organisation),
                         'organes': list(organisation.organes.values('id', 'code', 'type', 'name', 'official_name', 'status')),
                         'groups': list(GroupeCible.objects.filter(sc__version=organisation).values('id', 'code', 'name', 'sc_id', 'activity', 'status')),
                         'legacy_preserved': True})


class ConfigurationAPI(PhoenixAPIView):
    def check(self, user):
        from apps.governance.organisation_permissions import can_manage_organisation
        if not can_manage_organisation(user):
            raise PermissionDenied('Une habilitation de gestion CNE-ITP est nécessaire.')

    def get(self, request, kind, pk=None):
        self.check(request.user)
        if kind not in CONFIG_MODELS:
            return Response(status=404)
        organisation = version()
        objects = CONFIG_MODELS[kind].objects.all()
        if pk:
            objects = objects.filter(pk=pk)
        data = [{'id': obj.pk, **snapshot(obj, CONFIG_FIELDS[kind])} for obj in objects if object_version(obj).pk == organisation.pk]
        return Response(data)

    def post(self, request, kind, pk=None):
        self.check(request.user)
        if kind not in CONFIG_MODELS or (kind == 'version' and not pk):
            return Response(status=404)
        organisation = version()
        instance = get_object_or_404(CONFIG_MODELS[kind], pk=pk) if pk else None
        if instance and object_version(instance).pk != organisation.pk:
            return Response(status=404)
        data = request.data.copy()
        if 'configuration' in data and isinstance(data['configuration'], dict):
            data['configuration'] = json.dumps(data['configuration'])
        form = configuration_form(kind, organisation, data=data, instance=instance)
        if not form.is_valid():
            return Response({'errors': form.errors.get_json_data()}, status=400)
        try:
            obj = configure(request.user, organisation, kind, form.cleaned_data, pk=pk)
        except (ValidationError, IntegrityError) as error:
            return error_response(error)
        return Response({'id': obj.pk}, status=200 if pk else 201)


class ActivationAPI(PhoenixAPIView):
    def post(self, request):
        from apps.governance.organisation_permissions import can_activate_organisation
        if not can_activate_organisation(request.user):
            raise PermissionDenied('Une habilitation de mise en service CNE-ITP est nécessaire.')
        try:
            if request.data.get('operation') == 'suspend':
                obj = suspend(request.user, version(), request.data.get('reason', ''))
            else:
                form = ActivationForm(request.data)
                if not form.is_valid():
                    return Response({'errors': form.errors.get_json_data()}, status=400)
                obj = activate(request.user, version(), form.cleaned_data)
        except (ValidationError, IntegrityError) as error:
            return error_response(error)
        return Response({'status': obj.status})


class DossiersAPI(PhoenixAPIView):
    def get(self, request):
        dossiers = accessible_dossiers(request.user).order_by('-pk')
        if str(request.GET.get('sc', '')).isdecimal():
            dossiers = dossiers.filter(gt__sc_id=int(request.GET['sc']))
        page = Paginator(dossiers, 25).get_page(request.GET.get('page'))
        return Response({'count': page.paginator.count, 'page': page.number, 'results': [dossier_payload(dossier) for dossier in page]})

    def post(self, request):
        form = DossierCreateForm(request.data, user=request.user, version=version())
        if not form.is_valid():
            return Response({'errors': form.errors.get_json_data()}, status=400)
        try:
            dossier = create_dossier(request.user, **form.cleaned_data, origin={'ip':request.META.get('REMOTE_ADDR', ''), 'channel':'API'})
        except (ValidationError, IntegrityError) as error:
            return error_response(error)
        return Response(dossier_payload(dossier), status=201)


class DossierAPI(PhoenixAPIView):
    def get(self, request, pk):
        dossier = get_object_or_404(accessible_dossiers(request.user), pk=pk)
        actions = [{'mandate_id': mandate.pk, 'function': mandate.function,
                    'transitions': [{'id': rule['id'], 'label': rule['label'], 'action': rule['action']} for rule in permitted_transitions(request.user, mandate, dossier)]}
                   for mandate in mandates_for(request.user)]
        return Response({**dossier_payload(dossier), 'mandates': actions,
                         'versions': list(NormeVersion.all_objects.filter(norme=dossier.norme).values('id', 'version_number', 'content', 'summary', 'created_at', 'version_author_id')),
                         'pieces': [{'id': piece.pk, 'reference': piece.reference, 'kind': piece.kind, 'version_id': piece.version_id,
                                     'content': piece.content, 'sha256': piece.sha256,
                                     'download_url': f'/api/v2/organisation/pieces/{piece.pk}/' if piece.file else None} for piece in dossier.pieces.all()],
                         'decisions': list(dossier.decisions.values('id', 'from_state', 'to_state', 'document_version_id', 'decision_reference', 'reason', 'completed', 'created_at'))})


class OperationSerializer(serializers.Serializer):
    operation = serializers.ChoiceField(choices=['edit', 'attach', 'decision', 'inquiry', 'lock', 'unlock', 'meeting', 'presence'])
    mandate = serializers.IntegerField(min_value=1)
    revision = serializers.IntegerField(min_value=0)
    content = serializers.CharField(required=False, allow_blank=True)
    summary = serializers.CharField(required=False)
    kind = serializers.CharField(required=False, max_length=80)
    reference = serializers.CharField(required=False, max_length=250)
    file = serializers.FileField(required=False)
    transition = serializers.CharField(required=False, max_length=60)
    decision_reference = serializers.CharField(required=False, max_length=250)
    reason = serializers.CharField(required=False)
    request_key = serializers.CharField(required=False, max_length=100)
    starts_at = serializers.DateField(required=False)
    ends_at = serializers.DateField(required=False)
    report_id = serializers.IntegerField(required=False, min_value=1)
    title = serializers.CharField(required=False, max_length=250)
    agenda = serializers.CharField(required=False)
    starts = serializers.DateTimeField(required=False)
    location = serializers.CharField(required=False, max_length=250)
    participants = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False)
    participation_id = serializers.IntegerField(required=False, min_value=1)
    presence = serializers.ChoiceField(choices=['EXPECTED', 'PRESENT', 'ABSENT', 'EXCUSED'], required=False)


class DossierOperationAPI(PhoenixAPIView):
    def post(self, request, pk):
        get_object_or_404(accessible_dossiers(request.user), pk=pk)
        serializer = OperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mandate = get_object_or_404(mandates_for(request.user), pk=data['mandate'])
        args = [request.user, mandate, pk, data['revision']]
        origin = {'ip':request.META.get('REMOTE_ADDR', ''), 'channel':'API'}
        try:
            operation = data['operation']
            if operation == 'edit':
                save_version(*args, data.get('content', ''), data.get('summary', ''), origin=origin)
            elif operation == 'attach':
                attach_piece(*args, data.get('kind', ''), data.get('reference', ''), data.get('content', ''), data.get('file'), origin=origin)
            elif operation == 'decision':
                decide(*args, data.get('transition', ''), data.get('decision_reference', ''), data.get('reason', ''), data.get('request_key', ''), {'ip': request.META.get('REMOTE_ADDR', ''), 'channel': 'API'})
            elif operation == 'inquiry':
                if not data.get('starts_at') or not data.get('ends_at'):
                    raise ValidationError('Les dates de l’enquête sont obligatoires.')
                save_inquiry(*args, data.get('reference', ''), data['starts_at'], data['ends_at'], data.get('report_id'), origin=origin)
            elif operation == 'meeting':
                if not data.get('starts'):
                    raise ValidationError('Renseigner la date de la réunion.')
                plan_meeting(*args, data.get('title', ''), data.get('agenda', ''), data['starts'], data.get('location', ''), data.get('participants', []), origin=origin)
            elif operation == 'presence':
                if not data.get('participation_id') or not data.get('presence'):
                    raise ValidationError('Renseigner le participant et sa présence.')
                record_presence(*args, data['participation_id'], data['presence'], origin=origin)
            else:
                set_document_lock(*args, operation == 'lock', origin=origin)
        except (ValidationError, IntegrityError, OperationalError, PiecePhoenix.DoesNotExist, ParticipationPhoenix.DoesNotExist) as error:
            return error_response(error)
        dossier = get_object_or_404(accessible_dossiers(request.user), pk=pk)
        return Response(dossier_payload(dossier))


class PieceDownloadAPI(PhoenixAPIView):
    def get(self, request, pk):
        piece = get_object_or_404(PiecePhoenix.objects.filter(dossier__in=accessible_dossiers(request.user)), pk=pk)
        if not piece.file:
            raise Http404
        return FileResponse(piece.file.open('rb'), as_attachment=True, filename=piece.file.name.rsplit('/', 1)[-1])


class ExportAPI(PhoenixAPIView):
    def get(self, request, pk=None):
        from web.phoenix_views import PhoenixExportView
        return PhoenixExportView().get(request, pk=pk)
