# graphql package
from ariadne_graphql_modules import make_executable_schema


from .types import all_types



schema_type = [
    *all_types,
]


schema = make_executable_schema(
    *schema_type,
)

## import for graphql view
from typing import cast

from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from ariadne.exceptions import HttpBadRequestError
from ariadne.graphql import graphql_sync

from graphql import GraphQLSchema

from ariadne_django.views.base import BaseGraphQLView

from .auth import get_context_value



@method_decorator(csrf_exempt, name="dispatch")
class MyGraphQLView(BaseGraphQLView):
    def dispatch(self, *args, **kwargs):
        if not self.schema:
            raise ValueError("GraphQLView was initialized without schema.")
        try:
            return super().dispatch(*args, **kwargs)
        except HttpBadRequestError as error:
            return HttpResponseBadRequest(error.message)

    def get(self, *args, **kwargs):
        return self._get(*args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs):  # pylint: disable=unused-argument
        try:
            data = self.extract_data_from_request(request)
        except HttpBadRequestError as error:
            return HttpResponseBadRequest(error.message)
        
        context = get_context_value(request)

        success, result = graphql_sync(cast(GraphQLSchema, self.schema), data, context_value=context, debug=True)
        status_code = 200 if success else 400
        return JsonResponse(result, status=status_code)