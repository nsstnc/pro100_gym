import { useEffect, useState } from 'react';
import {
  fetchWorkoutPlan,
  generateWorkoutPlan,
  fetchActiveSession,
  startSession,
  completeSet,
  skipSet,
  finishSession,
  cancelSession,
  type WorkoutPlan,
  type ActiveWorkoutSession,
  type SessionSet,
} from '../../api';

const hasToken = () => {
  try {
    return Boolean(localStorage.getItem('accessToken'));
  } catch {
    return false;
  }
};

const WORKOUT_DURATION_STORAGE_KEY = 'workoutDurationMinutesBySession';

type DurationStore = Record<
  string,
  { user_id: number; minutes: number; completed_at: string | null }
>;

type SetInputState = {
  reps: string;
  weight: string;
};

const DashboardWorkout = () => {
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [session, setSession] = useState<ActiveWorkoutSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [setInputs, setSetInputs] = useState<Record<number, SetInputState>>({});
  const [busySetIds, setBusySetIds] = useState<Record<number, boolean>>({});
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);
  const [isCanceling, setIsCanceling] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [lastSessionSnapshot, setLastSessionSnapshot] = useState<ActiveWorkoutSession | null>(null);

  useEffect(() => {
    if (!hasToken()) {
      setIsLoading(false);
      return;
    }

    const loadData = async () => {
      try {
        setError(null);
        const [planData, sessionData] = await Promise.all([
          fetchWorkoutPlan(),
          fetchActiveSession(),
        ]);
        setPlan(planData);
        setSession(sessionData);
      } catch {
        setError('Не удалось загрузить тренировки.');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  useEffect(() => {
    if (!session) return;

    const nextInputs: Record<number, SetInputState> = {};
    session.session_days.forEach((day) => {
      day.session_exercises.forEach((exercise) => {
        exercise.session_sets.forEach((set) => {
          if (!setInputs[set.id]) {
            const reps = set.plan_reps_max ?? set.plan_reps_min ?? '';
            const weight = set.plan_weight ?? '';
            nextInputs[set.id] = {
              reps: reps === '' ? '' : String(reps),
              weight: weight === '' ? '' : String(weight),
            };
          }
        });
      });
    });

    if (Object.keys(nextInputs).length > 0) {
      setSetInputs((prev) => ({ ...prev, ...nextInputs }));
    }
  }, [session, setInputs]);

  useEffect(() => {
    if (!session || !session.started_at) {
      setElapsedSeconds(0);
      return undefined;
    }

    const startedAt = new Date(session.started_at).getTime();
    if (Number.isNaN(startedAt)) {
      setElapsedSeconds(0);
      return undefined;
    }

    const updateElapsed = () => {
      const deltaSeconds = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
      setElapsedSeconds(deltaSeconds);
    };

    updateElapsed();
    const timer = window.setInterval(updateElapsed, 1000);
    return () => window.clearInterval(timer);
  }, [session]);

  useEffect(() => {
    if (session) {
      setLastSessionSnapshot(session);
    }
  }, [session]);

  const loadDurationStore = (): DurationStore => {
    try {
      const raw = localStorage.getItem(WORKOUT_DURATION_STORAGE_KEY);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        return parsed as DurationStore;
      }
    } catch {
      // ignore
    }
    return {};
  };

  const saveDurationStore = (store: DurationStore) => {
    try {
      localStorage.setItem(WORKOUT_DURATION_STORAGE_KEY, JSON.stringify(store));
    } catch {
      // ignore
    }
  };

  const persistSessionDuration = (sessionData: ActiveWorkoutSession | null) => {
    if (!sessionData || !sessionData.started_at) return;

    const startTime = new Date(sessionData.started_at).getTime();
    if (Number.isNaN(startTime)) return;
    const endTime = sessionData.completed_at
      ? new Date(sessionData.completed_at).getTime()
      : Date.now();
    if (Number.isNaN(endTime)) return;

    const deltaMinutes = Math.max(1, Math.ceil((endTime - startTime) / 60000));
    const store = loadDurationStore();
    store[String(sessionData.id)] = {
      user_id: sessionData.user_id,
      minutes: deltaMinutes,
      completed_at: sessionData.completed_at ?? new Date().toISOString(),
    };
    saveDurationStore(store);
  };

  const shouldFinalizeSession = (sessionData: ActiveWorkoutSession | null) => {
    if (!sessionData) return false;

    let pendingSets = 0;
    sessionData.session_days.forEach((day) => {
      day.session_exercises.forEach((exercise) => {
        exercise.session_sets.forEach((set) => {
          if (set.status === 'pending') {
            pendingSets += 1;
          }
        });
      });
    });

    return pendingSets === 0;
  };

  const handleGeneratePlan = async () => {
    try {
      setIsGeneratingPlan(true);
      setError(null);
      const newPlan = await generateWorkoutPlan();
      setPlan(newPlan);
    } catch {
      setError('Не удалось сгенерировать план. Проверьте данные профиля.');
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const handleStartSession = async (dayIndex: number) => {
    if (!plan) return;
    try {
      setError(null);
      const newSession = await startSession(plan.id, dayIndex);
      console.info('[workout] started session', newSession);
      setSession(newSession);
    } catch {
      setError('Не удалось запустить тренировку.');
    }
  };

  const updateSetInput = (setId: number, field: keyof SetInputState, value: string) => {
    setSetInputs((prev) => ({
      ...prev,
      [setId]: {
        ...prev[setId],
        [field]: value,
      },
    }));
  };

  const handleCompleteSet = async (setId: number) => {
    const values = setInputs[setId];
    if (!values) return;
    const reps = Number(values.reps);
    const weight = Number(values.weight);
    if (!Number.isFinite(reps) || !Number.isFinite(weight)) {
      setError('Укажите корректные значения повторений и веса.');
      return;
    }

    try {
      setBusySetIds((prev) => ({ ...prev, [setId]: true }));
      setError(null);
      await completeSet(setId, reps, weight);

      const refreshed = await fetchActiveSession();
      console.info('[workout] completed set', { setId, reps, weight, refreshed });
      if (refreshed && shouldFinalizeSession(refreshed)) {
        try {
          const finished = await finishSession(refreshed.id);
          console.info('[workout] auto-finished session', finished);
          persistSessionDuration(finished);
          setSession(finished);
          return;
        } catch {
          // ignore and fallback to refresh
        }
      }
      if (!refreshed) {
        persistSessionDuration(lastSessionSnapshot ?? session);
      }
      setSession(refreshed);
    } catch {
      setError('Не удалось сохранить результат подхода.');
    } finally {
      setBusySetIds((prev) => ({ ...prev, [setId]: false }));
    }
  };

  const handleSkipSet = async (setId: number) => {
    try {
      setBusySetIds((prev) => ({ ...prev, [setId]: true }));
      setError(null);
      await skipSet(setId);

      const refreshed = await fetchActiveSession();
      console.info('[workout] skipped set', { setId, refreshed });
      if (refreshed && shouldFinalizeSession(refreshed)) {
        try {
          const finished = await finishSession(refreshed.id);
          console.info('[workout] auto-finished session', finished);
          persistSessionDuration(finished);
          setSession(finished);
          return;
        } catch {
          // ignore and fallback to refresh
        }
      }
      if (!refreshed) {
        persistSessionDuration(lastSessionSnapshot ?? session);
      }
      setSession(refreshed);
    } catch {
      setError('Не удалось пропустить подход.');
    } finally {
      setBusySetIds((prev) => ({ ...prev, [setId]: false }));
    }
  };

  const handleFinishSession = async () => {
    if (!session) return;
    try {
      setIsFinishing(true);
      setError(null);
      const finished = await finishSession(session.id);
      console.info('[workout] finished session', finished);
      persistSessionDuration(finished);
      setSession(finished);
    } catch {
      setError('Не удалось завершить тренировку.');
    } finally {
      setIsFinishing(false);
    }
  };

  const handleCancelSession = async () => {
    if (!session) return;
    try {
      setIsCanceling(true);
      setError(null);
      await cancelSession(session.id);
      setSession(null);
    } catch {
      setError('Не удалось отменить тренировку.');
    } finally {
      setIsCanceling(false);
    }
  };

  if (!hasToken()) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
        <p className="text-slate-600">Войдите, чтобы управлять тренировками.</p>
      </div>
    );
  }

  if (isLoading) {
    return <p className="text-slate-500">Загружаем тренировки...</p>;
  }

  const allSets = session
    ? session.session_days.flatMap((day) =>
        day.session_exercises.flatMap((exercise) => exercise.session_sets),
      )
    : [];
  const completedSets = allSets.filter((set) => set.status === 'completed').length;
  const skippedSets = allSets.filter((set) => set.status === 'skipped').length;
  const pendingSets = allSets.filter((set) => set.status === 'pending').length;
  const totalSets = allSets.length;
  const progressPercent = totalSets > 0 ? Math.round(((completedSets + skippedSets) / totalSets) * 100) : 0;
  const elapsedMinutes = Math.floor(elapsedSeconds / 60);
  const elapsedRemainderSeconds = elapsedSeconds % 60;
  const elapsedLabel = `${elapsedMinutes}:${String(elapsedRemainderSeconds).padStart(2, '0')}`;

  return (
    <div className="space-y-8">
      {error && <p className="text-red-600">{error}</p>}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold">Ваш план</h2>
            <p className="text-slate-500 text-sm">
              {plan ? `Сплит: ${plan.split_type ?? 'индивидуальный'}` : 'План пока не сформирован.'}
            </p>
          </div>
          <button
            type="button"
            onClick={handleGeneratePlan}
            disabled={isGeneratingPlan}
            className={`px-5 py-2 rounded-full text-sm font-semibold ${
              isGeneratingPlan
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                : 'bg-emerald-600 text-white hover:bg-emerald-700'
            }`}
          >
            {isGeneratingPlan ? 'Генерируем...' : 'Сгенерировать план'}
          </button>
        </div>

        {!plan && (
          <p className="mt-4 text-sm text-slate-500">
            Заполните профиль и нажмите «Сгенерировать план».
          </p>
        )}

        {plan && (
          <div className="mt-6 space-y-4">
            {plan.days.map((day, index) => (
              <div key={day.day_name} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-semibold text-slate-800">{day.day_name}</p>
                    <p className="text-xs text-slate-500">Упражнений: {day.exercises.length}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleStartSession(index)}
                    disabled={Boolean(session)}
                    className={`px-4 py-2 rounded-full text-xs font-semibold ${
                      session
                        ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                        : 'bg-slate-900 text-white hover:bg-slate-800'
                    }`}
                  >
                    {session ? 'Сессия активна' : 'Начать тренировку'}
                  </button>
                </div>
                <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {day.exercises.map((exercise) => (
                    <div key={exercise.name} className="rounded-lg bg-white border border-slate-100 p-3">
                      <p className="text-sm font-semibold text-slate-700">{exercise.name}</p>
                      <p className="text-xs text-slate-500">
                        {exercise.sets}x{exercise.reps[0]}–{exercise.reps[1]} · {exercise.weight} кг
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold">Текущая тренировка</h2>
            <p className="text-slate-500 text-sm">
              {session ? `Статус: ${session.status}` : 'Нет активной тренировки.'}
            </p>
            {session && (
              <p className="mt-1 text-sm text-slate-600">
                Время тренировки: <span className="font-semibold text-slate-800">{elapsedLabel}</span>
              </p>
            )}
          </div>
          {session && (
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleFinishSession}
                disabled={isFinishing}
                className={`px-5 py-2 rounded-full text-sm font-semibold ${
                  isFinishing
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'bg-amber-500 text-white hover:bg-amber-600'
                }`}
              >
                {isFinishing ? 'Завершаем...' : 'Завершить тренировку'}
              </button>
              <button
                type="button"
                onClick={handleCancelSession}
                disabled={isCanceling}
                className={`px-5 py-2 rounded-full text-sm font-semibold ${
                  isCanceling
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
                }`}
              >
                {isCanceling ? 'Отменяем...' : 'Отменить тренировку'}
              </button>
            </div>
          )}
        </div>

        {session && (
          <div className="mt-6 rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-700">Прогресс тренировки</p>
                <p className="text-xs text-slate-500">
                  Завершено: {completedSets} · Пропущено: {skippedSets} · Осталось: {pendingSets}
                </p>
              </div>
              <div className="text-sm font-semibold text-slate-700">{progressPercent}%</div>
            </div>
            <div className="mt-3 h-2 w-full rounded-full bg-slate-200">
              <div
                className="h-2 rounded-full bg-emerald-500 transition-all"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            {pendingSets === 0 ? (
              <p className="mt-3 text-sm text-emerald-700">
                Все подходы отмечены. Можно завершить тренировку.
              </p>
            ) : (
              <p className="mt-3 text-sm text-slate-500">
                Отмечайте каждый подход «Готово» или «Пропустить», чтобы статистика считалась корректно.
              </p>
            )}
          </div>
        )}

        {!session && (
          <p className="mt-4 text-sm text-slate-500">
            Запустите тренировку из плана, чтобы отслеживать подходы.
          </p>
        )}

        {session && (
          <div className="mt-6 space-y-6">
            {session.session_days.map((day) => (
              <div key={day.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <h3 className="text-lg font-semibold text-slate-800">{day.plan_day_name}</h3>
                <div className="mt-4 space-y-4">
                  {day.session_exercises.map((exercise) => (
                    <div key={exercise.id} className="rounded-lg bg-white border border-slate-100 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="font-semibold text-slate-700">{exercise.plan_exercise_name}</p>
                        <span className="text-xs uppercase tracking-wide text-slate-400">
                          {exercise.status}
                        </span>
                      </div>
                      <div className="mt-4 space-y-3">
                        {exercise.session_sets.map((set: SessionSet) => {
                          const input = setInputs[set.id] || { reps: '', weight: '' };
                          const isPending = set.status === 'pending';
                          return (
                            <div key={set.id} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                              <div className="flex flex-wrap items-center justify-between gap-3">
                                <div>
                                  <p className="text-sm font-semibold text-slate-700">Подход {set.order}</p>
                                  <p className="text-xs text-slate-500">
                                    План: {set.plan_reps_min ?? '-'}–{set.plan_reps_max ?? '-'} · {set.plan_weight ?? '-'} кг
                                  </p>
                                </div>
                                <span className="text-xs uppercase tracking-wide text-slate-400">
                                  {set.status}
                                </span>
                              </div>
                              {isPending ? (
                                <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_1fr_auto_auto]">
                                  <input
                                    type="number"
                                    min={0}
                                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                                    value={input.reps}
                                    onChange={(event) => updateSetInput(set.id, 'reps', event.target.value)}
                                    placeholder="Повторы"
                                  />
                                  <input
                                    type="number"
                                    min={0}
                                    step="0.5"
                                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                                    value={input.weight}
                                    onChange={(event) => updateSetInput(set.id, 'weight', event.target.value)}
                                    placeholder="Вес (кг)"
                                  />
                                  <button
                                    type="button"
                                    onClick={() => handleCompleteSet(set.id)}
                                    disabled={busySetIds[set.id]}
                                    className={`px-4 py-2 rounded-full text-xs font-semibold ${
                                      busySetIds[set.id]
                                        ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                                        : 'bg-emerald-600 text-white hover:bg-emerald-700'
                                    }`}
                                  >
                                    Готово
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleSkipSet(set.id)}
                                    disabled={busySetIds[set.id]}
                                    className="px-4 py-2 rounded-full text-xs font-semibold border border-slate-200 text-slate-600 hover:bg-white"
                                  >
                                    Пропустить
                                  </button>
                                </div>
                              ) : (
                                <p className="mt-3 text-xs text-slate-500">
                                  Выполнено: {set.reps_done ?? '-'} повторений · {set.weight_lifted ?? '-'} кг
                                </p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardWorkout;
