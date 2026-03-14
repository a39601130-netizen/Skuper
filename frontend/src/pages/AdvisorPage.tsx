import { useState, useEffect, useRef } from 'react';
import { askAdvisor } from '../api/client';
import type { AdvisorMessage } from '../types';

const STORAGE_KEY = 'advisor_history';
const MAX_HISTORY = 50;

function loadHistory(): AdvisorMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed.slice(-MAX_HISTORY);
    }
  } catch { /* ignore */ }
  return [];
}

function saveHistory(messages: AdvisorMessage[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-MAX_HISTORY)));
  } catch { /* ignore */ }
}

export default function AdvisorPage() {
  const [messages, setMessages] = useState<AdvisorMessage[]>(loadHistory);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [context, setContext] = useState<'finance' | 'workout'>('finance');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    saveHistory(messages);
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const send = async () => {
    const question = input.trim();
    if (!question || loading) return;

    setInput('');
    const newMessages = [...messages, { role: 'user' as const, text: question }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const historyForApi = newMessages.slice(-10).map((m) => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        text: m.text,
      }));
      const { response } = await askAdvisor(
        question, context, 'default', `advisor_${context}`, historyForApi,
      );
      setMessages((prev) => [...prev, { role: 'ai', text: response }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'ai', text: 'Ошибка. Попробуйте позже.' }]);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 className="page-title" style={{ margin: 0 }}>AI Советник</h1>
        {messages.length > 0 && (
          <button className="btn btn-ghost" style={{ fontSize: 12, padding: '4px 8px' }}
            onClick={clearHistory}>
            Очистить
          </button>
        )}
      </div>

      {/* Context toggle */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, marginTop: 8 }}>
        <button className={`btn ${context === 'finance' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setContext('finance')}>
          Финансы
        </button>
        <button className={`btn ${context === 'workout' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setContext('workout')}>
          Тренировки
        </button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', marginBottom: 12 }}>
        {messages.length === 0 && (
          <div className="empty">
            <div className="empty-icon">🤖</div>
            Задай вопрос о финансах или тренировках
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{
            padding: '10px 14px',
            marginBottom: 8,
            borderRadius: 12,
            maxWidth: '85%',
            ...(msg.role === 'user'
              ? { marginLeft: 'auto', background: 'var(--accent)', color: 'white' }
              : { background: 'var(--bg-card)' }),
            whiteSpace: 'pre-wrap',
            fontSize: 14,
            lineHeight: 1.5,
          }}>
            {msg.text}
          </div>
        ))}
        {loading && (
          <div style={{ padding: '10px 14px', background: 'var(--bg-card)', borderRadius: 12, maxWidth: '85%' }}>
            Думаю...
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Задайте вопрос..."
          style={{
            flex: 1, padding: '12px', fontSize: 15,
            background: 'var(--bg-card)', color: 'var(--text-primary)',
            border: '1px solid var(--border)', borderRadius: 10,
          }}
        />
        <button className="btn btn-primary" onClick={send} disabled={loading || !input.trim()}>
          ➤
        </button>
      </div>
    </div>
  );
}
