import { useState, useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { SuggestedQuestions } from './SuggestedQuestions';

export function ChatWindow({ portfolio }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async (overrideInput) => {
    const userMessage = overrideInput || input;
    if (!userMessage.trim() || isLoading) return;
    
    setInput('');
    setIsLoading(true);

    const newMessages = [...messages, { role: 'user', content: userMessage }];
    setMessages([...newMessages, { role: 'assistant', content: '', sources: [], signals: [], thinking: '' }]);

    try {
      const response = await fetch('http://localhost:8003/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: userMessage, 
          portfolio,
          conversation_history: newMessages.slice(-5) 
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(l => l.trim().startsWith('data: '));
        
        for (const line of lines) {
          const eventText = line.substring(5).trim();
          if (!eventText) continue;
          
          try {
            const event = JSON.parse(eventText);

            setMessages(prev => {
              const updated = [...prev];
              const last = { ...updated[updated.length - 1] };

              if (event.type === 'thinking') last.thinking = event.content;
              if (event.type === 'token') {
                  last.content += event.content;
              }
              if (event.type === 'signal_card') last.signals = [...(last.signals || []), event.content];
              if (event.type === 'source') last.sources = [...(last.sources || []), { url: event.url, title: event.title }];
              if (event.type === 'done') { 
                  last.thinking = ''; 
                  setIsLoading(false); 
              }
              if (event.type === 'error') {
                  last.content += `\n\nERROR: ${event.content}`;
                  setIsLoading(false);
              }

              updated[updated.length - 1] = last;
              return updated;
            });
          } catch(e) {
            console.error("Parse error logic", e, line);
          }
        }
      }
    } catch (e) {
      setMessages(p => [...p, { role: 'assistant', content: `[SYSTEM ERROR] Failed to connect: ${e.message}` }]);
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      
      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
        {messages.length === 0 && (
          <div className="animate-in" style={{ marginBottom: 24 }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.10em' }}>SYSTEM ADVISOR READY</span>
            <SuggestedQuestions onSelect={sendMessage} />
          </div>
        )}
        {messages.map((msg, i) => <MessageBubble key={i} message={msg} />)}
      </div>

      <div style={{ padding: 12, borderTop: '1px solid var(--border)', background: 'var(--bg-white)' }}>
        <div style={{ display: 'flex', alignItems: 'center', background: '#2c2c2c', border: '1px solid #444', height: 28 }}>
          <span style={{ color: '#888', fontSize: 11, padding: '0 8px', fontFamily: 'var(--mono)', flexShrink: 0 }}>
            PROMPT
          </span>
          <input 
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            disabled={isLoading}
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: '#fff', fontSize: 12, fontFamily: 'var(--mono)', caretColor: 'var(--green)',
            }} 
            placeholder="Query your portfolio..." 
          />
          <button 
            disabled={isLoading}
            onClick={() => sendMessage()}
            style={{
              background: isLoading ? 'var(--header-muted)' : 'var(--green)', border: 'none', color: '#fff',
              width: 36, height: 28, cursor: isLoading ? 'not-allowed' : 'pointer', fontSize: 14,
              display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'background 0.2s'
            }}>
            ›
          </button>
        </div>
      </div>
    </div>
  );
}
