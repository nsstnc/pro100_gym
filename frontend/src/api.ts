const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

function getAccessToken(): string | null {
  try {
    return localStorage.getItem('accessToken');
  } catch {
    return null;
  }
}

async function parseJson<T>(response: Response): Promise<T> {
  const payload = await response.json();
  if (payload && typeof payload === 'object' && 'data' in (payload as any)) {
    return (payload as any).data as T;
  }
  return payload as T;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  age: number | null;
  height: number | null;
  weight: number | null;
  fitness_goal: string | null;
  experience_level: string | null;
  workouts_per_week: number | null;
  session_duration: number | null;
}

export interface UserProfileUpdatePayload {
  age?: number;
  height?: number;
  weight?: number;
  fitness_goal?: string;
  experience_level?: string;
  workouts_per_week?: number;
  session_duration?: number;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface UserCreatePayload {
  username: string;
  email: string;
  password: string;
}

export interface RestrictionRule {
  id: number;
  slug: string;
  name: string;
  description: string | null;
}

export interface MuscleFocus {
  id: number;
  slug: string;
  name: string;
  muscle_group_id: number;
  priority_modifier: number;
}

export interface UserPreferencesResponse {
  restriction_rules: RestrictionRule[];
  muscle_focuses: MuscleFocus[];
}

export type SessionStatus = 'pending' | 'in_progress' | 'completed' | 'skipped';

export interface WorkoutExercise {
  name: string;
  muscle_group: string;
  sets: number;
  reps: [number, number];
  weight: number;
  equipment: string | null;
  rest_seconds: number;
}

export interface WorkoutDay {
  day_name: string;
  exercises: WorkoutExercise[];
}

export interface WorkoutPlan {
  id: number;
  user_id: number;
  name: string;
  split_type: string | null;
  generated_at: string;
  days: WorkoutDay[];
}

export interface SessionSet {
  id: number;
  session_exercise_id: number;
  order: number;
  status: SessionStatus;
  plan_reps_min: number | null;
  plan_reps_max: number | null;
  plan_weight: number | null;
  reps_done: number | null;
  weight_lifted: number | null;
}

export interface SessionExercise {
  id: number;
  session_day_id: number;
  plan_exercise_name: string;
  order: number;
  status: SessionStatus;
  session_sets: SessionSet[];
}

export interface SessionDay {
  id: number;
  workout_session_id: number;
  plan_day_name: string;
  order: number;
  status: SessionStatus;
  session_exercises: SessionExercise[];
}

export interface ActiveWorkoutSession {
  id: number;
  user_id: number;
  workout_plan_id: number | null;
  started_at: string;
  completed_at: string | null;
  status: SessionStatus;
  duration_minutes: number | null;
  rating: number | null;
  notes: string | null;
  session_days: SessionDay[];
}

export interface PersonalRecord {
  exercise_name: string;
  max_weight_kg: number;
  reps: number;
  date: string;
}

export interface VolumeByMuscleGroup {
  muscle_group: string;
  volume_kg: number;
}

export interface StatisticsSummary {
  total_workouts: number;
  total_duration_minutes: number;
  total_volume_kg: number;
  total_sets: number;
  total_reps: number;
  personal_records: PersonalRecord[];
}

export interface StatisticsResponse {
  summary: StatisticsSummary;
  volume_by_muscle_group: VolumeByMuscleGroup[];
  progress_charts: Record<string, unknown>;
}

export async function fetchCurrentUser(): Promise<UserProfile | null> {
  const token = getAccessToken();
  if (!token) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/users/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return null;
  }

  return await parseJson<UserProfile>(response);
}

export async function login(username: string, password: string): Promise<AuthToken> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });

  if (!response.ok) {
    throw new Error('Failed to login');
  }

  return await parseJson<AuthToken>(response);
}

export async function registerUser(payload: UserCreatePayload): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error('Failed to register');
  }

  return await parseJson<UserProfile>(response);
}

