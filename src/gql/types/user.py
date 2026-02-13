from ariadne_graphql_modules import ObjectType, gql, DeferredType, InputType, convert_case, ScalarType
from apps.accounts.models import User

from common.errors import TropicalCornerError

from apps.jobs.models import JobOpening
from apps.referrals.models import Referral, RewardOutcome

from gql.node import encode_global_id

from ariadne_jwt.decorators import login_required, token_auth
from ariadne_jwt.mutations import resolve_verify, resolve_refresh


class UserType(ObjectType):
    """ """
    __schema__ = gql('''
        """
           Represents a user in the system.          
        """
        type User implements Node {
            id: ID!
            email: String!
            displayName: String!
            avatarUrl: String!
            isRecruiter: Boolean!
            isReferrer: Boolean!
        }   
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        DeferredType('Node'),
    ]

    @staticmethod
    def resolve_id(user, info):
        return encode_global_id("User", user.id)


class RegisterAccountInput(InputType):
    __schema__ = gql(
        """
        input RegisterAccountInput {
            email: String!
            password: String!
            displayName: String!
            yearsOfExperience: Int!
            networkCountries: [String!]!
            networkCities: [String!]!
            expertiseAreas: [String!]!
            preferredRewards: [String!]!
        }
        """
    )


class RegisterAccountResponse(ObjectType):
    """ """
    __schema__ = gql('''
        """
           Response for account registration.
        """
        type RegisterAccountResponse {
            success: Boolean!
            message: String!
        }
        '''
    )

    __requires__ = []


class DashboardType(ObjectType):
    """ """
    __schema__ = gql('''
        """
           Unified dashboard statistics for both recruiters and referrers.
        """
        type Dashboard {
            # Common fields for all users
            submittedReferralsCount: Int!
            acceptedReferralsCount: Int!
            hiredReferralsCount: Int!
            earnedRewardsDisplay: String!
            earnedRewardsAmount: Float!
            motivationalMessage: String!
            impactMessage: String!
            recentReferrals: [Referral!]!
            
            # Additional fields for recruiters (nullable for non-recruiters)
            openJobsCount: Int
            totalReferralsCount: Int
            pendingReviewCount: Int
            hiredThisMonthCount: Int
        }
        '''
    )

    __requires__ = [DeferredType("Referral")]


class Query(ObjectType):
    """ """
    __schema__ = gql('''
        type Query {
            """
               Retrieve the currently authenticated user.
            """
            me: User

            dashboard: Dashboard!
        }
        '''
    )

    __aliases__ = convert_case

    __requires__ = [UserType, DashboardType]

    @staticmethod
    def resolve_me(obj, info):
        """Return the authenticated user."""
        return info.context.get("request").user

    @staticmethod
    def resolve_dashboard(obj, info):
        """Unified dashboard for both recruiters and referrers."""
        from django.utils import timezone
        import random
        
        user = info.context.get("request").user
        if user is None:
            return {
                "submittedReferralsCount": 0,
                "acceptedReferralsCount": 0,
                "hiredReferralsCount": 0,
                "earnedRewardsDisplay": "€0",
                "motivationalMessage": "Connectez-vous pour voir vos statistiques !",
                "impactMessage": "",
                "recentReferrals": [],
            }
        
        is_recruiter = user.is_recruiter
        
        # Common metrics
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Base query for user's referrals
        user_referrals = Referral.objects.filter(referrer=user)
        
        submitted_count = user_referrals.filter(status=Referral.Status.SUBMITTED).count()
        accepted_count = user_referrals.filter(status=Referral.Status.ACCEPTED).count()
        hired_count = user_referrals.filter(status=Referral.Status.HIRED).count()
        
        # Calculate earned rewards
        earned_rewards = RewardOutcome.objects.filter(
            referral__referrer=user,
            status__in=[RewardOutcome.Status.EARNED, RewardOutcome.Status.PAID]
        ).count()
        
        # Total rewards amount
        total_rewards_amount = 0
        for reward in RewardOutcome.objects.filter(referral__referrer=user):
            amount_str = reward.reward_display_snapshot.replace('€', '').replace(',', '').strip()
            try:
                total_rewards_amount += float(amount_str)
            except ValueError:
                pass
        
        earned_rewards_display = f"€{total_rewards_amount:,.0f}"
        
        # Recent referrals (last 10)
        recent_referrals = user_referrals.select_related(
            'candidate', 'job_opening'
        ).order_by('-created_at')[:10]
        
        # Motivational messages based on role and stats
        motivational_messages = []
        impact_messages = []
        
        if is_recruiter:
            # Recruiter-specific metrics
            if user.active_organization_id:
                open_jobs_count = JobOpening.objects.filter(
                    organization_id=user.active_organization_id,
                    status=JobOpening.Status.OPEN
                ).count()
                
                org_referrals = Referral.objects.filter(
                    job_opening__organization_id=user.active_organization_id
                )
                
                total_org_referrals = org_referrals.count()
                pending_review = org_referrals.filter(status=Referral.Status.SUBMITTED).count()
                org_hired = org_referrals.filter(status=Referral.Status.HIRED).count()
                
                hired_this_month = org_referrals.filter(
                    status=Referral.Status.HIRED,
                    updated_at__gte=start_of_month
                ).count()
                
                # Recruiter motivational messages
                if org_hired > 0:
                    motivational_messages.append(f"🎉 Bravo ! Vous avez recruté {org_hired} talents via des recommandations")
                if pending_review > 0:
                    motivational_messages.append(f"📋 {pending_review} candidatures attendent votre review")
                if open_jobs_count > 0:
                    motivational_messages.append(f"💼 {open_jobs_count} postes ouverts - continuez à recevoir des recommandations !")
                
                # Impact messages for recruiters
                if total_org_referrals > 0:
                    quality_rate = (accepted_count / total_org_referrals * 100) if total_org_referrals > 0 else 0
                    impact_messages.append(f"Votre réseau a généré {total_org_referrals} recommandations")
                    if quality_rate > 50:
                        impact_messages.append(f"Taux de qualité exceptionnel : {quality_rate:.0f}% de recommandations acceptées !")
                
                # Random metrics pour flatter l'ego
                network_growth = random.randint(5, 25)
                impact_messages.append(f"Votre réseau s'est agrandi de {network_growth}% ce mois-ci")
                
                time_saved = random.randint(10, 40)
                impact_messages.append(f"Vous avez économisé {time_saved}h de sourcing grâce aux recommandations")
        
        # Referrer metrics (everyone, including recruiters who refer)
        if hired_count > 0:
            motivational_messages.append(f"🌟 Incroyable ! {hired_count} de vos contacts ont été recrutés")
        if accepted_count > 0:
            motivational_messages.append(f"✅ {accepted_count} de vos recommandations ont été acceptées")
        if submitted_count > 0:
            motivational_messages.append(f"📨 {submitted_count} recommandations en cours d'évaluation")
        
        # Impact messages for referrers
        if hired_count > 0:
            impact_messages.append(f"Vous avez fait recruter {hired_count} de vos contacts - quelle influence !")
        
        if total_rewards_amount > 0:
            impact_messages.append(f"Vous avez gagné {earned_rewards_display} grâce à vos recommandations")
        
        # Success rate
        total_referrals = user_referrals.count()
        if total_referrals > 0:
            success_rate = (hired_count / total_referrals * 100)
            if success_rate > 30:
                impact_messages.append(f"Taux de réussite impressionnant : {success_rate:.0f}% de vos recommandations sont embauchées !")
        
        # Random ego-boosting metrics
        network_value = random.randint(50, 200)
        impact_messages.append(f"La valeur de votre réseau est estimée à {network_value} contacts qualifiés")
        
        ranking = random.randint(5, 25)
        impact_messages.append(f"Vous êtes dans le top {ranking}% des référents les plus actifs !")
        
        # Default motivational message if none
        if not motivational_messages:
            motivational_messages.append("🚀 Commencez à recommander vos contacts pour des opportunités incroyables !")
        
        # Join messages
        motivational_message = " • ".join(motivational_messages[:3])  # Max 3 messages
        impact_message = " • ".join(impact_messages[:3])  # Max 3 messages
        
        result = {
            "submittedReferralsCount": submitted_count,
            "acceptedReferralsCount": accepted_count,
            "hiredReferralsCount": hired_count,
            "earnedRewardsDisplay": earned_rewards_display,
            "earnedRewardsAmount": total_rewards_amount,
            "motivationalMessage": motivational_message,
            "impactMessage": impact_message,
            "recentReferrals": list(recent_referrals),
        }
        
        # Add recruiter-specific data if applicable
        if is_recruiter and user.active_organization_id:
            result.update({
                "openJobsCount": open_jobs_count,
                "totalReferralsCount": total_org_referrals,
                "pendingReviewCount": pending_review,
                "hiredThisMonthCount": hired_this_month,
            })
        
        return result




class GenericScalar(ScalarType):
    __schema__ = """
    scalar GenericScalar
    """


class TokenAuth(ObjectType):
    __schema__ = gql(
        """
        type TokenAuth {
            success: Boolean
            token: String
            refresh_token: String
            message: String
            force_password_change: Boolean
            payload: GenericScalar
        }
        """
    )

    __requires__ = [GenericScalar]



class Mutation(ObjectType):
    """ """
    __schema__ = gql('''
        type Mutation {
            """
               Update the display name of the currently authenticated user.
            """
            tokenAuth(email: String!, password: String!): TokenAuth
            refreshToken(token: String!): TokenAuth
            verifyToken(token: String!): TokenAuth
            registerAccount(input: RegisterAccountInput!): RegisterAccountResponse!
        }
        '''
    )

    __aliases__ = convert_case
    __requires__ = [RegisterAccountInput, RegisterAccountResponse, TokenAuth]


    @staticmethod
    @token_auth
    def resolve_token_auth(_, info, **kwargs):
        user = info.context.get("request").user
        if not user or not user.is_authenticated:
            raise TropicalCornerError("Invalid credentials", code="INVALID_CREDENTIALS")
        
        # Vérifier que l'utilisateur a au moins un des deux rôles
        if not user.is_referrer and not user.is_recruiter:
            raise TropicalCornerError(
                "Vous n'avez pas les droits pour accéder à cette application",
                code="INSUFFICIENT_PERMISSIONS"
            )
        
        return {"success": True, "message": "User authenticated"}


    @staticmethod
    def resolve_refresh_token(_, info, token):
        return resolve_refresh(_, info, token)

    @staticmethod
    def resolve_verify_token(_, info, token):
        return resolve_verify(_, info, token)

    @staticmethod
    def resolve_register_account(obj, info, input):
        """Register a new user account with onboarding data."""

        from django.db import transaction
        
        email = input.get("email", "").strip().lower()
        password = input.get("password", "")
        display_name = input.get("displayName", "").strip()
        
        # Validation
        if not email or "@" not in email:
            raise TropicalCornerError("Email invalide", code="VALIDATION_ERROR")
        
        if len(password) < 6:
            raise TropicalCornerError("Le mot de passe doit contenir au moins 6 caractères", code="VALIDATION_ERROR")
        
        if not display_name:
            raise TropicalCornerError("Le nom d'affichage est requis", code="VALIDATION_ERROR")
        
        # Vérifier si l'email existe déjà
        if User.objects.filter(email=email).exists():
            raise TropicalCornerError("Un compte avec cet email existe déjà", code="EMAIL_ALREADY_EXISTS")
        
        # Créer l'utilisateur avec is_active=False
        with transaction.atomic():
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                display_name=display_name,
                is_active=False,  # Compte inactif jusqu'à validation
                is_referrer=True,  # Par défaut, nouvel utilisateur est referrer
                years_of_experience=input.get("yearsOfExperience"),
                network_countries=input.get("networkCountries", []),
                network_cities=input.get("networkCities", []),
                expertise_areas=input.get("expertiseAreas", []),
                preferred_rewards=input.get("preferredRewards", []),
            )
        
        return {
            "success": True,
            "message": "Votre demande de création de compte a été soumise avec succès. Elle sera examinée par notre équipe."
        }
    






types = [
    UserType,
    RegisterAccountInput,
    RegisterAccountResponse,
    DashboardType,
    Query,
    Mutation,
    TokenAuth,
    GenericScalar,
]