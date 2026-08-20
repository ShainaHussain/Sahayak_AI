export const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिंदी" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "mr", label: "मराठी" },
  { code: "bn", label: "বাংলা" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "pa", label: "ਪੰਜਾਬੀ" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "ml", label: "മലയാളം" },
  { code: "ur", label: "اردو" },
];

export default function LanguageSelector({ value, onChange }) {
  return (
    <select
      className="mono-label"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        background: "var(--panel)",
        border: "1px solid var(--line)",
        borderRadius: 6,
        padding: "5px 8px",
        color: "var(--ink-soft)",
        fontSize: 12,
      }}
    >
      {LANGUAGES.map((l) => (
        <option key={l.code} value={l.code}>{l.label}</option>
      ))}
    </select>
  );
}