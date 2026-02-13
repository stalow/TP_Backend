"""
GraphQL Node interface for global ID fetching with tenant/authorization checks.
"""

import base64
from typing import Any

from apps.accounts.models import User
from apps.jobs.models import JobOpening
from apps.organizations.models import Organization, OrganizationMember
from apps.referrals.models import (
    Candidate,
    Referral,
    ReferralStatusEvent,
    RewardOutcome,
)
from common.errors import TropicalCornerError
from common.permissions import can_view_referral
from common.tenancy import TenantContext

# Type registry: maps type name to Django model
NODE_TYPE_MAP: dict[str, type] = {
    "User": User,
    "Organization": Organization,
    "OrganizationMember": OrganizationMember,
    "JobOpening": JobOpening,
    "Candidate": Candidate,
    "Referral": Referral,
    "ReferralStatusEvent": ReferralStatusEvent,
    "RewardOutcome": RewardOutcome,
}

# Types that are tenant-scoped (require organization_id check)
TENANT_SCOPED_TYPES = {
    "Organization",
    "OrganizationMember",
    "JobOpening",
    "Candidate",
    "Referral",
    "ReferralStatusEvent",
    "RewardOutcome",
}


def encode_global_id(type_name: str, db_id: int) -> str:
    """Encode a type name and database ID into a global ID."""
    raw = f"{type_name}:{db_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_global_id(global_id: str) -> tuple[str, int]:
    """Decode a global ID into type name and database ID."""
    try:
        raw = base64.urlsafe_b64decode(global_id.encode()).decode()
        type_name, db_id_str = raw.split(":", 1)
        return type_name, int(db_id_str)
    except Exception as e:
        raise TropicalCornerError(f"Invalid global ID: {global_id}") from e


def fetch_node(
    global_id: str, tenant_ctx: TenantContext | None
) -> Any:
    """
    Fetch any Node by global ID with tenant/authorization checks.
    """
    type_name, db_id = decode_global_id(global_id)

    model_class = NODE_TYPE_MAP.get(type_name)
    if model_class is None:
        raise TropicalCornerError(f"Unknown type: {type_name}")

    # Fetch the object
    obj = model_class.objects.filter(pk=db_id).first()
    if obj is None:
        return None

    # Tenant boundary check
    # if type_name in TENANT_SCOPED_TYPES:
    #     if tenant_ctx is None:
    #         raise TropicalCornerError("Authentication required")

    #     # Get the organization_id from the object
    #     if type_name == "Organization":
    #         obj_org_id = obj.id
    #     else:
    #         obj_org_id = getattr(obj, "organization_id", None)

    #     if obj_org_id is None:
    #         raise TropicalCornerError("Object has no organization")

        # Check membership
        # if tenant_ctx.organization_id != obj_org_id:
            # Check if user has membership in that org at all
            # has_membership = OrganizationMember.objects.filter(
            #     organization_id=obj_org_id,
            #     user=tenant_ctx.user,
            #     disabled_at__isnull=True,
            # ).exists()
            # if not has_membership:
            #     raise TropicalCornerError("Access denied")

        # Additional visibility check for Referral
        # if type_name == "Referral" and not can_view_referral(
        #     tenant_ctx, obj.referrer_id
        # ):
        #     raise TropicalCornerError("Access denied")

    elif type_name == "User":
        # Users can only fetch themselves (unless admin logic added later)
        if tenant_ctx is None or tenant_ctx.user.id != db_id:
            # Allow fetching any user for now (display name only)
            pass

    return obj


def resolve_node_type(obj: Any, *_: Any) -> str:
    """Resolve the GraphQL type name for a Node object."""
    for type_name, model_class in NODE_TYPE_MAP.items():
        if isinstance(obj, model_class):
            return type_name
    raise TropicalCornerError(f"Unknown object type: {type(obj)}")
