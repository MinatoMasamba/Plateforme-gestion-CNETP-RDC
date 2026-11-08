from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from apps.experts.models import Expert
from web.ctc_views import _ctc_shared_context


@login_required(login_url='/se-connecter/')
def report_workspace(request):
    """Ancien shell dédié : redirige vers le module rapports du shell CTC (sans rechargement ultérieur)."""
    expert = Expert.objects.filter(user=request.user).select_related('structure').first()
    context = _ctc_shared_context(expert) if expert else None
    if not context:
        return redirect('web:app')
    allowed = context.get('st_allowed_views') or []
    if 'rapports' not in allowed and context.get('st_post_code') not in ('ST-V3-06', 'ST-V3-10', 'ST-V3-11'):
        home = context.get('st_space_home') or 'dashboard'
        return redirect(f'/ctc/#{home}')
    return redirect('/ctc/#rapports')
