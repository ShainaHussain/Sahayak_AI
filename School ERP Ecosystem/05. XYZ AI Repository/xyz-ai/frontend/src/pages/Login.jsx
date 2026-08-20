import { useState } from "react";
import { login } from "../services/api";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(username, password);
      onLogin(data); // { access_token, role, profile_id }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.brandRow}>
          <div style={styles.mark}>XYZ</div>
          <div>
            <div className="display" style={styles.wordmark}>XYZ AI</div>
            <div className="mono-label" style={styles.tagline}>School Assistant</div>
          </div>
        </div>

        <p style={styles.intro}>
          Sign in to chat with your role-aware assistant — attendance,
          support, and escalation to real staff, in your language.
        </p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            <span className="mono-label" style={styles.labelText}>Username</span>
            <input
              autoFocus
              placeholder="e.g. parent_sunita"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
            />
          </label>

          <label style={styles.label}>
            <span className="mono-label" style={styles.labelText}>Password</span>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
            />
          </label>

          {error && (
            <div style={styles.errorBox}>
              <span style={styles.errorText}>{error}</span>
            </div>
          )}

          <button disabled={loading || !username || !password} style={styles.submitBtn}>
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <div style={styles.footNote}>
          Student · Parent · Teacher · Principal — one assistant, role-aware access.
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
    background: "linear-gradient(135deg, var(--paper) 0%, var(--sage) 150%)",
  },
  card: {
    width: 400,
    maxWidth: "100%",
    background: "var(--panel)",
    border: "1px solid var(--line)",
    borderRadius: 18,
    padding: "40px 34px 32px",
    boxShadow: "0 20px 50px -12px rgba(0,0,0,0.18), 0 4px 14px -4px rgba(0,0,0,0.08)",
  },
  brandRow: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    marginBottom: 20,
  },
  mark: {
    width: 48,
    height: 48,
    borderRadius: "50%",
    background: "linear-gradient(135deg, var(--teal), var(--teal-dark, var(--teal)))",
    color: "var(--paper)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: 0.5,
    flexShrink: 0,
    boxShadow: "0 4px 10px -2px rgba(0,0,0,0.25)",
  },
  wordmark: {
    fontSize: 23,
    fontWeight: 600,
    lineHeight: 1.1,
  },
  tagline: {
    marginTop: 3,
    opacity: 0.75,
  },
  intro: {
    fontSize: 13.5,
    color: "var(--ink-soft)",
    lineHeight: 1.6,
    margin: "0 0 28px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: 7,
  },
  labelText: {
    fontSize: 11,
    color: "var(--ink-soft)",
    letterSpacing: 0.4,
  },
  input: {
    border: "1px solid var(--line)",
    borderRadius: 8,
    background: "var(--paper)",
    padding: "10px 12px",
    fontSize: 14.5,
    color: "var(--ink)",
    outline: "none",
    transition: "border-color 0.15s ease",
  },
  errorBox: {
    background: "#fdeeee",
    border: "1px solid #e8b4b4",
    borderRadius: 8,
    padding: "10px 12px",
  },
  errorText: {
    fontSize: 13,
    color: "#a33",
  },
  submitBtn: {
    background: "var(--teal)",
    color: "var(--paper)",
    border: "none",
    borderRadius: 8,
    padding: "13px 0",
    fontSize: 14.5,
    fontWeight: 600,
    marginTop: 6,
    cursor: "pointer",
    boxShadow: "0 4px 12px -3px rgba(0,0,0,0.25)",
    transition: "opacity 0.15s ease",
  },
  footNote: {
    marginTop: 26,
    paddingTop: 20,
    borderTop: "1px solid var(--line)",
    fontSize: 11.5,
    color: "var(--ink-soft)",
    textAlign: "center",
    letterSpacing: 0.3,
    lineHeight: 1.6,
  },
};