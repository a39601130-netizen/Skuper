import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import BottomNav from './components/BottomNav';
import { ToastProvider } from './components/Toast';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import AddTransactionPage from './pages/AddTransactionPage';

// Lazy-loaded pages (heavy deps like recharts, large components)
const ExpensesPage = lazy(() => import('./pages/ExpensesPage'));
const WorkoutsPage = lazy(() => import('./pages/WorkoutsPage'));
const WorkoutHistoryPage = lazy(() => import('./pages/WorkoutHistoryPage'));
const ExerciseProgressPage = lazy(() => import('./pages/ExerciseProgressPage'));
const WorkoutSessionPage = lazy(() => import('./pages/WorkoutSessionPage'));
const AdvisorPage = lazy(() => import('./pages/AdvisorPage'));
const IncomeStatsPage = lazy(() => import('./pages/IncomeStatsPage'));

function PageLoader() {
  return <div className="page"><div className="loading">Загрузка...</div></div>;
}

export default function App() {
  return (
    <ToastProvider>
      <div className="app">
        <a href="#main-content" className="skip-link">Перейти к контенту</a>
        <main id="main-content">
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/add" element={<AddTransactionPage />} />
              <Route path="/income" element={<IncomeStatsPage />} />
              <Route path="/expenses" element={<ExpensesPage />} />
              <Route path="/workouts" element={<WorkoutsPage />} />
              <Route path="/workout-history" element={<WorkoutHistoryPage />} />
              <Route path="/exercise-progress" element={<ExerciseProgressPage />} />
              <Route path="/workout/session" element={<WorkoutSessionPage />} />
              <Route path="/advisor" element={<AdvisorPage />} />
            </Routes>
          </Suspense>
        </main>
        <BottomNav />
      </div>
    </ToastProvider>
  );
}
