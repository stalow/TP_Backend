from django.contrib import admin

from .models import JobOpening


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "status", "reward_display", "created_at")
    search_fields = ("title", "organization__name")
    list_filter = ("status", "organization")
