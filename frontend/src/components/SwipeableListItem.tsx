import { useRef, useState, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  onDelete: () => void;
}

export default function SwipeableListItem({ children, onDelete }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const startX = useRef(0);
  const [offset, setOffset] = useState(0);
  const [swiping, setSwiping] = useState(false);

  const handleTouchStart = (e: React.TouchEvent) => {
    startX.current = e.touches[0].clientX;
    setSwiping(true);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!swiping) return;
    const diff = startX.current - e.touches[0].clientX;
    if (diff > 0) {
      setOffset(Math.min(diff, 80));
    } else {
      setOffset(0);
    }
  };

  const handleTouchEnd = () => {
    setSwiping(false);
    if (offset > 60) {
      setOffset(80);
    } else {
      setOffset(0);
    }
  };

  return (
    <div style={{ position: 'relative', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', right: 0, top: 0, bottom: 0, width: 80,
        background: 'var(--danger)', display: 'flex', alignItems: 'center',
        justifyContent: 'center', color: 'white', fontWeight: 600, fontSize: 13,
        cursor: 'pointer',
      }} onClick={() => {
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
        onDelete();
      }}>
        Удалить
      </div>
      <div ref={ref}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{
          transform: `translateX(-${offset}px)`,
          transition: swiping ? 'none' : 'transform 0.2s ease',
          position: 'relative', zIndex: 1, background: 'var(--bg-card)',
        }}>
        {children}
      </div>
    </div>
  );
}
