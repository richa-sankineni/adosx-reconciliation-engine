import { useEffect, useState } from "react";
import FilterBar from "./components/FilterBar.jsx";
import DiscrepancyTable from "./components/DiscrepancyTable.jsx";

export default function App() {
  const [orgs, setOrgs] = useState([]);
  const [org, setOrg] = useState("");
  const [reasons, setReasons] = useState([]);
  const [reason, setReason] = useState("ALL");
  const [sort, setSort] = useState("desc");
  const [results, setResults] = useState([]);
  const [count, setCount] = useState(0);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  
  useEffect(() => {
    fetch("/api/orgs/")
      .then((r) => r.json())
      .then((data) => {
        setOrgs(data.results);
        if (data.results.length > 0) setOrg(data.results[0]);
      })
      .catch(() => setError("Could not reach the backend API. Is the Django server running on :8000?"));
  }, []);

  
  useEffect(() => {
    if (!org) return;
    setLoading(true);
    const params = new URLSearchParams({ org_id: org, reason, sort });
    fetch(`/api/discrepancies/?${params.toString()}`)
      .then((r) => {
        if (!r.ok) return r.json().then((body) => Promise.reject(body));
        return r.json();
      })
      .then((data) => {
        setResults(data.results);
        setCount(data.count);
        setReasons(data.reasons);
        setError(null);
      })
      .catch((err) => setError(err.error || "Failed to load discrepancies."))
      .finally(() => setLoading(false));
  }, [org, reason, sort]);

  return (
    <div className="app">
      <h1>Cross-System Reconciliation</h1>
      <p className="subtitle">
        Disagreements between System A and System B, scoped strictly to the selected tenant.
      </p>

      {error && <div className="error-banner">{error}</div>}

      {orgs.length > 0 && (
        <FilterBar
          orgs={orgs}
          org={org}
          onOrgChange={setOrg}
          reasons={reasons}
          reason={reason}
          onReasonChange={setReason}
          sort={sort}
          onSortToggle={() => setSort((s) => (s === "asc" ? "desc" : "asc"))}
        />
      )}

      {!loading && !error && (
        <div className="summary-bar">
          {count} discrepanc{count === 1 ? "y" : "ies"} for {org}
          {reason !== "ALL" ? ` · filtered to ${reason}` : ""}
        </div>
      )}

      {loading ? <p>Loading…</p> : <DiscrepancyTable items={results} />}
    </div>
  );
}
