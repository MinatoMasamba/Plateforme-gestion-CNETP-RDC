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
    
    # CTM - Choix multiples
    ctm_choices = forms.ModelMultipleChoiceField(
        queryset=CTM.objects.all(),
        required=True,
        label="Sous-Commissions Techniques (CTM)",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
        })
    )
    
    class Meta:
        model = Expert
        fields = ['structure', 'specialties', 'cv', 'ctm_choices']
    
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


class UserLoginForm(forms.Form):
    """Formulaire de connexion pour les utilisateurs simples"""
    
    # Classes Tailwind pour le Glassmorphism
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

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise ValidationError("Email ou mot de passe invalide.")
            cleaned_data['user'] = user
        return cleaned_data


class ExpertLoginForm(forms.Form):
    """Formulaire de connexion pour les experts (vérifie également qu'un Expert existe)"""
    
    # Classes Tailwind pour le Glassmorphism
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

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise ValidationError("Email ou mot de passe invalide.")
            # Vérifier qu'il existe un objet Expert lié
            if not Expert.objects.filter(user=user).exists():
                raise ValidationError("Accès refusé : Aucun profil expert associé à cet utilisateur.")
            cleaned_data['user'] = user
        return cleaned_data
