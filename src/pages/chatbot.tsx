import React, { useEffect, useRef, useState } from "react";
import "./chatbot.css";

type ChatPopupProps = {
  onClose: () => void;
  onHoursDetected?: (hours: number, transcript: string) => void; // NEW: lift value to parent if needed
};

// ---------------- Helpers ----------------
function supportsSpeechRecognition(): boolean {
  return (
      typeof window !== "undefined" &&
      (window.SpeechRecognition !== undefined ||
          window.webkitSpeechRecognition !== undefined)
  );
}

function parseHoursFromText(text: string): number | null {
  const cleaned = text.toLowerCase().trim();

  // numeric first: "2", "2.5 hours", "1 hr"
  const numMatch = cleaned.match(/(\d+(?:\.\d+)?)\s*(hour|hours|hr|hrs)?\b/);
  if (numMatch) return parseFloat(numMatch[1]);

  // words: "two", "two and a half", "one and quarter"
  const numberWords: Record<string, number> = {
    zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5,
    six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
    eleven: 11, twelve: 12,
  };
  const fracWords: Record<string, number> = {
    half: 0.5,
    quarter: 0.25,
    "three quarters": 0.75,
  };

  const andFrac = cleaned.match(
      /\b([a-z]+)\s+(?:and\s+)?(?:a\s+)?(half|quarter|three quarters)\b/
  );
  if (andFrac) {
    const base = numberWords[andFrac[1]];
    const frac = fracWords[andFrac[2]];
    if (typeof base === "number" && typeof frac === "number") return base + frac;
  }

  const wordMatch = cleaned.match(
      /\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b/
  );
  if (wordMatch) return numberWords[wordMatch[1]];

  return null;
}

// Centralized handler used by BOTH speech and typed input
function processUtterance(
    text: string,
    setMessages: React.Dispatch<React.SetStateAction<string[]>>,
    setLastHours: React.Dispatch<React.SetStateAction<number | null>>,
    onHoursDetected?: (hours: number, transcript: string) => void
) {
  setMessages(prev => [...prev, `You: ${text}`]);

  const hours = parseHoursFromText(text);
  setLastHours(hours);

  if (hours !== null) {
    if (onHoursDetected) onHoursDetected(hours, text);
    setMessages(prev => [
      ...prev,
      `Bot: Detected ${hours} hour${hours === 1 ? "" : "s"}.`,
    ]);
  } else {
    setMessages(prev => [...prev, "Bot: I didn’t catch a number of hours there."]);
  }
}

// ---------------- Component ----------------
const ChatPopup: React.FC<ChatPopupProps> = ({ onClose, onHoursDetected }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [interimText, setInterimText] = useState("");
  const [lastHours, setLastHours] = useState<number | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // initial welcome
  useEffect(() => {
    setMessages([
      "Bot: Welcome to the Chatbot! You can ask anything. e.g., 'Where is the best place to wait after 30 minutes?'",
    ]);
  }, []);

  // set up speech recognition
  useEffect(() => {
    const ok = supportsSpeechRecognition();
    setSupported(ok);
    if (!ok) return;

    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!SR) return;

    const recog = new SR();
    recog.lang = "en-US";
    recog.interimResults = true;
    recog.maxAlternatives = 1;
    recog.continuous = false;

    recog.onstart = () => {
      setListening(true);
      setInterimText("");
    };

    recog.onresult = (event: SpeechRecognitionEvent) => {
      const lastIdx = event.results.length - 1;
      const result = event.results[lastIdx];
      const transcript = result[0].transcript;
      const isFinal = result.isFinal;

      if (!isFinal) {
        setInterimText(transcript);
        return;
      }

      setInterimText("");
      processUtterance(transcript, setMessages, setLastHours, onHoursDetected);
    };

    recog.onerror = (e: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", e.error, e.message);
      setListening(false);
      setInterimText("");
      setMessages(prev => [
        ...prev,
        "Bot: (mic error — try again or check permissions)",
      ]);
    };

    recog.onend = () => setListening(false);

    recognitionRef.current = recog;

    return () => {
      try {
        recog.abort();
      } catch {
        /* ignore */
      }
    };
  }, [onHoursDetected]);

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    processUtterance(text, setMessages, setLastHours, onHoursDetected);
    setInput("");
  };

  const startListening = () => {
    recognitionRef.current?.start();
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
  };

  return (
      <div className="popup-overlay" onClick={onClose}>
        <div className="popup-content" onClick={e => e.stopPropagation()}>
          <button className="popup-close" onClick={onClose}>
            x
          </button>

          <div className="chat-messages">
            {messages.map((msg, idx) => {
              const isUser = msg.startsWith("You:");
              return (
                  <p key={idx} className={isUser ? "user-msg" : "bot-msg"}>
                    {msg.replace("You: ", "").replace("Bot: ", "")}
                  </p>
              );
            })}
            {listening && interimText && (
                <p className="user-msg user-msg--interim">{interimText}</p>
            )}
          </div>

          <div className="chat-input-row">
            <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Type your question..."
                onKeyDown={e => e.key === "Enter" && handleSend()}
            />

            <button
                className={`mic-btn ${listening ? "mic-btn--on" : ""}`}
                onClick={listening ? stopListening : startListening}
                disabled={!supported}
                title={
                  supported
                      ? (listening ? "Stop listening" : "Start voice input")
                      : "Speech recognition not supported"
                }
            >
              {listening ? "■" : "🎤"}
            </button>

            <button onClick={handleSend}>Send</button>
          </div>

          <div className="last-hours-hint">
            Last detected shift length: <strong>{lastHours ?? "–"}</strong>
          </div>
        </div>
      </div>
  );
};

export default ChatPopup;