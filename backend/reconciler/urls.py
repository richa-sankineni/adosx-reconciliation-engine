from django.urls import path

from .views import DiscrepancyListView, OrgListView

urlpatterns = [
    path("discrepancies/", DiscrepancyListView.as_view(), name="discrepancy-list"),
    path("orgs/", OrgListView.as_view(), name="org-list"),
]
