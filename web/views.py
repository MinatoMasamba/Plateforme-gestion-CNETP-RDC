from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM
from .forms import ExpertRegistrationForm, User_Simple, UserLoginForm, ExpertLoginForm
from django.contrib.auth import login as auth_login


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


class App(View):
    """
    Vue pour l'application principale (dashboard)
    Template: templates/app.html
    URL: /app/
    """
    template_name = 'app/app.html'
    

    def get(self, request):

        if not request.user.is_authenticated:
            return redirect('web:expert_registration')
        
            
            return redirect('web:home')
        # Récupérer les structures et CTM pour le dashboard
        user = request.user
        data_expert =  Expert.objects.filter(user=user).first()
        if not data_expert:
            print("User is authenticated but not an expert:", request.user.username)
            messages.warning(request, "Votre compte n'est pas encore validé en tant qu'expert. Veuillez patienter ou contacter l'administrateur.")
        structure = data_expert.structure if data_expert else None
        ctms = [data_expert.ctm] if data_expert and data_expert.ctm else []
        context = {
            'user': user.username,
            'structure' : structure,
            'ctms' : ctms,

        }
        

        return render(request, self.template_name, context)

class AboutView(View):
    """
    Vue pour la page "À propos"
    Template: templates/about.html
    URL: /about/
    """
    template_name = 'about.html'
    
    def get(self, request):
        context = {
            'siteName': 'CNETP - Plateforme Normative',
        }
        return render(request, self.template_name, context)
    

class ContactView(View):
    """
    Vue pour la page de contact
    Template: templates/contact.html
    URL: /contact/
    """
    template_name = 'contact.html'
    
    def get(self, request):
        context = {
            'siteName': 'CNETP - Plateforme Normative',
        }
        return render(request, self.template_name, context)

class User_RegistrationView(View):
    """
    Vue pour l'inscription des utilisateurs simples
    Template: user_templates/user_registration.html
    URL: /inscription/
    """
    template_name = 'user_templates/user_registration.html'
    form_class = User_Simple
    
    def get(self, request):
        form = self.form_class()
        context = {'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            try:
                user = form.save()
                messages.success(
                    request,
                    f"Inscription réussie! Bienvenue {user.get_full_name()}. Veuillez vérifier votre email pour confirmer."
                )
                return redirect('web:user_login')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'inscription: {str(e)}")
        
        context = {'form': form}
        return render(request, self.template_name, context)




class ExpertRegistrationView(View):
    """
    Vue pour l'inscription des experts avec formulaire Django
    Template: expert/expert_auth/expert_registration.html
    URL: /inscription-expert/
    """
    template_name = 'expert/expert_auth/expert_registration.html'
    form_class = ExpertRegistrationForm
    
    def get(self, request):
        form = self.form_class()
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                expert = form.save()
                messages.success(
                    request,
                    f"✅ Inscription réussie! Bienvenue {expert.user.get_full_name()}. Vous recevrez un email de confirmation une fois votre compte validé par l'administrateur."
                )
                return redirect('web:expert_login')
            except Exception as e:
                messages.error(request, f"❌ Erreur lors de l'inscription: {str(e)}")
        else:
            # Afficher les erreurs
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)





class UserLoginView(View):
    """Vue de connexion pour les utilisateurs simples"""
    template_name = 'user_templates/user_login.html'
    form_class = UserLoginForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            auth_login(request, user)
            messages.success(request, f"Bienvenue {user.get_full_name()}")
            return redirect('web:home')
        return render(request, self.template_name, {'form': form})


class ExpertLoginView(View):
    """Vue de connexion pour les experts"""
    template_name = 'expert/expert_auth/expert_login.html'
    form_class = ExpertLoginForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            auth_login(request, user)
            messages.success(request, f"Bienvenue expert {user.get_full_name()}")
            return redirect('web:app')
        return render(request, self.template_name, {'form': form})



from django.shortcuts import render
from django.http import HttpResponse

def component_api_view(request, module_id):
    """
    Cette vue intercepte la requête AJAX et renvoie uniquement le morceau 
    de HTML du composant demandé, sans le layout global.
    """
    # Dictionnaire de correspondance entre l'ID de l'onglet et le nom du fichier HTML
    templates_map = {
        'editor': 'app/composants/editor_area.html',
        'history': 'app/composants/history_area.html',
        'experts': 'app/composants/experts_groups_area.html',
        'meetings': 'app/composants/meetings_module.html',
        'financial': 'app/composants/financial_module.html',
        'sidebar': 'app/composants/sidebar.html',
        'messaging': 'app/composants/messaging_widget.html',
        'groupe_expert': 'app/composants/groupes_experts.html'
    }
    
    template_name = templates_map.get(module_id)
    
    if not template_name:
        return HttpResponse("<p>Module introuvable (404)</p>", status=404)
        
    # Ici, vous pouvez passer les variables dont le template a besoin
    context = {
        # 'documents': Document.objects.all(), etc.
    }
    
    # render() renvoie le HTML pur généré
    return render(request, template_name, context)