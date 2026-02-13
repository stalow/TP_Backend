from django.db import models

from apps.accounts.models import User
from apps.jobs.models import JobOpening
from apps.organizations.models import Organization, OrganizationMember


class Candidate(models.Model):
    """
    A candidate profile within an organization context.
    """

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="candidates"
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    
    # Profile information
    years_experience = models.IntegerField(default=0)  # Années d'expérience
    expertise_domain = models.CharField(
        max_length=50, 
        choices=JobOpening.ExpertiseDomain.choices,
        default=JobOpening.ExpertiseDomain.TECH
    )  # Expertise métier
    search_criteria = models.JSONField(default=list)  # 3 critères de recherche
    technical_skills = models.JSONField(default=list)  # Compétences techniques
    interpersonal_skills = models.JSONField(default=list)  # Compétences relationnelles
    
    # LinkedIn scraped profile data
    linkedin_headline = models.CharField(max_length=500, blank=True, null=True)
    linkedin_summary = models.TextField(blank=True, null=True)
    linkedin_experience = models.JSONField(blank=True, null=True)
    linkedin_education = models.JSONField(blank=True, null=True)
    linkedin_skills = models.JSONField(blank=True, null=True)
    linkedin_scraped_at = models.DateTimeField(null=True, blank=True)
    
    consent_confirmed = models.BooleanField(default=False)
    consent_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "candidates"
        indexes = [
            models.Index(fields=["organization", "email"]),
            models.Index(fields=["expertise_domain"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.organization.name})"


class Referral(models.Model):
    """
    A recommendation of a candidate for a job opening.
    """

    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        REVIEWED = "REVIEWED", "Reviewed"
        ACCEPTED = "ACCEPTED", "Accepted"
        HIRED = "HIRED", "Hired"
        REJECTED = "REJECTED", "Rejected"

    class RelationshipType(models.TextChoices):
        COMPANY = "COMPANY", "Ancien collègue (même entreprise)"
        HIERARCHICAL = "HIERARCHICAL", "Lien hiérarchique"
        ALUMNI = "ALUMNI", "Alumni (même école/université)"
        OTHER = "OTHER", "Autre"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="referrals"
    )
    job_opening = models.ForeignKey(
        JobOpening, on_delete=models.CASCADE, related_name="referrals"
    )
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="referrals"
    )
    referrer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="submitted_referrals"
    )
    relationship_context = models.TextField()
    
    # Nouveaux champs pour enrichir le contexte de recommandation
    relationship_type = models.CharField(
        max_length=20, 
        choices=RelationshipType.choices, 
        default=RelationshipType.OTHER,
        help_text="Type de relation avec le candidat"
    )
    profile_motivation = models.TextField(
        help_text="Pourquoi recommander ce profil pour ce poste?",
        null=True,
        blank=True
    )
    supporting_materials = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="Liens vers des matériaux de support (articles, conférences, photos, etc.)"
    )
    
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUBMITTED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "referrals"
        indexes = [
            models.Index(fields=["organization", "job_opening"]),
            models.Index(fields=["organization", "referrer"]),
            models.Index(fields=["organization", "status"]),
        ]

    def __str__(self) -> str:
        return f"Referral: {self.candidate.full_name} for {self.job_opening.title}"


class ReferralStatusEvent(models.Model):
    """
    Immutable audit trail for referral status changes.
    """

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="referral_events"
    )
    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="status_events"
    )
    from_status = models.CharField(max_length=20, blank=True, null=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        OrganizationMember,
        on_delete=models.SET_NULL,
        null=True,
        related_name="status_changes",
    )
    reason_category = models.CharField(max_length=100, blank=True, null=True)
    reason_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "referral_status_events"
        indexes = [
            models.Index(fields=["organization", "referral", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.referral} {self.from_status} → {self.to_status}"


class RewardOutcome(models.Model):
    """
    Reward record tied to a hired referral.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        EARNED = "earned", "Earned"
        PAID = "paid", "Paid"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="rewards"
    )
    referral = models.OneToOneField(
        Referral, on_delete=models.CASCADE, related_name="reward_outcome"
    )
    reward_display_snapshot = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reward_outcomes"
        indexes = [
            models.Index(fields=["organization", "status"]),
        ]

    def __str__(self) -> str:
        return f"Reward for {self.referral}: {self.reward_display_snapshot}"


class CandidateScore(models.Model):
    """
    Score calculé pour un referral (hybride: règles + LLM).
    Permet de ranker et classer les candidats recommandés.
    """

    class Grade(models.TextChoices):
        A = "A", "Excellent (80+)"
        B = "B", "Bon (60-79)"
        C = "C", "Moyen (40-59)"
        D = "D", "Faible (<40)"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="candidate_scores"
    )
    referral = models.OneToOneField(
        Referral, on_delete=models.CASCADE, related_name="score"
    )
    
    # Scores
    final_score = models.IntegerField(help_text="Score final hybride (0-100)")
    rule_score = models.IntegerField(help_text="Score basé sur les règles (0-100)")
    llm_score = models.IntegerField(help_text="Score basé sur l'analyse LLM (0-100)")
    grade = models.CharField(max_length=1, choices=Grade.choices)
    
    # Breakdown détaillé (règles)
    expertise_match = models.IntegerField(default=0)
    experience_match = models.IntegerField(default=0)
    interpersonal_skills_match = models.IntegerField(default=0)
    technical_skills_match = models.IntegerField(default=0)
    referral_quality = models.IntegerField(default=0)
    
    # Analyse LLM
    llm_strengths = models.JSONField(default=list, help_text="Points forts identifiés par le LLM")
    llm_gaps = models.JSONField(default=list, help_text="Points faibles identifiés par le LLM")
    llm_summary = models.TextField(blank=True, help_text="Résumé de l'analyse LLM")
    
    # Métadonnées
    scored_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    llm_model_used = models.CharField(max_length=50, blank=True, help_text="Modèle LLM utilisé")
    
    class Meta:
        db_table = "candidate_scores"
        indexes = [
            models.Index(fields=["organization", "final_score"]),
            models.Index(fields=["organization", "grade"]),
        ]
        ordering = ["-final_score"]

    def __str__(self) -> str:
        return f"Score {self.final_score} ({self.grade}) for {self.referral}"
