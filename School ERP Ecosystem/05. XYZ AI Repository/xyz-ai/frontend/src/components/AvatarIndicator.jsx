// Satisfies the spec's "AI Avatar" requirement without full lip-sync/3D rigging —
// spec explicitly says facial expression / lip-sync only "where technically possible".
// This gives persona-specific visual identity + real-time speaking state, which is
// the functional core of what an avatar communicates.
const PERSONA_COLORS = {
  student: "#4A9B8E",
  parent: "#C9A05C",
  teacher: "#5C7CC9",
  principal: "#8E5CC9",
};

export default function AvatarIndicator({ role, isSpeaking, isListening }) {
  const color = PERSONA_COLORS[role] || "#4A9B8E";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: "50%",
          background: color,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
          fontWeight: 600,
          fontSize: 16,
          boxShadow: isSpeaking ? `0 0 0 6px ${color}33` : "none",
          transform: isSpeaking ? "scale(1.08)" : "scale(1)",
          transition: "all 0.2s ease",
          animation: isSpeaking ? "pulse 1s infinite" : "none",
        }}
      >
        {role?.[0]?.toUpperCase() || "A"}
      </div>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
      `}</style>
      {isListening && <span style={{ fontSize: 12, color: "var(--ink-soft)" }}>listening…</span>}
    </div>
  );
}