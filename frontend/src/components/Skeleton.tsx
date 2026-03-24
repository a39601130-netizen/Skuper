interface SkeletonProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  className?: string;
}

export function Skeleton({ width = '100%', height = '16px', borderRadius = '8px', className = '' }: SkeletonProps) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{ width, height, borderRadius }}
      aria-hidden="true"
    />
  );
}

/** Skeleton for a card with stat value */
export function SkeletonCard() {
  return (
    <div className="card">
      <Skeleton width="80px" height="12px" borderRadius="4px" />
      <div style={{ marginTop: 8 }}>
        <Skeleton width="120px" height="24px" borderRadius="6px" />
      </div>
    </div>
  );
}

/** Skeleton for a list of items */
export function SkeletonList({ count = 4 }: { count?: number }) {
  return (
    <div className="card" style={{ padding: 0 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div className="list-item" key={i}>
          <Skeleton width="36px" height="36px" borderRadius="10px" />
          <div className="list-item-content" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <Skeleton width="60%" height="14px" />
            <Skeleton width="40%" height="12px" />
          </div>
          <Skeleton width="60px" height="16px" />
        </div>
      ))}
    </div>
  );
}

/** Full page loading skeleton for Dashboard */
export function DashboardSkeleton() {
  return (
    <div className="page" aria-busy="true" aria-label="Загрузка данных">
      <Skeleton width="100px" height="24px" borderRadius="6px" />
      <div style={{ marginTop: 16 }}>
        <Skeleton width="180px" height="16px" className="skeleton-center" />
      </div>
      <div className="grid-2" style={{ marginTop: 12 }}>
        <SkeletonCard />
        <SkeletonCard />
      </div>
      <SkeletonCard />
      <SkeletonList count={3} />
    </div>
  );
}

/** Full page loading skeleton for lists */
export function ListPageSkeleton() {
  return (
    <div className="page" aria-busy="true" aria-label="Загрузка данных">
      <Skeleton width="120px" height="24px" borderRadius="6px" />
      <div style={{ marginTop: 16 }}>
        <SkeletonList count={6} />
      </div>
    </div>
  );
}
