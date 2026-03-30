import re

from ariadne_graphql_modules import ObjectType, gql, DeferredType, InputType, convert_case

from django.utils import timezone


def parse_reward_points(display_str: str) -> int:
    """Extract an integer number of points from a reward display string."""
    if not display_str:
        return 0
    cleaned = re.sub(r"[^0-9]", "", display_str)
    if not cleaned:
        return 0
    try:
        return int(cleaned)
    except (ValueError, TypeError):
        return 0


def format_points_display(amount: int) -> str:
    return f"{amount:,} Points".replace(",", "'")

from apps.jobs.models import JobOpening
from apps.referrals.models import Candidate, Referral, ReferralStatusEvent, RewardOutcome, CandidateConsentToken
from apps.referrals.services import scrape_linkedin_profile
from common.errors import TropicalCornerError
from common.mail_service import send_candidate_consent_email
from gql.auth import require_auth
from gql.node import encode_global_id, decode_global_id


# Allowed status transitions
ALLOWED_TRANSITIONS = {
    "PENDING_CONSENT": {"SUBMITTED", "REJECTED"},   # confirmed → SUBMITTED, declined → REJECTED
    "SUBMITTED": {"REVIEWED", "REJECTED"},
    "REVIEWED": {"ACCEPTED", "REJECTED"},
    "ACCEPTED": {"HIRED", "REJECTED"},
    "HIRED": set(),  # Terminal
    "REJECTED": set(),  # Terminal
}


