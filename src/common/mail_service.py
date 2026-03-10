"""
Service d'envoi d'emails via Resend.
Centralisé ici pour être réutilisé par toutes les apps
(consentement candidat, inscription, notifications, etc.)

Tous les emails utilisent un template HTML de base commun
(templates/email_base.html) ; seul le contenu central change.
"""

import logging
from pathlib import Path
from typing import Optional

import resend
from django.conf import settings

logger = logging.getLogger(__name__)

# Chemin du template de base (à côté de ce fichier)
_BASE_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "email_base.html"
_DEFAULT_FOOTER = "© 2026 Korum · La cooptation simplifiée 🌴"


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------


def _get_client():
    """Initialise la clé API Resend."""
    api_key = getattr(settings, "RESEND_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "RESEND_API_KEY is not configured. "
            "Set it in your environment or Django settings."
        )
    resend.api_key = api_key


def _render_email(content: str, footer: str | None = None) -> str:
    """
    Injecte *content* (HTML) et un *footer* optionnel dans le template
    de base et renvoie le HTML complet prêt à l'envoi.
    """
    template = _BASE_TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.replace("{{CONTENT}}", content)
    html = html.replace("{{FOOTER_TEXT}}", footer or _DEFAULT_FOOTER)
    return html


def _cta_button(href: str, label: str) -> str:
    """Renvoie le HTML d'un bouton d'appel à l'action centré."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
      <tr><td align="center">
        <a href="{href}"
           style="display:inline-block;background:#26A69A;color:#ffffff;text-decoration:none;
                  padding:14px 40px;border-radius:50px;font-size:16px;font-weight:700;">
          {label}
        </a>
      </td></tr>
    </table>
    """


# ---------------------------------------------------------------------------
# Envoi générique
# ---------------------------------------------------------------------------


def send_email(
    to: str | list[str],
    subject: str,
    html: str,
    from_email: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> dict:
    """
    Envoie un email via Resend.

    Args:
        to: adresse(s) destinataire(s)
        subject: objet du mail
        html: contenu HTML du mail
        from_email: expéditeur (défaut: RESEND_FROM_EMAIL dans settings)
        reply_to: adresse de réponse optionnelle

    Returns:
        dict avec l'id du mail envoyé

    Raises:
        RuntimeError si la clé API n'est pas configurée
        resend.exceptions.ResendError en cas d'erreur API
    """
    _get_client()

    if isinstance(to, str):
        to = [to]

    params: dict = {
        "from": from_email or getattr(settings, "RESEND_FROM_EMAIL", "noreply@korumklub.app"),
        "to": to,
        "subject": subject,
        "html": html,
    }

    if reply_to:
        params["reply_to"] = reply_to

    logger.info("Sending email to %s — subject: %s", to, subject)
    result = resend.Emails.send(params)
    logger.info("Email sent successfully: %s", result)
    return result


# ---------------------------------------------------------------------------
# Emails spécifiques de l'application
# ---------------------------------------------------------------------------


def send_candidate_consent_email(
    candidate_name: str,
    candidate_email: str,
    job_title: str,
    referrer_name: str,
    organization_name: str,
    consent_token: str,
) -> dict:
    """
    Envoie un email au candidat référé pour lui demander de confirmer
    ou refuser sa candidature.

    Le lien pointe vers la page frontend /confirm-consent/<token>.
    """
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    consent_url = f"{frontend_url}/confirm-consent/{consent_token}"

    subject = (
        f"{referrer_name} vous a recommandé pour le poste "
        f"« {job_title} » — {organization_name}"
    )

    content = f"""
    <h2 style="color:#333;margin:0 0 16px;font-size:20px;">
      Bonjour {candidate_name} 👋
    </h2>

    <p style="color:#555;font-size:16px;line-height:1.6;margin:0 0 16px;">
      <strong>{referrer_name}</strong> vous a recommandé pour le poste
      <strong>« {job_title} »</strong> chez <strong>{organization_name}</strong>.
    </p>

    <p style="color:#555;font-size:16px;line-height:1.6;margin:0 0 24px;">
      Avant que votre candidature ne soit prise en compte par le recruteur,
      nous avons besoin de votre accord. Cliquez ci-dessous pour
      <strong>accepter</strong> ou <strong>décliner</strong> cette proposition.
    </p>

    {_cta_button(consent_url, "Voir la proposition et choisir")}

    <p style="color:#999;font-size:13px;line-height:1.5;margin:0 0 8px;">
      Ce lien est valable <strong>7 jours</strong>. Si vous ne faites rien,
      la recommandation sera automatiquement annulée.
    </p>

    <p style="color:#999;font-size:13px;line-height:1.5;margin:0;">
      Si vous n'êtes pas la bonne personne, ignorez simplement cet email.
    </p>
    """

    footer = (
        "© 2026 Korum · Cet email a été envoyé car quelqu'un "
        "vous a recommandé sur notre plateforme."
    )

    return send_email(
        to=candidate_email,
        subject=subject,
        html=_render_email(content, footer=footer),
    )


def send_account_activation_email(display_name: str, email: str) -> dict:
    """
    Envoie un email à l'utilisateur pour l'informer que son compte a été activé
    et qu'il peut maintenant se connecter.
    """
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    login_url = f"{frontend_url}/login"

    subject = "Votre compte Korum a été activé 🎉"

    content = f"""
    <h2 style="color:#333;margin:0 0 16px;font-size:20px;">
      Bienvenue, {display_name} ! 🎉
    </h2>

    <p style="color:#555;font-size:16px;line-height:1.6;margin:0 0 16px;">
      Bonne nouvelle : votre compte Korum vient d'être <strong>activé</strong> par notre équipe.
    </p>

    <p style="color:#555;font-size:16px;line-height:1.6;margin:0 0 24px;">
      Vous pouvez dès maintenant vous connecter et commencer à recommander des talents
      ou à publier des offres d'emploi.
    </p>

    {_cta_button(login_url, "Se connecter")}

    <p style="color:#999;font-size:13px;line-height:1.5;margin:0;">
      Si vous n'êtes pas à l'origine de cette inscription, ignorez cet email.
    </p>
    """

    return send_email(
        to=email,
        subject=subject,
        html=_render_email(content, footer="© 2026 Korum · Bienvenue dans la communauté 🌴"),
    )
