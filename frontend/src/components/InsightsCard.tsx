import { useEffect, useState } from 'react';
import { getInsights } from '../api/client';

export default function InsightsCard() {
  const [insights, setInsights] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getInsights()
      .then((data) => setInsights(data.insights))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading || insights.length === 0) return null;

  return (
    <div className="card">
      <div className="card-title">AI Инсайты</div>
      {insights.map((insight, i) => (
        <div key={i} style={{
          padding: '8px 12px', marginBottom: 8,
          background: 'var(--bg-secondary)', borderRadius: 8,
          fontSize: 13, lineHeight: 1.5,
        }}>
          {insight}
        </div>
      ))}
    </div>
  );
}
