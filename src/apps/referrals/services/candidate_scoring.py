"""
Service de scoring des candidats recommandés.
Stratégie 2: Scoring Hybride avec Analyse Sémantique (LLM-Assisted)

Combine:
1. Score déterministe par règles (50%)
2. Score sémantique via LLM (50%)
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from apps.jobs.models import JobOpening
from apps.referrals.models import Candidate, Referral

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


# =============================================================================
# Weights configuration
# =============================================================================

WEIGHTS = {
    # Rule-based scoring weights (total: 100)
    "expertise_match": 30,
    "experience_match": 20,
    "interpersonal_skills_match": 15,
    "technical_skills_match": 15,
    "referral_quality": 20,
    
    # Hybrid combination
    "rule_score_weight": 0.5,
    "llm_score_weight": 0.5,
}


# Experience level ranges (years)
EXPERIENCE_RANGES = {
    "TOP_MANAGEMENT": (12, 18),
    "C_LEVEL": (18, 25),
    "BOARD": (25, 50),
}


@dataclass
class ScoringBreakdown:
    """Détail du calcul du score."""
    expertise_match: int = 0
    experience_match: int = 0
    interpersonal_skills_match: int = 0
    technical_skills_match: int = 0
    referral_quality: int = 0
    
    # LLM analysis
    llm_score: int = 0
    llm_strengths: List[str] = None
    llm_gaps: List[str] = None
    llm_summary: str = ""
    
    # Final scores
    rule_score: int = 0
    final_score: int = 0
    
    def __post_init__(self):
        if self.llm_strengths is None:
            self.llm_strengths = []
        if self.llm_gaps is None:
            self.llm_gaps = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "expertise_match": self.expertise_match,
            "experience_match": self.experience_match,
            "interpersonal_skills_match": self.interpersonal_skills_match,
            "technical_skills_match": self.technical_skills_match,
            "referral_quality": self.referral_quality,
            "rule_score": self.rule_score,
            "llm_score": self.llm_score,
            "llm_strengths": self.llm_strengths,
            "llm_gaps": self.llm_gaps,
            "llm_summary": self.llm_summary,
            "final_score": self.final_score,
        }


@dataclass
class CandidateScoringResult:
    """Résultat complet du scoring."""
    referral_id: int
    candidate_id: int
    job_opening_id: int
    score: int
    grade: str  # A, B, C, D
    breakdown: ScoringBreakdown
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "referral_id": self.referral_id,
            "candidate_id": self.candidate_id,
            "job_opening_id": self.job_opening_id,
            "score": self.score,
            "grade": self.grade,
            "breakdown": self.breakdown.to_dict(),
        }


# =============================================================================
# Rule-based scoring
# =============================================================================

def compute_expertise_match(candidate: Candidate, job: JobOpening) -> int:
    """
    Score l'alignement du domaine d'expertise.
    Match exact = 30 points, sinon 0.
    """
    if candidate.expertise_domain == job.expertise_domain:
        return WEIGHTS["expertise_match"]
    return 0


def compute_experience_match(candidate: Candidate, job: JobOpening) -> int:
    """
    Score l'alignement du niveau d'expérience.
    Perfect match = 20, proche = 10, hors range = 0.
    """
    if not job.experience_level:
        return WEIGHTS["experience_match"] // 2  # Partial credit if job doesn't specify
    
    experience_range = EXPERIENCE_RANGES.get(job.experience_level)
    if not experience_range:
        return WEIGHTS["experience_match"] // 2
    
    min_years, max_years = experience_range
    candidate_years = candidate.years_experience
    
    if min_years <= candidate_years <= max_years:
        return WEIGHTS["experience_match"]  # Perfect match
    elif candidate_years >= min_years - 2 and candidate_years <= max_years + 3:
        return WEIGHTS["experience_match"] // 2  # Close enough
    return 0


def compute_interpersonal_skills_match(candidate: Candidate, job: JobOpening) -> int:
    """
    Score l'intersection des compétences relationnelles.
    Max 15 points (5 par skill en commun, max 3).
    """
    candidate_skills = set(candidate.interpersonal_skills or [])
    job_skills = set(job.interpersonal_skills or [])
    
    if not job_skills:
        return WEIGHTS["interpersonal_skills_match"] // 2
    
    intersection = candidate_skills & job_skills
    points_per_skill = WEIGHTS["interpersonal_skills_match"] // 3
    return min(len(intersection) * points_per_skill, WEIGHTS["interpersonal_skills_match"])


def compute_technical_skills_match(candidate: Candidate, job: JobOpening) -> int:
    """
    Score l'intersection des compétences techniques.
    Max 15 points basé sur le ratio de match.
    """
    candidate_skills = set(s.lower() for s in (candidate.technical_skills or []))
    job_skills = set(s.lower() for s in (job.technical_skills or []))
    
    # Also include LinkedIn skills if available
    if candidate.linkedin_skills:
        linkedin_skills = candidate.linkedin_skills if isinstance(candidate.linkedin_skills, list) else []
        candidate_skills.update(s.lower() for s in linkedin_skills)
    
    if not job_skills:
        return WEIGHTS["technical_skills_match"] // 2
    
    if not candidate_skills:
        return 0
    
    intersection = candidate_skills & job_skills
    ratio = len(intersection) / len(job_skills) if job_skills else 0
    return int(ratio * WEIGHTS["technical_skills_match"])


def compute_referral_quality(referral: Referral) -> int:
    """
    Score la qualité du referral lui-même.
    - Motivation remplie: +8 points
    - Supporting materials: +4 points
    - Relationship type fort: +8 points
    """
    score = 0
    
    # Profile motivation filled
    if referral.profile_motivation and len(referral.profile_motivation) > 50:
        score += 8
    elif referral.profile_motivation:
        score += 4
    
    # Supporting materials provided
    if referral.supporting_materials and len(referral.supporting_materials) > 0:
        score += 4
    
    # Strong relationship type
    strong_relationships = {"COMPANY", "HIERARCHICAL"}
    if referral.relationship_type in strong_relationships:
        score += 8
    elif referral.relationship_type == "ALUMNI":
        score += 4
    
    return min(score, WEIGHTS["referral_quality"])


def compute_rule_score(candidate: Candidate, job: JobOpening, referral: Referral) -> ScoringBreakdown:
    """
    Calcule le score basé sur les règles déterministes.
    Retourne un breakdown détaillé.
    """
    breakdown = ScoringBreakdown()
    
    breakdown.expertise_match = compute_expertise_match(candidate, job)
    breakdown.experience_match = compute_experience_match(candidate, job)
    breakdown.interpersonal_skills_match = compute_interpersonal_skills_match(candidate, job)
    breakdown.technical_skills_match = compute_technical_skills_match(candidate, job)
    breakdown.referral_quality = compute_referral_quality(referral)
    
    breakdown.rule_score = (
        breakdown.expertise_match +
        breakdown.experience_match +
        breakdown.interpersonal_skills_match +
        breakdown.technical_skills_match +
        breakdown.referral_quality
    )
    
    return breakdown


# =============================================================================
# LLM-based scoring
# =============================================================================

def build_llm_prompt(candidate: Candidate, job: JobOpening, referral: Referral) -> str:
    """
    Construit le prompt pour l'analyse LLM.
    """
    # Format job info
    job_challenges = ", ".join(job.key_challenges) if job.key_challenges else "Non spécifié"
    job_skills = ", ".join(job.interpersonal_skills) if job.interpersonal_skills else "Non spécifié"
    
    # Format candidate info
    candidate_skills = ", ".join(candidate.technical_skills) if candidate.technical_skills else "Non spécifié"
    candidate_interpersonal = ", ".join(candidate.interpersonal_skills) if candidate.interpersonal_skills else "Non spécifié"
    
    # LinkedIn data
    linkedin_exp = ""
    if candidate.linkedin_experience:
        experiences = candidate.linkedin_experience if isinstance(candidate.linkedin_experience, list) else []
        for exp in experiences[:3]:  # Limit to last 3 experiences
            if isinstance(exp, dict):
                linkedin_exp += f"- {exp.get('title', 'N/A')} chez {exp.get('company', 'N/A')}\n"
    
    linkedin_skills_str = ""
    if candidate.linkedin_skills:
        skills = candidate.linkedin_skills if isinstance(candidate.linkedin_skills, list) else []
        linkedin_skills_str = ", ".join(skills[:10])  # Limit to 10 skills
    
    prompt = f"""Tu es un expert en recrutement exécutif. Évalue l'alignement entre ce candidat et ce poste sur 100.

