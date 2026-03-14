import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import type { Category } from '../../types';

const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe',
  '#f472b6', '#fb7185', '#f97316', '#fbbf24', '#34d399'];

interface Props {
  categories: Category[];
}

export default function ExpensePieChart({ categories }: Props) {
  const data = categories
    .filter((c) => c.type === 'Расход' && c.spent > 0)
    .sort((a, b) => b.spent - a.spent)
    .slice(0, 10)
    .map((c) => ({ name: c.name, value: c.spent, emoji: c.emoji }));

  if (data.length === 0) return null;

  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="card">
      <div className="card-title">Расходы по категориям</div>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%"
            innerRadius={50} outerRadius={80} paddingAngle={2}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div style={{ marginTop: 8 }}>
        {data.map((d, i) => (
          <div key={d.name} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
            <span>
              <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
                background: COLORS[i % COLORS.length], marginRight: 6 }} />
              {d.emoji} {d.name}
            </span>
            <span>{d.value.toFixed(0)} ({((d.value / total) * 100).toFixed(0)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}
