from ariadne_graphql_modules import ObjectType, gql, DeferredType, InputType, convert_case

from apps.organizations.models import Organization, OrganizationMember
from common.errors import TropicalCornerError
from common.tenancy import set_active_organization
from gql.auth import require_auth
from gql.node import encode_global_id, decode_global_id


class OrganizationType(ObjectType):
    """ """

    __schema__ = gql(
        '''
        """
           Represents an organization in the system.
        """
        type Organization implements Node {
            id: ID!
            name: String!
            slug: String!
            createdAt: String!
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [
        DeferredType('Node'),
    ]

    @staticmethod
    def resolve_id(organization, info):
        return encode_global_id("Organization", organization.id)


class OrganizationMemberType(ObjectType):
    """ """

    __schema__ = gql(
        '''
        """
           Represents a member of an organization.
        """
        type OrganizationMember implements Node {
            id: ID!
            organization: Organization!
            user: User!
            roles: [String!]!
            disabledAt: String
        }
        '''
    )

    __aliases__ = convert_case

    __requires__ = [
        DeferredType('Node'),
        DeferredType('Organization'),
        DeferredType('User'),
    ]

    @staticmethod
    def resolve_id(member, info):
        return encode_global_id("OrganizationMember", member.id)


class CreateOrganizationInput(InputType):
    __schema__ = gql(
        """
        input CreateOrganizationInput {
            name: String!
            slug: String!
        }
        """
    )


class Query(ObjectType):
    __schema__ = gql(
        '''
        type Query {
            myOrganizations: [Organization!]!
            activeOrganization: Organization
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [OrganizationType]

    @staticmethod
    def resolve_my_organizations(obj, info):
        """Return organizations the user belongs to."""
        user = require_auth(info)
        org_ids = OrganizationMember.objects.filter(
            user=user, disabled_at__isnull=True
        ).values_list("organization_id", flat=True)
        return list(
            Organization.objects.filter(id__in=org_ids, status=Organization.Status.ACTIVE)
        )

    @staticmethod
    def resolve_active_organization(obj, info):
        """Return the user's active organization."""
        user = info.context.get("user")
        if user is None:
            return None
        tenant_ctx = info.context.get("tenant_ctx")
        return tenant_ctx.organization if tenant_ctx else None


class Mutation(ObjectType):
    __schema__ = gql(
        '''
        type Mutation {
            createOrganization(input: CreateOrganizationInput!): Organization!
            setActiveOrganization(organizationId: ID!): Organization!
        }
        '''
    )
    __aliases__ = convert_case

    __requires__ = [OrganizationType, CreateOrganizationInput, OrganizationMemberType]

    @staticmethod
    def resolve_create_organization(obj, info, input):
        """Create an organization; creator becomes admin."""
        user = require_auth(info)

        name = input["name"].strip()
        slug = input["slug"].strip().lower()

        if Organization.objects.filter(slug=slug).exists():
            raise TropicalCornerError("Organization slug already exists", code="SLUG_EXISTS")

        org = Organization.objects.create(name=name, slug=slug)

        # Creator becomes admin
        OrganizationMember.objects.create(
            organization=org,
            user=user,
            roles=[OrganizationMember.Role.ADMIN, OrganizationMember.Role.RECRUITER],
        )

        # Set as active org
        user.active_organization_id = org.id
        user.save(update_fields=["active_organization_id"])

        return org

    @staticmethod
    def resolve_set_active_organization(obj, info, organizationId):
        """Set the user's active organization."""
        user = require_auth(info)
        _, db_id = decode_global_id(organizationId)
        return set_active_organization(user, db_id)


types = [
    OrganizationType,
    OrganizationMemberType,
    CreateOrganizationInput,
    Query,
    Mutation,
]