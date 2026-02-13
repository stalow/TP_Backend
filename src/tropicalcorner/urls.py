"""
URL configuration for Tropical Corner.
"""

from django.contrib import admin
from django.urls import path

from gql import schema
from ariadne_django.views import GraphQLView
from gql import MyGraphQLView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", MyGraphQLView.as_view(schema=schema), name="graphql"),
]
