"""
Data models.

Design intent (see DECISIONS.md for the full reasoning):

- Location is the only table with an enforced identity (location_id is
  unique) because locations.csv is small, closed, and is the sole source of
  truth for tenant membership.
- SystemARecord and SystemBEntry deliberately do NOT use a database foreign
  key to link records across systems. The whole point of the exercise is
  that System B references System A rows that may not exist, may be
  duplicated, or may be spelled inconsistently. A real FK constraint would
  make ingestion of those rows impossible without dropping them, which
  violates "must survive all of it without silently dropping rows".
- Every raw string field is stored as ingested (TextField, nullable) rather
  than cast to int/decimal/date at import time. Parsing/normalization
  happens in the comparator, where it can be tested in isolation and where
  a bad value produces a documented discrepancy instead of an ingestion
  failure.
"""
from django.db import models


class Location(models.Model):
    location_id = models.CharField(max_length=64, unique=True)
    org_id = models.CharField(max_length=64)
    location_name = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["org_id"])]

    def __str__(self):
        return f"{self.location_id} ({self.org_id})"


class SystemARecord(models.Model):
    """One row per event, as System A recorded it. record_id is authoritative."""

    record_id = models.CharField(max_length=128)
    record_id_normalized = models.CharField(max_length=128, db_index=True)

    location_id_raw = models.CharField(max_length=128, blank=True, default="")
    event_date_raw = models.CharField(max_length=64, blank=True, default="")
    category_code = models.CharField(max_length=64, blank=True, default="")
    actor_id = models.CharField(max_length=64, blank=True, default="")

    base_value_raw = models.CharField(max_length=64, blank=True, default="")
    adjustment_raw = models.CharField(max_length=64, blank=True, default="")
    total_value_raw = models.CharField(max_length=64, blank=True, default="")
    state = models.CharField(max_length=64, blank=True, default="")

    # Full original row, kept verbatim for auditability / debugging.
    raw_row = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=["record_id_normalized"])]

    def __str__(self):
        return self.record_id


class SystemBEntry(models.Model):
    """One row per entry, as System B recorded it. record_ref points at System A."""

    entry_id = models.CharField(max_length=128)

    record_ref_raw = models.CharField(max_length=128, blank=True, default="")
    record_ref_normalized = models.CharField(max_length=128, db_index=True, blank=True, default="")

    location_id_raw = models.CharField(max_length=128, blank=True, default="")
    recorded_on_raw = models.CharField(max_length=64, blank=True, default="")
    value_raw = models.CharField(max_length=64, blank=True, default="")
    label = models.CharField(max_length=255, blank=True, default="")

    raw_row = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=["record_ref_normalized"])]

    def __str__(self):
        return self.entry_id
