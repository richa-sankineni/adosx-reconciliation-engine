"""
Robust CSV ingestion.

Guarantee: every data row present in the source CSVs ends up as exactly one
row in the corresponding table. Nothing is dropped because a value looks
wrong — bad values are stored as-is (raw) and dealt with later by the
comparator, which can report them as discrepancies instead of ingestion
failures. The only rows a CSV reader would ever skip are truly empty lines,
which are not data.
"""
import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from reconciler.models import Location, SystemARecord, SystemBEntry
from reconciler.services.parsing import normalize_reference


class Command(BaseCommand):
    help = "Import locations.csv, system_a.csv and system_b.csv into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            default=str(settings.DATA_DIR),
            help="Directory containing locations.csv, system_a.csv, system_b.csv",
        )

    def handle(self, *args, **options):
        data_dir = Path(options["data_dir"])

        with transaction.atomic():
            n_loc = self._import_locations(data_dir / "locations.csv")
            n_a = self._import_system_a(data_dir / "system_a.csv")
            n_b = self._import_system_b(data_dir / "system_b.csv")

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {n_loc} locations, {n_a} System A records, {n_b} System B entries."
            )
        )

    def _read_rows(self, path: Path):
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip genuinely blank lines (all fields empty/None); everything
                # else — however malformed — is kept.
                if row and any((v or "").strip() for v in row.values()):
                    yield row

    def _import_locations(self, path: Path) -> int:
        Location.objects.all().delete()
        rows = list(self._read_rows(path))
        objs = [
            Location(
                location_id=(row.get("location_id") or "").strip(),
                org_id=(row.get("org_id") or "").strip(),
                location_name=(row.get("location_name") or "").strip(),
            )
            for row in rows
        ]
        Location.objects.bulk_create(objs)
        return len(objs)

    def _import_system_a(self, path: Path) -> int:
        SystemARecord.objects.all().delete()
        rows = list(self._read_rows(path))
        objs = []
        for row in rows:
            record_id = (row.get("record_id") or "").strip()
            objs.append(
                SystemARecord(
                    record_id=record_id,
                    record_id_normalized=normalize_reference(record_id),
                    location_id_raw=(row.get("location_id") or "").strip(),
                    event_date_raw=(row.get("event_date") or "").strip(),
                    category_code=(row.get("category_code") or "").strip(),
                    actor_id=(row.get("actor_id") or "").strip(),
                    base_value_raw=(row.get("base_value") or "").strip(),
                    adjustment_raw=(row.get("adjustment") or "").strip(),
                    total_value_raw=(row.get("total_value") or "").strip(),
                    state=(row.get("state") or "").strip(),
                    raw_row=row,
                )
            )
        SystemARecord.objects.bulk_create(objs)
        return len(objs)

    def _import_system_b(self, path: Path) -> int:
        SystemBEntry.objects.all().delete()
        rows = list(self._read_rows(path))
        objs = []
        for row in rows:
            record_ref = (row.get("record_ref") or "").strip()
            objs.append(
                SystemBEntry(
                    entry_id=(row.get("entry_id") or "").strip(),
                    record_ref_raw=record_ref,
                    record_ref_normalized=normalize_reference(record_ref),
                    location_id_raw=(row.get("location_id") or "").strip(),
                    recorded_on_raw=(row.get("recorded_on") or "").strip(),
                    value_raw=(row.get("value") or "").strip(),
                    label=(row.get("label") or "").strip(),
                    raw_row=row,
                )
            )
        SystemBEntry.objects.bulk_create(objs)
        return len(objs)
