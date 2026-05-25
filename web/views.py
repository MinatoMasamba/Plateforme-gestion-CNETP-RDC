from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.experts.models import Structure


class HomeView(View):
    """
    Vue d'accueil principale
    Template: templates/index.html
    URL: /
    """
    template_name = 'index.html'
    
    def get(self, request):
        context = {
            'siteName': 'CNETP - Plateforme Normative',
        }
        return render(request, self.template_name, context)


class ExpertRegistrationView(View):
    """
    Vue pour afficher la page d'inscription des experts
    Template: templates/expert_registration.html
    URL: /inscription-expert/
    """
    template_name = 'expert_registration.html'
    
    def get(self, request):
        organizations = Structure.objects.all()
        context = {
            'organizations': organizations,
        }
        return render(request, self.template_name, context)
