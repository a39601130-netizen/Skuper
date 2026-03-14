import { useState } from 'react';
import { askAdvisor } from '../api/client';

interface Message {
  role: 'user' | 'ai';
  text: string;
}

export default function AdvisorPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [context, setContext] = useState<'finance' | 'workout'>('finance');

  const send = async () => {
    const question = input.trim();
    if (!question || loading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: question }]);
    setLoading(true);

    try {
      const { response } = await askAdvisor(question, context);
      setMessages((prev) => [...prev, { role: 'ai', text: response }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'ai', text: 'Ошибка. Попробуйте позже.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column' }}>
      <h1 className="page-title">AI Советник</h1>

      {/* Context toggle */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button className={`btn ${context === 'finance' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setContext('finance')}>
          💰 Финансы
        </button>
        <button className={`btn ${context === 'workout' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setContext('workout')}>
          🏋️ Тренировки
        </button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', marginBottom: 12 }}>
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
