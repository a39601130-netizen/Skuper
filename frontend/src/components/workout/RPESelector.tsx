interface Props {
  onSelect: (rpe: number) => void;
}

const RPE_COLORS: Record<number, string> = {
  5: '#4ade80',
  6: '#86efac',
  7: '#fbbf24',
  8: '#f97316',
  9: '#ef4444',
  10: '#dc2626',
};

const RPE_LABELS: Record<number, string> = {
  5: 'Легко',
  6: 'Умеренно',
  7: 'Средне',
  8: 'Тяжело',
  9: 'Очень тяжело',
  10: 'Максимум',
};

export default function RPESelector({ onSelect }: Props) {
  return (
    <div className="card">
      <div className="card-title">RPE — Как тяжело было?</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        {[5, 6, 7, 8, 9, 10].map((rpe) => (
          <button key={rpe} className="btn btn-ghost"
            style={{
              borderColor: RPE_COLORS[rpe],
              color: RPE_COLORS[rpe],
              fontWeight: 700,
              fontSize: 16,
            }}
            onClick={() => {
              window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
              onSelect(rpe);
            }}>
            <div>{rpe}</div>
            <div style={{ fontSize: 10, fontWeight: 400 }}>{RPE_LABELS[rpe]}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
