"""
URL configuration for Tropical Corner.
"""

from django.contrib import admin
from django.urls import path

from gql import schema
from ariadne_django.views import GraphQLView
from gql import MyGraphQLView

from apps.referrals.views import ConsentInfoView, ConsentConfirmView, ConsentDeclineView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", MyGraphQLView.as_view(schema=schema), name="graphql"),

    # Consent endpoints (public, no auth required)
    path("api/consent/<uuid:token>/", ConsentInfoView.as_view(), name="consent-info"),
    path("api/consent/<uuid:token>/confirm/", ConsentConfirmView.as_view(), name="consent-confirm"),
    path("api/consent/<uuid:token>/decline/", ConsentDeclineView.as_view(), name="consent-decline"),
]
