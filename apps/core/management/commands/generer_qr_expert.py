"""
Management command to generate a QR code for expert registration
Generates a single QR code pointing to the expert registration endpoint
"""

import os
import qrcode
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Génère un QR Code global dirigeant vers la vue d\'inscription des experts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default=None,
            help='L\'URL exacte de la vue d\'inscription (ex: http://127.0.0.1:8000/api/auth/register/)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='media/qrcodes/qr_inscription_expert.png',
            help='Chemin de sortie du fichier QR code'
        )

    def handle(self, *args, **options):
        # Déterminer l'URL
        if options['url']:
            url_inscription = options['url']
        else:
            # URL par défaut
            domain = os.getenv('DOMAIN', 'http://127.0.0.1:8000')
            url_inscription = f"{domain}/api/auth/register/"

        self.stdout.write(self.style.SUCCESS("\n" + "="*80))
        self.stdout.write("🔲 GÉNÉRATION DU QR CODE D'INSCRIPTION EXPERTS")
        self.stdout.write("="*80 + "\n")

        self.stdout.write(f"📍 URL d'inscription: {url_inscription}\n")

        try:
            # 1. Configuration du QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )

            # 2. Ajout de l'URL dans le QR code
            qr.add_data(url_inscription)
            qr.make(fit=True)

            # 3. Création de l'image
            img = qr.make_image(fill_color="black", back_color="white")

            # 4. Déterminer le chemin de sauvegarde
            output_path = options['output']
            
            # Si le chemin est relatif, le rendre absolu par rapport à BASE_DIR
            if not os.path.isabs(output_path):
                output_path = os.path.join(settings.BASE_DIR, output_path)

            # Créer le dossier s'il n'existe pas
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)

            # 5. Sauvegarde
            img.save(output_path)

            # Afficher les informations
            self.stdout.write(self.style.SUCCESS('✅ QR Code généré avec succès !\n'))
            self.stdout.write(f"📂 Emplacement: {output_path}\n")
            
            # Afficher les dimensions
            file_size = os.path.getsize(output_path)
            self.stdout.write(f"📊 Taille du fichier: {file_size} bytes\n")

            # Instructions d'utilisation
            self.stdout.write(self.style.WARNING("📋 INSTRUCTIONS D'UTILISATION:\n"))
            self.stdout.write("1. Imprimez le QR code généré")
            self.stdout.write("2. Affichhez-le sur des affiches ou documents")
            self.stdout.write("3. Envoyez-le par email aux experts")
            self.stdout.write("4. Les experts scannent le code avec leur téléphone")
            self.stdout.write("5. Ils accèdent directement au formulaire d'inscription\n")

            self.stdout.write("="*80 + "\n")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur lors de la génération du QR code: {e}"))
            raise
