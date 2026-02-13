"""
Types GraphQL pour le scoring des candidats.
"""

from ariadne_graphql_modules import ObjectType, gql, DeferredType, InputType, convert_case

from apps.referrals.models import CandidateScore, Referral
from apps.referrals.services.candidate_scoring import (
    compute_candidate_score,
    score_referrals_for_job,
    OPENAI_MODEL,
)
from common.errors import TropicalCornerError
from gql.auth import require_auth, require_tenant
from gql.node import encode_global_id, decode_global_id
from common.permissions import require_recruiter_or_admin


class ScoreBreakdownType(ObjectType):
    """Détail du breakdown du score."""
    
    __schema__ = gql(
        '''
        """
        Breakdown détaillé du score d'un candidat.
        """
        type ScoreBreakdown {
            "Score d'alignement expertise métier (0-30)"
            expertiseMatch: Int!
            "Score d'alignement niveau d'expérience (0-20)"
            experienceMatch: Int!
            "Score compétences relationnelles (0-15)"
            interpersonalSkillsMatch: Int!
            "Score compétences techniques (0-15)"
            technicalSkillsMatch: Int!
            "Score qualité du referral (0-20)"
            referralQuality: Int!
            "Score total règles (0-100)"
            ruleScore: Int!
            "Score analyse LLM (0-100)"
            llmScore: Int!
        }
        '''
    )
    __aliases__ = convert_case


class CandidateScoreType(ObjectType):
    """Score calculé pour un referral."""
    
    __schema__ = gql(
        '''
        """
        Score hybride (règles + LLM) pour un candidat recommandé.
        """
        type CandidateScore implements Node {
            id: ID!
            referral: Referral!
            
            "Score final hybride (0-100)"
            finalScore: Int!
            "Grade: A (80+), B (60-79), C (40-59), D (<40)"
            grade: String!
            
            "Score basé sur les règles (0-100)"
            ruleScore: Int!
            "Score basé sur l'analyse LLM (0-100)"
            llmScore: Int!
            
            "Breakdown détaillé du score"
            breakdown: ScoreBreakdown!
            
            "Points forts identifiés par le LLM"
            llmStrengths: [String!]!
            "Points faibles identifiés par le LLM"
            llmGaps: [String!]!
            "Résumé de l'analyse LLM"
            llmSummary: String!
            
            "Date du scoring"
            scoredAt: String!
            "Modèle LLM utilisé"
            llmModelUsed: String
        }
        '''
    )
    __aliases__ = convert_case
    
    __requires__ = [
        DeferredType('Node'),
        DeferredType('Referral'),
        ScoreBreakdownType,
    ]
    
    @staticmethod
    def resolve_id(score, info):
        return encode_global_id("CandidateScore", score.id)
    
    @staticmethod
    def resolve_breakdown(score, info):
        return {
            "expertise_match": score.expertise_match,
            "experience_match": score.experience_match,
            "interpersonal_skills_match": score.interpersonal_skills_match,
            "technical_skills_match": score.technical_skills_match,
            "referral_quality": score.referral_quality,
            "rule_score": score.rule_score,
            "llm_score": score.llm_score,
        }


class RankedReferralType(ObjectType):
    """Referral avec son score pour le ranking."""
    
    __schema__ = gql(
        '''
        """
        Referral avec son score pour affichage dans le ranking.
        """
        type RankedReferral {
            referral: Referral!
            score: CandidateScore
            rank: Int!
        }
        '''
    )
    __aliases__ = convert_case
    
    __requires__ = [
        DeferredType('Referral'),
        CandidateScoreType,
    ]


class ScoreReferralInput(InputType):
    """Input pour scorer un referral."""
    
    __schema__ = gql(
        """
        input ScoreReferralInput {
            "ID du referral à scorer"
            referralId: ID!
            "Utiliser l'analyse LLM (défaut: true)"
            useLlm: Boolean
        }
        """
    )


class ScoreJobReferralsInput(InputType):
    """Input pour scorer tous les referrals d'un job."""
    
    __schema__ = gql(
        """
        input ScoreJobReferralsInput {
            "ID du job opening"
            jobOpeningId: ID!
            "Utiliser l'analyse LLM (défaut: true)"
            useLlm: Boolean
        }
        """
    )


