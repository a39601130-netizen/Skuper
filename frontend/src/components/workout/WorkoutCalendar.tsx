import { useEffect, useState } from 'react';
import { getWorkoutCalendar } from '../../api/client';
import type { WorkoutCalendarEntry } from '../../types';

interface Props {
  onSelectWorkout?: (id: number) => void;
}

export default function WorkoutCalendar({ onSelectWorkout }: Props) {
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [entries, setEntries] = useState<WorkoutCalendarEntry[]>([]);

  useEffect(() => {
    getWorkoutCalendar(month, year).then(setEntries).catch(() => {});
  }, [month, year]);

  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDayOfWeek = (new Date(year, month - 1, 1).getDay() + 6) % 7; // Monday = 0
  const entryMap = new Map(entries.map((e) => [e.date, e]));

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(year - 1); }
    else setMonth(month - 1);
  };
  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear(year + 1); }
    else setMonth(month + 1);
  };

  const MONTH_NAMES = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
    'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <button className="btn btn-ghost" onClick={prevMonth} style={{ padding: '4px 12px' }}>&lt;</button>
        <div className="card-title" style={{ margin: 0 }}>{MONTH_NAMES[month - 1]} {year}</div>
        <button className="btn btn-ghost" onClick={nextMonth} style={{ padding: '4px 12px' }}>&gt;</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2, textAlign: 'center' }}>
        {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((d) => (
          <div key={d} style={{ fontSize: 11, color: 'var(--text-secondary)', padding: 4 }}>{d}</div>
        ))}

        {Array.from({ length: firstDayOfWeek }).map((_, i) => (
          <div key={`empty-${i}`} />
        ))}

        {Array.from({ length: daysInMonth }).map((_, i) => {
          const day = i + 1;
          const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
          const entry = entryMap.get(dateStr);
          const isToday = dateStr === new Date().toISOString().split('T')[0];

          return (
            <div key={day}
              onClick={() => entry && onSelectWorkout?.(entry.id)}
              style={{
                padding: 6, borderRadius: 8, fontSize: 13, cursor: entry ? 'pointer' : 'default',
                background: entry
                  ? entry.day_type === 'A' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(52, 211, 153, 0.2)'
                  : 'transparent',
                border: isToday ? '2px solid var(--accent)' : '2px solid transparent',
                fontWeight: isToday ? 700 : 400,
              }}>
              {day}
              {entry && (
                <div style={{ fontSize: 9, color: entry.day_type === 'A' ? '#6366f1' : '#34d399' }}>
                  {entry.day_type}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
