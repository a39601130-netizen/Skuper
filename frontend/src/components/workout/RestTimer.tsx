import { useState, useEffect, useRef } from 'react';

interface Props {
  seconds: number;
  onComplete: () => void;
  onSkip: () => void;
}

export default function RestTimer({ seconds, onComplete, onSkip }: Props) {
  const [remaining, setRemaining] = useState(seconds);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
          onComplete();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [seconds, onComplete]);

  const mins = Math.floor(remaining / 60);
  const secs = remaining % 60;
  const progress = ((seconds - remaining) / seconds) * 100;

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'var(--bg-primary)',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', zIndex: 100,
    }}>
      <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 16 }}>
        ОТДЫХ
      </div>
      <div style={{ fontSize: 72, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
        {mins}:{secs.toString().padStart(2, '0')}
      </div>
      <div className="progress-bar" style={{ width: '80%', marginTop: 24 }}>
        <div className="progress-fill ok" style={{ width: `${progress}%`, transition: 'width 1s linear' }} />
      </div>
      <button className="btn btn-ghost" style={{ marginTop: 32 }} onClick={() => {
        if (intervalRef.current) clearInterval(intervalRef.current);
        onSkip();
      }}>
        Пропустить
      </button>
    </div>
  );
}
