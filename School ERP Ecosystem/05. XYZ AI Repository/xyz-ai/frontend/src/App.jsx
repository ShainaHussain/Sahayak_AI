import { useState } from "react";
import Login from "./pages/Login";
import Chat from "./pages/Chat";

export default function App() {
  const [session, setSession] = useState(null);

  if (!session) {
    return <Login onLogin={setSession} />;
  }

  return <Chat session={session} onLogout={() => setSession(null)} />;
}