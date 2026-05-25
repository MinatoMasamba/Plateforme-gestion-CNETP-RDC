from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views import View
from django.utils.decorators import method_decorator
from django.shortcuts import render
import json
import os
from django.conf import settings

# Import models for default data
from apps.norms.models import Norme
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, WG # Assurez-vous d'avoir importé CTM et WG


class ReactAppView(View):
    """
    Serves the React SPA application.
    Injects initial state and serves React's index.html.
    """
    def get(self, request):
        return render(request,'index.html')

def get_initial_state(request):
    """Gathers data to be injected into the React app's initial state."""
    state = {
        'user': None,
        'csrfToken': get_token(request),
        'apiBase': "/api/v1/",
        'config': {
            'siteName': "CNETP - Plateforme Normative",
            'debug': settings.DEBUG,
        },
        'stats': {
            'norms_count': Norme.objects.count(),
            'experts_count': Expert.objects.count(),
            'ctm_count': CTM.objects.count(),
            'wg_count': WG.objects.count(),
        }
    }

    if request.user.is_authenticated:
        user = request.user
        state['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_expert': getattr(user, 'is_expert', False),
            'full_name': user.get_full_name(),
        }
    
    return state

def render_react(request):
    """
    Main function to serve React's index.html with Django context.
    """
    index_path = os.path.join(settings.BASE_DIR, 'frontend_static', 'index.html')
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            html = f.read()
    except FileNotFoundError:
        return HttpResponse(
            "<h1>React app not found</h1><p>Make sure the frontend build is in the frontend_static directory.</p>", 
            status=404
        )
    
    initial_state = get_initial_state(request)
    
    state_script = f"""
    <script>
        window.__INITIAL_STATE__ = {json.dumps(initial_state)};
    </script>
    """
    
    # Insert initial state before </head>
    html = html.replace('</head>', f'{state_script}</head>')
    
    return HttpResponse(html, content_type='text/html; charset=utf-8')


class ExpertRegistrationView(View):
    """
    Vue pour afficher la page d'inscription des experts
    Template: templates/expert_registration.html
    URL: /inscription-expert/
    """
    
    template_name = 'expert_registration.html'
    
    def get(self, request):
        # Charger les organisations pour le dropdown
        organizations = Structure.objects.all()
        
        context = {
            'organizations': organizations,
        }
        
        return render(request, self.template_name, context)


# ============================================================================
# MOCK DATA GENERATORS FOR HYBRID SYSTEM
# ============================================================================

def get_mock_documents():
    """Mock documents for EditorArea"""
    return [
        {
            "id": "doc-iso-9001",
            "title": "ISO 9001 - Système de Gestion de la Qualité",
            "currentVersion": "v2.1",
            "status": "in_review",
            "progress": 85,
            "author": "Prof. Masamba Édouard",
            "lastModified": "2025-05-21T14:32:00Z"
        },
        {
            "id": "doc-iso-14001",
            "title": "ISO 14001 - Management Environnemental",
            "currentVersion": "v1.8",
            "status": "draft",
            "progress": 62,
            "author": "Ir. Chantal Mwamba",
            "lastModified": "2025-05-20T10:15:00Z"
        }
    ]


def get_mock_collaborators():
    """Mock collaborators"""
    return [
        {
            "id": "col-1",
            "name": "Prof. Masamba Édouard",
            "email": "edmasamba100@gmail.com",
            "role": "Président",
            "avatarColor": "#f59e0b",
            "isActive": True,
            "structure": "Université de Kinshasa"
        },
        {
            "id": "col-2",
            "name": "Marie Laurent",
            "email": "marie.laurent@cnetp.cd",
            "role": "Secrétaire",
            "avatarColor": "#ec4899",
            "isActive": True,
            "structure": "Secrétariat Technique CNETP"
        },
        {
            "id": "col-3",
            "name": "Jean Kasongo",
            "email": "j.kasongo@cnetp.cd",
            "role": "Rédacteur",
            "avatarColor": "#3b82f6",
            "isActive": False,
            "structure": "Secrétariat Technique CNETP"
        }
    ]


