from ariadne_graphql_modules import ObjectType, gql, DeferredType, InputType, convert_case

from django.utils import timezone

from apps.jobs.models import JobOpening
from apps.referrals.models import Candidate, Referral, ReferralStatusEvent, RewardOutcome
from apps.referrals.services import scrape_linkedin_profile
from common.errors import TropicalCornerError
from gql.auth import require_auth
from gql.node import encode_global_id, decode_global_id


# Allowed status transitions
ALLOWED_TRANSITIONS = {
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
            expertiseDomain: ExpertiseDomain!
            searchCriteria: [String!]!
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
            rewardAmount: Float!
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
            totalEarnedAmount: Float!
            availableBalance: String!
            availableBalanceAmount: Float!
            pendingBalance: String!
            pendingBalanceAmount: Float!
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
            expertiseDomain: ExpertiseDomain!
            searchCriteria: [String!]!
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
            amount: Float!
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
                )
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

        # If recruiter, show referrals on their org's jobs
        if user.is_recruiter and user.active_organization_id:
            qs = Referral.objects.select_related(
                'candidate', 'job_opening', 'referrer'
            ).filter(job_opening__organization_id=user.active_organization_id)
        # If referrer, show only their own referrals
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
            # Extract amount from reward_display_snapshot (e.g., "€1,500" -> 1500)
            amount_str = reward.reward_display_snapshot.replace('€', '').replace(',', '').strip()
            try:
                amount = float(amount_str)
            except ValueError:
                amount = 0

            total_earned += amount

            if reward.status == RewardOutcome.Status.EARNED:
                available_balance += amount
            elif reward.status == RewardOutcome.Status.PENDING:
                pending_balance += amount

        # Format rewards for response
        rewards_list = []
        for reward in rewards:
            amount_str = reward.reward_display_snapshot.replace('€', '').replace(',', '').strip()
            try:
                amount = float(amount_str)
            except ValueError:
                amount = 0

            rewards_list.append({
                "id": reward.id,
                "rewardDisplay": reward.reward_display_snapshot,
                "rewardAmount": amount,
                "status": reward.status.upper(),
                "earnedAt": reward.created_at.isoformat(),
                "paidAt": reward.updated_at.isoformat() if reward.status == RewardOutcome.Status.PAID else None,
                "referral": reward.referral,
            })

        return {
            "totalEarned": f"€{total_earned:,.0f}",
            "totalEarnedAmount": total_earned,
            "availableBalance": f"€{available_balance:,.0f}",
            "availableBalanceAmount": available_balance,
            "pendingBalance": f"€{pending_balance:,.0f}",
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
        # tenant_ctx = require_tenant(info)
        # membership = require_referrer_or_above(tenant_ctx)
        user = info.context.get("request").user

        _, job_db_id = decode_global_id(input["jobOpeningId"])

        job = JobOpening.objects.filter(id=job_db_id).first()
        if job is None:
            raise TropicalCornerError("Job opening not found", code="JOB_NOT_FOUND")

        if job.status != JobOpening.Status.OPEN:
            raise TropicalCornerError("Job is not open for referrals", code="JOB_CLOSED")

        # Validation des critères de recherche (3 requis)
        search_criteria = input.get("searchCriteria", [])
        if len(search_criteria) != 3:
            raise TropicalCornerError("Exactly 3 search criteria are required", code="VALIDATION_ERROR")

        # Validation des compétences (au moins 1 de chaque)
        technical_skills = input.get("technicalSkills", [])
        interpersonal_skills = input.get("interpersonalSkills", [])

        if not technical_skills or len(technical_skills) == 0:
            raise TropicalCornerError("At least one technical skill is required", code="VALIDATION_ERROR")

        if not interpersonal_skills or len(interpersonal_skills) == 0:
            raise TropicalCornerError("At least one interpersonal skill is required", code="VALIDATION_ERROR")

        # Create or find candidate
        candidate = Candidate.objects.create(
            organization=job.organization,
            full_name=input["candidateFullName"].strip(),
            email=input.get("candidateEmail", "").strip() or None,
            linkedin_url=input.get("linkedinUrl", "").strip() or None,
            years_experience=input["yearsExperience"],
            expertise_domain=input["expertiseDomain"],
            search_criteria=search_criteria,
            technical_skills=technical_skills,
            interpersonal_skills=interpersonal_skills,
            consent_confirmed=input["consentConfirmed"],
            consent_confirmed_at=timezone.now() if input["consentConfirmed"] else None,
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
                # Log l'erreur mais ne bloque pas la création du referral
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
            status=Referral.Status.SUBMITTED,
        )
        # membership = require_referrer_or_above(job.organization)
        # Create initial status event
        ReferralStatusEvent.objects.create(
            organization=job.organization,
            referral=referral,
            from_status=None,
            to_status=Referral.Status.SUBMITTED,
            changed_by=None,
        )

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
                    "reward_display_snapshot": referral.job_opening.reward_display,
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
            raise TropicalCornerError("Minimum cash out amount is €50", code="AMOUNT_TOO_LOW")

        # Check available balance
        rewards = RewardOutcome.objects.filter(
            referral__referrer=user,
            status=RewardOutcome.Status.EARNED
        )

        available_balance = 0
        for reward in rewards:
            amount_str = reward.reward_display_snapshot.replace('€', '').replace(',', '').strip()
            try:
                available_balance += float(amount_str)
            except ValueError:
                pass

        if amount > available_balance:
            raise TropicalCornerError(
                f"Insufficient balance. Available: €{available_balance}",
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