## POSTE
- **Titre**: {job.title}
- **Description**: {job.description or 'Non spécifié'}
- **Secteur**: {job.get_activity_sector_display() if job.activity_sector else 'Non spécifié'}
- **Contexte entreprise**: {job.get_company_context_display() if job.company_context else 'Non spécifié'}
- **Enjeux clés**: {job_challenges}
- **Compétences relationnelles recherchées**: {job_skills}
- **Niveau d'expérience**: {job.get_experience_level_display() if job.experience_level else 'Non spécifié'}
- **Expertise métier**: {job.get_expertise_domain_display() if job.expertise_domain else 'Non spécifié'}

## CANDIDAT
- **Nom**: {candidate.full_name}
- **Années d'expérience**: {candidate.years_experience}
- **Domaine d'expertise**: {candidate.get_expertise_domain_display() if candidate.expertise_domain else 'Non spécifié'}
- **Compétences techniques**: {candidate_skills}
- **Compétences relationnelles**: {candidate_interpersonal}

### Données LinkedIn
- **Headline**: {candidate.linkedin_headline or 'Non disponible'}
- **Résumé**: {candidate.linkedin_summary or 'Non disponible'}
- **Expériences récentes**:
{linkedin_exp or 'Non disponible'}
- **Skills LinkedIn**: {linkedin_skills_str or 'Non disponible'}

