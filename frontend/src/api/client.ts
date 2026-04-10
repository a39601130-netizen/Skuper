import type {
  Transaction,
  TransactionCreate,
  Account,
  Category,
  MonthlySummary,
  ExerciseWeight,
  Exercise,
  WorkoutHistory,
  AdvisorResponse,
  References,
  IncomeStats,
  WeeklySummary,
  ExerciseProgress,
  WorkoutCreateData,
  WorkoutFull,
  SetCreateData,
  WorkoutSetData,
  NextWorkoutFull,
  ExerciseWithDetails,
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
    const detail = error.detail;
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((e: { msg?: string }) => e.msg || '').filter(Boolean).join('; ')
        : `HTTP ${response.status}`;
    throw new Error(message || `HTTP ${response.status}`);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

// --- Transactions ---
export const getTransactions = (
  limit = 20,
  filters?: { date_from?: string; date_to?: string; type?: string; category?: string; account?: string },
) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (filters?.date_from) params.set('date_from', filters.date_from);
  if (filters?.date_to) params.set('date_to', filters.date_to);
  if (filters?.type) params.set('type', filters.type);
  if (filters?.category) params.set('category', filters.category);
  if (filters?.account) params.set('account', filters.account);
  return request<Transaction[]>(`/transactions?${params}`);
};

export const createTransaction = (data: TransactionCreate) =>
  request<{ status: string; id: number }>('/transactions', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const deleteTransaction = (txId: number) =>
  request<{ status: string }>(`/transactions/${txId}`, { method: 'DELETE' });

// --- Accounts ---
export const getAccounts = () => request<Account[]>('/accounts');

export const updateAccountBalance = (accountId: number, balance: number) =>
  request<Account>(`/accounts/${accountId}`, {
    method: 'PUT',
    body: JSON.stringify({ balance }),
  });

// --- Categories ---
export const getCategories = () => request<Category[]>('/categories');
export const getReferences = () => request<References>('/categories/references');

// --- Stats ---
export const getMonthlySummary = (month?: number, year?: number) => {
  const params = new URLSearchParams();
  if (month) params.set('month', String(month));
  if (year) params.set('year', String(year));
  const qs = params.toString();
  return request<MonthlySummary>(`/stats/monthly${qs ? `?${qs}` : ''}`);
};

export const getIncomeStats = (month?: number, year?: number) => {
  const params = new URLSearchParams();
  if (month) params.set('month', String(month));
  if (year) params.set('year', String(year));
  const qs = params.toString();
  return request<IncomeStats>(`/stats/income${qs ? `?${qs}` : ''}`);
};
export const getWeeklySummary = (daysBack = 7) =>
  request<WeeklySummary>(`/stats/weekly?days_back=${daysBack}`);

// --- Workouts ---
export const getWorkoutHistory = (limit = 10) =>
  request<WorkoutHistory[]>(`/workouts/history?limit=${limit}`);

export const deleteWorkout = (workoutId: number) =>
  request<{ status: string }>(`/workouts/${workoutId}`, { method: 'DELETE' });

export const getCurrentWeights = () => request<ExerciseWeight[]>('/workouts/weights');

// --- Exercises ---
export const getExercises = (day?: 'A' | 'B') =>
  request<Exercise[]>(`/exercises${day ? `?day=${day}` : ''}`);

export const getExerciseProgress = (exerciseId: string) =>
  request<ExerciseProgress>(`/exercises/${exerciseId}/progress`);

export const getExerciseAlternative = (exerciseId: string) =>
  request<ExerciseWithDetails>(`/exercises/${exerciseId}/alternative`);

// --- Workout Session ---
export const getNextWorkoutFull = (day?: string) =>
  request<NextWorkoutFull>(day ? `/workouts/next?day=${day}` : '/workouts/next');

export const createWorkout = (data: WorkoutCreateData) =>
  request<WorkoutFull>('/workouts', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getWorkout = (id: number) => request<WorkoutFull>(`/workouts/${id}`);

export const addWorkoutSet = (workoutId: number, data: SetCreateData) =>
  request<WorkoutSetData>(`/workouts/${workoutId}/sets`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const completeWorkout = (workoutId: number, energyAfter: number, notes?: string) =>
  request<WorkoutFull>(`/workouts/${workoutId}/complete`, {
    method: 'PUT',
    body: JSON.stringify({ energy_after: energyAfter, notes }),
  });

// --- Advisor ---
export const askAdvisor = (question: string, contextType = 'finance', mode = 'default') =>
  request<AdvisorResponse>('/advisor/ask', {
    method: 'POST',
    body: JSON.stringify({ question, context_type: contextType, mode }),
  });

export const getAnalysis = (type = 'finance') =>
  request<{ response: string; summary: MonthlySummary }>(`/advisor/analysis?type=${type}`);
