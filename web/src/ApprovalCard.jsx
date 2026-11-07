import { useState } from "react";

const STATUS_WORDS = { approved: "Approved", rejected: "Rejected", done: "Done", failed: "Failed" };

function when(iso) {
  return new Date(iso).toLocaleString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function ApprovalCard({ item, onDecide }) {
  const [busy, setBusy] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  async function decide(approve) {
    setBusy(true);
    await onDecide(item, approve);
    setBusy(false);
  }

  return (
    <article className="card">
      <p className="meta">
        {when(item.created_at)}
        {item.status !== "pending" && (
          <span className={`status ${item.status}`}>{STATUS_WORDS[item.status]}</span>
        )}
      </p>

      {/* Written by code from the exact arguments, so it says exactly what will run */}
      <h2>{item.summary}</h2>

      <dl>
        <dt>Why</dt>
        <dd>{item.reason}</dd>
        <dt>You asked</dt>
        <dd>“{item.request}”</dd>
        <dt>Runs</dt>
        <dd>
          <code>{item.tool}</code>
          {item.tools_used.length > 0 && (
            <>
              {" "}
              after looking at{" "}
              {item.tools_used.map((tool) => (
                <code key={tool}>{tool}</code>
              ))}
            </>
          )}
        </dd>
      </dl>

      <button className="link small" onClick={() => setShowDetails(!showDetails)}>
        {showDetails ? "Hide exact details" : "Show exact details"}
      </button>
      {showDetails && <pre>{JSON.stringify(item.arguments, null, 2)}</pre>}

      {item.status === "pending" && (
        <div className="actions">
          <button className="secondary" disabled={busy} onClick={() => decide(false)}>
            Reject
          </button>
          <button className="primary" disabled={busy} onClick={() => decide(true)}>
            Approve
          </button>
        </div>
      )}
    </article>
  );
}