def get_mock_experts():
    """Mock experts for ExpertsModule"""
    return [
        {
            "id": "exp-1",
            "name": "Prof. Masamba Édouard",
            "email": "edmasamba100@gmail.com",
            "phone": "+243 812 345 678",
            "province": "Kinshasa",
            "structure": "Université de Kinshasa (UNIKIN)",
            "ctm": "CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale",
            "wg": "WG 8.1 : Matériaux de Construction Locaux",
            "role": "Président scientifique",
            "isApproved": True
        },
        {
            "id": "exp-2",
            "name": "Ir. Chantal Mwamba",
            "email": "chantal.mwamba@cnetp.cd",
            "phone": "+243 898 765 432",
            "province": "Haut-Katanga",
            "structure": "Office des Voiries et Drainage (OVD)",
            "ctm": "CTM 5 – Infrastructures de Transport Linéaire et Maritimes",
            "wg": "WG 5.1 : Ingénierie Routière",
            "role": "Secrétaire",
            "isApproved": True
        },
        {
            "id": "exp-3",
            "name": "Arch. Sylvain Lukusa",
            "email": "sylvain.l@workspace.org",
            "phone": "+243 821 112 233",
            "province": "Lualaba",
            "structure": "Ordre National des Architectes (ONA)",
            "ctm": "CTM 3 – Bâtiment, Urbanisme et Transition Numérique",
            "wg": "WG 3.2 : BIM & Numérisation (ISO 19650)",
            "role": "Rapporteur",
            "isApproved": True
        },
        {
            "id": "exp-4",
            "name": "Ir. Godefroid Munongo",
            "email": "g.munongo@sogert.cd",
            "phone": "+243 854 998 811",
            "province": "Nord-Kivu",
            "structure": "Office des Routes (OR)",
            "ctm": "CTM 1 – Géotechnique et Risques Naturels",
            "wg": "WG 1.2 : Sols Tropicaux & Ferrallitiques",
            "role": "Membre",
            "isApproved": True
        }
    ]


def get_mock_working_groups():
    """Mock working groups"""
    return [
        {"id": "wg-8.1", "code": "WG 8.1", "title": "Matériaux de Construction Locaux", "tag": "Actif"},
        {"id": "wg-1.1", "code": "WG 1.1", "title": "Sols & Géo-mécanique", "tag": "Session libre"},
        {"id": "wg-2.3", "code": "WG 2.3", "title": "Dosage & Résistance Bétons", "tag": "Votant"},
        {"id": "wg-3.1", "code": "WG 3.1", "title": "Charpente & Structures Bois", "tag": "Stable"},
        {"id": "wg-6.2", "code": "WG 6.2", "title": "Drainage & Assainissement", "tag": "Rédaction"}
    ]


def get_mock_meetings():
    """Mock meetings for MeetingsVotesModule"""
    return [
        {
            "id": "meet-1",
            "title": "Réunion Plénière CTM 8",
            "date": "2025-05-24T14:00:00Z",
            "location": "CNETP Siège, Kinshasa",
            "participants": 12,
            "status": "scheduled",
            "description": "Validation des normes ISO 9001 pour la qualité"
        },
        {
            "id": "meet-2",
            "title": "Session de Travail WG 5.1",
            "date": "2025-05-22T10:00:00Z",
            "location": "Virtuel (Zoom)",
            "participants": 8,
            "status": "in_progress",
            "description": "Révision des standards d'ingénierie routière"
        }
    ]


def get_mock_votes():
    """Mock votes for MeetingsVotesModule"""
    return [
        {
            "id": "vote-1",
            "title": "Adoption ISO 14001 v1.8",
            "status": "active",
            "yes": 15,
            "no": 2,
            "abstain": 3,
            "deadline": "2025-05-25T17:00:00Z"
        },
        {
            "id": "vote-2",
            "title": "Élection Président CTM 3",
            "status": "closed",
            "yes": 18,
            "no": 1,
            "abstain": 1,
            "result": "Adopté"
        }
    ]


def get_mock_financial():
    """Mock financial data for FinancialModule"""
    return {
        "budget": {
            "total": 500000,
            "allocated": 325000,
            "spent": 210000,
            "remaining": 265000
        },
        "expenses": [
            {"id": "exp-1", "description": "Réunion CTM 8 - Logistique", "amount": 45000, "date": "2025-05-20"},
            {"id": "exp-2", "description": "Production normes numériques", "amount": 85000, "date": "2025-05-15"},
            {"id": "exp-3", "description": "Formation experts", "amount": 80000, "date": "2025-05-10"}
        ]
    }


