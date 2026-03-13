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
  row_index: number;
  day: string;
  type: string;
  account: string;
  category: string;
  amount: string;
  to_account: string;
  comment: string;
  full_date: string;
  hours: string;
  exchange_rate: string;
  amount_to: string;
  currency: string;
}

export interface TransactionCreate {
  day: number;
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
  back_pain: number;
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

// Advisor types
export interface AdvisorResponse {
  response: string;
}

export interface References {
  types: string[];
  accounts: string[];
  categories: string[];
}
