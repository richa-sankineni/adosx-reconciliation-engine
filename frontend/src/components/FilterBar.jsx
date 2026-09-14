const REASON_LABELS = {
  ALL: "All",
  MISSING_IN_SYSTEM_B: "Missing in B",
  ORPHAN_IN_SYSTEM_B: "Orphan in B",
  DUPLICATE_IN_SYSTEM_B: "Duplicate in B",
  VALUE_MISMATCH: "Value mismatch",
};

export default function FilterBar({
  orgs,
  org,
  onOrgChange,
  reasons,
  reason,
  onReasonChange,
  sort,
  onSortToggle,
}) {
  return (
    <div className="controls">
      <label>
        Tenant
        <select value={org} onChange={(e) => onOrgChange(e.target.value)}>
          {orgs.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      </label>

      <label>
        Reason
        <select value={reason} onChange={(e) => onReasonChange(e.target.value)}>
          <option value="ALL">{REASON_LABELS.ALL}</option>
          {reasons.map((r) => (
            <option key={r} value={r}>
              {REASON_LABELS[r] || r}
            </option>
          ))}
        </select>
      </label>

      <label>
        Sort by value
        <button type="button" onClick={onSortToggle}>
          {sort === "asc" ? "Ascending ↑" : "Descending ↓"}
        </button>
      </label>
    </div>
  );
}
