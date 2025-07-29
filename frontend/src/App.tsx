import { useState, useRef, useEffect } from 'react';
import './App.css';
import ChatMessage from './components/ChatMessage';
import MessageInput from './components/MessageInput';

interface Message {
  id: string
  text: string
  sender: 'user' | 'jarvis'
  timestamp: Date
}

function App() {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem('jarvis-chat-history');
      if (saved) {
        const parsed = JSON.parse(saved);
        return parsed.map((msg: Message) => ({ ...msg, timestamp: new Date(msg.timestamp) }));
      }
    } catch (error) {
      console.error("Failed to load messages from local storage:", error);
    }
    return [{
      id: '1',
      text: "Hello! I'm Jarvis, your AI assistant. How can I help you today?",
      sender: 'jarvis',
      timestamp: new Date()
    }];
  });

  useEffect(() => {
    // Always save the current conversation to local storage when messages change.
    localStorage.setItem('jarvis-chat-history', JSON.stringify(messages));
  }, [messages]);

  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Check backend connection
    checkBackendConnection()
  }, [])

  const checkBackendConnection = async () => {
    try {
      // Use a simple GET request to the root to check for connectivity.
      const response = await fetch('http://127.0.0.1:8000/');
      setIsConnected(response.ok);
    } catch (error) {
      console.error('Connection check failed:', error);
      setIsConnected(false);
    }
  };

  const sendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ query: message, stream: true }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const processStream = async () => {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
      
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep the last, possibly incomplete line

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const json = JSON.parse(line.substring(6));
                if (json.content) {
                  setMessages(prev => {
                    const lastMessage = prev[prev.length - 1];
                    if (lastMessage.sender === 'jarvis') {
                      const updatedMessages = [...prev];
                      updatedMessages[prev.length - 1] = { ...lastMessage, text: lastMessage.text + json.content };
                      return updatedMessages;
                    } else {
                      return [...prev, { id: (Date.now() + 1).toString(), sender: 'jarvis', text: json.content, timestamp: new Date() }];
                    }
                  });
                }
              } catch (e) {
                console.error('Failed to parse stream data:', line, e);
              }
            }
          }
        }
      };

      await processStream();

    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I\'m having trouble connecting to my backend. Please make sure the server is running.',
        sender: 'jarvis',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }



  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedMessageId(id);
      setTimeout(() => setCopiedMessageId(null), 2000); // Reset after 2 seconds
    }).catch(err => {
      console.error('Failed to copy text: ', err);
    });
  };



  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">🤖</div>
            <h1>Jarvis AI</h1>
          </div>
          <div className="status">
            <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></div>
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages">
          {messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message} 
              copiedMessageId={copiedMessageId} 
              onCopy={handleCopy} 
            />
          ))}
          {isLoading && (
            <div className="message jarvis">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <MessageInput onSendMessage={sendMessage} isLoading={isLoading} />
    </div>
  )
}

export default App
