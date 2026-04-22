"""
Service d'extraction de données candidat depuis un profil LinkedIn scrappé.
Utilise OpenAI pour mapper les données brutes vers les champs du formulaire.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

VALID_EXPERTISE_DOMAINS = {
    "AUDIT_CONSULTING",
    "FINANCE",
    "INSURANCE",
    "LEGAL_TAX",
    "SALES",
    "RETAIL",
    "MARCOM",
    "MEDIA",
    "PROCUREMENT",
    "LOGISTICS_SUPPLY",
    "QUALITY",
    "TECH_IT",
    "DATA_AI",
    "DESIGN_CREATION",
    "HEALTH",
    "HR",
    "RD",
    "TECH",
}


def _build_extraction_prompt(raw_profile: Dict[str, Any]) -> str:
    headline = raw_profile.get("headline") or ""
    summary = raw_profile.get("summary") or ""
    skills = raw_profile.get("skills") or []
    experience = raw_profile.get("experience") or []
    name = raw_profile.get("name") or ""

    experience_text = ""
    for exp in experience[:10]:
        title = exp.get("title", "")
        company = exp.get("company", "")
        duration = exp.get("duration", "")
        dates = exp.get("dates", "")
        description = exp.get("description", "") or ""
        experience_text += f"- {title} chez {company} ({dates or duration}): {description[:200]}\n"

    skills_text = ", ".join(skills[:30]) if skills else "Non spécifié"

    return f"""Tu es un expert RH. Analyse ce profil LinkedIn et extrais les informations pour un formulaire de recommandation.

DONNÉES DU PROFIL LINKEDIN :
Nom : {name}
Titre : {headline}
Résumé : {summary[:800]}

Expériences :
{experience_text or "Non spécifié"}

Compétences LinkedIn : {skills_text}

INSTRUCTIONS :
1. Calcule les années d'expérience totales à partir des dates de postes (entier positif).
2. Choisit le domaine d'expertise parmi EXACTEMENT ces valeurs (une seule) :
   AUDIT_CONSULTING, FINANCE, INSURANCE, LEGAL_TAX, SALES, RETAIL, MARCOM, MEDIA,
   PROCUREMENT, LOGISTICS_SUPPLY, QUALITY, TECH_IT, DATA_AI, DESIGN_CREATION,
   HEALTH, HR, RD, TECH
3. Extrais jusqu'à 8 compétences techniques (hard skills, outils, langages, méthodes).
4. Extrais jusqu'à 5 compétences relationnelles / soft skills.
5. Génère une phrase de 10-20 mots décrivant ce que ce candidat recherche probablement.

Réponds UNIQUEMENT avec un JSON valide (sans markdown, sans ```):
{{"fullName": "<nom complet ou null>", "yearsExperience": <entier ou null>, "expertiseDomain": "<valeur enum ou null>", "technicalSkills": ["..."], "interpersonalSkills": ["..."], "searchCriteria": "<phrase ou null>"}}"""


def extract_candidate_from_linkedin_profile(
    raw_profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Prend le dict brut de scrape_linkedin_profile() et retourne les champs
    candidat pré-remplis via OpenAI.

    Tous les champs peuvent être None/vide — l'appelant doit gérer gracieusement.
    """
    empty: Dict[str, Any] = {
        "fullName": None,
        "yearsExperience": None,
        "expertiseDomain": None,
        "technicalSkills": [],
        "interpersonalSkills": [],
        "searchCriteria": None,
    }

    try:
        from apps.referrals.services.candidate_scoring import call_openai_api
    except ImportError as e:
        logger.error(f"Cannot import call_openai_api: {e}")
        return empty

    prompt = _build_extraction_prompt(raw_profile)

    result = call_openai_api(prompt)
    if not result:
        return empty

    # Valider et nettoyer chaque champ
    full_name = result.get("fullName")
    if not isinstance(full_name, str) or not full_name.strip():
        full_name = None

    years_exp = result.get("yearsExperience")
    if not isinstance(years_exp, int) or years_exp < 0:
        years_exp = None

    expertise = result.get("expertiseDomain")
    if expertise not in VALID_EXPERTISE_DOMAINS:
        expertise = None

    tech_skills: List[str] = [
        s for s in (result.get("technicalSkills") or []) if isinstance(s, str) and s.strip()
    ]

    interp_skills: List[str] = [
        s for s in (result.get("interpersonalSkills") or []) if isinstance(s, str) and s.strip()
    ]

    search_criteria = result.get("searchCriteria")
    if not isinstance(search_criteria, str) or len(search_criteria.split()) < 4:
        search_criteria = None

    return {
        "fullName": full_name,
        "yearsExperience": years_exp,
        "expertiseDomain": expertise,
        "technicalSkills": tech_skills,
        "interpersonalSkills": interp_skills,
        "searchCriteria": search_criteria,
    }
