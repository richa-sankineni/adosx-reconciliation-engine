from reconciler.services.comparator import (
    REASON_DUPLICATE,
    REASON_MISSING,
    REASON_ORPHAN,
    REASON_VALUE_MISMATCH,
    reconcile_records,
)


def test_detects_record_missing_in_system_b():
    records_a = [{"record_id": "REC-01", "value": "100", "location_id": "LOC-1"}]
    records_b = []
    location_map = {"LOC-1": "ORG-1"}

    results = reconcile_records(records_a, records_b, location_map)

    assert len(results) == 1
    assert results[0].reason == REASON_MISSING
    assert results[0].record_ref == "REC-01"
    assert results[0].org_id == "ORG-1"


def test_detects_orphan_record_in_system_b():
    records_a = []
    records_b = [{"entry_id": "ENT-1", "record_ref": "REC-999", "value": "250", "location_id": "LOC-1"}]
    location_map = {"LOC-1": "ORG-1"}

    results = reconcile_records(records_a, records_b, location_map)

    assert len(results) == 1
    assert results[0].reason == REASON_ORPHAN
    assert results[0].system_b_entry_ids == ["ENT-1"]


def test_detects_duplicate_entries_in_system_b():
   
    records_a = [{"record_id": "REC-01", "value": "100", "location_id": "LOC-1"}]
    records_b = [
        {"entry_id": "ENT-1", "record_ref": "REC-01", "value": "100", "location_id": "LOC-1"},
        {"entry_id": "ENT-2", "record_ref": " rec-01 ", "value": "100", "location_id": "LOC-1"},
    ]
    location_map = {"LOC-1": "ORG-1"}

    results = reconcile_records(records_a, records_b, location_map)

    assert len(results) == 1
    assert results[0].reason == REASON_DUPLICATE
    assert set(results[0].system_b_entry_ids) == {"ENT-1", "ENT-2"}


def test_duplicate_takes_precedence_over_value_mismatch():
  
    records_a = [{"record_id": "REC-01", "value": "100.00", "location_id": "LOC-1"}]
    records_b = [
        {"entry_id": "ENT-1", "record_ref": "REC-01", "value": "100.00", "location_id": "LOC-1"},
        {"entry_id": "ENT-2", "record_ref": "REC-01", "value": "999.99", "location_id": "LOC-1"},
    ]
    location_map = {"LOC-1": "ORG-1"}

    results = reconcile_records(records_a, records_b, location_map)

    assert len(results) == 1
    assert results[0].reason == REASON_DUPLICATE


def test_detects_value_mismatch():
    records_a = [{"record_id": "REC-01", "value": "100.00", "location_id": "LOC-1"}]
    records_b = [{"entry_id": "ENT-1", "record_ref": "REC-01", "value": "120.00", "location_id": "LOC-1"}]
    location_map = {"LOC-1": "ORG-1"}

    results = reconcile_records(records_a, records_b, location_map)

    assert len(results) == 1
    assert results[0].reason == REASON_VALUE_MISMATCH
    assert results[0].val_a == "100.00"
    assert results[0].val_b == "120.00"


def test_value_mismatch_tolerates_currency_formatting_and_still_matches():
   
    records_a = [{"record_id": "REC-01", "value": "$1,200.50", "location_id": "LOC-1"}]
    records_b = [{"entry_id": "ENT-1", "record_ref": "REC-01", "value": "1200.50", "location_id": "LOC-1"}]
    location_map = {"LOC-1": "ORG-1"}

    results = reconcile_records(records_a, records_b, location_map)

    assert results == []


def test_matching_records_produce_no_discrepancy():
    records_a = [{"record_id": "REC-01", "value": "100.00", "location_id": "LOC-1"}]
    records_b = [{"entry_id": "ENT-1", "record_ref": "REC-01", "value": "100.00", "location_id": "LOC-1"}]
    location_map = {"LOC-1": "ORG-1"}

    assert reconcile_records(records_a, records_b, location_map) == []


def test_unparseable_null_values_are_not_silently_treated_as_equal():
  
    records_a = [{"record_id": "REC-01", "value": "N/A", "location_id": "LOC-1"}]
    records_b = [{"entry_id": "ENT-1", "record_ref": "REC-01", "value": "100.00", "location_id": "LOC-1"}]
    location_map = {"LOC-1": "ORG-1"}

    results = reconcile_records(records_a, records_b, location_map)

    assert len(results) == 1
    assert results[0].reason == REASON_VALUE_MISMATCH


def test_bare_numeric_reference_normalizes_to_same_key_as_prefixed_id():
    records_a = [{"record_id": "REC-1112", "value": "50.00", "location_id": "LOC-1"}]
    records_b = [{"entry_id": "ENT-1", "record_ref": "1112", "value": "50.00", "location_id": "LOC-1"}]
    location_map = {"LOC-1": "ORG-1"}

    assert reconcile_records(records_a, records_b, location_map) == []
