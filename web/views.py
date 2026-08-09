import json
import logging
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.staticfiles import finders
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, PilotageMembreship, CTCMembership
from .forms import (
    ExpertRegistrationForm, User_Simple, UserLoginForm, ExpertLoginForm,
    UserProfileForm, ExpertProfileForm,
)
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


def app_manifest_view(request):
    """Sert le manifest PWA de l'espace de travail sous /app/manifest.json
    (scope /app/, distinct du manifest éventuel du site public)."""
    path = finders.find('app-manifest.json')
    if not path:
        raise Http404
    with open(path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='application/manifest+json')


def app_service_worker_view(request):
    """Sert le service worker de l'espace de travail sous /app/sw.js pour que
    son scope se limite à /app/ (distinct du service worker global /sw.js)."""
    path = finders.find('app-sw.js')
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


@method_decorator(ensure_csrf_cookie, name='dispatch')
class App(View):
    """
    Vue pour l'application principale (SPA statique cnetp-app.html) — toutes les
    données (profil, normes, experts, réunions...) sont chargées côté client via
    fetch vers /api/v1/..., ce gabarit ne reçoit donc aucun contexte serveur.
    Template: templates/app/app.html
    URL: /app/
    """
    template_name = 'app/app.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('web:home')

        if not Expert.objects.filter(user=request.user).exists():
            messages.warning(request, "Votre compte n'est pas encore validé en tant qu'expert. Veuillez patienter ou contacter l'administrateur.")
            return redirect('web:home')

        return render(request, self.template_name)

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



from django.contrib.auth.decorators import login_required

class ExpertProfileView(View):
    """
    Vue du profil de l'expert connecté.
    Template: templates/expert/profile.html
    """
    template_name = 'expert/profile.html'

    @method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
    def get(self, request):
        expert = (
            Expert.objects
            .filter(user=request.user)
            .select_related('structure', 'user', 'ctm')
            .first()
        )
        if not expert:
            messages.error(request, "Profil expert introuvable.")
            return redirect('web:home')

        from apps.governance.models import Affectation, CTCMembership, PilotageMembreship
        from web.ctc_views import get_ctc_context

        affectations = (
            Affectation.objects
            .filter(expert=expert)
            .select_related('ctm', 'wg')
            .order_by('ctm__name', 'wg__name')
        )
        ctc_memberships = (
            CTCMembership.objects
            .filter(expert=expert)
            .select_related('ctc')
            .order_by('ctc__name')
        )
        pilotage_memberships = (
            PilotageMembreship.objects
            .filter(expert=expert)
            .select_related('comite')
        )

        ctc_ctx = get_ctc_context(expert) or {}
        sidebar_nav_config = ctc_ctx.get('sidebar_nav_config') or {
            'principal': [
                {'view': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
                {'view': 'assignations', 'label': 'Mes Assignations', 'icon': 'file-check'},
            ],
            'system': [
                {'view': 'archives', 'label': 'Archives', 'icon': 'history'},
                {'view': 'parametres', 'label': 'Paramètres', 'icon': 'settings'},
            ],
        }

        profile_badges = []
        if expert.status:
            profile_badges.append(expert.get_status_display())
        if request.user.is_expert:
            profile_badges.append("Expert")
        if expert.user.is_ctc_staff:
            profile_badges.append("CTC")

        user_form = UserProfileForm(instance=request.user)
        expert_form = ExpertProfileForm(instance=expert)

        return render(request, self.template_name, {
            'expert': expert,
            'profile_user': request.user,
            'user_form': user_form,
            'expert_form': expert_form,
            'affectations': affectations,
            'ctc_memberships': ctc_memberships,
            'pilotage_memberships': pilotage_memberships,
            'profile_badges': profile_badges,
            'sidebar_nav_config': sidebar_nav_config,
            'pole_label': ctc_ctx.get('pole_label', 'Profil Expert'),
            'sidebar_pole': ctc_ctx.get('ctc_sub_role', 'profil'),
            'ctc_ctx_json': ctc_ctx or {
                'is_ctc_member': False,
                'ctc_sub_role': 'profil',
                'ctc_pole': 'profil',
                'pole_label': 'Profil Expert',
                'pole_badge': '',
                'poste': None,
                'membership': None,
                'pending_ctc_requests_count': 0,
                'my_pending_reviews_count': 0,
                'active_processus_count': 0,
            },
        })

    @method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
    def post(self, request):
        expert = (
            Expert.objects
            .filter(user=request.user)
            .select_related('structure', 'user', 'ctm')
            .first()
        )
        if not expert:
            messages.error(request, "Profil expert introuvable.")
            return redirect('web:home')

        user_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        expert_form = ExpertProfileForm(request.POST, request.FILES, instance=expert)

        if user_form.is_valid() and expert_form.is_valid():
            user_form.save()
            expert_form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect('web:expert_profile')

        from apps.governance.models import Affectation
        from web.ctc_views import get_ctc_context

        affectations = (
            Affectation.objects
            .filter(expert=expert)
            .select_related('ctm', 'wg')
            .order_by('ctm__name', 'wg__name')
        )
        ctc_memberships = CTCMembership.objects.filter(expert=expert).select_related('ctc').order_by('ctc__name')
        pilotage_memberships = PilotageMembreship.objects.filter(expert=expert).select_related('comite')
        ctc_ctx = get_ctc_context(expert) or {}
        sidebar_nav_config = ctc_ctx.get('sidebar_nav_config') or {
            'principal': [
                {'view': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
                {'view': 'assignations', 'label': 'Mes Assignations', 'icon': 'file-check'},
            ],
            'system': [
                {'view': 'archives', 'label': 'Archives', 'icon': 'history'},
                {'view': 'parametres', 'label': 'Paramètres', 'icon': 'settings'},
            ],
        }
        profile_badges = []
        if expert.status:
            profile_badges.append(expert.get_status_display())
        if request.user.is_expert:
            profile_badges.append("Expert")
        if expert.user.is_ctc_staff:
            profile_badges.append("CTC")
        return render(request, self.template_name, {
            'expert': expert,
            'profile_user': request.user,
            'affectations': affectations,
            'ctc_memberships': ctc_memberships,
            'pilotage_memberships': pilotage_memberships,
            'profile_badges': profile_badges,
            'sidebar_nav_config': sidebar_nav_config,
            'pole_label': ctc_ctx.get('pole_label', 'Profil Expert'),
            'sidebar_pole': ctc_ctx.get('ctc_sub_role', 'profil'),
            'ctc_ctx_json': ctc_ctx or {
                'is_ctc_member': False,
                'ctc_sub_role': 'profil',
                'ctc_pole': 'profil',
                'pole_label': 'Profil Expert',
                'pole_badge': '',
                'poste': None,
                'membership': None,
                'pending_ctc_requests_count': 0,
                'my_pending_reviews_count': 0,
                'active_processus_count': 0,
            },
            'user_form': user_form,
            'expert_form': expert_form,
        })

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
