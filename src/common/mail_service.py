"""
Service d'envoi d'emails via Resend.
Centralisé ici pour être réutilisé par toutes les apps
(consentement candidat, inscription, notifications, etc.)

Tous les emails utilisent un template HTML de base commun
(templates/email_base.html) ; seul le contenu central change.
"""

import logging
from html import escape
from pathlib import Path
from typing import Optional

import resend
from django.conf import settings

logger = logging.getLogger(__name__)

# Chemin du template de base (à côté de ce fichier)
_BASE_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "email_base.html"
_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
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


def _render_content_template(template_name: str, context: dict[str, str]) -> str:
    """Rend un template HTML de contenu en remplaçant des placeholders {{KEY}}."""
    template_path = _TEMPLATES_DIR / template_name
    html = template_path.read_text(encoding="utf-8")
    for key, value in context.items():
        html = html.replace(f"{{{{{key}}}}}", value)
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


def _build_info_section(title: str, rows: list[tuple[str, str]]) -> str:
    """Construit un bloc d'information compact pour les emails."""
    if not rows:
        return ""

    items = "".join(
        f"<li style=\"margin:0 0 6px;\"><strong>{escape(label)} :</strong> {escape(value)}</li>"
        for label, value in rows
    )

    return (
        "<table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" "
        "style=\"margin:0 0 18px;background:#f8fffe;border:1px solid #d4efeb;border-radius:12px;\">"
        "<tr><td style=\"padding:14px 16px;\">"
        f"<p style=\"margin:0 0 10px;color:#00695c;font-size:14px;font-weight:700;\">{escape(title)}</p>"
        f"<ul style=\"margin:0;padding-left:18px;color:#455a64;font-size:14px;line-height:1.5;\">{items}</ul>"
        "</td></tr></table>"
    )


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
    referrer_email: str | None = None,
    referrer_experience_years: int | None = None,
    job_location: str | None = None,
    job_contract_types: list[str] | None = None,
    job_experience_level: str | None = None,
    job_reward: str | None = None,
    job_description: str | None = None,
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

    referrer_rows: list[tuple[str, str]] = [("Nom", referrer_name)]
    if referrer_email:
        referrer_rows.append(("Email", referrer_email))
    if referrer_experience_years is not None:
        suffix = "an" if referrer_experience_years == 1 else "ans"
        referrer_rows.append(("Experience", f"{referrer_experience_years} {suffix}"))

    job_rows: list[tuple[str, str]] = []
    if job_location:
        job_rows.append(("Localisation", job_location))
    if job_contract_types:
        job_rows.append(("Type de contrat", ", ".join(job_contract_types)))
    if job_experience_level:
        job_rows.append(("Niveau d'experience", job_experience_level))
    if job_reward:
        job_rows.append(("Prime de cooptation", job_reward))
    if job_description:
        job_rows.append(("Apercu du poste", job_description))

    content = _render_content_template(
        "candidate_consent_email.html",
        {
            "CANDIDATE_NAME": escape(candidate_name),
            "REFERRER_NAME": escape(referrer_name),
            "JOB_TITLE": escape(job_title),
            "ORGANIZATION_NAME": escape(organization_name),
            "REFERRER_DETAILS_SECTION": _build_info_section(
                "Votre contact chez Korum", referrer_rows
            ),
            "JOB_DETAILS_SECTION": _build_info_section(
                "Quelques details sur le poste", job_rows
            ),
            "CONSENT_CTA": _cta_button(consent_url, "Voir la proposition et choisir"),
            "CONSENT_URL": escape(consent_url),
        },
    )

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

    content = _render_content_template(
        "account_activation_email.html",
        {
            "DISPLAY_NAME": escape(display_name),
            "LOGIN_CTA": _cta_button(login_url, "Se connecter"),
            "LOGIN_URL": escape(login_url),
        },
    )

    return send_email(
        to=email,
        subject=subject,
        html=_render_email(content, footer="© 2026 Korum · Bienvenue dans la communauté 🌴"),
    )


def send_new_opportunity_email(
    contact_name: str,
    contact_email: str,
    job_title: str,
    job_sector: str,
    job_location: str,
) -> dict:
    """Envoie un email pour informer un contact d'une nouvelle opportunite."""
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    login_url = f"{frontend_url}/login"

    subject = f"Nouvelle opportunite C-level: {job_title}"

    content = _render_content_template(
        "new_opportunity_email.html",
        {
            "CONTACT_NAME": escape(contact_name),
            "JOB_TITLE": escape(job_title),
            "JOB_SECTOR": escape(job_sector),
            "JOB_LOCATION": escape(job_location),
            "OPPORTUNITY_CTA": _cta_button(login_url, "Se connecter et recommander"),
            "LOGIN_URL": escape(login_url),
        },
    )

    return send_email(
        to=contact_email,
        subject=subject,
        html=_render_email(
            content,
            footer="© 2026 Korum · Merci de faire vivre un reseau d'exception.",
        ),
    )
