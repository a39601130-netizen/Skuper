import type {
  Transaction,
  TransactionCreate,
  Account,
  Category,
  MonthlySummary,
  ExerciseWeight,
  Exercise,
  WorkoutHistory,
  NextWorkout,
  AdvisorResponse,
  References,
  WorkoutCreate,
  WorkoutComplete,
  WorkoutSetCreate,
  WorkoutDetail,
  DailySpending,
  WorkoutCalendarEntry,
  RecurringTransaction,
  RecurringTransactionCreate,
} from '../types';

const API_BASE = '/api';

function getInitData(): string {
  return window.Telegram?.WebApp?.initData || '';
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Telegram-Init-Data': getInitData(),
    ...(options.headers as Record<string, string> || {}),
  };

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

// --- Transactions ---
export const getTransactions = (limit = 20, filters?: {
  date_from?: string; date_to?: string; category?: string; type?: string; account?: string;
}) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (filters) {
    if (filters.date_from) params.set('date_from', filters.date_from);
    if (filters.date_to) params.set('date_to', filters.date_to);
    if (filters.category) params.set('category', filters.category);
    if (filters.type) params.set('type', filters.type);
    if (filters.account) params.set('account', filters.account);
  }
  return request<Transaction[]>(`/transactions?${params}`);
};

export const createTransaction = (data: TransactionCreate) =>
  request<{ status: string; id: number }>('/transactions', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const deleteTransaction = (id: number) =>
  request<{ status: string }>(`/transactions/${id}`, { method: 'DELETE' });

// --- Accounts ---
export const getAccounts = () => request<Account[]>('/accounts');

// --- Categories ---
export const getCategories = () => request<Category[]>('/categories');
export const getReferences = () => request<References>('/categories/references');

// --- Stats ---
export const getMonthlySummary = () => request<MonthlySummary>('/stats/monthly');
export const getIncomeStats = () => request<Record<string, unknown>>('/stats/income');
export const getWeeklySummary = (daysBack = 7) =>
  request<Record<string, unknown>>(`/stats/weekly?days_back=${daysBack}`);
export const getDailySpending = () => request<DailySpending[]>('/stats/daily-spending');

// --- Workouts ---
export const getWorkoutHistory = (limit = 10) =>
  request<WorkoutHistory[]>(`/workouts/history?limit=${limit}`);

export const getNextWorkout = () => request<NextWorkout>('/workouts/next');
export const getCurrentWeights = () => request<ExerciseWeight[]>('/workouts/weights');

export const createWorkout = (data: WorkoutCreate) =>
  request<WorkoutDetail>('/workouts', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getWorkout = (id: number) =>
  request<WorkoutDetail>(`/workouts/${id}`);

export const completeWorkout = (id: number, data: WorkoutComplete) =>
  request<WorkoutDetail>(`/workouts/${id}/complete`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const addWorkoutSet = (workoutId: number, data: WorkoutSetCreate) =>
  request<{ status: string; id: number }>(`/workouts/${workoutId}/sets`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getWorkoutCalendar = (month: number, year: number) =>
  request<WorkoutCalendarEntry[]>(`/workouts/calendar?month=${month}&year=${year}`);

export const getWorkoutComparison = (id: number) =>
  request<{ current: WorkoutDetail; previous: WorkoutDetail | null }>(`/workouts/${id}/compare`);

// --- Exercises ---
export const getExercises = (day?: 'A' | 'B') =>
  request<Exercise[]>(`/exercises${day ? `?day=${day}` : ''}`);

export const getExerciseProgress = (exerciseId: string) =>
  request<Record<string, unknown>>(`/exercises/${exerciseId}/progress`);

export const updateExerciseWeight = (exerciseId: string, weight: number) =>
  request<{ status: string }>(`/exercises/${exerciseId}/weight`, {
    method: 'PUT',
    body: JSON.stringify({ weight }),
  });

// --- Advisor ---
export const askAdvisor = (
  question: string,
  contextType = 'finance',
  mode = 'default',
  screenContext?: string,
  history?: { role: string; text: string }[],
) =>
  request<AdvisorResponse>('/advisor/ask', {
    method: 'POST',
    body: JSON.stringify({
      question,
      context_type: contextType,
      mode,
      screen_context: screenContext,
      history,
    }),
  });

export const getAnalysis = (type = 'finance') =>
  request<{ response: string; summary: MonthlySummary }>(`/advisor/analysis?type=${type}`);

export const getInsights = () =>
  request<{ insights: string[] }>('/advisor/insights');

// --- Recurring Transactions ---
export const getRecurringTransactions = () =>
  request<RecurringTransaction[]>('/recurring');

export const createRecurringTransaction = (data: RecurringTransactionCreate) =>
  request<RecurringTransaction>('/recurring', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const deleteRecurringTransaction = (id: number) =>
  request<{ status: string }>(`/recurring/${id}`, { method: 'DELETE' });

export const applyRecurringTransaction = (id: number) =>
  request<{ status: string; transaction_id: number }>(`/recurring/${id}/apply`, { method: 'POST' });
