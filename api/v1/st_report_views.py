from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.http import HttpResponse
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.governance.st_report_models import STReportTemplate, STReportDispatch
from apps.governance.st_reports import visible_reports, save_report, get_report_version, create_report_template
from apps.governance.st_operations import actor_mandate
from apps.governance.st_report_exports import export_report_pdf, export_report_docx
from apps.messaging.dispatch_services import send_dispatch, visible_dispatches


class ReportInput(serializers.Serializer):
    source_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    document = serializers.JSONField(required=False)
    title = serializers.CharField(max_length=250)
    sections = serializers.JSONField(required=False)
    template_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    revision = serializers.IntegerField(min_value=1, required=False)
    period_start = serializers.DateField(required=False, allow_null=True)
    period_end = serializers.DateField(required=False, allow_null=True)


def report_data(report, user, dispatch_links=()):
    versions = list(report.versions.all())
    links = list(dispatch_links) if dispatch_links is not None else None
    if links is None:
        allowed_dispatches = visible_dispatches(user).values('pk')
        links = STReportDispatch.objects.filter(version__report=report, dispatch__in=allowed_dispatches).select_related('version', 'dispatch')
    return {'id': report.pk, 'reference': report.reference, 'revision': report.revision, 'template_id': report.template_id,
        'owner_name': report.owner.get_full_name() or report.owner.username, 'pole_code': report.pole_code,
        'mine': report.owner_id == user.pk, 'dispatch_count': len(links),
        'updated_at': report.updated_at.isoformat(),
        'versions': [{'number': v.number, 'title': v.title, 'sections': v.sections, 'source_id': v.source_id, 'document': v.document,
            'period_start': v.period_start.isoformat() if v.period_start else None,
            'period_end': v.period_end.isoformat() if v.period_end else None,
            'author_name': v.author_name, 'created_at': v.created_at.isoformat()} for v in versions],
        'dispatches': [{'id': link.dispatch_id, 'revision': link.version.number, 'target_code': link.dispatch.target_code,
            'created_at': link.created_at.isoformat()} for link in links]}


class STReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response({'detail': exc.messages}, status=409 if getattr(exc, 'code', None) == 'conflict' else 400)
        return super().handle_exception(exc)

    def list(self, request):
        reports = list(visible_reports(request.user)[:100])
        allowed = visible_dispatches(request.user).values('pk')
        links = STReportDispatch.objects.filter(version__report__in=[r.pk for r in reports], dispatch__in=allowed).select_related('version', 'dispatch')
        grouped = {}
        for link in links:
            grouped.setdefault(link.version.report_id, []).append(link)
        return Response({'results': [report_data(report, request.user, grouped.get(report.pk, ())) for report in reports]})

    def retrieve(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        return Response(report_data(get_object_or_404(visible_reports(request.user), pk=pk), request.user))

    def create(self, request):
        serializer = ReportInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(report_data(save_report(request.user, serializer.validated_data), request.user), status=201)

    @action(detail=True, methods=['post'])
    def revise(self, request, pk=None):
        serializer = ReportInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(report_data(save_report(request.user, serializer.validated_data, pk), request.user))

    @action(detail=False, methods=['get', 'post'])
    def templates(self, request):
        actor_mandate(request.user)
        if request.method == 'POST':
            class Input(serializers.Serializer):
                name = serializers.CharField(max_length=200)
                sections = serializers.JSONField()
                source_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
                document = serializers.JSONField(required=False)
            serializer = Input(data=request.data)
            serializer.is_valid(raise_exception=True)
            template = create_report_template(request.user, **serializer.validated_data)
            return Response({'id': template.pk, 'name': template.name, 'sections': template.sections, 'source_id': template.source_id, 'document': template.document}, status=201)
        return Response({'results': [{'id': t.pk, 'name': t.name, 'sections': t.sections, 'builtin': bool(t.system_code), 'source_id': t.source_id, 'document': t.document, 'collection': 'page_bleue' if (t.system_code or '').startswith('pack-blue-') else 'reference'} for t in STReportTemplate.objects.all()]})

    @action(detail=False, methods=['post'], url_path='cover-preview')
    def cover_preview(self, request):
        from apps.governance.st_report_cover import cover_png
        actor_mandate(request.user)
        response = HttpResponse(cover_png(request.data), content_type='image/png')
        response['Cache-Control'] = 'private, no-store'
        return response

    @action(detail=False, methods=['post'], url_path='import-document')
    def import_document(self, request):
        from apps.governance.st_report_documents import import_source, source_data
        from apps.governance.st_operations import writable
        actor_mandate(request.user)
        writable()
        upload = request.FILES.get('file')
        if upload is None:
            raise ValidationError('Choisissez un document à importer.')
        return Response(source_data(import_source(upload, request.user)), status=201)

    @action(detail=False, methods=['get'], url_path=r'sources/(?P<source_id>[^/.]+)')
    def source(self, request, source_id=None):
        from django.shortcuts import get_object_or_404
        from apps.governance.st_report_documents import accessible_sources, report_storage, source_data
        actor_mandate(request.user)
        source = get_object_or_404(accessible_sources(request.user), pk=source_id)
        storage = report_storage()
        if request.query_params.get('original') == '1':
            from django.http import FileResponse
            response = FileResponse(storage.open(source.original, 'rb'), as_attachment=True, filename=source.name)
        elif 'page' in request.query_params:
            import fitz
            try:
                number = int(request.query_params['page'])
            except ValueError:
                raise ValidationError('Page invalide.')
            if not 0 <= number < len(source.pages):
                raise ValidationError('Page invalide.')
            with storage.open(source.preview, 'rb') as stream, fitz.open(stream=stream.read(), filetype='pdf') as pdf:
                page = pdf[number]
                limit = 240 if request.query_params.get('thumbnail') == '1' else 1400
                scale = min(1.5, limit / max(page.rect.width, page.rect.height))
                response = HttpResponse(page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes('png'), content_type='image/png')
        else:
            return Response(source_data(source))
        response['Cache-Control'] = 'private, no-store'
        return response

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        try:
            number = int(request.query_params['revision']) if request.query_params.get('revision') else None
        except ValueError:
            raise ValidationError('Numéro de version invalide.')
        version = get_report_version(request.user, pk, number)
        file_format = request.query_params.get('file_format', 'pdf')
        if file_format not in ('pdf', 'docx'):
            raise ValidationError('Format PDF ou DOCX attendu.')
        content = export_report_pdf(version) if file_format == 'pdf' else export_report_docx(version)
        mime = 'application/pdf' if file_format == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        response = HttpResponse(content, content_type=mime)
        response['Content-Disposition'] = f'attachment; filename="{version.report.reference}-v{version.number}.{file_format}"'
        response['Cache-Control'] = 'private, no-store'
        return response

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        class Input(serializers.Serializer):
            revision = serializers.IntegerField(min_value=1)
            body = serializers.CharField(max_length=100000)
            sc_id = serializers.IntegerField(min_value=1, required=False)
            gt_id = serializers.IntegerField(min_value=1, required=False)
            request_key = serializers.UUIDField()
        serializer = Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data.copy()
        version = get_report_version(request.user, pk, values.pop('revision'))
        document = SimpleUploadedFile(f'{version.report.reference}-v{version.number}.pdf', export_report_pdf(version), content_type='application/pdf')
        with transaction.atomic():
            dispatch, created = send_dispatch(request.user, subject=version.title, upload=document, **values)
            STReportDispatch.objects.get_or_create(dispatch=dispatch, defaults={'version': version})
        return Response({'dispatch_id': dispatch.pk, 'created': created, 'recipient_count': dispatch.recipients.count()}, status=201 if created else 200)
