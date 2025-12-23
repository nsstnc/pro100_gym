import { NavLink, Outlet } from 'react-router-dom';

const tabClassName = ({ isActive }: { isActive: boolean }) =>
  `px-4 py-2 rounded-full text-sm font-semibold transition ${
    isActive
      ? 'bg-slate-900 text-white'
      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
  }`;

const DashboardLayout = () => (
  <div className="min-h-screen bg-slate-50 text-slate-900">
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Личный кабинет</p>
          <h1 className="text-3xl font-bold">Ваш прогресс</h1>
        </div>
        <div className="flex flex-wrap gap-3">
          <NavLink to="/dashboard" end className={tabClassName}>
            Дашборд
          </NavLink>
          <NavLink to="/dashboard/workout" className={tabClassName}>
            Текущая тренировка
          </NavLink>
          <NavLink to="/dashboard/statistics" className={tabClassName}>
            Статистика
          </NavLink>
        </div>
      </div>

      <div className="mt-8">
        <Outlet />
      </div>
    </div>
  </div>
);

export default DashboardLayout;
