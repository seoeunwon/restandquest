import React, { useState, useEffect } from "react";
import "./chatbot.css";

type ChatPopupProps = {
  onClose: () => void;
};

const ChatPopup: React.FC<ChatPopupProps> = ({ onClose }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    setMessages([
      "Bot: Welcome to the Chatbot! You can ask anything. e.g., 'Where is the best place to wait after 30 minutes?'",
    ]);
  }, []);

  const handleSend = () => {
    if (!input) return;
    setMessages([...messages, `You: ${input}`, `Bot: work in progress...`]);
    setInput("");
  };

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-content" onClick={(e) => e.stopPropagation()}>
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
        </div>

        <div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question..."
          />
          <button onClick={handleSend}>Send</button>
        </div>
      </div>
    </div>
  );
};

export default ChatPopup;
