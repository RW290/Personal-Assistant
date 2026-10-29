// Every call to the server goes through here. The app is served from the same address
// as the server, so the session cookie rides along on its own and no token is ever
// kept in the browser.

export class SignedOutError extends Error {}

async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const body = await response.json().catch(() => ({}));
  if (response.status === 401) throw new SignedOutError(body.detail ?? "Signed out");
  if (!response.ok) throw new Error(body.detail ?? `Something went wrong (HTTP ${response.status})`);
  return body;
}

export const api = {
  me: () => request("/me"),
  signIn: (token) => request("/login", { method: "POST", body: JSON.stringify({ token }) }),
  signOut: () => request("/logout", { method: "POST" }),
  approvals: (status) => request(status ? `/approvals?status=${status}` : "/approvals"),
  approve: (id) => request(`/approvals/${id}/approve`, { method: "POST" }),
  reject: (id) => request(`/approvals/${id}/reject`, { method: "POST" }),
};