class ScoringQuery(ObjectType):
    """Queries pour le scoring."""
    
    __schema__ = gql(
        '''
        type Query {
            """
            Récupère le score d'un referral (le calcule s'il n'existe pas).
            """
            referralScore(referralId: ID!): CandidateScore
            
            """
            Récupère tous les referrals d'un job classés par score.
            """
            rankedReferrals(jobOpeningId: ID!, status: ReferralStatus): [RankedReferral!]!
        }
        '''
    )
    __aliases__ = convert_case
    
    __requires__ = [
        CandidateScoreType,
        RankedReferralType,
        DeferredType('ReferralStatus'),
    ]
    
    @staticmethod
    def resolve_referral_score(obj, info, referralId):
        """Récupère ou calcule le score d'un referral."""
        tenant_ctx = require_tenant(info)
        require_recruiter_or_admin(tenant_ctx)
        org = tenant_ctx.require_organization()
        
        _, db_id = decode_global_id(referralId)
        
        # Try to get existing score
        score = CandidateScore.objects.filter(
            referral_id=db_id,
            organization=org
        ).first()
        
        if score:
            return score
        
        # Score doesn't exist, need to compute it
        referral = Referral.objects.select_related(
            'candidate', 'job_opening'
        ).filter(id=db_id, organization=org).first()
        
        if not referral:
            raise TropicalCornerError("Referral not found", code="REFERRAL_NOT_FOUND")
        
        # Compute and save score
        result = compute_candidate_score(referral, use_llm=True)
        
        score = CandidateScore.objects.create(
            organization=org,
            referral=referral,
            final_score=result.score,
            rule_score=result.breakdown.rule_score,
            llm_score=result.breakdown.llm_score,
            grade=result.grade,
            expertise_match=result.breakdown.expertise_match,
            experience_match=result.breakdown.experience_match,
            interpersonal_skills_match=result.breakdown.interpersonal_skills_match,
            technical_skills_match=result.breakdown.technical_skills_match,
            referral_quality=result.breakdown.referral_quality,
            llm_strengths=result.breakdown.llm_strengths,
            llm_gaps=result.breakdown.llm_gaps,
            llm_summary=result.breakdown.llm_summary,
            llm_model_used=OPENAI_MODEL,
        )
        
        return score
    
    @staticmethod
    def resolve_ranked_referrals(obj, info, jobOpeningId, status=None):
        """Récupère tous les referrals d'un job classés par score."""
        tenant_ctx = require_tenant(info)
        require_recruiter_or_admin(tenant_ctx)
        org = tenant_ctx.require_organization()
        
        _, job_db_id = decode_global_id(jobOpeningId)
        
        # Get referrals for this job
        referrals_qs = Referral.objects.select_related(
            'candidate', 'job_opening'
        ).filter(
            job_opening_id=job_db_id,
            organization=org
        )
        
        if status:
            referrals_qs = referrals_qs.filter(status=status)
        
        referrals = list(referrals_qs)
        
        if not referrals:
            return []
        
        # Get existing scores
        referral_ids = [r.id for r in referrals]
        existing_scores = {
            s.referral_id: s 
            for s in CandidateScore.objects.filter(referral_id__in=referral_ids)
        }
        
        # Build results with scores
        results = []
        for referral in referrals:
            score = existing_scores.get(referral.id)
            results.append({
                "referral": referral,
                "score": score,
                "final_score": score.final_score if score else 0,
            })
        
        # Sort by score descending
        results.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Add rank
        ranked_results = []
        for idx, result in enumerate(results, start=1):
            ranked_results.append({
                "referral": result["referral"],
                "score": result["score"],
                "rank": idx,
            })
        
        return ranked_results


