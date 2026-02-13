from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for Tropical Corner.
    Extends Django's AbstractUser with platform-specific fields.
    """

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    active_organization_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_recruiter = models.BooleanField(default=False)
    is_referrer = models.BooleanField(default=False)
    
    # Onboarding fields
    years_of_experience = models.IntegerField(null=True, blank=True)
    network_countries = models.JSONField(default=list, blank=True)  # List of country codes
    network_cities = models.JSONField(default=list, blank=True)  # List of city names
    expertise_areas = models.JSONField(default=list, blank=True)  # List of expertise areas
    preferred_rewards = models.JSONField(default=list, blank=True)  # List of reward types

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return self.email

    @property
    def avatar_url(self) -> str:
        """Generate a deterministic placeholder avatar URL."""
        from apps.accounts.services.avatar import get_avatar_url

        return get_avatar_url(self.id, self.email)
