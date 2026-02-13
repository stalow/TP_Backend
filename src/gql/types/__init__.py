from .gql_enum_types import types as enum_types
from .user import types as user_types
from .organizations import types as organization_types
from .commons import types as common_types
from .referrals import types as referral_types
from .jobs import types as job_types
from .scoring import types as scoring_types


all_types = [
    *enum_types,
    *user_types,
    *organization_types,
    *common_types,
    *referral_types,
    *job_types,
    *scoring_types,
]