class ScoringMutation(ObjectType):
    """Mutations pour le scoring."""
    
    __schema__ = gql(
        '''
        type Mutation {
            """
            Score un referral spécifique.
            """
            scoreReferral(input: ScoreReferralInput!): CandidateScore!
            
            """
            Score tous les referrals d'un job.
            """
            scoreJobReferrals(input: ScoreJobReferralsInput!): [CandidateScore!]!
            
            """
            Recalcule le score d'un referral (force le recalcul même si déjà scoré).
            """
            rescoreReferral(input: ScoreReferralInput!): CandidateScore!
        }
        '''
    )
    __aliases__ = convert_case
    
    __requires__ = [
        CandidateScoreType,
        ScoreReferralInput,
        ScoreJobReferralsInput,
    ]
    
    @staticmethod
    def resolve_score_referral(obj, info, input):
        """Score un referral spécifique."""
        tenant_ctx = require_tenant(info)
        require_recruiter_or_admin(tenant_ctx)
        org = tenant_ctx.require_organization()
        
        _, referral_db_id = decode_global_id(input["referralId"])
        use_llm = input.get("useLlm", True)
        
        referral = Referral.objects.select_related(
            'candidate', 'job_opening'
        ).filter(id=referral_db_id, organization=org).first()
        
        if not referral:
            raise TropicalCornerError("Referral not found", code="REFERRAL_NOT_FOUND")
        
        # Check if already scored
        existing_score = CandidateScore.objects.filter(referral=referral).first()
        if existing_score:
            return existing_score
        
        # Compute score
        result = compute_candidate_score(referral, use_llm=use_llm)
        
        score = CandidateScore.objects.create(
            organization=org,
            referral=referral,
            final_score=result.score,
            rule_score=result.breakdown.rule_score,
            llm_score=result.breakdown.llm_score,
            grade=result.grade,
            expertise_match=result.breakdown.expertise_match,
            experience_match=result.breakdown.experience_match,
            interpersonal_skills_match=result.breakdown.interpersonal_skills_match,
            technical_skills_match=result.breakdown.technical_skills_match,
            referral_quality=result.breakdown.referral_quality,
            llm_strengths=result.breakdown.llm_strengths,
            llm_gaps=result.breakdown.llm_gaps,
            llm_summary=result.breakdown.llm_summary,
            llm_model_used=OPENAI_MODEL if use_llm else "",
        )
        
        return score
    
    @staticmethod
    def resolve_score_job_referrals(obj, info, input):
        """Score tous les referrals d'un job."""
        tenant_ctx = require_tenant(info)
        require_recruiter_or_admin(tenant_ctx)
        org = tenant_ctx.require_organization()
        
        _, job_db_id = decode_global_id(input["jobOpeningId"])
        use_llm = input.get("useLlm", True)
        
        referrals = Referral.objects.select_related(
            'candidate', 'job_opening'
        ).filter(job_opening_id=job_db_id, organization=org)
        
        scores = []
        for referral in referrals:
            # Check if already scored
            existing_score = CandidateScore.objects.filter(referral=referral).first()
            if existing_score:
                scores.append(existing_score)
                continue
            
            # Compute score
            result = compute_candidate_score(referral, use_llm=use_llm)
            
            score = CandidateScore.objects.create(
                organization=org,
                referral=referral,
                final_score=result.score,
                rule_score=result.breakdown.rule_score,
                llm_score=result.breakdown.llm_score,
                grade=result.grade,
                expertise_match=result.breakdown.expertise_match,
                experience_match=result.breakdown.experience_match,
                interpersonal_skills_match=result.breakdown.interpersonal_skills_match,
                technical_skills_match=result.breakdown.technical_skills_match,
                referral_quality=result.breakdown.referral_quality,
                llm_strengths=result.breakdown.llm_strengths,
                llm_gaps=result.breakdown.llm_gaps,
                llm_summary=result.breakdown.llm_summary,
                llm_model_used=OPENAI_MODEL if use_llm else "",
            )
            scores.append(score)
        
        # Return sorted by score
        return sorted(scores, key=lambda s: s.final_score, reverse=True)
    
    @staticmethod
    def resolve_rescore_referral(obj, info, input):
        """Recalcule le score d'un referral (force le recalcul)."""
        tenant_ctx = require_tenant(info)
        require_recruiter_or_admin(tenant_ctx)
        org = tenant_ctx.require_organization()
        
        _, referral_db_id = decode_global_id(input["referralId"])
        use_llm = input.get("useLlm", True)
        
        referral = Referral.objects.select_related(
            'candidate', 'job_opening'
        ).filter(id=referral_db_id, organization=org).first()
        
        if not referral:
            raise TropicalCornerError("Referral not found", code="REFERRAL_NOT_FOUND")
        
        # Delete existing score if any
        CandidateScore.objects.filter(referral=referral).delete()
        
        # Compute new score
        result = compute_candidate_score(referral, use_llm=use_llm)
        
        score = CandidateScore.objects.create(
            organization=org,
            referral=referral,
            final_score=result.score,
            rule_score=result.breakdown.rule_score,
            llm_score=result.breakdown.llm_score,
            grade=result.grade,
            expertise_match=result.breakdown.expertise_match,
            experience_match=result.breakdown.experience_match,
            interpersonal_skills_match=result.breakdown.interpersonal_skills_match,
            technical_skills_match=result.breakdown.technical_skills_match,
            referral_quality=result.breakdown.referral_quality,
            llm_strengths=result.breakdown.llm_strengths,
            llm_gaps=result.breakdown.llm_gaps,
            llm_summary=result.breakdown.llm_summary,
            llm_model_used=OPENAI_MODEL if use_llm else "",
        )
        
        return score


types = [
    ScoreBreakdownType,
    CandidateScoreType,
    RankedReferralType,
    ScoreReferralInput,
    ScoreJobReferralsInput,
    ScoringQuery,
    ScoringMutation,
]
