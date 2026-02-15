from django.db import models

from apps.organizations.models import Organization, OrganizationMember


class JobOpening(models.Model):
    """
    A job opening in an organization.
    """

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"

    # === Contexte d'entreprise ===
    class CompanyContext(models.TextChoices):
        # Croissance et Développement
        STARTUP = "STARTUP", "Start-up / Lancement"
        SCALEUP = "SCALEUP", "Hyper-croissance (Scale-up)"
        INTERNATIONALIZATION = "INTERNATIONALIZATION", "Internationalisation"
        DIVERSIFICATION = "DIVERSIFICATION", "Diversification"
        # Stabilité et Maturité
        CRUISING = "CRUISING", "Vitesse de croisière"
        SUCCESSION = "SUCCESSION", "Transmission / Succession"
        # Crise et Difficulté
        RESTRUCTURING = "RESTRUCTURING", "Redressement judiciaire"
        REPUTATION_CRISIS = "REPUTATION_CRISIS", "Crise de réputation"
        TECH_DISRUPTION = "TECH_DISRUPTION", "Rupture technologique"

    # === Structure de l'actionnariat ===
    class ShareholderStructure(models.TextChoices):
        # Listée
        LISTED_FAMILY = "LISTED_FAMILY", "Listée - Familial"
        LISTED_FUND = "LISTED_FUND", "Listée - Financier (fonds)"
        LISTED_STATE = "LISTED_STATE", "Listée - État"
        # Non listée
        UNLISTED_FAMILY = "UNLISTED_FAMILY", "Non listée - Familial"
        UNLISTED_FUND = "UNLISTED_FUND", "Non listée - Financier (fonds)"
        UNLISTED_EMPLOYEE = "UNLISTED_EMPLOYEE", "Non listée - Salarié"

    # === Contexte du mandat ===
    class MandateContext(models.TextChoices):
        POSITION_CREATION = "POSITION_CREATION", "Création de poste"
        REPLACEMENT = "REPLACEMENT", "Remplacement"
        MATERNITY_LEAVE = "MATERNITY_LEAVE", "Congés maternité"

    # === Secteur d'activité ===
    class ActivitySector(models.TextChoices):
        # Finance et Services Professionnels
        BANKING = "BANKING", "Banque et Services Financiers"
        INSURANCE_SECTOR = "INSURANCE_SECTOR", "Assurance"
        CONSULTING_AUDIT = "CONSULTING_AUDIT", "Conseil et Audit"
        # Immobilier
        REAL_ESTATE_PROMOTION = "REAL_ESTATE_PROMOTION", "Promotion immobilière"
        REAL_ESTATE_ASSET = "REAL_ESTATE_ASSET", "Gestion d'actifs (Asset Management)"
        REAL_ESTATE_LUXURY = "REAL_ESTATE_LUXURY", "Immobilier de prestige"
        # Industrie du Luxe et de la Consommation
        LUXURY = "LUXURY", "Luxe (Haute couture, maroquinerie, horlogerie, joaillerie)"
        RETAIL_DISTRIBUTION = "RETAIL_DISTRIBUTION", "Retail / Distribution"
        FOOD_INDUSTRY = "FOOD_INDUSTRY", "Agroalimentaire"
        COSMETICS_BEAUTY = "COSMETICS_BEAUTY", "Cosmétiques et Beauté"
        # Technologie et Communication
        IT_SOFTWARE = "IT_SOFTWARE", "Informatique et Software (IT)"
        TELECOM = "TELECOM", "Télécommunications"
        # Médias et Divertissement
        ADVERTISING = "ADVERTISING", "Publicité"
        STREAMING = "STREAMING", "Streaming"
        VIDEO_GAMES = "VIDEO_GAMES", "Jeux vidéo"
        PRESS = "PRESS", "Presse"
        # Industrie, Énergie et Santé
        ENERGY_UTILITIES = "ENERGY_UTILITIES", "Énergie et Utilities"
        HEALTH_PHARMA = "HEALTH_PHARMA", "Santé et Pharma"
        AUTOMOTIVE_AEROSPACE = "AUTOMOTIVE_AEROSPACE", "Automobile et Aéronautique"
        CHEMISTRY_MATERIALS = "CHEMISTRY_MATERIALS", "Chimie et Matériaux"
        # Services aux Personnes et Tourisme
        HOSPITALITY = "HOSPITALITY", "Hôtellerie et Restauration"
        TRANSPORT_LOGISTICS = "TRANSPORT_LOGISTICS", "Transports et Logistique"
        LEISURE_CULTURE = "LEISURE_CULTURE", "Loisirs et Culture"

    # === Enjeux clefs ===
    class KeyChallenge(models.TextChoices):
        AI_AUTOMATION = "AI_AUTOMATION", "Intelligence artificielle et hyper automatisation"
        ECOLOGICAL_TRANSITION = "ECOLOGICAL_TRANSITION", "Transition écologique et décarbonation"
        TALENT_WAR = "TALENT_WAR", "Guerre des talents et hybridation au travail"
        CYBERSECURITY = "CYBERSECURITY", "Cybersécurité et résilience"
        CUSTOMER_EXPERIENCE = "CUSTOMER_EXPERIENCE", "Expérience client"
        SOVEREIGNTY = "SOVEREIGNTY", "Souveraineté et délocalisation"
        DATA_GOVERNANCE = "DATA_GOVERNANCE", "Data gouvernance et éthique"
        REVENUE_MODELS = "REVENUE_MODELS", "Mutation des modèles de revenus"
        MENTAL_HEALTH = "MENTAL_HEALTH", "Santé mentale"
        SKILLS_OBSOLESCENCE = "SKILLS_OBSOLESCENCE", "Obsolescence des compétences"
        INTANGIBLE_ASSETS = "INTANGIBLE_ASSETS", "Valorisation des actifs immatériels"
        COMPLIANCE = "COMPLIANCE", "Compliance et judiciarisation"
        ORG_DESIGN = "ORG_DESIGN", "Design des organisations"

    # === Expertise métier ===
    class ExpertiseDomain(models.TextChoices):
        # Finance, Gestion et Risques
        AUDIT_CONSULTING = "AUDIT_CONSULTING", "Audit et conseil"
        FINANCE = "FINANCE", "Finance"
        INSURANCE = "INSURANCE", "Assurance"
        LEGAL_TAX = "LEGAL_TAX", "Juridique et fiscalité"
        # Développement Commercial et Relation Client
        SALES = "SALES", "Ventes"
        RETAIL = "RETAIL", "Retail"
        MARCOM = "MARCOM", "Marcom"
        MEDIA = "MEDIA", "Média"
        # Opérations, Supply chain et Achats
        PROCUREMENT = "PROCUREMENT", "Achats"
        LOGISTICS_SUPPLY = "LOGISTICS_SUPPLY", "Logistique et supply chain"
        QUALITY = "QUALITY", "Qualité"
        # Technologie et innovation
        TECH_IT = "TECH_IT", "Tech / IT"
        DATA_AI = "DATA_AI", "Data et IA"
        DESIGN_CREATION = "DESIGN_CREATION", "Design / Création"
        # Secteurs spécialisés
        HEALTH = "HEALTH", "Santé"
        HR = "HR", "RH"
        RD = "RD", "R&D"
        TECH = "TECH", "Technique / Ingénierie"

    # === Compétences relationnelles ===
    class InterpersonalSkill(models.TextChoices):
        EMOTIONAL_INTELLIGENCE = "EMOTIONAL_INTELLIGENCE", "Intelligence Émotionnelle"
        INSPIRING_COMMUNICATION = "INSPIRING_COMMUNICATION", "Communication Inspirante"
        INFLUENCE_PERSUASION = "INFLUENCE_PERSUASION", "Influence et Persuasion"
        ADAPTABILITY = "ADAPTABILITY", "Adaptabilité et Agilité Mentale"
        DELEGATION_EMPOWERMENT = "DELEGATION_EMPOWERMENT", "Capacité de Délégation et d'Empowerment"

    # === Niveau d'expérience ===
    class ExperienceLevel(models.TextChoices):
        TOP_MANAGEMENT = "TOP_MANAGEMENT", "Top Management : 12 - 18 ans"
        C_LEVEL = "C_LEVEL", "C-Level (Comex) : 18 - 25+ ans"
        BOARD = "BOARD", "Board (Conseil) : 25+ ans"

    # === Type de contrat ===
    class ContractType(models.TextChoices):
        CDI = "CDI", "CDI"
        CDD = "CDD", "CDD"
        INTERIM_MANAGEMENT = "INTERIM_MANAGEMENT", "Interim management"
        CONSULTING_MISSION = "CONSULTING_MISSION", "Mission de conseil"
        FULL_TIME = "FULL_TIME", "Temps plein"
        PART_TIME = "PART_TIME", "Temps partiel"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="job_openings"
    )
    created_by = models.ForeignKey(
        OrganizationMember,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_jobs",
    )

    # === SECTION 1: Contexte de l'entreprise ===
    company_context = models.CharField(
        max_length=50,
        choices=CompanyContext.choices,
        null=True,
        blank=True,
        help_text="Contexte d'entreprise"
    )
    shareholder_structure = models.CharField(
        max_length=50,
        choices=ShareholderStructure.choices,
        null=True,
        blank=True,
        help_text="Structure de l'actionnariat"
    )

    # === SECTION 2: Contexte du mandat ===
    mandate_context = models.CharField(
        max_length=50,
        choices=MandateContext.choices,
        null=True,
        blank=True,
        help_text="Contexte du mandat"
    )

    # === SECTION 3: Localisation (format: ville, canton, pays) ===
    location_city = models.CharField(max_length=100, null=True, blank=True, help_text="Ville")
    location_canton = models.CharField(max_length=100, null=True, blank=True, help_text="Canton")
    location_country = models.CharField(max_length=100, default="Suisse", help_text="Pays")

    # === SECTION 4: Secteur d'activité ===
    activity_sector = models.CharField(
        max_length=50,
        choices=ActivitySector.choices,
        null=True,
        blank=True,
        help_text="Secteur d'activité"
    )

    # === SECTION 5: Enjeux clefs (3 choix max) ===
    key_challenges = models.JSONField(
        default=list,
        help_text="3 enjeux clefs (liste de valeurs KeyChallenge)"
    )

    # === SECTION 6: Poste ===
    title = models.CharField(max_length=255, help_text="Intitulé de poste")
    description = models.TextField(max_length=1000, help_text="Description du poste (5 lignes max)")

    # === SECTION 7: Expertise métier ===
    expertise_domain = models.CharField(
        max_length=50,
        choices=ExpertiseDomain.choices,
        null=True,
        blank=True,
        help_text="Expertise métier"
    )

    # === SECTION 8: Compétences relationnelles (3 choix) ===
    interpersonal_skills = models.JSONField(
        default=list,
        help_text="3 compétences relationnelles fondamentales"
    )

    # === SECTION 9: Expérience ===
    experience_level = models.CharField(
        max_length=50,
        choices=ExperienceLevel.choices,
        null=True,
        blank=True,
        help_text="Niveau d'expérience souhaité"
    )
    years_experience_required = models.IntegerField(null=True, blank=True)

    # === SECTION 10: Type de contrat (2 choix possibles) ===
    contract_types = models.JSONField(
        default=list,
        help_text="Types de contrat (liste de valeurs ContractType, max 2)"
    )

    # === SECTION 11: Package salarial ===
    salary_fixed = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Rémunération fixe"
    )
    salary_variable = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Rémunération variable"
    )
    salary_benefits = models.TextField(
        null=True,
        blank=True,
        help_text="Avantages"
    )
    salary_other = models.TextField(
        null=True,
        blank=True,
        help_text="Autres"
    )

    # === SECTION 12: Process de recrutement ===
    recruitment_process = models.JSONField(
        default=list,
        help_text="Process de recrutement: liste de {role: string, objective: string}"
    )

    # === Métadonnées ===
    published_date = models.DateField(auto_now_add=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    reward_display = models.CharField(max_length=100, help_text="Récompense affichée (ex: €1,500)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # === Anciens champs conservés pour compatibilité ===
    location = models.CharField(max_length=255, null=True, blank=True)
    sector = models.CharField(max_length=255, null=True, blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    technical_skills = models.JSONField(default=list, blank=True)
    contract_type = models.CharField(max_length=50, null=True, blank=True)
    organization_size = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "job_openings"
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["expertise_domain"]),
            models.Index(fields=["published_date"]),
            models.Index(fields=["activity_sector"]),
            models.Index(fields=["company_context"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} @ {self.organization.name}"

    @property
    def location_display(self) -> str:
        """Retourne la localisation formatée: Ville, Canton, Pays"""
        parts = [p for p in [self.location_city, self.location_canton, self.location_country] if p]
        return ", ".join(parts) if parts else self.location or ""
