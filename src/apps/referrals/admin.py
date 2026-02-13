from django.contrib import admin

from .models import Candidate, Referral, ReferralStatusEvent, RewardOutcome


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "organization", "consent_confirmed", "created_at")
    search_fields = ("full_name", "email", "organization__name")
    list_filter = ("organization", "consent_confirmed")


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        "candidate",
        "job_opening",
        "referrer",
        "status",
        "created_at",
    )
    search_fields = (
        "candidate__full_name",
        "job_opening__title",
        "referrer__user__email",
    )
    list_filter = ("status", "organization")


@admin.register(ReferralStatusEvent)
class ReferralStatusEventAdmin(admin.ModelAdmin):
    list_display = ("referral", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("to_status", "organization")


@admin.register(RewardOutcome)
class RewardOutcomeAdmin(admin.ModelAdmin):
    list_display = ("referral", "reward_display_snapshot", "status", "created_at")
    list_filter = ("status", "organization")
