from ariadne_graphql_modules import ObjectType, gql, InterfaceType

from gql.node import resolve_node_type


class NodeInterface(InterfaceType):
    """ """
    __schema__ = gql('''
        """
           Represents a node in the system.
        """
        interface Node {
            id: ID!
        }
        '''
    )

    __requires__ = []
    
    @staticmethod
    def resolve_type(obj, *_):
        """Resolve the GraphQL type name for a Node object."""
        return resolve_node_type(obj)



class ValidationErrorType(ObjectType):
    """ """
    __schema__ = gql('''
        """
           Represents a validation error.
        """
        type ValidationError {
            message: String!
            field: String!
        }
        '''
    )

    __requires__ = []


types = [
    NodeInterface,
    ValidationErrorType,
]