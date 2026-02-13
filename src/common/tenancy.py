"""
Tenancy helpers for multi-tenant data access.
"""

from typing import TYPE_CHECKING

from apps.organizations.models import Organization, OrganizationMember

if TYPE_CHECKING:
    from apps.accounts.models import User


class TenantContext:
    """
    Holds the active organization context for a request.
    """

    def __init__(self, user: "User", organization: Organization | None = None) -> None:
        self.user = user
        self._organization = organization
        self._membership: OrganizationMember | None = None

    @property
    def organization(self) -> Organization | None:
        return self._organization

    @property
    def organization_id(self) -> int | None:
        return self._organization.id if self._organization else None

    @property
    def membership(self) -> OrganizationMember | None:
        if self._membership is None and self._organization is not None:
            self._membership = OrganizationMember.objects.filter(
                organization=self._organization,
                user=self.user,
                disabled_at__isnull=True,
            ).first()
        return self._membership

    def require_organization(self) -> Organization:
        """Raise if no active organization is set."""
        if self._organization is None:
            from common.errors import TropicalCornerError

            raise TropicalCornerError("No active organization selected")
        return self._organization

    def require_membership(self) -> OrganizationMember:
        """Raise if user is not a member of the active org."""
        membership = self.membership
        if membership is None:
            from common.errors import TropicalCornerError

            raise TropicalCornerError("You are not a member of this organization")
        return membership


def get_tenant_context(user: "User") -> TenantContext:
    """
    Build a TenantContext from the user's active_organization_id.
    """
    org: Organization | None = None
    if user.active_organization_id:
        org = Organization.objects.filter(
            id=user.active_organization_id, status=Organization.Status.ACTIVE
        ).first()
    return TenantContext(user, org)


def set_active_organization(user: "User", organization_id: int) -> Organization:
    """
    Set the user's active organization and return it.
    Validates membership before setting.
    """
    from common.errors import TropicalCornerError

    org = Organization.objects.filter(
        id=organization_id, status=Organization.Status.ACTIVE
    ).first()
    if org is None:
        raise TropicalCornerError("Organization not found")

    membership = OrganizationMember.objects.filter(
        organization=org, user=user, disabled_at__isnull=True
    ).first()
    if membership is None:
        raise TropicalCornerError("You are not a member of this organization")

    user.active_organization_id = org.id
    user.save(update_fields=["active_organization_id"])
    return org
