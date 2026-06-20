import json
import logging
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.staticfiles import finders
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, PilotageMembreship, CTCMembership
from .forms import ExpertRegistrationForm, User_Simple, UserLoginForm, ExpertLoginForm
from django.contrib.auth import login as auth_login, get_user_model

logger = logging.getLogger(__name__)


def service_worker_view(request):
    """
    Sert sw.js à la racine (/sw.js) plutôt que sous /static/, pour que le
    scope par défaut du Service Worker couvre tout le site (et pas seulement
    /static/).
    """
    path = finders.find('sw.js')
    if not path:
        raise Http404
    with open(path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='application/javascript')


def wg_redirect(request, wg_id=None):
    """Redirige /wgs/ et /wgs/<id>/ vers l'application principale."""
    if not request.user.is_authenticated:
        return redirect('web:expert_login')
    return redirect('web:app')


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
            return redirect('web:home')
        
        # Récupérer les structures et CTM pour le dashboard
        user = request.user
        data_expert = Expert.objects.filter(user=user).first()
        
        if not data_expert:
            print("User is authenticated but not an expert:", request.user.username)
            messages.warning(request, "Votre compte n'est pas encore validé en tant qu'expert. Veuillez patienter ou contacter l'administrateur.")
            return redirect('web:home')
        
        structure = data_expert.structure
        
        # Récupérer les affectations (CTM et WG)
        from apps.governance.models import Affectation
        affectations = Affectation.objects.filter(expert=data_expert).select_related('ctm', 'wg')
        
        # Construire la liste des affectations avec rôles
        affectations_list = []
        for aff in affectations:
            affectations_list.append({
                'ctm': aff.ctm,
                'wg': aff.wg,
                'ctm_role': aff.ctm_role,
                'wg_role': aff.wg_role,
                'role': aff.role,
                'is_primary_ctm': aff.is_primary_ctm,
                'is_primary_wg': aff.is_primary_wg,
            })
        
        # Récupérer les rôles dans les comités
        from apps.governance.models import PilotageMembreship, CTCMembership
        pilotage_roles = [
            membership.get_role_display()
            for membership in PilotageMembreship.objects.filter(expert=data_expert)
        ]
        ctc_roles = [
            membership.get_role_display()
            for membership in CTCMembership.objects.filter(expert=data_expert)
        ]
        active_role = 'Utilisateur'
        if pilotage_roles:
            active_role = pilotage_roles[0]
        elif ctc_roles:
            active_role = ctc_roles[0]
        elif affectations_list:
            active_role = affectations_list[0]['role']
        elif user.is_superuser:
            active_role = 'Administrateur'
        
        context = {
            'user': user.username,
            'user_id': user.id,
            'expert': data_expert,
            'structure': structure,
            'affectations': affectations_list,
            'pilotage_roles': list(pilotage_roles),
            'ctc_roles': list(ctc_roles),
            'active_role': active_role,
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
            'sous_commissions': [
                "Géotechnique",
                "Ouvrages d'art — Barrages, ponts, portiques",
                "Bâtiments — Habitation, administratifs, industriels",
                "Aéroports",
                "Routes, Chemins de fer et Ports",
                "Ressources en eau et Ingénierie hydraulique",
                "Assainissement",
                "Recherche, Simulation et Sciences des matériaux",
            ],
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

    def post(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not (name and email and message):
            messages.error(request, "Merci de remplir tous les champs obligatoires.")
            return redirect('web:contact')

        try:
            send_mail(
                subject=f"[Contact CNETP] {subject or 'Nouveau message'}",
                message=f"De : {name} <{email}>\n\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            messages.success(request, "Votre message a bien été envoyé. Nous vous répondrons dans les plus brefs délais.")
        except Exception:
            messages.error(request, "Erreur lors de l'envoi du message. Veuillez réessayer plus tard.")

        return redirect('web:contact')

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
            return redirect(self._get_redirect_url(user))
        return render(request, self.template_name, {'form': form})

    @staticmethod
    def _get_redirect_url(user):
        _DIRECTOIRE = {'PRESIDENT', 'VICE_PRESIDENT', 'SECRETARY', 'RAPPORTEUR'}
        expert = Expert.objects.filter(user=user).first()
        if expert:
            membership = PilotageMembreship.objects.filter(expert=expert).first()
            if membership:
                role = membership.role
                if role in _DIRECTOIRE:
                    return 'web:pilotage_directoire_app'
                if role == 'CONSEILLER_POLITIQUE':
                    return 'web:pilotage_conseillers_app'
                if role == 'ADMIN_TECH_FIN':
                    return 'web:pilotage_atf_app'
                return 'web:pilotage_dashboard'
            if CTCMembership.objects.filter(expert=expert).exists():
                return 'web:ctc_dashboard'
        return 'web:app'



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
        'groupe_expert': 'app/composants/groupes_experts.html',
        'legistique': 'app/composants/legistique_module.html',
        'validation': 'app/composants/validation_module.html',
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


# ========== RÉINITIALISATION MOT DE PASSE ==========

@require_POST
@csrf_protect
def password_reset_request(request):
    """Étape 1 : reçoit un email, génère un code et l'envoie."""
    User = get_user_model()
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Requête invalide.'}, status=400)

    email = (data.get('email') or '').strip().lower()
    if not email:
        return JsonResponse({'ok': False, 'error': 'Email requis.'}, status=400)

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Réponse neutre pour ne pas révéler l'existence du compte,
        # mais on log côté serveur pour pouvoir diagnostiquer les "code jamais reçu".
        logger.warning('[password_reset_request] Aucun compte pour cet email: %s', email)
        return JsonResponse({'ok': True})

    from apps.core.models import PasswordResetCode
    reset = PasswordResetCode.generate_for(user)

    context = {
        'user': user,
        'code': reset.code,
        'expires_minutes': 15,
        'site_name': 'CNETP',
    }
    try:
        html_message = render_to_string('emails/password_reset_code.html', context)
    except Exception:
        html_message = (
            f"<p>Bonjour {user.get_full_name()},</p>"
            f"<p>Votre code de réinitialisation : <strong>{reset.code}</strong></p>"
            f"<p>Il expire dans 15 minutes.</p>"
        )

    try:
        send_mail(
            subject='[CNETP] Code de réinitialisation de mot de passe',
            message=f"Votre code : {reset.code} (valable 15 min)",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception('[password_reset_request] Erreur envoi code reset pour %s: %s', user.email, exc)
        return JsonResponse({'ok': False, 'error': 'Impossible d\'envoyer l\'email. Réessayez.'}, status=500)

    logger.info('[password_reset_request] Code envoyé avec succès à %s', user.email)
    return JsonResponse({'ok': True})


@require_POST
@csrf_protect
def password_reset_confirm(request):
    """Étape 2 : vérifie le code et met à jour le mot de passe."""
    User = get_user_model()
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Requête invalide.'}, status=400)

    email = (data.get('email') or '').strip().lower()
    code = (data.get('code') or '').strip()
    password = data.get('password', '')
    password2 = data.get('password2', '')

    if not all([email, code, password, password2]):
        return JsonResponse({'ok': False, 'error': 'Tous les champs sont requis.'}, status=400)
    if password != password2:
        return JsonResponse({'ok': False, 'error': 'Les mots de passe ne correspondent pas.'}, status=400)
    if len(password) < 8:
        return JsonResponse({'ok': False, 'error': 'Le mot de passe doit contenir au moins 8 caractères.'}, status=400)

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Code invalide ou expiré.'}, status=400)

    from apps.core.models import PasswordResetCode
    reset = PasswordResetCode.objects.filter(user=user, is_used=False).order_by('-created_at').first()

    if not reset or not reset.is_valid:
        return JsonResponse({'ok': False, 'error': 'Code expiré. Faites une nouvelle demande.'}, status=400)

    if reset.code != code:
        reset.attempts += 1
        reset.save(update_fields=['attempts'])
        remaining = max(0, 3 - reset.attempts)
        return JsonResponse({
            'ok': False,
            'error': f'Code incorrect. {remaining} tentative(s) restante(s).'
        }, status=400)

    reset.is_used = True
    reset.save(update_fields=['is_used'])
    user.set_password(password)
    user.save(update_fields=['password'])

    return JsonResponse({'ok': True})
