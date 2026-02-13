from ariadne_graphql_modules import gql, EnumType


class ReferralStatusEnum(EnumType):
    __schema__ = gql(
        """
        enum ReferralStatus {
            SUBMITTED
            REVIEWED
            ACCEPTED
            HIRED
            REJECTED
        }
        """
    )


class JobStatusEnum(EnumType):
    __schema__ = gql(
        """
        enum JobStatus {
            OPEN
            CLOSED
        }
        """
    )


class RewardStatusEnum(EnumType):
    __schema__ = gql(
        """
        enum RewardStatus {
            PENDING
            EARNED
            PAID
        }
        """
    )


# === Nouveaux enums pour les jobs ===

class CompanyContextEnum(EnumType):
    __schema__ = gql(
        """
        "Contexte d'entreprise"
        enum CompanyContext {
            "Croissance et Développement"
            STARTUP
            SCALEUP
            INTERNATIONALIZATION
            DIVERSIFICATION
            "Stabilité et Maturité"
            CRUISING
            SUCCESSION
            "Crise et Difficulté"
            RESTRUCTURING
            REPUTATION_CRISIS
            TECH_DISRUPTION
        }
        """
    )


class ShareholderStructureEnum(EnumType):
    __schema__ = gql(
        """
        "Structure de l'actionnariat"
        enum ShareholderStructure {
            "Listée"
            LISTED_FAMILY
            LISTED_FUND
            LISTED_STATE
            "Non listée"
            UNLISTED_FAMILY
            UNLISTED_FUND
            UNLISTED_EMPLOYEE
        }
        """
    )


class MandateContextEnum(EnumType):
    __schema__ = gql(
        """
        "Contexte du mandat"
        enum MandateContext {
            POSITION_CREATION
            REPLACEMENT
            MATERNITY_LEAVE
        }
        """
    )


class ActivitySectorEnum(EnumType):
    __schema__ = gql(
        """
        "Secteur d'activité"
        enum ActivitySector {
            "Finance et Services Professionnels"
            BANKING
            INSURANCE_SECTOR
            CONSULTING_AUDIT
            "Immobilier"
            REAL_ESTATE_PROMOTION
            REAL_ESTATE_ASSET
            REAL_ESTATE_LUXURY
            "Industrie du Luxe et de la Consommation"
            LUXURY
            RETAIL_DISTRIBUTION
            FOOD_INDUSTRY
            COSMETICS_BEAUTY
            "Technologie et Communication"
            IT_SOFTWARE
            TELECOM
            "Médias et Divertissement"
            ADVERTISING
            STREAMING
            VIDEO_GAMES
            PRESS
            "Industrie, Énergie et Santé"
            ENERGY_UTILITIES
            HEALTH_PHARMA
            AUTOMOTIVE_AEROSPACE
            CHEMISTRY_MATERIALS
            "Services aux Personnes et Tourisme"
            HOSPITALITY
            TRANSPORT_LOGISTICS
            LEISURE_CULTURE
        }
        """
    )


class KeyChallengeEnum(EnumType):
    __schema__ = gql(
        """
        "Enjeux clefs"
        enum KeyChallenge {
            AI_AUTOMATION
            ECOLOGICAL_TRANSITION
            TALENT_WAR
            CYBERSECURITY
            CUSTOMER_EXPERIENCE
            SOVEREIGNTY
            DATA_GOVERNANCE
            REVENUE_MODELS
            MENTAL_HEALTH
            SKILLS_OBSOLESCENCE
            INTANGIBLE_ASSETS
            COMPLIANCE
            ORG_DESIGN
        }
        """
    )


class ExpertiseDomainEnum(EnumType):
    __schema__ = gql(
        """
        "Expertise métier"
        enum ExpertiseDomain {
            "Finance, Gestion et Risques"
            AUDIT_CONSULTING
            FINANCE
            INSURANCE
            LEGAL_TAX
            "Développement Commercial et Relation Client"
            SALES
            RETAIL
            MARCOM
            MEDIA
            "Opérations, Supply chain et Achats"
            PROCUREMENT
            LOGISTICS_SUPPLY
            QUALITY
            "Technologie et innovation"
            TECH_IT
            DATA_AI
            DESIGN_CREATION
            "Secteurs spécialisés"
            HEALTH
            HR
            RD
            "Technique / Ingénierie"
            TECH
        }
        """
    )


class InterpersonalSkillEnum(EnumType):
    __schema__ = gql(
        """
        "Compétences relationnelles fondamentales"
        enum InterpersonalSkill {
            EMOTIONAL_INTELLIGENCE
            INSPIRING_COMMUNICATION
            INFLUENCE_PERSUASION
            ADAPTABILITY
            DELEGATION_EMPOWERMENT
        }
        """
    )


class ExperienceLevelEnum(EnumType):
    __schema__ = gql(
        """
        "Niveau d'expérience"
        enum ExperienceLevel {
            TOP_MANAGEMENT
            C_LEVEL
            BOARD
        }
        """
    )


class ContractTypeEnum(EnumType):
    __schema__ = gql(
        """
        "Type de contrat"
        enum ContractType {
            CDI
            CDD
            INTERIM_MANAGEMENT
            CONSULTING_MISSION
            FULL_TIME
            PART_TIME
        }
        """
    )


class RelationshipTypeEnum(EnumType):
    __schema__ = gql(
        """
        enum RelationshipType {
            COMPANY
            HIERARCHICAL
            ALUMNI
            OTHER
        }
        """
    )


types = [
    ReferralStatusEnum,
    JobStatusEnum,
    RewardStatusEnum,
    CompanyContextEnum,
    ShareholderStructureEnum,
    MandateContextEnum,
    ActivitySectorEnum,
    KeyChallengeEnum,
    ExpertiseDomainEnum,
    InterpersonalSkillEnum,
    ExperienceLevelEnum,
    ContractTypeEnum,
    RelationshipTypeEnum,
]
