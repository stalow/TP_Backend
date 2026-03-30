"""
Commande de test d'integration des emails transactionnels.

Exemple:
    python manage.py send_test_emails --to test@example.com
"""

from django.core.management.base import BaseCommand, CommandError
from time import sleep

from common.mail_service import (
    send_account_activation_email,
    send_candidate_consent_email,
    send_new_opportunity_email,
)


class Command(BaseCommand):
    help = "Envoie un exemplaire de chaque email transactionnel a une adresse donnee"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to_email",
            required=True,
            help="Adresse email qui recevra les emails de test",
        )

    def handle(self, *args, **options):
        to_email = (options.get("to_email") or "").strip()
        if not to_email:
            raise CommandError("L'option --to est obligatoire")

        self.stdout.write(self.style.WARNING(f"Envoi des emails de test vers {to_email}..."))

        sent = []

        try:
            activation_result = send_account_activation_email(
                display_name="Utilisateur Test",
                email=to_email,
            )
            sent.append(("account_activation", activation_result))
            self.stdout.write(self.style.SUCCESS("Email account_activation envoye"))
        except Exception as exc:
            raise CommandError(f"Echec envoi account_activation: {exc}") from exc

        try:
            consent_result = send_candidate_consent_email(
                candidate_name="Alex Martin",
                candidate_email=to_email,
                job_title="Head of Growth",
                referrer_name="Camille Dupont",
                organization_name="Korum",
                consent_token="test-consent-token-123",
                referrer_email="camille.dupont@example.com",
                referrer_experience_years=12,
                job_location="Geneve, Suisse",
                job_contract_types=["CDI", "Temps plein"],
                job_experience_level="Top Management",
                job_reward="5'000 Points",
                job_description=(
                    "Pilotage de la strategie de croissance, management transversal "
                    "et acceleration commerciale sur le marche europeen."
                ),
            )
            sent.append(("candidate_consent", consent_result))
            self.stdout.write(self.style.SUCCESS("Email candidate_consent envoye"))
        except Exception as exc:
            raise CommandError(f"Echec envoi candidate_consent: {exc}") from exc

        try:
            sleep(2)
            opportunity_result = send_new_opportunity_email(
                contact_name="Sophie Bernard",
                contact_email=to_email,
                job_title="Chief Financial Officer (CFO)",
                job_sector="Banque et Services Financiers",
                job_location="Zurich, Suisse",
            )
            sent.append(("new_opportunity", opportunity_result))
            self.stdout.write(self.style.SUCCESS("Email new_opportunity envoye"))
        except Exception as exc:
            raise CommandError(f"Echec envoi new_opportunity: {exc}") from exc

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Tous les emails de test ont ete envoyes."))
        for key, result in sent:
            self.stdout.write(f"- {key}: {result}")
