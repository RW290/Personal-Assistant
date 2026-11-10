import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import Approvals from "./Approvals.jsx";
import SignIn from "./SignIn.jsx";

export default function App() {
  // null while checking with the server, then true or false
  const [signedIn, setSignedIn] = useState(null);
  const signOut = useCallback(() => setSignedIn(false), []);

  useEffect(() => {
    api
      .me()
      .then(() => setSignedIn(true))
      .catch(() => setSignedIn(false));
  }, []);

  if (signedIn === null) return <main className="center muted">Loading…</main>;
  if (!signedIn) return <SignIn onSignedIn={() => setSignedIn(true)} />;
  return <Approvals onSignedOut={signOut} />;
}
