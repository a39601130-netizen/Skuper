// Telegram WebApp types
export interface TelegramWebApp {
  ready: () => void;
  expand: () => void;
  close: () => void;
  setHeaderColor: (color: string) => void;
  setBackgroundColor: (color: string) => void;
  initData: string;
  initDataUnsafe: {
    user?: TelegramUser;
  };
  colorScheme: 'light' | 'dark';
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy') => void;
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
    selectionChanged: () => void;
  };
  MainButton: {
    text: string;
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
    showProgress: (leaveActive?: boolean) => void;
    hideProgress: () => void;
    isVisible: boolean;
  };
  BackButton: {
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
  };
}

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

// Finance types
export interface Account {
  name: string;
  currency: string;
  current: number;
  initial: number;
  emoji?: string;
}

export interface Category {
  name: string;
  type: string;
  budget: number;
  spent: number;
  remaining: number;
  progress: number;
  emoji?: string;
}

export interface Transaction {
  id: number;
  date: string;
  day: number;
  full_date: string;
  type: string;
  account: string;
  category: string;
  amount: number;
  to_account: string;
  comment: string;
  hours: number | null;
  exchange_rate: number | null;
  amount_to: number | null;
  currency: string;
}

export interface TransactionCreate {
  date?: string;
  type: string;
  account: string;
  category?: string;
  amount: number;
  to_account?: string;
  comment?: string;
  hours?: number;
  exchange_rate?: number;
  amount_to?: number;
  currency?: string;
}

export interface MonthlySummary {
  total_income: number;
  total_expense: number;
  balance: number;
  total_on_accounts: number;
  accounts: Account[];
  categories: Category[];
  over_budget: Category[];
  near_limit: Category[];
}

export interface References {
  types: string[];
  accounts: string[];
  categories: string[];
  income_categories: string[];
}

// Workout types
export interface Exercise {
  exercise_id: string;
  name: string;
  day: string;
  order: number;
  category: string;
  weight_step: number;
  current_weight?: number;
  target_reps?: string;
  status?: string;
}

export interface WorkoutHistory {
  date: string;
  day_type: string;
  week: number;
  phase: string;
  energy_before: number;
  energy_after: number;
  sleep_hours: number;
  sleep_quality: string;
  back_pain: string;
  emotional_wave: string;
  notes: string;
}

export interface ExerciseWeight {
  exercise_id: string;
  name: string;
  day: string;
  category: string;
  current_weight: number;
  target_reps: string;
  status: string;
}

export interface ExerciseProgress {
  exercise_id: string;
  current_weight: number;
  target_reps: string;
  status: string;
  trend: 'up' | 'down' | 'stable' | 'no_data';
  history_by_workout: WorkoutSetGroup[];
}

export interface WorkoutSetGroup {
  date: string;
  day_type: string;
  sets: WorkoutSetData[];
}

export interface WorkoutSetData {
  set_number: number;
  weight: number;
  reps: number;
  rpe: number;
}

export interface NextWorkout {
  next_day: string;
  phase: {
    current_week: number;
    phase_name: string;
    rpe_min: number;
    rpe_max: number;
    sets_modifier: number;
  };
  exercises: Exercise[];
}

export interface IncomeStats {
  month: number;
  year: number;
  days: IncomeDay[];
  total_income: number;
  total_hours: number;
  base_hourly_rate: number;
}

export interface IncomeDay {
  day: number;
  date: string;
  total: number;
  salary: number;
  tips: number;
  other: number;
  hours: number;
  transactions: IncomeTx[];
}

export interface IncomeTx {
  id: number;
  amount: number;
  currency: string;
  category: string;
  comment: string;
  hours: number | null;
}

export interface WeeklySummary {
  from_date: string;
  to_date: string;
  days_back: number;
  total_income: number;
  total_expense: number;
  balance: number;
  expense_by_category: Record<string, number>;
  transaction_count: number;
}

// Advisor types
export interface AdvisorResponse {
  response: string;
}
