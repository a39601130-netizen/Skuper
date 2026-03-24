import { useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, History, PlusCircle, Dumbbell, Bot } from 'lucide-react';

const tabs = [
  { path: '/', icon: LayoutDashboard, label: 'Главная' },
  { path: '/history', icon: History, label: 'История' },
  { path: '/add', icon: PlusCircle, label: 'Добавить' },
  { path: '/workouts', icon: Dumbbell, label: 'Тренировки' },
  { path: '/advisor', icon: Bot, label: 'AI' },
];

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  // Determine context for accent coloring
  const isWorkoutContext = ['/workouts', '/workout-history', '/exercise-progress', '/workout/session'].some(
    (p) => location.pathname.startsWith(p)
  );

  return (
    <nav className="bottom-nav" role="navigation" aria-label="Основная навигация">
      {tabs.map((tab) => {
        const isActive = location.pathname === tab.path;
        const Icon = tab.icon;
        const isWorkoutTab = tab.path === '/workouts';
        const activeClass = isActive
          ? isWorkoutTab || isWorkoutContext ? 'active workout-active' : 'active'
          : '';

        return (
          <button
            key={tab.path}
            className={`nav-item ${activeClass}`}
            onClick={() => {
              navigate(tab.path);
              window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
            }}
            aria-label={tab.label}
            aria-current={isActive ? 'page' : undefined}
          >
            <Icon size={22} strokeWidth={isActive ? 2.5 : 2} />
            <span className="nav-label">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
