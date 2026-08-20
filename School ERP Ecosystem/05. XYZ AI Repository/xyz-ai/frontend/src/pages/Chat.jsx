import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { sendMessage } from "../services/api";
import LanguageSelector from "../components/LanguageSelector";
import { useVoice } from "../hooks/useVoice";
import AvatarIndicator from "../components/AvatarIndicator";

const PERSONA = {
  student: { label: "Academic Assistant", initials: "AA", accent: "var(--teal)" },
  parent: { label: "Parent Support Assistant", initials: "PS", accent: "var(--gold)" },
  teacher: { label: "Teaching Assistant", initials: "TA", accent: "var(--ink)" },
  principal: { label: "Management Assistant", initials: "MA", accent: "var(--teal-dark)" },
};

const ESCALATION_ROLES = ["student", "parent"];

export default function Chat({ session, onLogout }) {
  const persona = PERSONA[session.role] || PERSONA.student;
  const [messages, setMessages] = useState([
    { role: "assistant", text: `Hi, I'm XYZ AI — your ${persona.label.toLowerCase()}. How can I help today?` },
  ]);
  const [language, setLanguage] = useState("en");
  const {
    isListening,
    isSpeaking,
    voiceSupported,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  } = useVoice(language);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function pushMessageAndReply(text) {
    if (!text.trim() || sending) return;

    const userMsg = { role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const data = await sendMessage(session.access_token, text, language);
      setMessages((prev) => [...prev, { role: "assistant", text: data.response }]);
      speak(data.response);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", text: `Something went wrong: ${err.message}` }]);
    } finally {
      setSending(false);
    }
  }

  function handleSend(e) {
    e.preventDefault();
    pushMessageAndReply(input);
  }

  function handleQuickAction(text) {
    pushMessageAndReply(text);
  }

  function handleMicClick() {
    if (isListening) {
      stopListening();
      return;
    }
    startListening(
      (transcript) => {
        setInput(transcript);
        pushMessageAndReply(transcript);
      },
      (errMsg) => {
        setMessages((prev) => [...prev, { role: "assistant", text: errMsg }]);
      }
    );
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>

        <div style={styles.header}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <AvatarIndicator role={session.role} isSpeaking={isSpeaking} isListening={isListening} />
            <div style={{ ...styles.badge, background: persona.accent }}>{persona.initials}</div>
            <div>
              <div className="display" style={styles.personaName}>{persona.label}</div>
              <div className="mono-label">{session.role} · {session.profile_id}</div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <LanguageSelector value={language} onChange={setLanguage} />
            <button onClick={onLogout} style={styles.logoutBtn}>Sign out</button>
          </div>
        </div>

        <div style={styles.divider} />

        <div style={styles.messages}>
          {messages.map((m, i) => (
            <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              <div
                className={m.role === "user" ? "user-bubble" : "assistant-bubble"}
                style={m.role === "user" ? styles.userBubble : styles.assistantBubble}
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
              </div>
            </div>
          ))}
          {sending && <p style={styles.typing}>XYZ AI is typing…</p>}
          <div ref={bottomRef} />
        </div>

        {ESCALATION_ROLES.includes(session.role) && (
          <div style={styles.quickActions}>
            <button
              type="button"
              disabled={sending}
              style={styles.quickBtn}
              onClick={() => handleQuickAction("I want to talk to my child's teacher.")}
            >
              Talk to Teacher
            </button>
            <button
              type="button"
              disabled={sending}
              style={styles.quickBtn}
              onClick={() => handleQuickAction("I want to contact school management.")}
            >
              Contact School Management
            </button>
          </div>
        )}

        <form onSubmit={handleSend} style={styles.inputBar}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Write a message…"
            style={styles.textInput}
          />
          <button
            type="button"
            onClick={handleMicClick}
            disabled={!voiceSupported.stt || sending}
            style={{
              ...styles.iconBtn,
              background: isListening ? "var(--gold)" : "var(--panel)",
              opacity: voiceSupported.stt ? 1 : 0.4,
            }}
            title={voiceSupported.stt ? "Speak your message" : "Voice not supported for this language"}
          >
            {isListening ? "● Listening…" : "🎤"}
          </button>
          {isSpeaking && (
            <button type="button" onClick={stopSpeaking} style={styles.iconBtn} title="Stop speaking">
              ⏹
            </button>
          )}
          <button disabled={sending || !input.trim()} style={styles.sendBtn}>Send</button>
        </form>

      </div>
    </div>
  );
}

const styles = {
  page: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 20 },
  card: {
    width: 640,
    maxWidth: "100%",
    background: "var(--panel)",
    border: "1px solid var(--line)",
    borderRadius: 14,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "20px 24px",
  },
  badge: {
    width: 40, height: 40, borderRadius: "50%",
    display: "flex", alignItems: "center", justifyContent: "center",
    color: "var(--paper)", fontFamily: "'IBM Plex Mono', monospace",
    fontSize: 13, fontWeight: 500, flexShrink: 0,
  },
  personaName: { fontSize: 18, fontWeight: 600 },
  logoutBtn: {
    background: "none", border: "none", color: "var(--ink-soft)",
    fontSize: 13.5, textDecoration: "underline", padding: 0,
  },
  divider: { height: 1, background: "var(--line)" },
  messages: {
    height: 380, overflowY: "auto", padding: "20px 24px",
    display: "flex", flexDirection: "column", gap: 14,
    background: "var(--paper)",
  },
  userBubble: {
    background: "var(--ink)", color: "var(--paper)",
    padding: "10px 15px", borderRadius: "12px 12px 2px 12px",
    maxWidth: "78%", fontSize: 14.5, lineHeight: 1.5,
  },
  assistantBubble: {
    background: "var(--sage)", color: "var(--ink)",
    padding: "10px 15px", borderRadius: "12px 12px 12px 2px",
    maxWidth: "78%", fontSize: 14.5, lineHeight: 1.5,
  },
  typing: { fontSize: 13, color: "var(--ink-soft)", fontStyle: "italic", margin: 0 },
  quickActions: {
    display: "flex", gap: 8, padding: "12px 24px 0",
    borderTop: "1px solid var(--line)", background: "var(--panel)",
  },
  quickBtn: {
    background: "var(--sage)", color: "var(--ink)", border: "1px solid var(--line)",
    borderRadius: 20, padding: "6px 14px", fontSize: 13, fontWeight: 500,
  },
  inputBar: {
    display: "flex", gap: 10, padding: "16px 24px",
    borderTop: "1px solid var(--line)", background: "var(--panel)",
  },
  textInput: {
    flex: 1, border: "none", borderBottom: "1.5px solid var(--line)",
    background: "transparent", padding: "8px 2px", color: "var(--ink)",
  },
  iconBtn: {
    border: "1px solid var(--line)", borderRadius: 8, padding: "0 12px",
    fontSize: 13, color: "var(--ink)", cursor: "pointer",
  },
  sendBtn: {
    background: "var(--teal)", color: "var(--paper)", border: "none",
    borderRadius: 8, padding: "0 20px", fontSize: 14.5, fontWeight: 500,
  },
};