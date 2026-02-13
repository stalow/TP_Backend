"""
Permission helpers for role-based access control.
"""

from apps.organizations.models import OrganizationMember

from .errors import TropicalCornerError
from .tenancy import TenantContext



def require_roles(
    tenant_ctx: TenantContext, *roles: str, message: str | None = None
) -> OrganizationMember:
    """
    Require that the current user has at least one of the given roles.
    Returns the membership if successful.
    """
    membership = tenant_ctx.require_membership()
    if not membership.has_any_role(*roles):
        raise TropicalCornerError(
            message or f"Requires one of: {', '.join(roles)}"
        )
    return membership


def require_admin(tenant_ctx: TenantContext) -> OrganizationMember:
    return require_roles(
        tenant_ctx, OrganizationMember.Role.ADMIN, message="Admin access required"
    )


def require_recruiter_or_admin(tenant_ctx: TenantContext) -> OrganizationMember:
    return require_roles(
        tenant_ctx,
        OrganizationMember.Role.ADMIN,
        OrganizationMember.Role.RECRUITER,
        message="Recruiter or admin access required",
    )


def require_referrer_or_above(tenant_ctx: TenantContext) -> OrganizationMember:
    return require_roles(
        tenant_ctx,
        OrganizationMember.Role.ADMIN,
        OrganizationMember.Role.RECRUITER,
        OrganizationMember.Role.REFERRER,
        message="Membership required",
    )


def can_view_referral(tenant_ctx: TenantContext, referral_referrer_id: int) -> bool:
    """
    Determine if the current user can view a specific referral.
    Recruiters/admins can view all; referrers can only view their own.
    """
    membership = tenant_ctx.membership
    if membership is None:
        return False
    if membership.has_any_role(
        OrganizationMember.Role.ADMIN, OrganizationMember.Role.RECRUITER
    ):
        return True
    # Referrer can view their own referrals
    return membership.id == referral_referrer_id