export async function updateCurrentUserProfile(
  data: UserProfileUpdatePayload,
): Promise<UserProfile | null> {
  const token = getAccessToken();
  if (!token) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/users/me`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update profile');
  }

  return await parseJson<UserProfile>(response);
}

export async function fetchRestrictionRules(): Promise<RestrictionRule[]> {
  const response = await fetch(`${API_BASE_URL}/options/restriction-rules`);
  if (!response.ok) {
    throw new Error('Failed to load restriction rules');
  }
  return await parseJson<RestrictionRule[]>(response);
}

export async function fetchMuscleFocuses(): Promise<MuscleFocus[]> {
  const response = await fetch(`${API_BASE_URL}/options/muscle-focuses`);
  if (!response.ok) {
    throw new Error('Failed to load muscle focuses');
  }
  return await parseJson<MuscleFocus[]>(response);
}

export async function fetchMyPreferences(): Promise<UserPreferencesResponse | null> {
  const token = getAccessToken();
  if (!token) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/preferences/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return null;
  }

  return await parseJson<UserPreferencesResponse>(response);
}

export async function logoutUser(): Promise<void> {
  const token = getAccessToken();
  if (!token) {
    return;
  }

  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function updateMyPreferences(params: {
  restriction_rule_ids: number[];
  muscle_focus_ids: number[];
}): Promise<UserPreferencesResponse | null> {
  const token = getAccessToken();
  if (!token) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/preferences/me`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error('Failed to update preferences');
  }

  return await parseJson<UserPreferencesResponse>(response);
}

export async function fetchWorkoutPlan(): Promise<WorkoutPlan | null> {
  const token = getAccessToken();
  if (!token) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/workouts/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return null;
  }

  return await parseJson<WorkoutPlan>(response);
}

export async function generateWorkoutPlan(): Promise<WorkoutPlan> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authorized');
  }

  const response = await fetch(`${API_BASE_URL}/workouts/generate`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to generate workout plan');
  }

  return await parseJson<WorkoutPlan>(response);
}

export async function fetchActiveSession(): Promise<ActiveWorkoutSession | null> {
  const token = getAccessToken();
  if (!token) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/sessions/active`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return null;
  }

  return await parseJson<ActiveWorkoutSession | null>(response);
}

export async function startSession(planId: number, dayIndex: number): Promise<ActiveWorkoutSession> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authorized');
  }

  const response = await fetch(`${API_BASE_URL}/sessions/start`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ workout_plan_id: planId, day_index: dayIndex }),
  });

  if (!response.ok) {
    throw new Error('Failed to start session');
  }

  return await parseJson<ActiveWorkoutSession>(response);
}

export async function completeSet(setId: number, repsDone: number, weightLifted: number): Promise<SessionSet> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authorized');
  }

  const response = await fetch(`${API_BASE_URL}/sessions/sets/${setId}/complete`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ reps_done: repsDone, weight_lifted: weightLifted }),
  });

  if (!response.ok) {
    throw new Error('Failed to complete set');
  }

  return await parseJson<SessionSet>(response);
}

export async function skipSet(setId: number): Promise<SessionSet> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authorized');
  }

  const response = await fetch(`${API_BASE_URL}/sessions/sets/${setId}/skip`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to skip set');
  }

  return await parseJson<SessionSet>(response);
}

export async function finishSession(sessionId: number): Promise<ActiveWorkoutSession> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authorized');
  }

  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/finish`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to finish session');
  }

  return await parseJson<ActiveWorkoutSession>(response);
}

export async function cancelSession(sessionId: number): Promise<void> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authorized');
  }

  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/cancel`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to cancel session');
  }
}

export async function fetchStatistics(period = 'all_time'): Promise<StatisticsResponse | null> {
  const token = getAccessToken();
  if (!token) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/statistics/me?period=${encodeURIComponent(period)}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return null;
  }

  return await parseJson<StatisticsResponse>(response);
}
