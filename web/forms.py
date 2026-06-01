from django import forms
from django.contrib.auth.models import User
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


class User_Simple(forms.ModelForm):
    """ Formulaire pour inscrire les utilisateurs simples """
    
    # Classes Tailwind Néo-Glassmorphism pour les inputs
    GLASS_INPUT_CLASSES = 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-300'

    first_name = forms.CharField(
        max_length=150,
        required=False,
        label='Prénom',
        widget=forms.TextInput(attrs={
            'class': GLASS_INPUT_CLASSES,
            'placeholder': 'Votre prénom'
        })
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': GLASS_INPUT_CLASSES,
            'placeholder': 'Votre nom'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': GLASS_INPUT_CLASSES,
            'placeholder': 'votre.email@exemple.com'
        })
    )
    
    password = forms.CharField(
        min_length=8,
        required=True,
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': GLASS_INPUT_CLASSES,
            'placeholder': 'Min 8 caractères'
        })
    )
    
    password_confirm = forms.CharField(
        min_length=8,
        required=True,
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': GLASS_INPUT_CLASSES,
            'placeholder': 'Confirmez votre mot de passe'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password'] # Eviter '__all__' pour des raisons de sécurité

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password']
        )
        return user
    



class ExpertRegistrationForm(forms.ModelForm):
    """Formulaire d'inscription pour les experts"""
    
    # Champs utilisateur
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Prénom",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Votre prénom'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Votre nom'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'votre.email@exemple.com'
        })
    )
    
    password = forms.CharField(
        min_length=8,
        required=True,
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Min 8 caractères'
        })
    )
    
    password_confirm = forms.CharField(
        min_length=8,
        required=True,
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Confirmez votre mot de passe'
        })
    )
    
    # Champs Expert
    structure = forms.ModelChoiceField(
        queryset=Structure.objects.all(),
        required=True,
        label="Organisation",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    specialties = forms.CharField(
        max_length=500,
        required=False,
        label="Domaines de compétence",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Ex: Géotechnique, Structures en béton, ...',
            'rows': 3
        })
    )
    
    cv = forms.FileField(
        required=False,
        label="Curriculum Vitae (CV)",
        widget=forms.FileInput(attrs={
            'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50',
            'accept': '.pdf,.doc,.docx,.txt'
        })
    )
    
    # CTM - Choix unique
    ctm = forms.ModelChoiceField(
        queryset=CTM.objects.all(),
        required=True,
        label="Sous-Commission Technique (CTM) principale",
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg',
        })
    )

    class Meta:
        model = Expert
        fields = ['structure', 'specialties', 'cv', 'ctm']
    
    def clean_password_confirm(self):
        """Vérifier que les mots de passe correspondent"""
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError(
                    "Les mots de passe ne correspondent pas.",
                    code='password_mismatch'
                )
        
        return password_confirm
    
    def clean_email(self):
        """Vérifier que l'email n'existe pas déjà"""
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Cet email est déjà utilisé.",
                code='email_exists'
            )
        
        return email
    
    def clean_cv(self):
        """Vérifier la taille du fichier CV"""
        cv = self.cleaned_data.get('cv')
        
        if cv:
            if cv.size > 5 * 1024 * 1024:  # 5 MB
                raise forms.ValidationError(
                    "Le fichier CV ne doit pas dépasser 5 MB.",
                    code='cv_too_large'
                )
        
        return cv
    
    def save(self, commit=True):
        """Créer l'utilisateur et l'expert"""
        # Créer l'utilisateur Django
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password']
        )
        
        # Créer l'expert
        expert = super().save(commit=False)
        expert.user = user
        expert.status = 'PENDING' # CHOIX POUR LEQUEL J'AI PAS CONSENTIE
        
        if commit:
            expert.save()
            # Ajouter les CTM choisis
            self.save_m2m()
        
        return expert

import logging
import traceback
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from apps.core.models import User
from apps.experts.models import Expert

logger = logging.getLogger(__name__)

