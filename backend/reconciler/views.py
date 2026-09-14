from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Location, SystemARecord, SystemBEntry
from .services.comparator import ALL_REASONS, reconcile_records

DISCREPANCY_CACHE_KEY = "reconciler:discrepancies:v1"


def _compute_all_discrepancies():
    
    cached = cache.get(DISCREPANCY_CACHE_KEY)
    if cached is not None:
        return cached

    location_org_map = {loc.location_id: loc.org_id for loc in Location.objects.all()}

    records_a = [
        {
            "record_id": r.record_id,
            "location_id": r.location_id_raw,
            "value": r.total_value_raw or None,
        }
        for r in SystemARecord.objects.all()
    ]
    records_b = [
        {
            "entry_id": e.entry_id,
            "record_ref": e.record_ref_raw,
            "location_id": e.location_id_raw,
            "value": e.value_raw or None,
        }
        for e in SystemBEntry.objects.all()
    ]

    discrepancies = [d.as_dict() for d in reconcile_records(records_a, records_b, location_org_map)]
    cache.set(DISCREPANCY_CACHE_KEY, discrepancies, timeout=60 * 5)
    return discrepancies


class DiscrepancyListView(APIView):
    

    def get(self, request):
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"error": "org_id query parameter is required"}, status=400)

        known_orgs = set(Location.objects.values_list("org_id", flat=True))
        if org_id not in known_orgs:
            return Response({"error": f"unknown org_id '{org_id}'"}, status=404)

        reason = request.query_params.get("reason")
        sort = (request.query_params.get("sort") or "desc").lower()

        all_discrepancies = _compute_all_discrepancies()

        tenant_data = [d for d in all_discrepancies if d["org_id"] == org_id]

        if reason and reason != "ALL":
            if reason not in ALL_REASONS:
                return Response({"error": f"unknown reason '{reason}'"}, status=400)
            tenant_data = [d for d in tenant_data if d["reason"] == reason]

        tenant_data.sort(key=lambda d: d["sort_value"], reverse=(sort != "asc"))

        return Response(
            {
                "org_id": org_id,
                "count": len(tenant_data),
                "reasons": list(ALL_REASONS),
                "results": tenant_data,
            }
        )


class OrgListView(APIView):

    def get(self, request):
        orgs = sorted(set(Location.objects.values_list("org_id", flat=True)))
        return Response({"results": orgs})
