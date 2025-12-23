import { useEffect, useState } from 'react';

import { fetchCurrentUser, fetchStatistics, type StatisticsResponse } from '../../api';

const hasToken = () => {
  try {
    return Boolean(localStorage.getItem('accessToken'));
  } catch {
    return false;
  }
};

const DashboardStats = () => {
  const [period, setPeriod] = useState('all_time');
  const [stats, setStats] = useState<StatisticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<number | null>(null);

  const loadDurationStore = () => {
    try {
      const raw = localStorage.getItem('workoutDurationMinutesBySession');
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        return parsed as Record<string, { user_id: number; minutes: number }>;
      }
    } catch {
      // ignore
    }
    return {};
  };

  useEffect(() => {
    if (!hasToken()) {
      setIsLoading(false);
      return;
    }

    const loadStats = async () => {
      try {
        setError(null);
        setIsLoading(true);
        const [data, user] = await Promise.all([fetchStatistics(period), fetchCurrentUser()]);
        console.info('[stats] loaded statistics', { period, data });
        setStats(data);
        setUserId(user?.id ?? null);
      } catch {
        setError('Не удалось загрузить статистику.');
      } finally {
        setIsLoading(false);
      }
    };

    loadStats();
  }, [period]);

  if (!hasToken()) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
        <p className="text-slate-600">Войдите, чтобы увидеть статистику.</p>
      </div>
    );
  }

  if (isLoading) {
    return <p className="text-slate-500">Загружаем статистику...</p>;
  }

  if (error) {
    return <p className="text-red-600">{error}</p>;
  }

  if (!stats) {
    return <p className="text-slate-500">Нет данных.</p>;
  }

  const durationStore = loadDurationStore();
  const localDurationMinutes = Object.values(durationStore)
    .filter((item) => (userId ? item.user_id === userId : true))
    .reduce((acc, item) => acc + item.minutes, 0);
  const effectiveDurationMinutes =
    stats.summary.total_duration_minutes > 0
      ? stats.summary.total_duration_minutes
      : localDurationMinutes;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Статистика тренировок</h2>
          <p className="text-slate-500 text-sm">Выберите период для анализа прогресса.</p>
        </div>
        <select
          value={period}
          onChange={(event) => setPeriod(event.target.value)}
          className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm"
        >
          <option value="all_time">Все время</option>
          <option value="last_month">Последний месяц</option>
          <option value="last_week">Последняя неделя</option>
        </select>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        {[
          { label: 'Тренировок', value: stats.summary.total_workouts },
          { label: 'Длительность (мин)', value: effectiveDurationMinutes.toFixed(0) },
          { label: 'Объем (кг)', value: stats.summary.total_volume_kg.toFixed(0) },
          { label: 'Подходов', value: stats.summary.total_sets },
          { label: 'Повторов', value: stats.summary.total_reps },
        ].map((item) => (
          <div key={item.label} className="rounded-2xl border border-slate-200 bg-white p-4 text-center">
            <p className="text-xs uppercase tracking-widest text-slate-400">{item.label}</p>
            <p className="mt-2 text-xl font-semibold">{item.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h3 className="text-lg font-semibold">Личные рекорды</h3>
          <div className="mt-4 space-y-3">
            {stats.summary.personal_records.length === 0 && (
              <p className="text-sm text-slate-500">Рекордов пока нет.</p>
            )}
            {stats.summary.personal_records.map((record) => (
              <div key={`${record.exercise_name}-${record.date}`} className="rounded-lg bg-slate-50 px-4 py-3">
                <p className="font-semibold text-slate-700">{record.exercise_name}</p>
                <p className="text-sm text-slate-500">
                  {record.max_weight_kg} кг · {record.reps} повторов · {record.date}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h3 className="text-lg font-semibold">Объем по группам мышц</h3>
          <div className="mt-4 space-y-3">
            {stats.volume_by_muscle_group.length === 0 && (
              <p className="text-sm text-slate-500">Данных пока нет.</p>
            )}
            {stats.volume_by_muscle_group.map((item) => (
              <div key={item.muscle_group} className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
                <span className="font-semibold text-slate-700">{item.muscle_group}</span>
                <span className="text-sm text-slate-500">{item.volume_kg.toFixed(0)} кг</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardStats;
