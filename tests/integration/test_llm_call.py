"""
Test d'intégration réel : appel à l'API OpenAI via call_openai_api.

Lance avec :
    docker compose exec backend pytest tests/integration/test_llm_call.py -v

Ignoré automatiquement si OPENAI_API_KEY n'est pas configuré.
"""

import os
import pytest

# call_openai_api n'a aucune dépendance Django — import direct possible
from apps.referrals.services.candidate_scoring import call_openai_api, build_llm_prompt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_PROMPT = """Tu es un expert en recrutement exécutif.

Évalue l'alignement entre ce candidat fictif et ce poste fictif sur 100.

## POSTE
- Titre: Directeur Financier
- Expertise: Finance
- Niveau d'expérience: C-Level (18-25 ans)

## CANDIDAT
- Nom: Jean Dupont
- Années d'expérience: 20
- Expertise: Finance
- Compétences techniques: Excel, SAP, Consolidation
- Compétences relationnelles: Leadership, Communication

## RECOMMANDATION
- Type de relation: Ancien collègue (même entreprise)
- Motivation: Jean a dirigé notre équipe finance pendant 5 ans avec excellence.

Réponds UNIQUEMENT avec un JSON valide (sans markdown, sans ```):
{"score": <0-100>, "strengths": ["point fort 1"], "gaps": ["point faible 1"], "summary": "Résumé court"}
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY non configuré — test LLM ignoré",
)
def test_call_openai_api_returns_valid_structure():
    """L'API OpenAI répond avec le JSON attendu : score, strengths, gaps, summary."""
    result = call_openai_api(MINIMAL_PROMPT)

    assert result is not None, "L'API a retourné None (erreur réseau ou rate-limit)"

    assert "score" in result, "Clé 'score' manquante dans la réponse"
    assert "strengths" in result, "Clé 'strengths' manquante"
    assert "gaps" in result, "Clé 'gaps' manquante"
    assert "summary" in result, "Clé 'summary' manquante"


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY non configuré — test LLM ignoré",
)
def test_call_openai_api_score_in_range():
    """Le score retourné est un entier entre 0 et 100."""
    result = call_openai_api(MINIMAL_PROMPT)
    assert result is not None

    score = result["score"]
    assert isinstance(score, (int, float)), f"Score non numérique : {score!r}"
    assert 0 <= score <= 100, f"Score hors plage [0, 100] : {score}"


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY non configuré — test LLM ignoré",
)
def test_call_openai_api_lists_are_lists():
    """strengths et gaps doivent être des listes."""
    result = call_openai_api(MINIMAL_PROMPT)
    assert result is not None

    assert isinstance(result["strengths"], list), "'strengths' devrait être une liste"
    assert isinstance(result["gaps"], list), "'gaps' devrait être une liste"
    assert isinstance(result["summary"], str), "'summary' devrait être une chaîne"


def test_call_openai_api_returns_none_without_key(monkeypatch):
    """Sans clé API, call_openai_api retourne None sans lever d'exception."""
    monkeypatch.setattr(
        "apps.referrals.services.candidate_scoring.OPENAI_API_KEY", ""
    )
    result = call_openai_api(MINIMAL_PROMPT)
    assert result is None
