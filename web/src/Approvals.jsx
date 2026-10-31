import { useCallback, useEffect, useState } from "react";
import { api, SignedOutError } from "./api.js";
import ApprovalCard from "./ApprovalCard.jsx";

export default function Approvals({ onSignedOut }) {
  const [tab, setTab] = useState("pending"); // "pending" or "history"
  const [items, setItems] = useState(null); // null while loading
  const [error, setError] = useState("");

  const handleError = useCallback(
    (e) => (e instanceof SignedOutError ? onSignedOut() : setError(e.message)),
    [onSignedOut]
  );

  const load = useCallback(async () => {
    setError("");
    try {
      if (tab === "pending") {
        setItems(await api.approvals("pending"));
      } else {
        setItems((await api.approvals()).filter((item) => item.status !== "pending"));
      }
    } catch (e) {
      handleError(e);
    }
  }, [tab, handleError]);

  useEffect(() => {
    setItems(null);
    load();
  }, [load]);

  async function decide(item, approve) {
    try {
      await (approve ? api.approve(item.id) : api.reject(item.id));
      setItems((current) => current.filter((other) => other.id !== item.id));
    } catch (e) {
      handleError(e);
    }
  }

  async function signOut() {
    await api.signOut().catch(() => {});
    onSignedOut();
  }

  return (
    <div className="page">
      <header>
        <h1>Approvals</h1>
        <button className="link" onClick={signOut}>
          Sign out
        </button>
      </header>

      <nav className="tabs">
        <button className={tab === "pending" ? "active" : ""} onClick={() => setTab("pending")}>
          Waiting
        </button>
        <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")}>
          History
        </button>
      </nav>

      {error && <p className="error">{error}</p>}
      {items === null && <p className="muted">Loading…</p>}
      {items?.length === 0 && (
        <p className="empty muted">{tab === "pending" ? "Nothing is waiting for you." : "Nothing decided yet."}</p>
      )}
      {items?.map((item) => (
        <ApprovalCard key={item.id} item={item} onDecide={decide} />
      ))}

      <button className="link refresh" onClick={load}>
        Refresh
      </button>
    </div>
  );
}
