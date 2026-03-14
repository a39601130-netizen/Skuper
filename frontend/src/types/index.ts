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
  created_at: string;
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
  month: number;
  year: number;
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
  reps_min?: number;
  reps_max?: number;
  rest_seconds?: number;
  default_sets?: number;
}

export interface WorkoutHistory {
  id: number;
  date: string;
  day_type: string;
  week: number;
  phase: string;
  energy_before: number;
  energy_after: number;
  sleep_hours: number;
  back_pain: number;
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

export interface NextWorkout {
  next_day: string;
  phase: Record<string, string | number>;
  exercises: Exercise[];
}

// Workout session types
export interface WorkoutCreate {
  day_type: string;
  energy_before: number;
  sleep_hours?: number;
  sleep_quality?: number;
  back_pain?: number;
  emotional_wave?: string;
}

export interface WorkoutComplete {
  energy_after: number;
  notes?: string;
}

export interface WorkoutSetCreate {
  exercise_id: string;
  set_number: number;
  weight: number;
  reps: number;
  rpe?: number;
  notes?: string;
}

export interface WorkoutDetail {
  id: number;
  date: string;
  day_type: string;
  week: number | null;
  phase: string;
  energy_before: number | null;
  energy_after: number | null;
  sleep_hours: number | null;
  sleep_quality: number | null;
  back_pain: number | null;
  emotional_wave: string;
  notes: string;
  sets: WorkoutSetData[];
}

export interface WorkoutSetData {
  id: number;
  exercise_id: string;
  exercise_name: string;
  set_number: number;
  weight: number;
  reps: number;
  rpe: number | null;
}

// Advisor types
export interface AdvisorMessage {
  role: 'user' | 'ai';
  text: string;
}

export interface AdvisorResponse {
  response: string;
}

// Recurring transactions
export interface RecurringTransaction {
  id: number;
  name: string;
  type: string;
  account: string;
  category: string;
  amount: number;
  currency: string;
  frequency: string;
  next_date: string;
  is_active: boolean;
}

export interface RecurringTransactionCreate {
  name: string;
  type: string;
  account: string;
  category?: string;
  amount: number;
  currency?: string;
  frequency: string;
  next_date: string;
}

export interface References {
  types: string[];
  accounts: string[];
  categories: string[];
  income_categories: string[];
}

// Stats types
export interface DailySpending {
  date: string;
  total: number;
  by_category: Record<string, number>;
}

// Calendar types
export interface WorkoutCalendarEntry {
  date: string;
  day_type: string;
  id: number;
}
