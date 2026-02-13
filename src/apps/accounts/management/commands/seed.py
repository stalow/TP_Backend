"""
Seed command to populate the database with fake data for demos and testing.
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.jobs.models import JobOpening
from apps.organizations.models import Organization, OrganizationMember
from apps.referrals.models import Candidate, Referral, ReferralStatusEvent, RewardOutcome

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        # Create users
        admin_user, _ = User.objects.get_or_create(
            email="admin@tropicalcorner.com",
            defaults={
                "username": "admin",
                "display_name": "Alice Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("admin123")
        admin_user.save()

        recruiter_user, _ = User.objects.get_or_create(
            email="recruiter@tropicalcorner.com",
            defaults={
                "username": "recruiter",
                "display_name": "Rachel Recruiter",
            },
        )
        recruiter_user.set_password("recruiter123")
        recruiter_user.save()

        referrer_user, _ = User.objects.get_or_create(
            email="referrer@tropicalcorner.com",
            defaults={
                "username": "referrer",
                "display_name": "Robert Referrer",
            },
        )
        referrer_user.set_password("referrer123")
        referrer_user.save()

        # Create organizations
        org1, _ = Organization.objects.get_or_create(
            slug="acme-corp",
            defaults={"name": "ACME Corporation"},
        )

        org2, _ = Organization.objects.get_or_create(
            slug="startup-inc",
            defaults={"name": "Startup Inc."},
        )

        # Create memberships
        admin_member, _ = OrganizationMember.objects.get_or_create(
            organization=org1,
            user=admin_user,
            defaults={"roles": ["admin", "recruiter"]},
        )

        recruiter_member, _ = OrganizationMember.objects.get_or_create(
            organization=org1,
            user=recruiter_user,
            defaults={"roles": ["recruiter"]},
        )

        referrer_member, _ = OrganizationMember.objects.get_or_create(
            organization=org1,
            user=referrer_user,
            defaults={"roles": ["referrer"]},
        )

        # Create job openings
        today = date.today()

        # Job 1: Directeur Technique / CTO - Contexte Scale-up Tech
        job1, _ = JobOpening.objects.get_or_create(
            organization=org1,
            title="Directeur Technique (CTO)",
            defaults={
                "description": "Nous recherchons un(e) CTO visionnaire pour piloter la stratégie technologique de notre scale-up en hyper-croissance. Vous dirigerez une équipe de 25 ingénieurs et serez responsable de l'architecture technique et de l'innovation produit.",
                # Contexte entreprise
                "company_context": JobOpening.CompanyContext.SCALEUP,
                "shareholder_structure": JobOpening.ShareholderStructure.UNLISTED_FUND,
                "mandate_context": JobOpening.MandateContext.POSITION_CREATION,
                # Localisation
                "location_city": "Genève",
                "location_canton": "Genève",
                "location_country": "Suisse",
                # Secteur
                "activity_sector": JobOpening.ActivitySector.IT_SOFTWARE,
                # Enjeux clefs
                "key_challenges": [
                    JobOpening.KeyChallenge.AI_AUTOMATION,
                    JobOpening.KeyChallenge.CYBERSECURITY,
                    JobOpening.KeyChallenge.TALENT_WAR,
                ],
                # Expertise et compétences
                "expertise_domain": JobOpening.ExpertiseDomain.TECH_IT,
                "interpersonal_skills": [
                    JobOpening.InterpersonalSkill.INSPIRING_COMMUNICATION,
                    JobOpening.InterpersonalSkill.DELEGATION_EMPOWERMENT,
                    JobOpening.InterpersonalSkill.ADAPTABILITY,
                ],
                # Expérience et contrat
                "experience_level": JobOpening.ExperienceLevel.C_LEVEL,
                "contract_types": [
                    JobOpening.ContractType.CDI,
                ],
                # Package salarial
                "salary_fixed": "CHF 280'000 - 350'000",
                "salary_variable": "Bonus annuel jusqu'à 30% sur objectifs",
                "salary_benefits": "• Actions/Stock options (ESOP)\n• Voiture de fonction\n• Assurance complémentaire premium\n• Budget formation illimité",
                "salary_other": "Relocation package si nécessaire",
                # Process de recrutement
                "recruitment_process": [
                    {"role": "HR Director", "objective": "Premier entretien de découverte et validation culturelle"},
                    {"role": "CEO", "objective": "Vision stratégique et alignement avec la roadmap"},
                    {"role": "Board Member", "objective": "Évaluation du leadership et de la vision technique"},
                    {"role": "Technical Assessment", "objective": "Cas pratique d'architecture et présentation"},
                ],
                "published_date": today - timedelta(days=10),
                "status": JobOpening.Status.OPEN,
                "reward_display": "CHF 5'000",
                "created_by": admin_member,
            },
        )

        # Job 2: Directeur Financier (CFO) - Banque privée
        job2, _ = JobOpening.objects.get_or_create(
            organization=org1,
            title="Chief Financial Officer (CFO)",
            defaults={
                "description": "Rejoignez une banque privée de premier plan pour piloter la direction financière. Vous serez membre du Comex et responsable de la stratégie financière, du contrôle de gestion et des relations investisseurs.",
                # Contexte entreprise
                "company_context": JobOpening.CompanyContext.CRUISING,
                "shareholder_structure": JobOpening.ShareholderStructure.LISTED_FAMILY,
                "mandate_context": JobOpening.MandateContext.REPLACEMENT,
                # Localisation
                "location_city": "Zürich",
                "location_canton": "Zürich",
                "location_country": "Suisse",
                # Secteur
                "activity_sector": JobOpening.ActivitySector.BANKING,
                # Enjeux clefs
                "key_challenges": [
                    JobOpening.KeyChallenge.COMPLIANCE,
                    JobOpening.KeyChallenge.DATA_GOVERNANCE,
                    JobOpening.KeyChallenge.REVENUE_MODELS,
                ],
                # Expertise et compétences
                "expertise_domain": JobOpening.ExpertiseDomain.FINANCE,
                "interpersonal_skills": [
                    JobOpening.InterpersonalSkill.EMOTIONAL_INTELLIGENCE,
                    JobOpening.InterpersonalSkill.INFLUENCE_PERSUASION,
                    JobOpening.InterpersonalSkill.INSPIRING_COMMUNICATION,
                ],
                # Expérience et contrat
                "experience_level": JobOpening.ExperienceLevel.C_LEVEL,
                "contract_types": [
                    JobOpening.ContractType.CDI,
                ],
                # Package salarial
                "salary_fixed": "CHF 400'000 - 500'000",
                "salary_variable": "Bonus annuel de 50% à 100% selon performance",
                "salary_benefits": "• Participation au capital\n• Retraite complémentaire LPP++\n• Véhicule de fonction haut de gamme\n• Club privé et représentation",
                "salary_other": "Golden parachute contractuel",
                # Process de recrutement
                "recruitment_process": [
                    {"role": "CHRO", "objective": "Validation du fit culturel et des attentes"},
                    {"role": "CEO", "objective": "Alignement stratégique et vision"},
                    {"role": "Président du Conseil", "objective": "Entretien final et négociation"},
                ],
                "published_date": today - timedelta(days=20),
                "status": JobOpening.Status.OPEN,
                "reward_display": "CHF 8'000",
                "created_by": recruiter_member,
            },
        )

        # Job 3: Directeur Marketing & Communication - Luxe
        job3, _ = JobOpening.objects.get_or_create(
            organization=org1,
            title="Directeur Marketing & Communication",
            defaults={
                "description": "Prenez la direction du marketing et de la communication pour une maison de luxe suisse en pleine internationalisation. Vous piloterez la stratégie de marque et l'expérience client premium.",
                # Contexte entreprise
                "company_context": JobOpening.CompanyContext.INTERNATIONALIZATION,
                "shareholder_structure": JobOpening.ShareholderStructure.UNLISTED_FAMILY,
                "mandate_context": JobOpening.MandateContext.POSITION_CREATION,
                # Localisation
                "location_city": "Lausanne",
                "location_canton": "Vaud",
                "location_country": "Suisse",
                # Secteur
                "activity_sector": JobOpening.ActivitySector.LUXURY,
                # Enjeux clefs
                "key_challenges": [
                    JobOpening.KeyChallenge.CUSTOMER_EXPERIENCE,
                    JobOpening.KeyChallenge.INTANGIBLE_ASSETS,
                    JobOpening.KeyChallenge.ECOLOGICAL_TRANSITION,
                ],
                # Expertise et compétences
                "expertise_domain": JobOpening.ExpertiseDomain.MARCOM,
                "interpersonal_skills": [
                    JobOpening.InterpersonalSkill.INSPIRING_COMMUNICATION,
                    JobOpening.InterpersonalSkill.ADAPTABILITY,
                    JobOpening.InterpersonalSkill.INFLUENCE_PERSUASION,
                ],
                # Expérience et contrat
                "experience_level": JobOpening.ExperienceLevel.TOP_MANAGEMENT,
                "contract_types": [
                    JobOpening.ContractType.CDI,
                    JobOpening.ContractType.FULL_TIME,
                ],
                # Package salarial
                "salary_fixed": "CHF 220'000 - 280'000",
                "salary_variable": "Bonus sur objectifs (20-30%)",
                "salary_benefits": "• Produits de la maison\n• Voyages business class\n• Événements VIP\n• Budget formation",
                "salary_other": None,
                # Process de recrutement
                "recruitment_process": [
                    {"role": "DRH", "objective": "Entretien de découverte"},
                    {"role": "Directeur Général", "objective": "Vision marketing et stratégie de marque"},
                    {"role": "Famille fondatrice", "objective": "Validation des valeurs et de la vision long terme"},
                ],
                "published_date": today - timedelta(days=45),
                "status": JobOpening.Status.CLOSED,
                "reward_display": "CHF 4'000",
                "created_by": recruiter_member,
            },
        )

        # Job 4: Directeur des Opérations - Pharma
        job4, _ = JobOpening.objects.get_or_create(
            organization=org1,
            title="Chief Operating Officer (COO)",
            defaults={
                "description": "Dirigez les opérations d'un groupe pharmaceutique suisse en pleine transformation digitale. Vous optimiserez la supply chain et les processus de production pour accompagner la croissance internationale.",
                # Contexte entreprise
                "company_context": JobOpening.CompanyContext.DIVERSIFICATION,
                "shareholder_structure": JobOpening.ShareholderStructure.LISTED_FUND,
                "mandate_context": JobOpening.MandateContext.REPLACEMENT,
                # Localisation
                "location_city": "Bâle",
                "location_canton": "Bâle-Ville",
                "location_country": "Suisse",
                # Secteur
                "activity_sector": JobOpening.ActivitySector.HEALTH_PHARMA,
                # Enjeux clefs
                "key_challenges": [
                    JobOpening.KeyChallenge.AI_AUTOMATION,
                    JobOpening.KeyChallenge.SOVEREIGNTY,
                    JobOpening.KeyChallenge.COMPLIANCE,
                ],
                # Expertise et compétences
                "expertise_domain": JobOpening.ExpertiseDomain.LOGISTICS_SUPPLY,
                "interpersonal_skills": [
                    JobOpening.InterpersonalSkill.DELEGATION_EMPOWERMENT,
                    JobOpening.InterpersonalSkill.EMOTIONAL_INTELLIGENCE,
                    JobOpening.InterpersonalSkill.ADAPTABILITY,
                ],
                # Expérience et contrat
                "experience_level": JobOpening.ExperienceLevel.C_LEVEL,
                "contract_types": [
                    JobOpening.ContractType.CDI,
                ],
                # Package salarial
                "salary_fixed": "CHF 350'000 - 420'000",
                "salary_variable": "Bonus annuel 40-60% + LTI",
                "salary_benefits": "• Plan de pension suisse premium\n• Assurance internationale famille\n• Véhicule de fonction\n• Actions gratuites (RSU)",
                "salary_other": "Budget relocation et aide à l'installation",
                # Process de recrutement
                "recruitment_process": [
                    {"role": "VP HR", "objective": "Entretien de qualification"},
                    {"role": "CEO", "objective": "Vision opérationnelle et fit stratégique"},
                    {"role": "Comité de nomination", "objective": "Présentation devant le board"},
                    {"role": "Assessment Center", "objective": "Évaluation des compétences managériales"},
                ],
                "published_date": today - timedelta(days=5),
                "status": JobOpening.Status.OPEN,
                "reward_display": "CHF 6'000",
                "created_by": admin_member,
            },
        )

        # Job 5: Membre du Conseil d'Administration - Energie
        job5, _ = JobOpening.objects.get_or_create(
            organization=org1,
            title="Administrateur Indépendant (Board Member)",
            defaults={
                "description": "Rejoignez le conseil d'administration d'un leader suisse de l'énergie renouvelable. Vous apporterez votre expertise stratégique et votre réseau international pour accompagner la transition énergétique.",
                # Contexte entreprise
                "company_context": JobOpening.CompanyContext.TECH_DISRUPTION,
                "shareholder_structure": JobOpening.ShareholderStructure.LISTED_STATE,
                "mandate_context": JobOpening.MandateContext.POSITION_CREATION,
                # Localisation
                "location_city": "Berne",
                "location_canton": "Berne",
                "location_country": "Suisse",
                # Secteur
                "activity_sector": JobOpening.ActivitySector.ENERGY_UTILITIES,
                # Enjeux clefs
                "key_challenges": [
                    JobOpening.KeyChallenge.ECOLOGICAL_TRANSITION,
                    JobOpening.KeyChallenge.SOVEREIGNTY,
                    JobOpening.KeyChallenge.DATA_GOVERNANCE,
                ],
                # Expertise et compétences
                "expertise_domain": JobOpening.ExpertiseDomain.AUDIT_CONSULTING,
                "interpersonal_skills": [
                    JobOpening.InterpersonalSkill.INFLUENCE_PERSUASION,
                    JobOpening.InterpersonalSkill.EMOTIONAL_INTELLIGENCE,
                    JobOpening.InterpersonalSkill.INSPIRING_COMMUNICATION,
                ],
                # Expérience et contrat
                "experience_level": JobOpening.ExperienceLevel.BOARD,
                "contract_types": [
                    JobOpening.ContractType.CONSULTING_MISSION,
                    JobOpening.ContractType.PART_TIME,
                ],
                # Package salarial
                "salary_fixed": "CHF 80'000 - 120'000 / an (jetons de présence)",
                "salary_variable": None,
                "salary_benefits": "• Assurance D&O\n• Frais de déplacement\n• Accès aux comités spécialisés",
                "salary_other": "4 à 6 réunions par an + comités",
                # Process de recrutement
                "recruitment_process": [
                    {"role": "Président du Conseil", "objective": "Entretien de connaissance mutuelle"},
                    {"role": "Comité de nomination", "objective": "Validation du profil et des compétences"},
                    {"role": "Due diligence", "objective": "Vérification des références et conflits d'intérêts"},
                ],
                "published_date": today - timedelta(days=3),
                "status": JobOpening.Status.OPEN,
                "reward_display": "CHF 3'000",
                "created_by": admin_member,
            },
        )

        # Job 6: Directeur des Ressources Humaines - Assurance
        job6, _ = JobOpening.objects.get_or_create(
            organization=org1,
            title="Chief Human Resources Officer (CHRO)",
            defaults={
                "description": "Pilotez la transformation RH d'un assureur majeur. Vous définirez la stratégie talents, la culture d'entreprise et accompagnerez la digitalisation des pratiques RH.",
                # Contexte entreprise
                "company_context": JobOpening.CompanyContext.SUCCESSION,
                "shareholder_structure": JobOpening.ShareholderStructure.LISTED_FAMILY,
                "mandate_context": JobOpening.MandateContext.REPLACEMENT,
                # Localisation
                "location_city": "Winterthur",
                "location_canton": "Zürich",
                "location_country": "Suisse",
                # Secteur
                "activity_sector": JobOpening.ActivitySector.INSURANCE_SECTOR,
                # Enjeux clefs
                "key_challenges": [
                    JobOpening.KeyChallenge.TALENT_WAR,
                    JobOpening.KeyChallenge.SKILLS_OBSOLESCENCE,
                    JobOpening.KeyChallenge.MENTAL_HEALTH,
                ],
                # Expertise et compétences
                "expertise_domain": JobOpening.ExpertiseDomain.HR,
                "interpersonal_skills": [
                    JobOpening.InterpersonalSkill.EMOTIONAL_INTELLIGENCE,
                    JobOpening.InterpersonalSkill.DELEGATION_EMPOWERMENT,
                    JobOpening.InterpersonalSkill.INSPIRING_COMMUNICATION,
                ],
                # Expérience et contrat
                "experience_level": JobOpening.ExperienceLevel.C_LEVEL,
                "contract_types": [
                    JobOpening.ContractType.CDI,
                ],
                # Package salarial
                "salary_fixed": "CHF 300'000 - 380'000",
                "salary_variable": "Bonus annuel 30-50%",
                "salary_benefits": "• Plan de pension premium\n• Assurance famille complète\n• Véhicule de fonction\n• Jours de congés additionnels",
                "salary_other": None,
                # Process de recrutement
                "recruitment_process": [
                    {"role": "Directeur Général adjoint", "objective": "Premier contact et alignement"},
                    {"role": "CEO", "objective": "Vision RH et culture d'entreprise"},
                    {"role": "Président du Conseil", "objective": "Validation finale"},
                ],
                "published_date": today - timedelta(days=15),
                "status": JobOpening.Status.OPEN,
                "reward_display": "CHF 5'500",
                "created_by": recruiter_member,
            },
        )

        # Create candidates and referrals
        candidate1, _ = Candidate.objects.get_or_create(
            organization=org1,
            full_name="Marc Dubois",
            email="marc.dubois@example.com",
            defaults={"consent_confirmed": True},
        )

        candidate2, _ = Candidate.objects.get_or_create(
            organization=org1,
            full_name="Sophie Müller",
            email="sophie.mueller@example.com",
            defaults={"consent_confirmed": True},
        )

        candidate3, _ = Candidate.objects.get_or_create(
            organization=org1,
            full_name="Thomas Schneider",
            email="thomas.schneider@example.com",
            defaults={"consent_confirmed": True},
        )

        # Create referrals
        referral1, created = Referral.objects.get_or_create(
            organization=org1,
            job_opening=job1,
            candidate=candidate1,
            referrer=referrer_user,
            defaults={
                "relationship_context": "Ancien collègue chez Google Zürich. Excellent architecte technique avec une vision produit forte.",
                "status": Referral.Status.REVIEWED,
            },
        )
        if created:
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral1,
                from_status=None,
                to_status=Referral.Status.SUBMITTED,
                changed_by=referrer_member,
            )
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral1,
                from_status=Referral.Status.SUBMITTED,
                to_status=Referral.Status.REVIEWED,
                changed_by=recruiter_member,
            )

        referral2, created = Referral.objects.get_or_create(
            organization=org1,
            job_opening=job2,
            candidate=candidate2,
            referrer=referrer_user,
            defaults={
                "relationship_context": "Rencontrée lors d'une conférence finance à Zürich. 15 ans d'expérience en banque privée, actuellement CFO adjoint chez UBS.",
                "status": Referral.Status.HIRED,
            },
        )
        if created:
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral2,
                from_status=None,
                to_status=Referral.Status.SUBMITTED,
                changed_by=referrer_member,
            )
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral2,
                from_status=Referral.Status.SUBMITTED,
                to_status=Referral.Status.REVIEWED,
                changed_by=recruiter_member,
            )
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral2,
                from_status=Referral.Status.REVIEWED,
                to_status=Referral.Status.ACCEPTED,
                changed_by=recruiter_member,
            )
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral2,
                from_status=Referral.Status.ACCEPTED,
                to_status=Referral.Status.HIRED,
                changed_by=recruiter_member,
            )
            RewardOutcome.objects.get_or_create(
                referral=referral2,
                defaults={
                    "organization": org1,
                    "reward_display_snapshot": job2.reward_display,
                    "status": RewardOutcome.Status.EARNED,
                },
            )

        referral3, created = Referral.objects.get_or_create(
            organization=org1,
            job_opening=job1,
            candidate=candidate3,
            referrer=referrer_user,
            defaults={
                "relationship_context": "Ami d'université (EPFL). Parcours impressionnant chez Swisscom puis Microsoft. Cherche à revenir en Suisse.",
                "status": Referral.Status.SUBMITTED,
            },
        )
        if created:
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral3,
                from_status=None,
                to_status=Referral.Status.SUBMITTED,
                changed_by=referrer_member,
            )

        referral4, created = Referral.objects.get_or_create(
            organization=org1,
            job_opening=job4,
            candidate=candidate1,
            referrer=referrer_user,
            defaults={
                "relationship_context": "Marc a également une solide expérience opérationnelle acquise chez Roche. Il serait parfait pour ce poste de COO.",
                "status": Referral.Status.ACCEPTED,
            },
        )
        if created:
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral4,
                from_status=None,
                to_status=Referral.Status.SUBMITTED,
                changed_by=referrer_member,
            )
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral4,
                from_status=Referral.Status.SUBMITTED,
                to_status=Referral.Status.REVIEWED,
                changed_by=recruiter_member,
            )
            ReferralStatusEvent.objects.create(
                organization=org1,
                referral=referral4,
                from_status=Referral.Status.REVIEWED,
                to_status=Referral.Status.ACCEPTED,
                changed_by=admin_member,
            )

        # Set active organization for users
        admin_user.active_organization_id = org1.id
        admin_user.save(update_fields=["active_organization_id"])
        recruiter_user.active_organization_id = org1.id
        recruiter_user.save(update_fields=["active_organization_id"])
        referrer_user.active_organization_id = org1.id
        referrer_user.save(update_fields=["active_organization_id"])

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
        self.stdout.write("")
        self.stdout.write("Demo accounts:")
        self.stdout.write("  admin@tropicalcorner.com / admin123 (admin)")
        self.stdout.write("  recruiter@tropicalcorner.com / recruiter123 (recruiter)")
        self.stdout.write("  referrer@tropicalcorner.com / referrer123 (referrer)")
        self.stdout.write("")
        self.stdout.write(f"Jobs created: {JobOpening.objects.count()}")
        self.stdout.write(f"Referrals created: {Referral.objects.count()}")

