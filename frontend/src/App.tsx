import { Routes, Route } from 'react-router-dom';
import BottomNav from './components/BottomNav';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import WorkoutsPage from './pages/WorkoutsPage';
import AdvisorPage from './pages/AdvisorPage';
import AddTransactionPage from './pages/AddTransactionPage';
import IncomeStatsPage from './pages/IncomeStatsPage';
import ExpensesPage from './pages/ExpensesPage';
import WorkoutHistoryPage from './pages/WorkoutHistoryPage';
import ExerciseProgressPage from './pages/ExerciseProgressPage';
import WorkoutSessionPage from './pages/WorkoutSessionPage';

export default function App() {
  return (
    <div className="app">
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
      <BottomNav />
    </div>
  );
}
