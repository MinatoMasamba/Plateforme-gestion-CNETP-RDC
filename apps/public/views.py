from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.norms.models import Norme

from .forms import PublicAmendementSubmissionForm

# Create your views here.


class PublicInquiryFormView(View):
    """
    Formulaire public de soumission d'un amendement pour une norme en enquête publique.
    Template: templates/public/inquiry_form.html
    URL: /public/enquete/<norme_id>/
    """
    template_name = 'public/inquiry_form.html'

    def get(self, request, norme_id):
        norme = get_object_or_404(Norme, id=norme_id)
        context = {
            'norme': norme,
            'is_open': norme.status == 'PUBLIC_INQUIRY',
            'form': PublicAmendementSubmissionForm(),
        }
        return render(request, self.template_name, context)

    def post(self, request, norme_id):
        norme = get_object_or_404(Norme, id=norme_id)

        if norme.status != 'PUBLIC_INQUIRY':
            messages.error(request, "Cette norme n'est plus en phase d'enquête publique.")
            return redirect('public:inquiry_form', norme_id=norme.id)

        form = PublicAmendementSubmissionForm(request.POST)
        if form.is_valid():
            amendement = form.save(commit=False)
            amendement.norme = norme
            amendement.save()
            return redirect('public:inquiry_thanks', norme_id=norme.id)

        context = {'norme': norme, 'is_open': True, 'form': form}
        return render(request, self.template_name, context)


class PublicInquiryThanksView(View):
    """
    Page de confirmation après soumission d'un amendement public.
    Template: templates/public/inquiry_thanks.html
    URL: /public/enquete/<norme_id>/merci/
    """
    template_name = 'public/inquiry_thanks.html'

    def get(self, request, norme_id):
        norme = get_object_or_404(Norme, id=norme_id)
        return render(request, self.template_name, {'norme': norme})
