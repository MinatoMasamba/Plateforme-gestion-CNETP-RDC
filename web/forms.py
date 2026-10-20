from django import forms
from django.contrib.auth import get_user_model
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, ComitePilotage, TechnicalCell, WG, Affectation
from apps.governance.models import Organe, GroupeCible
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from apps.core.constants import province_choices

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    province = forms.ChoiceField(
        required=False, label='Province',
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'province', 'bio', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Prénom', 'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Nom', 'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Téléphone', 'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Biographie', 'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'w-full text-sm'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.instance.province if self.instance and self.instance.pk else None
        self.fields['province'].choices = province_choices(current)


class ExpertCVUserForm(UserProfileForm):
    """Identité demandée dans le parcours de mise à jour, comme à l'inscription."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['last_name'].label = 'Nom et post-nom'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Votre nom et post-nom'


class ExpertProfileForm(forms.ModelForm):
    class Meta:
        model = Expert
        fields = ['specialties', 'whatsapp_number', 'mobile_money_number', 'bank_name', 'bank_account', 'cv']
        widgets = {
            'specialties': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Spécialités', 'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
            'whatsapp_number': forms.TextInput(attrs={'placeholder': 'WhatsApp', 'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
            'mobile_money_number': forms.TextInput(attrs={'placeholder': 'Mobile Money', 'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
            'bank_name': forms.TextInput(attrs={'placeholder': 'Banque', 'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
            'bank_account': forms.TextInput(attrs={'placeholder': 'Compte bancaire', 'class': 'w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-black/25 border border-slate-200 dark:border-white/10'}),
            'cv': forms.ClearableFileInput(attrs={'class': 'w-full text-sm'}),
        }


class ExpertProfileUpdateForm(forms.Form):
    """Nouveau formulaire autonome de mise à jour du profil expert.

    Reprend le parcours de la candidature (identité, compétences/CV,
    affectation) sans dépendre du wizard Phoenix existant.
    """

    first_name = forms.CharField(max_length=150, label="Prénom")
    last_name = forms.CharField(max_length=150, label="Nom et post-nom")
    phone = forms.CharField(max_length=20, required=False, label="Téléphone")
    province = forms.ChoiceField(required=False, label="Province")
    whatsapp_number = forms.CharField(max_length=20, required=False, label="Numéro WhatsApp")
    specialties = forms.CharField(max_length=500, label="Domaines de compétence")
    bio = forms.CharField(required=False, label="Biographie professionnelle")
    cv = forms.FileField(required=False, label="Curriculum Vitae (CV)")
    ctm = forms.ModelChoiceField(
        queryset=CTM.objects.none(), required=False, label="Sous-commission (CTM)",
    )
    wg = forms.ModelChoiceField(
        queryset=WG.objects.none(), required=False, label="Groupe de travail",
    )

    def __init__(self, *args, user=None, expert=None, version=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.expert = expert
        self.version = version

        self.fields['ctm'].queryset = CTM.objects.all().order_by('number')

        ctm_id = None
        if self.is_bound:
            raw_ctm_id = str(self.data.get('ctm') or '').strip()
            if raw_ctm_id.isdigit():
                ctm_id = int(raw_ctm_id)
        elif expert is not None:
            ctm_id = getattr(expert, 'ctm_id', None)

        if ctm_id:
            self.fields['wg'].queryset = (
                WG.objects.filter(ctm_id=ctm_id).select_related('ctm').order_by('number')
            )
        else:
            self.fields['wg'].queryset = WG.objects.none()

        if self.fields['ctm'].queryset.exists():
            self.fields['ctm'].required = True
            self.fields['wg'].required = self.fields['wg'].queryset.exists()

        current_province = user.province if user else None
        self.fields['province'].choices = province_choices(current_province)

        if not self.is_bound:
            if user:
                self.fields['first_name'].initial = user.first_name
                self.fields['last_name'].initial = user.last_name
                self.fields['phone'].initial = user.phone
                self.fields['province'].initial = user.province
                self.fields['bio'].initial = user.bio
            if expert:
                self.fields['specialties'].initial = expert.specialties
                self.fields['whatsapp_number'].initial = expert.whatsapp_number
                if getattr(expert, 'ctm_id', None):
                    self.fields['ctm'].initial = expert.ctm_id
                    current = (
                        expert.governance_affectations
                        .filter(ctm_id=expert.ctm_id, wg__isnull=False)
                        .select_related('wg').first()
                    )
                    if current:
                        self.fields['wg'].initial = current.wg_id

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv and cv.size > 5 * 1024 * 1024:
            raise ValidationError("Le fichier CV ne doit pas dépasser 5 MB.", code='cv_too_large')
        return cv

    def clean(self):
        cleaned = super().clean()
        ctm = cleaned.get('ctm')
        wg = cleaned.get('wg')
        if wg and ctm and wg.ctm_id != ctm.id:
            raise ValidationError(
                "Le groupe de travail sélectionné n'appartient pas au CTM choisi.",
                code='wg_ctm_mismatch',
            )
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = self.user
        expert = self.expert

        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.phone = data.get('phone') or ''
        user.province = data.get('province') or ''
        user.bio = data.get('bio') or ''
        user.save(update_fields=['first_name', 'last_name', 'phone', 'province', 'bio'])

        expert.specialties = data.get('specialties') or ''
        expert.whatsapp_number = data.get('whatsapp_number') or ''
        if data.get('cv'):
            expert.cv = data['cv']
        ctm = data.get('ctm')
        wg = data.get('wg')
        if ctm:
            expert.ctm = ctm
        expert.save()

        affectation = None
        if ctm and wg:
            from django.db import transaction

            from apps.governance.models import Affectation

            with transaction.atomic():
                affectation = (
                    expert.governance_affectations
                    .filter(is_primary_ctm=True)
                    .order_by('pk')
                    .first()
                ) or expert.governance_affectations.order_by('pk').first()
                if affectation is None:
                    affectation = Affectation.objects.create(
                        expert=expert, ctm=ctm, wg=wg,
                        is_primary_ctm=True, is_primary_wg=True,
                    )
                else:
                    expert.governance_affectations.exclude(pk=affectation.pk).delete()
                    affectation.ctm = ctm
                    affectation.wg = wg
                    affectation.is_primary_ctm = True
                    affectation.is_primary_wg = True
                    affectation.save()
        return affectation


class ExpertOrganisationChoiceForm(forms.Form):
    sc = forms.ModelChoiceField(
        label='Nouvelle sous-commission', queryset=Organe.objects.none(),
        empty_label='Choisir une sous-commission',
    )
    source_wg = forms.ModelChoiceField(
        label='Groupe de travail actuel à classer', queryset=WG.objects.all(),
        empty_label='Choisir un groupe existant', required=False,
    )
    groupe = forms.ModelChoiceField(
        label='Groupe de travail souhaité', queryset=GroupeCible.objects.none(),
        empty_label='Choisir un groupe de travail', required=False,
    )

    def __init__(self, *args, version, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = version
        self.uses_adopted_gt = GroupeCible.objects.filter(sc__version=version).exists()
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full rounded-xl border border-slate-300 bg-white px-4 py-3 '
                'text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white'
            )
        self.fields['sc'].queryset = Organe.objects.filter(
            version=version, type=Organe.Type.SC,
        ).exclude(status='ARCHIVED').order_by('code')
        self.fields['source_wg'].queryset = WG.objects.select_related('ctm').order_by('ctm__number', 'number', 'name')
        self.fields['source_wg'].required = not self.uses_adopted_gt
        self.fields['groupe'].required = self.uses_adopted_gt
        self.fields['groupe'].queryset = GroupeCible.objects.filter(sc__version=version).order_by('sc__code', 'code')

    def clean(self):
        cleaned = super().clean()
        sc = cleaned.get('sc')
        groupe = cleaned.get('groupe')
        if groupe and sc and groupe.sc_id != sc.pk:
            self.add_error('groupe', 'Choisissez un groupe de cette sous-commission.')
        return cleaned


class User_Simple(forms.ModelForm):
    """ Formulaire pour inscrire les utilisateurs simples """
    
    # Classes Tailwind Néo-Glassmorphism pour les inputs
    GLASS_INPUT_CLASSES = 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#009FE3]/50 focus:border-[#009FE3] transition-all duration-300'

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
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#009FE3] focus:border-transparent',
            'placeholder': 'Votre prénom'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nom et Post-nom",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#009FE3] focus:border-transparent',
            'placeholder': 'Votre nom et post-nom'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#009FE3] focus:border-transparent',
            'placeholder': 'votre.email@exemple.com'
        })
    )
    
    password = forms.CharField(
        min_length=8,
        required=True,
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#009FE3] focus:border-transparent',
            'placeholder': 'Min 8 caractères'
        })
    )
    
    password_confirm = forms.CharField(
        min_length=8,
        required=True,
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#009FE3] focus:border-transparent',
            'placeholder': 'Confirmez votre mot de passe'
        })
    )
    
    # Champs Expert
    structure = forms.ModelChoiceField(
        queryset=Structure.objects.all(),
        required=True,
        label="Organisation",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#009FE3] focus:border-transparent'
        })
    )
    
    specialties = forms.CharField(
        max_length=500,
        required=False,
        label="Domaines de compétence",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#009FE3] focus:border-transparent',
            'placeholder': 'Ex: Géotechnique, Structures en béton, ...',
            'rows': 3
        })
    )
    
    whatsapp_number = forms.CharField(
        max_length=20,
        required=False,
        label="Numéro WhatsApp",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#009FE3] focus:border-transparent',
            'placeholder': '+243 81 234 5678'
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
        required=False,
        label="Sous-Commission Technique (CTM)",
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg',
        })
    )
    
    # Comité de Pilotage
    pilotage_member = forms.BooleanField(
        required=False,
        label="Membre du Comité de Pilotage",
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded',
        })
    )
    
    pilotage_role = forms.ChoiceField(
        required=False,
        label="Rôle au Comité de Pilotage",
        choices=[
            ('CONSEILLER', 'Conseiller'),
            ('CONSEILLER_POLITIQUE', 'Conseiller Institutionnel et Politique'),
            ('ADMIN_TECH_FIN', 'Administrateur Technique et Financier'),
            ('PARTENAIRE_SOC_CIV', 'Partenaire Sectoriel et Société Civile'),
            ('RAPPORTEUR', 'Rapporteur Général (Bureau)'),
            ('SECRETARY', 'Secrétaire (Bureau)'),
            ('VICE_PRESIDENT', 'Vice-Président (Bureau)'),
            ('PRESIDENT', 'Président (Bureau)'),
        ],
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg',
        })
    )
    
    # Champ de compatibilité historique ; aucune nomination à l'inscription.
    ctc_member = forms.BooleanField(
        required=False,
        label="Rattachement à la Coordination du Secrétariat technique",
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded',
        })
    )
    
    ctc_role = forms.ChoiceField(
        required=False,
        label="Rôle à la Cellule Technique",
        choices=[
            ('ISO_EXPERT', 'Expert Veille ISO'),
            ('LEGAL', 'Légiste'),
            ('ENVIRONMENTAL', 'Environnementaliste'),
            ('PLANNER', 'Planificateur'),
            ('ECONOMIST', 'Économiste'),
            ('SCIENTIFIC', 'Conseiller Scientifique'),
            ('ACCOUNTANT', 'Comptable'),
            ('ENQUIRY_MANAGER', 'Responsable Enquêtes'),
            ('INDUSTRIAL', 'Liaison Industrielle'),
            ('COMMUNICATOR', 'Communicateur'),
            ('EXECUTIVE', 'Assistant Exécutif'),
            ('CARTOGRAPHER', 'Cartographe SIG'),
            ('DATA_ENTRY', 'Opérateur de Saisie'),
            ('IT_ADMIN', 'Administrateur IT'),
            ('VICE_COORDINATOR', 'Vice-Coordonnateur'),
            ('COORDINATOR', 'Coordonnateur'),
        ],
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg',
        })
    )

    # WG (Groupe de Travail) selection
    wg = forms.ModelChoiceField(
        queryset=WG.objects.none(),
        required=False,
        label="Groupe de Travail (WG)",
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg',
        })
    )

    class Meta:
        model = Expert
        fields = ['structure', 'specialties', 'cv', 'whatsapp_number']
    
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

    def __init__(self, *args, **kwargs):
        # Allow dynamic population of WG queryset based on provided CTM
        data = kwargs.get('data') if 'data' in kwargs else (args[0] if args else None)
        super().__init__(*args, **kwargs)
        ctm_id = None
        if data and hasattr(data, 'get'):
            ctm_id = data.get('ctm') or data.get('ctm')
        # If editing an instance, use its CTM
        if not ctm_id and hasattr(self, 'instance') and getattr(self.instance, 'ctm', None):
            ctm_id = getattr(self.instance, 'ctm').id

        if ctm_id:
            try:
                self.fields['wg'].queryset = WG.objects.filter(ctm_id=ctm_id).order_by('number')
            except Exception:
                self.fields['wg'].queryset = WG.objects.none()
        else:
            self.fields['wg'].queryset = WG.objects.none()
    
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
        """Créer l'utilisateur et l'expert avec ses affiliations aux comités"""
        # Créer l'utilisateur Django
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password'],
            is_expert=True
        )

        # Créer l'expert
        expert = super().save(commit=False)
        expert.user = user
        expert.status = 'PENDING'
        expert.whatsapp_number = self.cleaned_data.get('whatsapp_number', '')

        if commit:
            expert.save()
        
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
    
    GLASS_INPUT_CLASSES = 'w-full px-4 py-3 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 transition-all duration-300'

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
    
    GLASS_INPUT_CLASSES = 'w-full px-4 py-3 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 transition-all duration-300'

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
