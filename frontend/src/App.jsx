import { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello! Welcome to QuickCart. How can I help you today?",
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [theme, setTheme] = useState(
    () => localStorage.getItem("quickcart-theme") || "light"
  );

  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    localStorage.setItem("quickcart-theme", theme);
  }, [theme]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const hasUserMessage = messages.some((item) => item.role === "user");

  function toggleTheme() {
    setTheme((previous) => (previous === "light" ? "dark" : "light"));
  }

  function startVoiceInput() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is not supported. Please use Chrome.");
      return;
    }

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setListening(true);

    recognition.onresult = (event) => {
      setMessage(event.results[0][0].transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setListening(false);
    };

    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
  }

  async function sendMessage(event) {
    event.preventDefault();

    const userMessage = message.trim();
    if (!userMessage || loading) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", text: userMessage },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong.");
      }

      setMessages((previous) => [
        ...previous,
        { role: "assistant", text: data.response },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: "I could not connect to the server. Please check that the backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function chooseSuggestion(text) {
    setMessage(text);
  }

  return (
    <div className={`app theme-${theme}`}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">Q</div>
          <div className="brand-text">
            <h2>QuickCart</h2>
            <p>Customer Support</p>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="section-label">WORKSPACE</p>

          <div className="nav-item active">
            <span>⌂</span>
            AI Chat Support
          </div>
        </div>
        <div className="sidebar-bottom">
          <div className="sidebar-profile">
            <div className="profile-icon">
              <span>✦</span>
            </div>

            <div className="profile-info">
              <strong>QuickCart AI</strong>
              <span>Your shopping assistant</span>
            </div>

            <span className="online-dot"></span>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="page-heading">
            <h1>AI Customer Assistant</h1>
          </div>

          <button
            className="theme-button"
            type="button"
            onClick={toggleTheme}
            title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
            aria-label="Toggle theme"
          >
            {theme === "light" ? "☾" : "☀"}
          </button>
        </header>

        <section className="chat-area">
          {!hasUserMessage && (
            <div className="welcome">
              <div className="assistant-avatar">Q</div>
              <p className="welcome-label">QUICKCART SUPPORT</p>
              <h2>How can I help you today?</h2>
              <p className="welcome-description">
                Get help with your orders, store timings, or speak to our
                support team.
              </p>
            </div>
          )}

          <div className="messages">
            {messages.map((item, index) => (
              <div
                className={`message-row ${item.role}`}
                key={`${index}-${item.role}`}
              >
                {item.role === "assistant" && (
                  <div className="message-avatar">Q</div>
                )}

                <div className="message-content">
                  <span className="message-sender">
                    {item.role === "assistant"
                      ? "QuickCart Assistant"
                      : "You"}
                  </span>

                  <div className="message-bubble">{item.text}</div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="message-row assistant">
                <div className="message-avatar">Q</div>
                <div className="message-content">
                  <span className="message-sender">QuickCart Assistant</span>
                  <div className="message-bubble typing">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="chat-bottom">
            {!hasUserMessage && (
              <div className="quickstart">
                <div className="quickstart-heading">
                  <span className="quickstart-line" />
                  <span>QUICK START</span>
                </div>

                <div className="suggestions">
                  <button
                    type="button"
                    onClick={() =>
                      chooseSuggestion("What are your business hours?")
                    }
                  >
                    <span className="suggestion-icon">◷</span>
                    <span>
                      <strong>Store hours</strong>
                      <small>When are you open?</small>
                    </span>
                    <span className="suggestion-arrow">↗</span>
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      chooseSuggestion(
                        "What is my order status for QC1001?"
                      )
                    }
                  >
                    <span className="suggestion-icon">↗</span>
                    <span>
                      <strong>Track an order</strong>
                      <small>Check delivery status</small>
                    </span>
                    <span className="suggestion-arrow">↗</span>
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      chooseSuggestion("Can I speak to a human agent?")
                    }
                  >
                    <span className="suggestion-icon">♧</span>
                    <span>
                      <strong>Human support</strong>
                      <small>Talk to our team</small>
                    </span>
                    <span className="suggestion-arrow">↗</span>
                  </button>
                </div>
              </div>
            )}

            <form className="chat-form" onSubmit={sendMessage}>
              <button
                type="button"
                className={`mic-button ${listening ? "listening" : ""}`}
                onClick={startVoiceInput}
                title={listening ? "Stop listening" : "Speak your message"}
                aria-label="Voice input"
              >
                {listening ? "■" : "🎙"}
              </button>

              <input
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder={
                  listening
                    ? "Listening... speak now"
                    : "Type your message here..."
                }
                aria-label="Your message"
                disabled={loading}
              />

              <button
                className="send-button"
                type="submit"
                disabled={loading || !message.trim()}
              >
                {loading ? "Sending..." : "Send"}
                <span>↑</span>
              </button>
            </form>

            <p className="disclaimer">
              QuickCart AI Assistant · Demo environment · Sample order data
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;