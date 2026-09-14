const REASON_LABELS = {
  MISSING_IN_SYSTEM_B: "Missing in B",
  ORPHAN_IN_SYSTEM_B: "Orphan in B",
  DUPLICATE_IN_SYSTEM_B: "Duplicate in B",
  VALUE_MISMATCH: "Value mismatch",
};

function fmt(value) {
  if (value === null || value === undefined || value === "") {
    return <span className="muted">—</span>;
  }
  return value;
}

export default function DiscrepancyTable({ items }) {
  if (items.length === 0) {
    return <div className="empty-state">No discrepancies match the current filters.</div>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Reason</th>
          <th>Record</th>
          <th>Location</th>
          <th>Tenant</th>
          <th>System A value</th>
          <th>System B value</th>
          <th>Detail</th>
        </tr>
      </thead>
      <tbody>
        {items.map((row, idx) => (
          <tr key={`${row.reason}-${row.record_ref}-${idx}`}>
            <td>
              <span className={`reason-badge reason-${row.reason}`}>
                {REASON_LABELS[row.reason] || row.reason}
              </span>
            </td>
            <td className="mono">{row.record_ref}</td>
            <td className="mono">{fmt(row.location_id)}</td>
            <td>{row.org_id}</td>
            <td className="mono">{fmt(row.val_a)}</td>
            <td className="mono">{fmt(row.val_b)}</td>
            <td className="muted">{row.detail}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
