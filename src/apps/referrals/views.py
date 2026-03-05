"""
Vues HTTP publiques (sans auth) pour la confirmation / refus
du consentement candidat via un token envoyé par email.

Endpoints:
    GET  /api/consent/<token>/           → infos sur le poste et le candidat
    POST /api/consent/<token>/confirm/   → le candidat accepte
    POST /api/consent/<token>/decline/   → le candidat refuse
"""

import json
import logging

from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.referrals.models import CandidateConsentToken, Referral, ReferralStatusEvent

logger = logging.getLogger(__name__)


def _get_token_or_error(token_str: str):
    """
    Récupère le CandidateConsentToken à partir de la chaîne UUID.
    Retourne (token_obj, None) si OK, ou (None, JsonResponse) si erreur.
    """
    try:
        consent = CandidateConsentToken.objects.select_related(
            "referral__candidate",
            "referral__job_opening",
            "referral__job_opening__organization",
            "referral__referrer",
        ).get(token=token_str)
    except (CandidateConsentToken.DoesNotExist, ValueError):
        return None, JsonResponse(
            {"error": "Token invalide ou introuvable.", "code": "TOKEN_NOT_FOUND"},
            status=404,
        )

    if consent.is_used:
        already = "confirmée" if consent.confirmed_at else "déclinée"
        return None, JsonResponse(
            {"error": f"Vous avez déjà {already} cette proposition.", "code": "TOKEN_ALREADY_USED"},
            status=409,
        )

    if consent.is_expired:
        return None, JsonResponse(
            {"error": "Ce lien a expiré. Demandez au parrain de soumettre une nouvelle recommandation.",
             "code": "TOKEN_EXPIRED"},
            status=410,
        )

    return consent, None


@method_decorator(csrf_exempt, name="dispatch")
class ConsentInfoView(View):
    """
    GET /api/consent/<token>/
    Retourne les infos nécessaires pour que le candidat prenne sa décision.
    """

    def get(self, request, token):
        consent, error_response = _get_token_or_error(token)
        if error_response:
            return error_response

        referral = consent.referral
        candidate = referral.candidate
        job = referral.job_opening
        org = job.organization
        referrer = referral.referrer

        return JsonResponse({
            "candidateName": candidate.full_name,
            "candidateEmail": candidate.email,
            "jobTitle": job.title,
            "jobDescription": job.description if hasattr(job, "description") else "",
            "jobLocation": job.location if hasattr(job, "location") else "",
            "organizationName": org.name,
            "referrerName": referrer.display_name or referrer.email,
            "expiresAt": consent.expires_at.isoformat(),
        })


@method_decorator(csrf_exempt, name="dispatch")
class ConsentConfirmView(View):
    """
    POST /api/consent/<token>/confirm/
    Le candidat accepte la proposition → referral passe de PENDING_CONSENT à SUBMITTED.
    """

    def post(self, request, token):
        consent, error_response = _get_token_or_error(token)
        if error_response:
            return error_response

        referral = consent.referral

        if referral.status != Referral.Status.PENDING_CONSENT:
            return JsonResponse(
                {"error": "Ce référral n'est plus en attente de consentement.", "code": "INVALID_STATE"},
                status=409,
            )

        now = timezone.now()

        # Update consent token
        consent.confirmed_at = now
        consent.save(update_fields=["confirmed_at"])

        # Update candidate consent
        candidate = referral.candidate
        candidate.consent_confirmed = True
        candidate.consent_confirmed_at = now
        candidate.save(update_fields=["consent_confirmed", "consent_confirmed_at"])

        # Transition referral to SUBMITTED
        referral.status = Referral.Status.SUBMITTED
        referral.save(update_fields=["status", "updated_at"])

        ReferralStatusEvent.objects.create(
            organization=referral.organization,
            referral=referral,
            from_status=Referral.Status.PENDING_CONSENT,
            to_status=Referral.Status.SUBMITTED,
            changed_by=None,
            reason_note="Consentement confirmé par le candidat via email.",
        )

        # Trigger scoring now that the candidate is confirmed
        try:
            from apps.referrals.services import compute_candidate_score
            compute_candidate_score(referral)
        except Exception as e:
            logger.error(f"Failed to score referral after consent confirmation: {e}")

        logger.info(f"Consent confirmed for referral {referral.id} by candidate {candidate.email}")

        return JsonResponse({
            "status": "confirmed",
            "message": "Votre candidature a été confirmée. Le recruteur peut maintenant examiner votre profil.",
        })


@method_decorator(csrf_exempt, name="dispatch")
class ConsentDeclineView(View):
    """
    POST /api/consent/<token>/decline/
    Le candidat refuse → referral passe de PENDING_CONSENT à REJECTED.
    """

    def post(self, request, token):
        consent, error_response = _get_token_or_error(token)
        if error_response:
            return error_response

        referral = consent.referral

        if referral.status != Referral.Status.PENDING_CONSENT:
            return JsonResponse(
                {"error": "Ce référral n'est plus en attente de consentement.", "code": "INVALID_STATE"},
                status=409,
            )

        now = timezone.now()

        # Update consent token
        consent.declined_at = now
        consent.save(update_fields=["declined_at"])

        # Transition referral to REJECTED
        referral.status = Referral.Status.REJECTED
        referral.save(update_fields=["status", "updated_at"])

        ReferralStatusEvent.objects.create(
            organization=referral.organization,
            referral=referral,
            from_status=Referral.Status.PENDING_CONSENT,
            to_status=Referral.Status.REJECTED,
            changed_by=None,
            reason_note="Candidat a décliné la proposition via email.",
        )

        logger.info(f"Consent declined for referral {referral.id} by candidate {referral.candidate.email}")

        return JsonResponse({
            "status": "declined",
            "message": "Vous avez décliné cette proposition. Aucune candidature ne sera soumise.",
        })
