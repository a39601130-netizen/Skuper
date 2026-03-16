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
  IncomeStats,
  WeeklySummary,
  ExerciseProgress,
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
export const getTransactions = (limit = 20) =>
  request<Transaction[]>(`/transactions?limit=${limit}`);

export const createTransaction = (data: TransactionCreate) =>
  request<{ status: string; id: number }>('/transactions', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const deleteTransaction = (txId: number) =>
  request<{ status: string }>(`/transactions/${txId}`, { method: 'DELETE' });

// --- Accounts ---
export const getAccounts = () => request<Account[]>('/accounts');

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

export const getNextWorkout = () => request<NextWorkout>('/workouts/next');
export const getCurrentWeights = () => request<ExerciseWeight[]>('/workouts/weights');

// --- Exercises ---
export const getExercises = (day?: 'A' | 'B') =>
  request<Exercise[]>(`/exercises${day ? `?day=${day}` : ''}`);

export const getExerciseProgress = (exerciseId: string) =>
  request<ExerciseProgress>(`/exercises/${exerciseId}/progress`);

// --- Advisor ---
export const askAdvisor = (question: string, contextType = 'finance', mode = 'default') =>
  request<AdvisorResponse>('/advisor/ask', {
    method: 'POST',
    body: JSON.stringify({ question, context_type: contextType, mode }),
  });

export const getAnalysis = (type = 'finance') =>
  request<{ response: string; summary: MonthlySummary }>(`/advisor/analysis?type=${type}`);
