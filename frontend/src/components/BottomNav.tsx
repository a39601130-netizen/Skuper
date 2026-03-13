import { useLocation, useNavigate } from 'react-router-dom';

const tabs = [
  { path: '/', icon: '📊', label: 'Главная' },
  { path: '/history', icon: '📜', label: 'История' },
  { path: '/add', icon: '➕', label: 'Добавить' },
  { path: '/workouts', icon: '🏋️', label: 'Тренировки' },
  { path: '/advisor', icon: '🤖', label: 'AI' },
];

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav className="bottom-nav">
      {tabs.map((tab) => (
        <button
          key={tab.path}
          className={`nav-item ${location.pathname === tab.path ? 'active' : ''}`}
          onClick={() => {
            navigate(tab.path);
            window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
          }}
        >
          <span className="nav-icon">{tab.icon}</span>
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
