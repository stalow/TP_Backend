import logging

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import User

logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "display_name", "is_recruiter", "is_referrer", "is_staff", "is_active", "activate_button")
    search_fields = ("email", "display_name")
    ordering = ("email",)
    actions = ["activate_accounts"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Rôles TropicalCorner", {
            "fields": ("is_recruiter", "is_referrer", "display_name", "active_organization_id"),
        }),
        ("Onboarding", {
            "classes": ("collapse",),
            "fields": ("years_of_experience", "network_countries", "network_cities", "expertise_areas", "preferred_rewards"),
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:user_id>/activate/",
                self.admin_site.admin_view(self.activate_account_view),
                name="accounts_user_activate",
            ),
        ]
        return custom_urls + urls

    def activate_button(self, obj):
        """Affiche un bouton 'Activer' dans la liste si le compte est inactif."""
        if obj.is_active:
            return format_html('<span style="color:green;">✔ Actif</span>')
        url = reverse("admin:accounts_user_activate", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="background:#26A69A;color:#fff;padding:4px 10px;border-radius:4px;text-decoration:none;">Activer</a>',
            url,
        )

    activate_button.short_description = "Activation"
    activate_button.allow_tags = True

    def activate_account_view(self, request, user_id):
        """Vue custom pour activer un compte et envoyer l'email de confirmation."""
        from common.mail_service import send_account_activation_email

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            self.message_user(request, "Utilisateur introuvable.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:accounts_user_changelist"))

        if user.is_active:
            self.message_user(request, f"{user.email} est déjà actif.", level=messages.WARNING)
        else:
            user.is_active = True
            user.save(update_fields=["is_active"])
            try:
                send_account_activation_email(
                    display_name=user.display_name or user.email,
                    email=user.email,
                )
                self.message_user(
                    request,
                    f"Compte activé et email envoyé à {user.email}.",
                    level=messages.SUCCESS,
                )
            except Exception as exc:
                logger.exception("Failed to send activation email to %s", user.email)
                self.message_user(
                    request,
                    f"Compte activé mais l'email n'a pas pu être envoyé ({exc}).",
                    level=messages.WARNING,
                )

        return HttpResponseRedirect(
            reverse("admin:accounts_user_change", args=[user_id])
        )

    @admin.action(description="Activer les comptes sélectionnés et envoyer l'email")
    def activate_accounts(self, request, queryset):
        """Action de liste pour activer plusieurs comptes d'un coup."""
        from common.mail_service import send_account_activation_email

        to_activate = queryset.filter(is_active=False)
        activated = 0
        email_errors = 0

        for user in to_activate:
            user.is_active = True
            user.save(update_fields=["is_active"])
            try:
                send_account_activation_email(
                    display_name=user.display_name or user.email,
                    email=user.email,
                )
            except Exception:
                logger.exception("Failed to send activation email to %s", user.email)
                email_errors += 1
            activated += 1

        msg = f"{activated} compte(s) activé(s)."
        if email_errors:
            msg += f" {email_errors} email(s) n'ont pas pu être envoyés."
        self.message_user(request, msg, level=messages.SUCCESS if not email_errors else messages.WARNING)
