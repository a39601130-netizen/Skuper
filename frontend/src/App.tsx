import { Routes, Route } from 'react-router-dom';
import BottomNav from './components/BottomNav';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import WorkoutsPage from './pages/WorkoutsPage';
import AdvisorPage from './pages/AdvisorPage';
import AddTransactionPage from './pages/AddTransactionPage';
import IncomeStatsPage from './pages/IncomeStatsPage';
import WeeklyReportPage from './pages/WeeklyReportPage';
import WorkoutHistoryPage from './pages/WorkoutHistoryPage';
import ExerciseProgressPage from './pages/ExerciseProgressPage';

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/add" element={<AddTransactionPage />} />
        <Route path="/income" element={<IncomeStatsPage />} />
        <Route path="/report" element={<WeeklyReportPage />} />
        <Route path="/workouts" element={<WorkoutsPage />} />
        <Route path="/workout-history" element={<WorkoutHistoryPage />} />
        <Route path="/exercise-progress" element={<ExerciseProgressPage />} />
        <Route path="/advisor" element={<AdvisorPage />} />
      </Routes>
      <BottomNav />
    </div>
  );
}