class CandidateType(ObjectType):
    """ """

    __schema__ = gql(
        '''
        """
           Represents a candidate for a job opening.
        """
        type Candidate implements Node {
            id: ID!
            organization: Organization!
            fullName: String!
            email: String
            linkedinUrl: String
            yearsExperience: Int!
            expertiseDomain: String!
            searchCriteria: String!
            technicalSkills: [String!]!
            interpersonalSkills: [String!]!
            linkedinHeadline: String
            linkedinSummary: String
            linkedinExperience: GenericScalar
            linkedinEducation: GenericScalar
            linkedinSkills: GenericScalar
            linkedinScrapedAt: String
            consentConfirmed: Boolean!
            createdAt: String!
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        DeferredType('Node'),
        DeferredType('Organization'),
        DeferredType('GenericScalar'),
        DeferredType('ExpertiseDomain'),
    ]

    @staticmethod
    def resolve_id(candidate, info):
        return encode_global_id("Candidate", candidate.id)


class ReferralType(ObjectType):
    """ """

    __schema__ = gql(
        '''
        """
           Represents a referral for a job opening.
        """
        type Referral implements Node {
            id: ID!
            organization: Organization!
            jobOpening: JobOpening!
            candidate: Candidate!
            referrer: User!
            relationshipContext: String!
            relationshipType: RelationshipType!
            profileMotivation: String
            supportingMaterials: [String!]!
            status: ReferralStatus!
            statusHistory: [ReferralStatusEvent!]!
            score: CandidateScore
            createdAt: String!
            updatedAt: String!
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        DeferredType('Node'),
        DeferredType('User'),
        DeferredType('Organization'),
        DeferredType('JobOpening'),
        DeferredType('Candidate'),
        DeferredType('OrganizationMember'),
        DeferredType('CandidateScore'),
        DeferredType('ReferralStatus'),
        DeferredType('RelationshipType'),
        DeferredType('ReferralStatusEvent'),
    ]

    @staticmethod
    def resolve_id(referral, info):
        return encode_global_id("Referral", referral.id)

    @staticmethod
    def resolve_status_history(referral, info):
        """Return the status history events for this referral."""
        return ReferralStatusEvent.objects.filter(referral_id=referral.id).order_by("created_at")

    @staticmethod
    def resolve_score(referral, info):
        """Return the score for this referral if it exists."""
        from apps.referrals.models import CandidateScore
        try:
            return CandidateScore.objects.get(referral_id=referral.id)
        except CandidateScore.DoesNotExist:
            return None


class ReferralStatusEventType(ObjectType):
    """ """

    __schema__ = gql(
        '''
        """
           Represents a status change event for a referral.
        """
        type ReferralStatusEvent implements Node {
            id: ID!
            referral: Referral!
            fromStatus: ReferralStatus
            toStatus: ReferralStatus!
            changedBy: OrganizationMember!
            reasonCategory: String
            reasonNote: String
            createdAt: String!
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        DeferredType('Node'),
        DeferredType('Referral'),
        DeferredType('ReferralStatus'),
        DeferredType('OrganizationMember'),
    ]

    @staticmethod
    def resolve_id(event, info):
        return encode_global_id("ReferralStatusEvent", event.id)


class RewardOutcomeType(ObjectType):
    """ """

    __schema__ = gql(
        '''
        """
           Represents a reward outcome for a referral.
        """
        type RewardOutcome implements Node {
            id: ID!
            referral: Referral!
            rewardPoints: Int!
            rewardDisplaySnapshot: String!
            status: RewardStatus!
            createdAt: String!
            updatedAt: String!
        }
        '''
    )

    __aliases__ = convert_case

    __requires__ = [
        DeferredType('Node'),
        DeferredType('Referral'),
        DeferredType('RewardStatus'),
    ]

    @staticmethod
    def resolve_id(reward, info):
        return encode_global_id("RewardOutcome", reward.id)


class RewardType(ObjectType):
    __schema__ = gql(
        '''
        type Reward {
            id: ID!
            rewardDisplay: String!
            rewardAmount: Int!
            status: String!
            earnedAt: String
            paidAt: String
            referral: Referral!
        }
    '''
    )

    __requires__ = [DeferredType("Referral")]


class MyRewardsType(ObjectType):
    __schema__ = gql(
        '''
        type MyRewards {
            totalEarned: String!
            totalEarnedAmount: Int!
            availableBalance: String!
            availableBalanceAmount: Int!
            pendingBalance: String!
            pendingBalanceAmount: Int!
            rewards: [Reward!]!
        }
    '''
    )

    __requires__ = [DeferredType("Reward")]


class CashOutResponseType(ObjectType):
    __schema__ = gql(
        '''
        type CashOutResponse {
            id: ID!
            status: String!
            message: String!
        }
    '''
    )


class SubmitReferralInput(InputType):
    __schema__ = gql(
        """
        input SubmitReferralInput {
            jobOpeningId: ID!
            candidateFullName: String!
            candidateEmail: String
            linkedinUrl: String
            yearsExperience: Int!
            expertiseDomain: String!
            searchCriteria: String!
            technicalSkills: [String!]!
            interpersonalSkills: [String!]!
            consentConfirmed: Boolean!
            relationshipContext: String!
            relationshipType: RelationshipType!
            profileMotivation: String!
            supportingMaterials: [String!]!
        }
        """
    )

    __requires__ = [
        DeferredType("ExpertiseDomain"),
        DeferredType("RelationshipType"),
    ]


class UpdateReferralStatusInput(InputType):
    __schema__ = gql(
        """
        input UpdateReferralStatusInput {
            referralId: ID!
            toStatus: ReferralStatus!
            reasonCategory: String
            reasonNote: String
        }
        """
    )

    __requires__ = [DeferredType("ReferralStatus")]


class CashOutInput(InputType):
    __schema__ = gql(
        """
        input CashOutInput {
            amount: Int!
            paymentMethod: String!
            paymentDetails: GenericScalar
            notes: String
        }
        """
    )

    __requires__ = [DeferredType("GenericScalar")]


class Query(ObjectType):
    __schema__ = gql(
        '''
        type Query {
            referral(id: ID!): Referral
            referrals(jobId: ID, status: ReferralStatus, first: Int = 20, after: String): [Referral!]!
            myReferrals(status: ReferralStatus, first: Int = 20, after: String): [Referral!]!
            myRewards: MyRewards!
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        ReferralType,
        DeferredType('ReferralStatus'),
        MyRewardsType,
    ]

    @staticmethod
    def resolve_referral(obj, info, id):
        """Get a single referral by ID. Accessible by the referrer or a recruiter of the org."""
        user = info.context.get("request").user
        if user is None or not user.is_authenticated:
            return None

        try:
            _, db_id = decode_global_id(id)
        except Exception:
            return None

        try:
            referral = Referral.objects.select_related(
                'candidate', 'job_opening', 'referrer'
            ).get(id=db_id)
            if referral.status == "SUBMITTED":
                referral.status="REVIEWED"
                referral.save()
        except Referral.DoesNotExist:
            return None

        # Security: referrer can see their own, recruiter can see their org's
        if referral.referrer_id == user.id:
            return referral
        if user.is_recruiter and user.active_organization_id and \
           referral.job_opening.organization_id == user.active_organization_id:
            return referral

        return None

    @staticmethod
    def resolve_referrals(obj, info, jobId=None, status=None, first=20, after=None):
        """List referrals in the active organization (filtered by role)."""
        user = info.context.get("user")
        if user is None:
            return []

        # If recruiter and jobId provided, get referrals for that job
        if jobId:
            # Decode the global ID to get the database ID
            try:
                _, db_id = decode_global_id(jobId)
            except Exception:
                return []
            
            # Security: verify user is a recruiter and job belongs to their org
            if user.is_recruiter and user.active_organization_id:
                qs = Referral.objects.select_related(
                    'candidate', 'job_opening', 'referrer'
                ).filter(
                    job_opening_id=db_id,
                    job_opening__organization_id=user.active_organization_id
                ).exclude(status=Referral.Status.PENDING_CONSENT)
            else:
                # Non-recruiter cannot access job applications
                return []
        else:
            # Otherwise, get referrals created by the user
            qs = Referral.objects.select_related(
                'candidate', 'job_opening', 'referrer'
            ).filter(referrer=user)

        if status:
            qs = qs.filter(status=status)

        qs = qs.order_by("-created_at")

        if after:
            try:
                _, db_id = decode_global_id(after)
                qs = qs.filter(id__lt=db_id)
            except Exception:
                pass

        return list(qs[:first])

    @staticmethod
    def resolve_my_referrals(obj, info, status=None, first=20, after=None):
        """List referrals for the recruiter's organization jobs, or user's own referrals for referrers."""
        user = info.context.get("request").user
        print(info.context)
        if user is None:
            return []

        # If recruiter, show referrals on their org's jobs (excluding pending consent)
        if user.is_recruiter and user.active_organization_id:
            qs = Referral.objects.select_related(
                'candidate', 'job_opening', 'referrer'
            ).filter(
                job_opening__organization_id=user.active_organization_id
            ).exclude(status=Referral.Status.PENDING_CONSENT)
        # If referrer, show only their own referrals (including PENDING_CONSENT so they see the status)
        else:
            qs = Referral.objects.filter(referrer=user)

        if status:
            qs = qs.filter(status=status)

        qs = qs.order_by("-created_at")

        if after:
            try:
                _, db_id = decode_global_id(after)
                qs = qs.filter(id__lt=db_id)
            except Exception:
                pass

        return list(qs[:first])

    @staticmethod
    def resolve_my_rewards(obj, info):
        """Get rewards summary for the authenticated user."""
        user = require_auth(info)

        # Get all reward outcomes for the user's referrals
        rewards = RewardOutcome.objects.select_related(
            'referral__candidate',
            'referral__job_opening'
        ).filter(referral__referrer=user)

        # Calculate totals
        total_earned = 0
        available_balance = 0
        pending_balance = 0

        for reward in rewards:
            amount = reward.reward_points or parse_reward_points(reward.reward_display_snapshot)

            total_earned += amount

            if reward.status == RewardOutcome.Status.EARNED:
                available_balance += amount
            elif reward.status == RewardOutcome.Status.PENDING:
                pending_balance += amount

        # Format rewards for response
        rewards_list = []
        for reward in rewards:
            amount = reward.reward_points or parse_reward_points(reward.reward_display_snapshot)

            rewards_list.append({
                "id": reward.id,
                "rewardDisplay": format_points_display(amount),
                "rewardAmount": amount,
                "status": reward.status.upper(),
                "earnedAt": reward.created_at.isoformat(),
                "paidAt": reward.updated_at.isoformat() if reward.status == RewardOutcome.Status.PAID else None,
                "referral": reward.referral,
            })

        return {
            "totalEarned": format_points_display(total_earned),
            "totalEarnedAmount": total_earned,
            "availableBalance": format_points_display(available_balance),
            "availableBalanceAmount": available_balance,
            "pendingBalance": format_points_display(pending_balance),
            "pendingBalanceAmount": pending_balance,
            "rewards": rewards_list,
        }


class Mutation(ObjectType):
    __schema__ = gql(
        '''
        type Mutation {
            submitReferral(input: SubmitReferralInput!): Referral !
            updateReferralStatus(input: UpdateReferralStatusInput!): Referral!
            requestCashOut(input: CashOutInput!): CashOutResponse!
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        ReferralType,
        SubmitReferralInput,
        UpdateReferralStatusInput,
        CashOutInput,
        CashOutResponseType,
    ]
    
    @staticmethod
    def resolve_submit_referral(obj, info, input):
        """Submit a candidate referral."""
        user = info.context.get("request").user

        _, job_db_id = decode_global_id(input["jobOpeningId"])

        job = JobOpening.objects.filter(id=job_db_id).first()
        if job is None:
            raise TropicalCornerError("Job opening not found", code="JOB_NOT_FOUND")

        if job.status != JobOpening.Status.OPEN:
            raise TropicalCornerError("Job is not open for referrals", code="JOB_CLOSED")

        # Validation des critères de recherche
        search_criteria = input.get("searchCriteria", "").strip()
        # if len(search_criteria) != 3:
        #     raise TropicalCornerError("Exactly 3 search criteria are required", code="VALIDATION_ERROR")

        # Validation des compétences (au moins 1 de chaque)
        technical_skills = input.get("technicalSkills", [])
        interpersonal_skills = input.get("interpersonalSkills", [])

        if not technical_skills or len(technical_skills) == 0:
            raise TropicalCornerError("At least one technical skill is required", code="VALIDATION_ERROR")

        if not interpersonal_skills or len(interpersonal_skills) == 0:
            raise TropicalCornerError("At least one interpersonal skill is required", code="VALIDATION_ERROR")

        candidate_email = input.get("candidateEmail", "").strip() or None

        # If candidate has an email → needs consent first (PENDING_CONSENT)
        # If no email → auto-confirm consent (legacy behaviour)
        needs_consent = bool(candidate_email)
        initial_status = Referral.Status.PENDING_CONSENT if needs_consent else Referral.Status.SUBMITTED

        # Create candidate
        candidate = Candidate.objects.create(
            organization=job.organization,
            full_name=input["candidateFullName"].strip(),
            email=candidate_email,
            linkedin_url=input.get("linkedinUrl", "").strip() or None,
            years_experience=input["yearsExperience"],
            expertise_domain=input["expertiseDomain"],
            search_criteria=search_criteria,
            technical_skills=technical_skills,
            interpersonal_skills=interpersonal_skills,
            consent_confirmed=not needs_consent and input["consentConfirmed"],
            consent_confirmed_at=timezone.now() if (not needs_consent and input["consentConfirmed"]) else None,
        )

        # Scrape LinkedIn profile si une URL est fournie
        if candidate.linkedin_url:
            try:
                profile_data = scrape_linkedin_profile(candidate.linkedin_url)
                candidate.linkedin_headline = profile_data.get("headline")
                candidate.linkedin_summary = profile_data.get("summary")
                candidate.linkedin_experience = profile_data.get("experience")
                candidate.linkedin_education = profile_data.get("education")
                candidate.linkedin_skills = profile_data.get("skills")
                candidate.linkedin_scraped_at = timezone.now()
                candidate.save()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to scrape LinkedIn profile: {e}")

        referral = Referral.objects.create(
            organization=job.organization,
            job_opening=job,
            candidate=candidate,
            referrer=user,
            relationship_context=input["relationshipContext"].strip(),
            relationship_type=input["relationshipType"],
            profile_motivation=input["profileMotivation"].strip(),
            supporting_materials=input.get("supportingMaterials", []),
            status=initial_status,
        )

        # Create initial status event
        ReferralStatusEvent.objects.create(
            organization=job.organization,
            referral=referral,
            from_status=None,
            to_status=initial_status,
            changed_by=None,
        )

        # Compute score immediately after referral creation
        try:
            from gql.types.scoring import create_score_for_referral
            referral_with_relations = Referral.objects.select_related(
                'candidate', 'job_opening'
            ).get(id=referral.id)
            create_score_for_referral(referral_with_relations, job.organization, use_llm=True)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to compute score for referral {referral.id}: {e}")

        # Send consent email if candidate has an email
        if needs_consent:
            consent_token = CandidateConsentToken.objects.create(referral=referral)
            contract_type_labels = []
            for contract_type in (job.contract_types or []):
                try:
                    contract_type_labels.append(JobOpening.ContractType(contract_type).label)
                except ValueError:
                    contract_type_labels.append(contract_type)

            job_description_preview = (job.description or "").strip()
            if len(job_description_preview) > 280:
                job_description_preview = f"{job_description_preview[:277].rstrip()}..."

            try:
                job_reward_points = job.reward_points or parse_reward_points(job.reward_display)
                send_candidate_consent_email(
                    candidate_name=candidate.full_name,
                    candidate_email=candidate.email,
                    job_title=job.title,
                    referrer_name=user.display_name or user.email,
                    organization_name=job.organization.name,
                    consent_token=str(consent_token.token),
                    referrer_email=user.email,
                    referrer_experience_years=user.years_of_experience,
                    job_location=job.location_display,
                    job_contract_types=contract_type_labels,
                    job_experience_level=job.get_experience_level_display() if job.experience_level else None,
                    job_reward=format_points_display(job_reward_points),
                    job_description=job_description_preview,
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send consent email: {e}")

        return referral

    @staticmethod
    def resolve_update_referral_status(obj, info, input):
        """Update referral status (recruiter only)."""

        user = info.context.get("request").user
        _, referral_db_id = decode_global_id(input["referralId"])
        to_status = input["toStatus"]

        referral = Referral.objects.filter(
            id=referral_db_id
        ).first()
        if referral is None:
            raise TropicalCornerError("Referral not found", code="REFERRAL_NOT_FOUND")

        from_status = referral.status
        allowed = ALLOWED_TRANSITIONS.get(from_status, set())

        if to_status.upper() not in allowed:
            raise TropicalCornerError(
                f"Cannot transition from {from_status} to {to_status}",
                code="INVALID_TRANSITION",
            )

        # Update referral
        referral.status = to_status.upper()
        referral.save(update_fields=["status", "updated_at"])

        # Create status event
        ReferralStatusEvent.objects.create(
            organization=referral.organization,
            referral=referral,
            from_status=from_status,
            to_status=to_status,
            reason_category=input.get("reasonCategory"),
            reason_note=input.get("reasonNote"),
        )

        # Create reward outcome on hired
        if to_status == Referral.Status.HIRED:
            RewardOutcome.objects.update_or_create(
                referral=referral,
                defaults={
                    "organization": referral.organization,
                    "reward_points": referral.job_opening.reward_points,
                    "reward_display_snapshot": format_points_display(referral.job_opening.reward_points),
                    "status": RewardOutcome.Status.EARNED,
                },
            )

        return referral

    @staticmethod
    def resolve_request_cash_out(obj, info, input):
        """Request a cash out for earned rewards."""
        from apps.referrals.models_cashout import CashOutRequest

        user = require_auth(info)

        # Validate amount
        amount = input.get("amount", 0)
        if amount < 50:
            raise TropicalCornerError("Minimum cash out amount is 50 Points", code="AMOUNT_TOO_LOW")

        # Check available balance
        rewards = RewardOutcome.objects.filter(
            referral__referrer=user,
            status=RewardOutcome.Status.EARNED
        )

        available_balance = 0
        for reward in rewards:
            available_balance += reward.reward_points or parse_reward_points(reward.reward_display_snapshot)

        if amount > available_balance:
            raise TropicalCornerError(
                f"Insufficient balance. Available: {available_balance} Points",
                code="INSUFFICIENT_BALANCE"
            )

        # Create cash out request
        cash_out = CashOutRequest.objects.create(
            user=user,
            amount=amount,
            payment_method=input.get("paymentMethod"),
            payment_details=input.get("paymentDetails", {}),
            notes=input.get("notes", ""),
            status=CashOutRequest.Status.PENDING
        )

        # TODO: In the future, integrate with payment providers
        # TODO: Mark rewards as PAID when cash out is completed

        return {
            "id": cash_out.id,
            "status": "PENDING",
            "message": "Cash out request submitted successfully. You will receive an email confirmation within 3-5 business days."
        }


types = [ 
    CandidateType,
    ReferralType,
    ReferralStatusEventType,
    RewardOutcomeType,
    RewardType,
    MyRewardsType,
    CashOutResponseType,
    SubmitReferralInput,
    UpdateReferralStatusInput,
    CashOutInput,
    Query,
    Mutation,
]