import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { getDailySpending } from '../../api/client';
import type { DailySpending } from '../../types';

export default function SpendingTrendChart() {
  const [data, setData] = useState<DailySpending[]>([]);

  useEffect(() => {
    getDailySpending().then(setData).catch(() => {});
  }, []);

  if (data.length < 2) return null;

  const chartData = data.map((d) => ({
    date: d.date.slice(5), // MM-DD
    total: Math.round(d.total),
  }));

  return (
    <div className="card">
      <div className="card-title">Расходы по дням</div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={chartData}>
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} width={40} />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 8, fontSize: 13,
            }}
          />
          <Line type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
