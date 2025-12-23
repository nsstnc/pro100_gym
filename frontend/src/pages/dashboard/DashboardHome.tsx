import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  fetchWorkoutPlan,
  fetchActiveSession,
  fetchStatistics,
  fetchCurrentUser,
  type WorkoutPlan,
  type ActiveWorkoutSession,
  type StatisticsResponse,
  type UserProfile,
} from '../../api';

const hasToken = () => {
  try {
    return Boolean(localStorage.getItem('accessToken'));
  } catch {
    return false;
  }
};

const DashboardHome = () => {
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [session, setSession] = useState<ActiveWorkoutSession | null>(null);
  const [stats, setStats] = useState<StatisticsResponse | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasToken()) {
      setIsLoading(false);
      return;
    }

    const loadData = async () => {
      try {
        setError(null);
        const [planData, sessionData, statsData, userData] = await Promise.all([
          fetchWorkoutPlan(),
          fetchActiveSession(),
          fetchStatistics('all_time'),
          fetchCurrentUser(),
        ]);
        setPlan(planData);
        setSession(sessionData);
        setStats(statsData);
        setUser(userData);
      } catch {
        setError('Не удалось загрузить данные кабинета.');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  if (!hasToken()) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
        <p className="text-slate-600">Войдите, чтобы увидеть личный кабинет.</p>
        <Link
          to="/login"
          className="inline-flex mt-4 px-6 py-2 rounded-full bg-slate-900 text-white font-semibold"
        >
          Войти
        </Link>
      </div>
    );
  }

  if (isLoading) {
    return <p className="text-slate-500">Загружаем кабинет...</p>;
  }

  if (error) {
    return <p className="text-red-600">{error}</p>;
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm md:col-span-2">
          <p className="text-xs uppercase tracking-widest text-slate-400">Профиль</p>
          <h3 className="mt-3 text-xl font-semibold">
            {user ? user.username : 'Профиль не загружен'}
          </h3>
          <p className="mt-1 text-sm text-slate-500">{user?.email ?? '—'}</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-50 px-3 py-2">
              <p className="text-xs text-slate-500">Возраст</p>
              <p className="text-sm font-semibold text-slate-700">{user?.age ?? '—'}</p>
            </div>
            <div className="rounded-xl bg-slate-50 px-3 py-2">
              <p className="text-xs text-slate-500">Рост</p>
              <p className="text-sm font-semibold text-slate-700">{user?.height ?? '—'} см</p>
            </div>
            <div className="rounded-xl bg-slate-50 px-3 py-2">
              <p className="text-xs text-slate-500">Вес</p>
              <p className="text-sm font-semibold text-slate-700">{user?.weight ?? '—'} кг</p>
            </div>
          </div>
          <Link to="/onboarding" className="inline-flex mt-4 text-sm font-semibold text-emerald-600">
            Обновить профиль →
          </Link>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
          <p className="text-xs uppercase tracking-widest text-slate-400">План</p>
          <h3 className="mt-3 text-xl font-semibold">{plan ? plan.name : 'План не создан'}</h3>
          <p className="mt-2 text-sm text-slate-500">
            {plan ? `Сплит: ${plan.split_type ?? 'индивидуальный'}` : 'Создайте план, чтобы начать.'}
          </p>
          <Link to="/dashboard/workout" className="inline-flex mt-4 text-sm font-semibold text-emerald-600">
            Перейти к тренировкам →
          </Link>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
          <p className="text-xs uppercase tracking-widest text-slate-400">Текущая сессия</p>
          <h3 className="mt-3 text-xl font-semibold">
            {session ? session.session_days[0]?.plan_day_name ?? 'Тренировка' : 'Нет активной тренировки'}
          </h3>
          <p className="mt-2 text-sm text-slate-500">
            {session ? 'Продолжайте тренировку или завершите.' : 'Запустите тренировку из плана.'}
          </p>
          <Link to="/dashboard/workout" className="inline-flex mt-4 text-sm font-semibold text-emerald-600">
            Управлять тренировкой →
          </Link>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
          <p className="text-xs uppercase tracking-widest text-slate-400">Статистика</p>
          <h3 className="mt-3 text-xl font-semibold">
            {stats ? `${stats.summary.total_workouts} тренировок` : 'Нет данных'}
          </h3>
          <p className="mt-2 text-sm text-slate-500">
            {stats ? `${stats.summary.total_volume_kg.toFixed(0)} кг суммарного объема` : 'Проведите первую тренировку.'}
          </p>
          <Link to="/dashboard/statistics" className="inline-flex mt-4 text-sm font-semibold text-emerald-600">
            Смотреть статистику →
          </Link>
        </div>
      </div>

      <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-8">
        <h2 className="text-2xl font-semibold">Следующий шаг</h2>
        <p className="mt-2 text-slate-700">
          {plan
            ? 'Откройте текущую тренировку и отметьте выполненные подходы.'
            : 'Заполните профиль и сгенерируйте план тренировок.'}
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            to={plan ? '/dashboard/workout' : '/onboarding'}
            className="px-5 py-2 rounded-full bg-slate-900 text-white font-semibold"
          >
            {plan ? 'Открыть тренировку' : 'Заполнить профиль'}
          </Link>
          <Link
            to="/dashboard/statistics"
            className="px-5 py-2 rounded-full border border-slate-900 text-slate-900 font-semibold"
          >
            Посмотреть статистику
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DashboardHome;
