from ariadne_graphql_modules import ObjectType, gql, DeferredType, InputType, convert_case

from apps.jobs.models import JobOpening
from apps.organizations.models import OrganizationMember, Organization
from apps.referrals.models import Referral
from common.errors import TropicalCornerError
from gql.auth import require_auth
from gql.node import encode_global_id, decode_global_id, fetch_node


class RecruitmentProcessStepType(ObjectType):
    """Étape du process de recrutement"""
    __schema__ = gql(
        '''
        type RecruitmentProcessStep {
            role: String!
            objective: String!
        }
        '''
    )


class RecruitmentProcessStepInput(InputType):
    """Input pour une étape du process de recrutement"""
    __schema__ = gql(
        '''
        input RecruitmentProcessStepInput {
            role: String!
            objective: String!
        }
        '''
    )


class JobOpeningType(ObjectType):
    """ """

    __schema__ = gql(
        '''
        """
           Represents a job opening in an organization.
        """
        type JobOpening implements Node {
            id: ID!
            organization: Organization!
            
            "Contexte de l'entreprise"
            companyContext: CompanyContext
            shareholderStructure: ShareholderStructure
            
            "Contexte du mandat"
            mandateContext: MandateContext
            
            "Localisation"
            locationCity: String
            locationCanton: String
            locationCountry: String
            locationDisplay: String!
            
            "Secteur d'activité"
            activitySector: ActivitySector
            
            "Enjeux clefs (3 max)"
            keyChallenges: [KeyChallenge!]!
            
            "Poste"
            title: String!
            description: String!
            
            "Expertise métier"
            expertiseDomain: ExpertiseDomain
            
            "Compétences relationnelles (3 max)"
            interpersonalSkills: [InterpersonalSkill!]!
            
            "Expérience"
            experienceLevel: ExperienceLevel
            
            "Types de contrat (2 max)"
            contractTypes: [ContractType!]!
            
            "Package salarial"
            salaryFixed: String
            salaryVariable: String
            salaryBenefits: String
            salaryOther: String
            
            "Process de recrutement"
            recruitmentProcess: [RecruitmentProcessStep!]!
            
            "Métadonnées"
            publishedDate: String!
            status: JobStatus!
            rewardDisplay: String!
            referralCount: Int!
            referrals: [Referral!]!
            createdAt: String!
            updatedAt: String!
            
            "Champs legacy pour compatibilité"
            location: String
            sector: String
            salaryMin: Float
            salaryMax: Float
            yearsExperienceRequired: Int
            contractType: String
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        DeferredType('Node'),
        DeferredType('Organization'),
        DeferredType('JobStatus'),
        DeferredType('Referral'),
        DeferredType('CompanyContext'),
        DeferredType('ShareholderStructure'),
        DeferredType('MandateContext'),
        DeferredType('ActivitySector'),
        DeferredType('KeyChallenge'),
        DeferredType('ExpertiseDomain'),
        DeferredType('InterpersonalSkill'),
        DeferredType('ExperienceLevel'),
        DeferredType('ContractType'),
        RecruitmentProcessStepType,
    ]

    @staticmethod
    def resolve_id(job_opening, info):
        return encode_global_id("JobOpening", job_opening.id)

    @staticmethod
    def resolve_referral_count(job_opening, info):
        """Return the number of referrals for this job opening."""
        return Referral.objects.filter(job_opening_id=job_opening.id).count()

    @staticmethod
    def resolve_referrals(job_opening, info):
        """Return the referrals for this job opening."""
        return Referral.objects.filter(job_opening_id=job_opening.id)

    @staticmethod
    def resolve_location_display(job_opening, info):
        """Return formatted location string."""
        return job_opening.location_display

    @staticmethod
    def resolve_key_challenges(job_opening, info):
        """Return key challenges as list."""
        return job_opening.key_challenges or []

    @staticmethod
    def resolve_interpersonal_skills(job_opening, info):
        """Return interpersonal skills as list."""
        return job_opening.interpersonal_skills or []

    @staticmethod
    def resolve_contract_types(job_opening, info):
        """Return contract types as list."""
        return job_opening.contract_types or []

    @staticmethod
    def resolve_recruitment_process(job_opening, info):
        """Return recruitment process steps."""
        return job_opening.recruitment_process or []


class CreateJobOpeningInput(InputType):
    __schema__ = gql(
        """
        input CreateJobOpeningInput {
            "Contexte de l'entreprise"
            companyContext: CompanyContext
            shareholderStructure: ShareholderStructure
            
            "Contexte du mandat"
            mandateContext: MandateContext
            
            "Localisation"
            locationCity: String
            locationCanton: String
            locationCountry: String
            
            "Secteur d'activité"
            activitySector: ActivitySector
            
            "Enjeux clefs (3 max)"
            keyChallenges: [KeyChallenge!]!
            
            "Poste"
            title: String!
            description: String!
            
            "Expertise métier"
            expertiseDomain: ExpertiseDomain
            
            "Compétences relationnelles (3 max)"
            interpersonalSkills: [InterpersonalSkill!]!
            
            "Expérience"
            experienceLevel: ExperienceLevel
            
            "Types de contrat (2 max)"
            contractTypes: [ContractType!]!
            
            "Package salarial"
            salaryFixed: String
            salaryVariable: String
            salaryBenefits: String
            salaryOther: String
            
            "Process de recrutement"
            recruitmentProcess: [RecruitmentProcessStepInput!]
            
            "Récompense"
            rewardDisplay: String!
        }
        """
    )

    __requires__ = [
        DeferredType("CompanyContext"),
        DeferredType("ShareholderStructure"),
        DeferredType("MandateContext"),
        DeferredType("ActivitySector"),
        DeferredType("KeyChallenge"),
        DeferredType("ExpertiseDomain"),
        DeferredType("InterpersonalSkill"),
        DeferredType("ExperienceLevel"),
        DeferredType("ContractType"),
        RecruitmentProcessStepInput,
    ]


class UpdateJobOpeningInput(InputType):
    __schema__ = gql(
        """
        input UpdateJobOpeningInput {
            jobOpeningId: ID!
            
            "Contexte de l'entreprise"
            companyContext: CompanyContext
            shareholderStructure: ShareholderStructure
            
            "Contexte du mandat"
            mandateContext: MandateContext
            
            "Localisation"
            locationCity: String
            locationCanton: String
            locationCountry: String
            
            "Secteur d'activité"
            activitySector: ActivitySector
            
            "Enjeux clefs (3 max)"
            keyChallenges: [KeyChallenge!]
            
            "Poste"
            title: String
            description: String
            
            "Expertise métier"
            expertiseDomain: ExpertiseDomain
            
            "Compétences relationnelles (3 max)"
            interpersonalSkills: [InterpersonalSkill!]
            
            "Expérience"
            experienceLevel: ExperienceLevel
            
            "Types de contrat (2 max)"
            contractTypes: [ContractType!]
            
            "Package salarial"
            salaryFixed: String
            salaryVariable: String
            salaryBenefits: String
            salaryOther: String
            
            "Process de recrutement"
            recruitmentProcess: [RecruitmentProcessStepInput!]
            
            "Récompense et statut"
            rewardDisplay: String
            status: JobStatus
        }
        """
    )

    __requires__ = [
        DeferredType("CompanyContext"),
        DeferredType("ShareholderStructure"),
        DeferredType("MandateContext"),
        DeferredType("ActivitySector"),
        DeferredType("KeyChallenge"),
        DeferredType("ExpertiseDomain"),
        DeferredType("InterpersonalSkill"),
        DeferredType("ExperienceLevel"),
        DeferredType("ContractType"),
        DeferredType("JobStatus"),
        RecruitmentProcessStepInput,
    ]


class Query(ObjectType):
    __schema__ = gql(
        '''
        type Query {
            jobOpenings(status: JobStatus, first: Int = 20, after: String): [JobOpening!]!
            jobOpening(id: ID!): JobOpening
            myJobs(status: JobStatus, first: Int = 20, after: String): [JobOpening!]!
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        JobOpeningType,
        DeferredType('JobStatus'),
    ]

    @staticmethod
    def resolve_job_openings(obj, info, status=None, first=20, after=None):
        """List job openings in the active organization."""
        qs = JobOpening.objects.all()

        if status:
            qs = qs.filter(status=status)

        qs = qs.order_by("-created_at")

        # Simple offset pagination via cursor
        if after:
            try:
                _, db_id = decode_global_id(after)
                qs = qs.filter(id__lt=db_id)
            except Exception:
                pass

        return list(qs[:first])

    @staticmethod
    def resolve_job_opening(obj, info, id):
        """Fetch a specific job opening by ID."""
        job_opening = fetch_node(id, tenant_ctx=None)
        if not isinstance(job_opening, JobOpening):
            return None
        return job_opening

    @staticmethod
    def resolve_my_jobs(obj, info, status=None, first=20, after=None):
        """List job openings created by the recruiter's organization."""
        user = info.context.get("request").user
        if user is None or not user.is_recruiter:
            return []

        if not user.active_organization_id:
            return []

        qs = JobOpening.objects.filter(organization_id=user.active_organization_id)

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


class Mutation(ObjectType):
    __schema__ = gql(
        '''
        type Mutation {
            createJobOpening(input: CreateJobOpeningInput!): JobOpening!
            updateJobOpening(input: UpdateJobOpeningInput!): JobOpening!
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        JobOpeningType,
        CreateJobOpeningInput,
        UpdateJobOpeningInput,
    ]

    @staticmethod
    def resolve_create_job_opening(obj, info, input):
        """Create a job opening in the active organization."""
        user = require_auth(info)

        if not user.is_recruiter:
            raise TropicalCornerError("Only recruiters can create jobs", code="INSUFFICIENT_PERMISSIONS")

        if not user.active_organization_id:
            raise TropicalCornerError("No active organization selected", code="NO_ACTIVE_ORG")

        org = Organization.objects.filter(
            id=user.active_organization_id,
            status=Organization.Status.ACTIVE
        ).first()

        if org is None:
            raise TropicalCornerError("Organization not found", code="ORG_NOT_FOUND")

        membership = OrganizationMember.objects.filter(
            organization=org,
            user=user,
            disabled_at__isnull=True
        ).first()

        if membership is None:
            raise TropicalCornerError("You are not a member of this organization", code="NOT_MEMBER")

        # Validation des champs requis
        title = input.get("title", "").strip()
        description = input.get("description", "").strip()

        if not title:
            raise TropicalCornerError("Title is required", code="VALIDATION_ERROR")
        if not description:
            raise TropicalCornerError("Description is required", code="VALIDATION_ERROR")
        if len(description) > 1000:
            raise TropicalCornerError("Description must be max 1000 characters", code="VALIDATION_ERROR")

        # Validation des listes
        key_challenges = input.get("keyChallenges", [])
        interpersonal_skills = input.get("interpersonalSkills", [])
        contract_types = input.get("contractTypes", [])

        if len(key_challenges) > 3:
            raise TropicalCornerError("Maximum 3 key challenges allowed", code="VALIDATION_ERROR")
        if len(interpersonal_skills) > 3:
            raise TropicalCornerError("Maximum 3 interpersonal skills allowed", code="VALIDATION_ERROR")
        if len(contract_types) > 2:
            raise TropicalCornerError("Maximum 2 contract types allowed", code="VALIDATION_ERROR")

        job = JobOpening.objects.create(
            organization=org,
            created_by=membership,
            # Contexte entreprise
            company_context=input.get("companyContext"),
            shareholder_structure=input.get("shareholderStructure"),
            # Contexte mandat
            mandate_context=input.get("mandateContext"),
            # Localisation
            location_city=input.get("locationCity"),
            location_canton=input.get("locationCanton"),
            location_country=input.get("locationCountry", "Suisse"),
            # Secteur
            activity_sector=input.get("activitySector"),
            # Enjeux
            key_challenges=key_challenges,
            # Poste
            title=title,
            description=description,
            # Expertise
            expertise_domain=input.get("expertiseDomain"),
            # Compétences relationnelles
            interpersonal_skills=interpersonal_skills,
            # Expérience
            experience_level=input.get("experienceLevel"),
            # Contrat
            contract_types=contract_types,
            # Package salarial
            salary_fixed=input.get("salaryFixed"),
            salary_variable=input.get("salaryVariable"),
            salary_benefits=input.get("salaryBenefits"),
            salary_other=input.get("salaryOther"),
            # Process recrutement
            recruitment_process=input.get("recruitmentProcess", []),
            # Récompense
            reward_display=input.get("rewardDisplay", ""),
        )
        return job

    @staticmethod
    def resolve_update_job_opening(obj, info, input):
        """Update an existing job opening."""
        user = require_auth(info)

        if not user.is_recruiter:
            raise TropicalCornerError("Only recruiters can update jobs", code="INSUFFICIENT_PERMISSIONS")

        job_id = input.get("jobOpeningId")
        _, db_id = decode_global_id(job_id)

        job = JobOpening.objects.filter(id=db_id).first()
        if job is None:
            raise TropicalCornerError("Job opening not found", code="JOB_NOT_FOUND")

        if not user.active_organization_id or job.organization_id != user.active_organization_id:
            raise TropicalCornerError("You don't have access to this job", code="ACCESS_DENIED")

        membership = OrganizationMember.objects.filter(
            organization=job.organization,
            user=user,
            disabled_at__isnull=True
        ).first()

        if membership is None:
            raise TropicalCornerError("You are not a member of this organization", code="NOT_MEMBER")

        # Update fields
        if "companyContext" in input:
            job.company_context = input["companyContext"]
        if "shareholderStructure" in input:
            job.shareholder_structure = input["shareholderStructure"]
        if "mandateContext" in input:
            job.mandate_context = input["mandateContext"]
        if "locationCity" in input:
            job.location_city = input["locationCity"]
        if "locationCanton" in input:
            job.location_canton = input["locationCanton"]
        if "locationCountry" in input:
            job.location_country = input["locationCountry"]
        if "activitySector" in input:
            job.activity_sector = input["activitySector"]
        
        if "keyChallenges" in input and input["keyChallenges"] is not None:
            if len(input["keyChallenges"]) > 3:
                raise TropicalCornerError("Maximum 3 key challenges allowed", code="VALIDATION_ERROR")
            job.key_challenges = input["keyChallenges"]

        if "title" in input and input["title"] is not None:
            title = input["title"].strip()
            if not title:
                raise TropicalCornerError("Title cannot be empty", code="VALIDATION_ERROR")
            job.title = title

        if "description" in input and input["description"] is not None:
            description = input["description"].strip()
            if not description:
                raise TropicalCornerError("Description cannot be empty", code="VALIDATION_ERROR")
            if len(description) > 1000:
                raise TropicalCornerError("Description must be max 1000 characters", code="VALIDATION_ERROR")
            job.description = description

        if "expertiseDomain" in input:
            job.expertise_domain = input["expertiseDomain"]

        if "interpersonalSkills" in input and input["interpersonalSkills"] is not None:
            if len(input["interpersonalSkills"]) > 3:
                raise TropicalCornerError("Maximum 3 interpersonal skills allowed", code="VALIDATION_ERROR")
            job.interpersonal_skills = input["interpersonalSkills"]

        if "experienceLevel" in input:
            job.experience_level = input["experienceLevel"]

        if "contractTypes" in input and input["contractTypes"] is not None:
            if len(input["contractTypes"]) > 2:
                raise TropicalCornerError("Maximum 2 contract types allowed", code="VALIDATION_ERROR")
            job.contract_types = input["contractTypes"]

        if "salaryFixed" in input:
            job.salary_fixed = input["salaryFixed"]
        if "salaryVariable" in input:
            job.salary_variable = input["salaryVariable"]
        if "salaryBenefits" in input:
            job.salary_benefits = input["salaryBenefits"]
        if "salaryOther" in input:
            job.salary_other = input["salaryOther"]

        if "recruitmentProcess" in input:
            job.recruitment_process = input["recruitmentProcess"] or []

        if "rewardDisplay" in input and input["rewardDisplay"] is not None:
            job.reward_display = input["rewardDisplay"]

        if "status" in input and input["status"] is not None:
            valid_statuses = [s.value for s in JobOpening.Status]
            if input["status"] not in valid_statuses:
                raise TropicalCornerError(f"Invalid status: {input['status']}", code="VALIDATION_ERROR")
            job.status = input["status"]

        job.save()
        return job


types = [
    RecruitmentProcessStepType,
    RecruitmentProcessStepInput,
    JobOpeningType,
    CreateJobOpeningInput,
    UpdateJobOpeningInput,
    Query,
    Mutation,
]