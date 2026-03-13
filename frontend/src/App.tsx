import { Routes, Route } from 'react-router-dom';
import BottomNav from './components/BottomNav';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import WorkoutsPage from './pages/WorkoutsPage';
import AdvisorPage from './pages/AdvisorPage';
import AddTransactionPage from './pages/AddTransactionPage';

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/workouts" element={<WorkoutsPage />} />
        <Route path="/advisor" element={<AdvisorPage />} />
        <Route path="/add" element={<AddTransactionPage />} />
      </Routes>
      <BottomNav />
    </div>
  );
}
