import { useState, useRef, useCallback } from "react";

const SPEECH_LANG_MAP = {
  en: "en-IN", hi: "hi-IN", ta: "ta-IN", te: "te-IN",
  mr: "mr-IN", bn: "bn-IN", gu: "gu-IN", pa: "pa-IN",
  kn: "kn-IN", ml: "ml-IN", ur: "ur-IN",
};

const getVoicesAsync = () => {
  return new Promise((resolve) => {
    let voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      resolve(voices);
      return;
    }
    const onVoicesChanged = () => {
      voices = window.speechSynthesis.getVoices();
      window.speechSynthesis.removeEventListener("voiceschanged", onVoicesChanged);
      resolve(voices);
    };
    window.speechSynthesis.addEventListener("voiceschanged", onVoicesChanged);
    // Safety timeout in case the event never fires on this browser
    setTimeout(() => resolve(window.speechSynthesis.getVoices()), 1000);
  });
};

export function useVoice(language) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState({ stt: true, tts: true });
  const recognitionRef = useRef(null);
  const speechLang = SPEECH_LANG_MAP[language] || "en-IN";

  const startListening = useCallback((onResult, onError) => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceSupported((s) => ({ ...s, stt: false }));
      onError?.("Speech recognition isn't supported in this browser. Use Chrome, or type instead.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = speechLang;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event) => onResult(event.results[0][0].transcript);
    recognition.onerror = (event) => {
      setIsListening(false);
      if (event.error === "language-not-supported") {
        setVoiceSupported((s) => ({ ...s, stt: false }));
        onError?.("Voice input isn't supported for this language yet. Please type instead.");
      } else if (event.error === "no-speech") {
        onError?.("Didn't catch that — try again.");
      } else {
        onError?.(`Voice input error: ${event.error}`);
      }
    };
    recognitionRef.current = recognition;
    recognition.start();
  }, [speechLang]);

  const stopListening = useCallback(() => recognitionRef.current?.stop(), []);

  const speak = useCallback(async (text) => {
    if (!window.speechSynthesis) {
      setVoiceSupported((s) => ({ ...s, tts: false }));
      return;
    }

    window.speechSynthesis.cancel();

    const voices = await getVoicesAsync();
    const match = voices.find((v) => v.lang === speechLang);
    const partialMatch = voices.find((v) => v.lang.startsWith(speechLang.split("-")[0]));

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speechLang;

    if (match) {
      utterance.voice = match;
    } else if (partialMatch) {
      utterance.voice = partialMatch;
    } else {
      // No installed voice can render this language at all — speaking would
      // silently fail or badly mispronounce, so surface it instead of pretending.
      setVoiceSupported((s) => ({ ...s, tts: false }));
      return;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  }, [speechLang]);

  const stopSpeaking = useCallback(() => {
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
  }, []);

  return { isListening, isSpeaking, voiceSupported, startListening, stopListening, speak, stopSpeaking };
}