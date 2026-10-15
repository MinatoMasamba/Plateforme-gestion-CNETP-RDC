from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from apps.experts.models import Expert
from web.pilotage_views import get_pilotage_context

from .models import AgentSession, RAGDocument
from .services.permissions import user_can_access_scope
from .services.rag import accessible_source_ids


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageIAConsoleView(View):
    """Page dédiée de l'agent IA pour le Comité de Pilotage : chat large + graphiques."""

    template_name = 'ia_agent/pilotage_console/console.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        if not priv:
            messages.info(
                request,
                "L'espace « Pilotage IA » est réservé aux membres du Comité de Pilotage."
            )
            return redirect('web:app')

        ia_sessions = AgentSession.objects.filter(user=request.user, scope='pilotage')[:20]

        context = {
            'expert': expert,
            'ia_sessions': ia_sessions,
            **priv,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class RAGSourceView(View):
    """Affiche une source RAG et ses passages avec des liens contrôlés."""

    template_name = 'ia_agent/rag_source.html'

    def get(self, request, pk):
        source = get_object_or_404(accessible_source_ids(request.user), pk=pk)
        metadata = source.metadata or {}
        object_url = None
        if source.source_kind in {'NORME', 'NORME_VERSION'} and metadata.get('norme_id'):
            if user_can_access_scope(request.user, 'ctc'):
                object_url = reverse('web:ctc_norme_read', args=[metadata['norme_id']])
            else:
                object_url = f"/api/v1/norms/{metadata['norme_id']}/"
        elif source.source_kind == 'DOCUMENT' and metadata.get('document_id'):
            object_url = reverse('web:ia_rag_source_download', args=[source.pk])
        elif source.source_kind == 'EXPERT_CV' and metadata.get('expert_id'):
            object_url = f"/api/v1/experts/{metadata['expert_id']}/"

        return render(request, self.template_name, {
            'source': source,
            'chunks': source.chunks.all()[:80],
            'object_url': object_url,
            'download_url': reverse('web:ia_rag_source_download', args=[source.pk])
            if source.source_kind in {'DOCUMENT', 'EXPERT_CV'} else None,
        })


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class RAGSourceDownloadView(View):
    """Sert un fichier source uniquement après vérification des permissions RAG."""

    def get(self, request, pk):
        source = get_object_or_404(accessible_source_ids(request.user), pk=pk)
        metadata = source.metadata or {}
        file_field = None
        filename = source.title

        if source.source_kind == 'DOCUMENT' and metadata.get('document_id'):
            from apps.documents.models import DocumentFile
            document = get_object_or_404(DocumentFile, pk=metadata['document_id'])
            file_field = document.file
            filename = document.file.name.rsplit('/', 1)[-1]
        elif source.source_kind == 'EXPERT_CV' and metadata.get('expert_id'):
            from apps.experts.models import Expert
            expert = get_object_or_404(Expert, pk=metadata['expert_id'])
            file_field = expert.cv
            filename = expert.cv.name.rsplit('/', 1)[-1] if expert.cv else filename

        if not file_field:
            raise Http404('Cette source ne possède pas de fichier téléchargeable.')

        response = FileResponse(
            file_field.open('rb'),
            content_type=source.mime_type or 'application/octet-stream',
        )
        response['Content-Disposition'] = f'inline; filename="{filename.replace(chr(34), "")}"'
        return response
