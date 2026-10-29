import { useState } from "react";
import { api } from "./api.js";

export default function SignIn({ onSignedIn }) {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.signIn(token);
      onSignedIn();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="center">
      <form className="card sign-in" onSubmit={submit}>
        <h1>Assistant</h1>
        <p className="muted">
          Paste your token once. You stay signed in for two weeks, and the token itself isn't saved on this
          phone.
        </p>
        <input
          type="password"
          autoComplete="off"
          placeholder="Token"
          value={token}
          onChange={(event) => setToken(event.target.value)}
        />
        <button className="primary" disabled={busy || !token}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
        {error && <p className="error">{error}</p>}
      </form>
    </main>
  );
}