class UserLoginForm(forms.Form):
    """Formulaire de connexion pour les utilisateurs simples"""
    
    GLASS_INPUT_CLASSES = 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-300'

    email = forms.EmailField(
        label='Email', 
        widget=forms.EmailInput(attrs={
            'class': GLASS_INPUT_CLASSES,
            'placeholder': 'votre.email@exemple.com'
        })
    )
    
    password = forms.CharField(
        label='Mot de passe', 
        widget=forms.PasswordInput(attrs={
            'class': GLASS_INPUT_CLASSES,
            'placeholder': '••••••••'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info(f"[UserLoginForm] - Initialisation du formulaire")
        self._validation_errors = []

    def clean_email(self):
        method = "clean_email"
        email = self.cleaned_data.get('email')
        logger.info(f"[UserLoginForm]-[{method}] - Validation de l'email: {email if email else 'None'}")
        if not email:
            logger.warning(f"[UserLoginForm]-[{method}] - Email manquant")
            raise ValidationError("L'adresse email est obligatoire.")
        if '@' not in email:
            logger.warning(f"[UserLoginForm]-[{method}] - Format email invalide: {email}")
            raise ValidationError("Veuillez entrer une adresse email valide.")
        logger.info(f"[UserLoginForm]-[{method}] - Email valide: {email}")
        return email

    def clean_password(self):
        method = "clean_password"
        password = self.cleaned_data.get('password')
        logger.info(f"[UserLoginForm]-[{method}] - Validation du mot de passe")
        if not password:
            logger.warning(f"[UserLoginForm]-[{method}] - Mot de passe manquant")
            raise ValidationError("Le mot de passe est obligatoire.")
        if len(password) < 4:
            logger.warning(f"[UserLoginForm]-[{method}] - Mot de passe trop court: {len(password)} caractères")
            raise ValidationError("Le mot de passe doit contenir au moins 4 caractères.")
        logger.info(f"[UserLoginForm]-[{method}] - Mot de passe valide")
        return password

    def clean(self):
        method = "clean"
        logger.info(f"[UserLoginForm]-[{method}] - Début de la validation globale")
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        logger.info(f"[UserLoginForm]-[{method}] - Tentative d'authentification pour: {email if email else 'email non fourni'}")
        try:
            if email and password:
                logger.info(f"[UserLoginForm]-[{method}] - Appel à authenticate()")
                user = authenticate(email=email, password=password)
                if user is None:
                    logger.warning(f"[UserLoginForm]-[{method}] - Échec d'authentification - Email ou mot de passe invalide: {email}")
                    raise ValidationError("Email ou mot de passe invalide.")
                logger.info(f"[UserLoginForm]-[{method}] - Authentification réussie pour: {email} (ID: {user.id})")
                cleaned_data['user'] = user
            else:
                logger.warning(f"[UserLoginForm]-[{method}] - Email ou mot de passe manquant")
        except Exception as e:
            logger.error(f"[UserLoginForm]-[{method}] - ERREUR CRITIQUE: {str(e)}")
            logger.error(traceback.format_exc())
            raise ValidationError("Une erreur technique est survenue. Veuillez réessayer.")
        logger.info(f"[UserLoginForm]-[{method}] - Fin validation - SUCCÈS")
        return cleaned_data


class ExpertLoginForm(forms.Form):
    """Formulaire de connexion pour les experts avec diagnostic précis"""
    
    GLASS_INPUT_CLASSES = 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-300'

    email = forms.EmailField(
        label='Email', 
        widget=forms.EmailInput(attrs={
            'class': GLASS_INPUT_CLASSES,
            'placeholder': 'expert@cnetp.cd'
        })
    )
    
    password = forms.CharField(
        label='Mot de passe', 
        widget=forms.PasswordInput(attrs={
            'class': GLASS_INPUT_CLASSES,
            'placeholder': '••••••••'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("[ExpertLoginForm] - Initialisation du formulaire expert")
        self._user = None
        self._expert_profile = None

    def clean_email(self):
        method = "clean_email"
        email = self.cleaned_data.get('email')
        logger.info(f"[ExpertLoginForm]-[{method}] - Validation email: {email}")
        if not email:
            raise ValidationError("L'adresse email est obligatoire.")
        if '@' not in email or '.' not in email:
            raise ValidationError("Veuillez entrer une adresse email valide.")
        
        # Vérifier si l'utilisateur existe (sans lever d'erreur tout de suite)
        user_exists = User.objects.filter(email=email).exists()
        logger.info(f"[ExpertLoginForm]-[{method}] - Utilisateur existe: {user_exists}")
        if not user_exists:
            # On stocke l'info pour le clean global
            self._user = None
        else:
            self._user = User.objects.get(email=email)
        return email

    def clean_password(self):
        method = "clean_password"
        password = self.cleaned_data.get('password')
        logger.info(f"[ExpertLoginForm]-[{method}] - Validation mot de passe")
        if not password:
            raise ValidationError("Le mot de passe est obligatoire.")
        if len(password) < 6:
            raise ValidationError("Le mot de passe doit contenir au moins 6 caractères.")
        return password

    def clean(self):
        method = "clean"
        logger.info(f"[ExpertLoginForm]-[{method}] - DÉBUT validation globale")
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        # --- Étape 1 : Vérifier si l'utilisateur existe ---
        if not email or not password:
            logger.warning(f"[ExpertLoginForm]-[{method}] - Email ou mot de passe manquant")
            return cleaned_data

        try:
            user = self._user  # déjà récupéré dans clean_email
            if user is None:
                logger.warning(f"[ExpertLoginForm]-[{method}] - ❌ Utilisateur inexistant: {email}")
                raise ValidationError("Aucun compte associé à cet email. Veuillez vous inscrire.")
            
            logger.info(f"[ExpertLoginForm]-[{method}] - Utilisateur trouvé: ID={user.id}, is_active={user.is_active}")
            
            # --- Étape 2 : Vérifier le mot de passe ---
            password_valid = check_password(password, user.password)
            logger.info(f"[ExpertLoginForm]-[{method}] - Mot de passe valide: {password_valid}")
            
            if not password_valid:
                logger.warning(f"[ExpertLoginForm]-[{method}] - ❌ Mot de passe incorrect pour {email}")
                raise ValidationError("Mot de passe incorrect.")
            
            # --- Étape 3 : Vérifier si l'utilisateur est actif ---
            if not user.is_active:
                logger.warning(f"[ExpertLoginForm]-[{method}] - ❌ Compte utilisateur désactivé: {email}")
                raise ValidationError("Votre compte est désactivé. Contactez l'administrateur.")
            
            # --- Étape 4 : Vérifier l'existence du profil expert ---
            try:
                expert_profile = Expert.objects.select_related('structure').get(user=user)
                self._expert_profile = expert_profile
                logger.info(f"[ExpertLoginForm]-[{method}] - Profil expert trouvé: ID={expert_profile.id}, statut={expert_profile.status}")
            except Expert.DoesNotExist:
                logger.error(f"[ExpertLoginForm]-[{method}] - ❌ Pas de profil expert pour l'utilisateur {email}")
                raise ValidationError("Vous n'êtes pas inscrit en tant qu'expert. Veuillez utiliser le formulaire d'inscription expert.")
            
            # --- Étape 5 : Vérifier le statut de l'expert ---
            if expert_profile.status == 'INACTIVE':
                logger.warning(f"[ExpertLoginForm]-[{method}] - ❌ Expert inactif: {email}")
                raise ValidationError("Votre profil expert est inactif. Veuillez contacter le secrétariat.")
            
            if expert_profile.status == 'PENDING':
                logger.warning(f"[ExpertLoginForm]-[{method}] - ⏳ Expert en attente de validation: {email}")
                raise ValidationError("Votre inscription est en attente de validation par le comité. Vous serez notifié par email.")
            
            # --- Étape 6 : Authentification finale (optionnelle, mais on peut aussi utiliser authenticate) ---
            # On authentifie manuellement car on a déjà validé le mot de passe
            from django.contrib.auth import login
            # On ne fait pas login ici, on retourne juste l'utilisateur
            cleaned_data['user'] = user
            cleaned_data['expert_profile'] = expert_profile
            
            logger.info(f"[ExpertLoginForm]-[{method}] - ✅ AUTHENTIFICATION EXPERT RÉUSSIE - {email}")
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"[ExpertLoginForm]-[{method}] - ERREUR CRITIQUE: {str(e)}")
            logger.error(traceback.format_exc())
            raise ValidationError("Une erreur technique est survenue. Veuillez réessayer.")
        
        logger.info(f"[ExpertLoginForm]-[{method}] - FIN validation - SUCCÈS")
        return cleaned_data
    
    def get_expert_profile(self):
        return self._expert_profile