## RECOMMANDATION
- **Type de relation**: {referral.get_relationship_type_display()}
- **Contexte de la relation**: {referral.relationship_context}
- **Motivation du recommandeur**: {referral.profile_motivation or 'Non spécifié'}
- **Matériaux de support**: {len(referral.supporting_materials or [])} document(s) fourni(s)

## INSTRUCTIONS
Analyse en profondeur l'adéquation candidat/poste. Considère:
1. L'alignement des compétences et de l'expérience
2. La pertinence du parcours pour le contexte de l'entreprise
3. La qualité et la crédibilité de la recommandation
4. Les signaux positifs et négatifs du profil LinkedIn

Réponds UNIQUEMENT avec un JSON valide (sans markdown, sans ```):
{{"score": <0-100>, "strengths": ["point fort 1", "point fort 2", "point fort 3"], "gaps": ["point faible 1", "point faible 2"], "summary": "Résumé en 2-3 phrases de l'évaluation"}}
"""
    return prompt


def call_openai_api(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Appelle l'API OpenAI et parse la réponse.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, skipping LLM scoring")
        return None
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Tu es un expert en recrutement exécutif. Tu réponds uniquement en JSON valide."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    
    try:
        response = requests.post(
            OPENAI_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        # Clean potential markdown wrapping
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        return json.loads(content)
        
    except requests.RequestException as e:
        logger.error(f"OpenAI API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Unexpected OpenAI API response structure: {e}")
        return None


def compute_llm_score(candidate: Candidate, job: JobOpening, referral: Referral) -> Dict[str, Any]:
    """
    Calcule le score via l'analyse LLM.
    Retourne un dict avec score, strengths, gaps, summary.
    """
    prompt = build_llm_prompt(candidate, job, referral)
    
    result = call_openai_api(prompt)
    
    if result is None:
        # Fallback: return neutral score
        return {
            "score": 50,
            "strengths": [],
            "gaps": [],
            "summary": "Analyse LLM non disponible."
        }
    
    # Validate and sanitize response
    return {
        "score": max(0, min(100, int(result.get("score", 50)))),
        "strengths": result.get("strengths", [])[:5],
        "gaps": result.get("gaps", [])[:5],
        "summary": str(result.get("summary", ""))[:500],
    }


# =============================================================================
# Main scoring function
# =============================================================================

def score_to_grade(score: int) -> str:
    """Convertit un score en grade A/B/C/D."""
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    return "D"


def compute_candidate_score(
    referral: Referral,
    use_llm: bool = True
) -> CandidateScoringResult:
    """
    Calcule le score hybride complet pour un referral.
    
    Args:
        referral: Le referral à scorer
        use_llm: Si True, utilise l'analyse LLM (peut être désactivé pour les tests)
        
    Returns:
        CandidateScoringResult avec le score final et le breakdown
    """
    candidate = referral.candidate
    job = referral.job_opening
    
    # Step 1: Compute rule-based score
    breakdown = compute_rule_score(candidate, job, referral)
    
    # Step 2: Compute LLM score (if enabled)
    if use_llm:
        llm_result = compute_llm_score(candidate, job, referral)
        breakdown.llm_score = llm_result["score"]
        breakdown.llm_strengths = llm_result["strengths"]
        breakdown.llm_gaps = llm_result["gaps"]
        breakdown.llm_summary = llm_result["summary"]
    else:
        breakdown.llm_score = breakdown.rule_score  # Use rule score as fallback
    
    # Step 3: Compute final hybrid score
    breakdown.final_score = int(
        breakdown.rule_score * WEIGHTS["rule_score_weight"] +
        breakdown.llm_score * WEIGHTS["llm_score_weight"]
    )
    
    return CandidateScoringResult(
        referral_id=referral.id,
        candidate_id=candidate.id,
        job_opening_id=job.id,
        score=breakdown.final_score,
        grade=score_to_grade(breakdown.final_score),
        breakdown=breakdown,
    )


def score_referrals_for_job(job_opening_id: int, use_llm: bool = True) -> List[CandidateScoringResult]:
    """
    Score tous les referrals pour un job et les retourne triés par score décroissant.
    
    Args:
        job_opening_id: ID du job
        use_llm: Si True, utilise l'analyse LLM
        
    Returns:
        Liste de CandidateScoringResult triés par score décroissant
    """
    referrals = Referral.objects.select_related(
        'candidate', 'job_opening'
    ).filter(job_opening_id=job_opening_id)
    
    results = []
    for referral in referrals:
        try:
            result = compute_candidate_score(referral, use_llm=use_llm)
            results.append(result)
        except Exception as e:
            logger.error(f"Error scoring referral {referral.id}: {e}")
            continue
    
    # Sort by score descending
    results.sort(key=lambda x: x.score, reverse=True)
    
    return results