def get_mock_validation():
    """Mock validation data for ValidationPublicModule"""
    return {
        "status": "in_progress",
        "completionRate": 72,
        "tasks": [
            {"id": "val-1", "title": "Vérification conformité ISO 9001", "status": "completed", "reviewer": "Prof. Masamba"},
            {"id": "val-2", "title": "Audit indépendant", "status": "in_progress", "reviewer": "Audit Conseil RDC"},
            {"id": "val-3", "title": "Approbation gouvernementale", "status": "pending", "reviewer": "Ministère Travaux Publics"}
        ]
    }


def get_mock_legistique():
    """Mock legal/legislative data for LegistiqueModule"""
    return {
        "references": [
            {
                "id": "leg-1",
                "code": "Décret 24/15",
                "title": "Normalisation Technique en RDC",
                "status": "active",
                "date": "2024-03-15"
            },
            {
                "id": "leg-2",
                "code": "Ordonnance 18/09",
                "title": "Standards d'Ingénierie Civile",
                "status": "active",
                "date": "2023-09-20"
            }
        ],
        "documents": [
            {"id": "ldoc-1", "name": "Cahier des charges", "version": "v3.2", "lastUpdate": "2025-05-10"},
            {"id": "ldoc-2", "name": "Guide de conformité", "version": "v2.1", "lastUpdate": "2025-05-01"}
        ]
    }


def get_mock_versions():
    """Mock document versions for HistoryArea"""
    return [
        {
            "id": "v-1",
            "version": "v2.1",
            "author": "Prof. Masamba Édouard",
            "authorEmail": "edmasamba100@gmail.com",
            "timestamp": "2025-05-21T14:32:00Z",
            "changes": "Mise à jour clause 4.1 selon feedback CTM"
        },
        {
            "id": "v-2",
            "version": "v2.0",
            "author": "Marie Laurent",
            "authorEmail": "marie.laurent@cnetp.cd",
            "timestamp": "2025-05-19T10:15:00Z",
            "changes": "Intégration commentaires rédacteurs"
        },
        {
            "id": "v-3",
            "version": "v1.9",
            "author": "Ir. Chantal Mwamba",
            "authorEmail": "chantal.mwamba@cnetp.cd",
            "timestamp": "2025-05-15T09:00:00Z",
            "changes": "Ajout section infrastructure"
        }
    ]


# ============================================================================
# API ENDPOINTS FOR HYBRID SYSTEM
# ============================================================================

@require_http_methods(["GET"])
def api_documents(request):
    """API endpoint for documents list"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_documents()
    })


@require_http_methods(["GET"])
def api_collaborators(request):
    """API endpoint for collaborators"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_collaborators()
    })


@require_http_methods(["GET"])
def api_experts(request):
    """API endpoint for experts"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_experts()
    })


@require_http_methods(["GET"])
def api_working_groups(request):
    """API endpoint for working groups"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_working_groups()
    })


@require_http_methods(["GET"])
def api_meetings(request):
    """API endpoint for meetings"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_meetings()
    })


@require_http_methods(["GET"])
def api_votes(request):
    """API endpoint for votes"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_votes()
    })


@require_http_methods(["GET"])
def api_financial(request):
    """API endpoint for financial data"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_financial()
    })


@require_http_methods(["GET"])
def api_validation(request):
    """API endpoint for validation data"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_validation()
    })


@require_http_methods(["GET"])
def api_legistique(request):
    """API endpoint for legislative data"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_legistique()
    })


@require_http_methods(["GET"])
def api_versions(request):
    """API endpoint for document versions"""
    return JsonResponse({
        "status": "success",
        "data": get_mock_versions()
    })


@require_http_methods(["GET"])
def api_app_data(request):
    """Combined endpoint for all app data"""
    return JsonResponse({
        "status": "success",
        "data": {
            "documents": get_mock_documents(),
            "collaborators": get_mock_collaborators(),
            "experts": get_mock_experts(),
            "workingGroups": get_mock_working_groups(),
            "meetings": get_mock_meetings(),
            "votes": get_mock_votes(),
            "financial": get_mock_financial(),
            "validation": get_mock_validation(),
            "legistique": get_mock_legistique(),
            "versions": get_mock_versions()
        }
    })
