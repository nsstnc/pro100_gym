import { Link } from 'react-router-dom';

const getHasToken = () => {
  try {
    return Boolean(localStorage.getItem('accessToken'));
  } catch {
    return false;
  }
};

const Home = () => {
  const hasToken = getHasToken();

  return (
    <div className="bg-slate-50 text-slate-900">
      <section className="relative overflow-hidden">
        <div className="absolute -top-24 -right-24 h-80 w-80 rounded-full bg-amber-200/40 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-72 w-72 rounded-full bg-emerald-200/40 blur-3xl" />

        <div className="max-w-6xl mx-auto px-6 pt-16 pb-20 lg:pt-24 lg:pb-28">
          <div className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-amber-700 font-semibold">
                Персональные тренировки
              </p>
              <h1 className="mt-4 text-4xl sm:text-5xl lg:text-6xl font-black leading-tight">
                pro100gym — умный план тренировок без хаоса и мотивационных качелей
              </h1>
              <p className="mt-5 text-lg text-slate-600 max-w-xl">
                Сервис подбирает тренировки под ваш уровень, цели и ограничения, чтобы вы
                быстрее прогрессировали и не теряли фокус.
              </p>
              <div className="mt-8 flex flex-wrap gap-4">
                {hasToken ? (
                  <>
                    <Link
                      to="/dashboard"
                      className="px-6 py-3 rounded-full bg-emerald-600 text-white font-semibold shadow hover:bg-emerald-700 transition"
                    >
                      Перейти в кабинет
                    </Link>
                    <Link
                      to="/onboarding"
                      className="px-6 py-3 rounded-full border border-slate-300 text-slate-700 font-semibold hover:bg-white transition"
                    >
                      Обновить профиль
                    </Link>
                  </>
                ) : (
                  <>
                    <Link
                      to="/register"
                      className="px-6 py-3 rounded-full bg-amber-600 text-white font-semibold shadow hover:bg-amber-700 transition"
                    >
                      Начать бесплатно
                    </Link>
                    <Link
                      to="/login"
                      className="px-6 py-3 rounded-full border border-slate-300 text-slate-700 font-semibold hover:bg-white transition"
                    >
                      Войти
                    </Link>
                  </>
                )}
              </div>
              <div className="mt-6 flex items-center gap-4 text-sm text-slate-500">
                <span>Без рекламы</span>
                <span className="h-1 w-1 rounded-full bg-slate-300" />
                <span>Подходит новичкам</span>
                <span className="h-1 w-1 rounded-full bg-slate-300" />
                <span>Поддержка ограничений</span>
              </div>
            </div>
            <div className="relative">
              <div className="rounded-3xl bg-white shadow-xl border border-slate-100 p-6">
                <p className="text-sm font-semibold text-slate-500">Сегодняшний фокус</p>
                <h3 className="mt-2 text-2xl font-bold">Силовой прогресс</h3>
                <div className="mt-4 space-y-4">
                  {[
                    { name: 'Жим лежа', reps: '4x8–10', rest: '60 сек' },
                    { name: 'Тяга в наклоне', reps: '4x10–12', rest: '75 сек' },
                    { name: 'Разводка гантелей', reps: '3x12–15', rest: '45 сек' },
                  ].map((item) => (
                    <div key={item.name} className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
                      <div>
                        <p className="font-semibold text-slate-800">{item.name}</p>
                        <p className="text-xs text-slate-500">{item.reps}</p>
                      </div>
                      <span className="text-xs uppercase tracking-wide text-emerald-600 font-semibold">
                        Отдых {item.rest}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="mt-6 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                  План обновляется автоматически на основе вашей формы и прогресса.
                </div>
              </div>
              <div className="absolute -bottom-6 -left-6 hidden md:block rounded-2xl bg-slate-900 text-white px-5 py-4 shadow-lg">
                <p className="text-xs uppercase tracking-widest text-amber-300">Ритм недели</p>
                <p className="text-lg font-semibold">3 тренировки · 45 мин</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid gap-6 lg:grid-cols-3">
          {[
            {
              title: 'Персональные сплиты',
              text: 'Фуллбади, верх/низ или жим-тяга-ноги — всё рассчитывается под ваш темп.',
            },
            {
              title: 'Учет ограничений',
              text: 'Убираем травмоопасные упражнения и подбираем безопасные альтернативы.',
            },
            {
              title: 'Прогресс под контролем',
              text: 'Фиксируйте подходы, вес и субъективную сложность — система подстроится.',
            },
          ].map((feature) => (
            <div key={feature.title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-xl font-semibold">{feature.title}</h3>
              <p className="mt-3 text-slate-600">{feature.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold">Как это работает</h2>
              <p className="mt-4 text-slate-300">
                Мы делаем классический путь пользователя в фитнесе проще: сбор данных,
                генерация плана, сопровождение тренировок.
              </p>
            </div>
            <div className="space-y-6">
              {[
                { step: '01', title: 'Заполните профиль', text: 'Цели, опыт, частота и доступное время.' },
                { step: '02', title: 'Укажите ограничения', text: 'Колени, спина, нежелательные группы.' },
                { step: '03', title: 'Получите план', text: 'Готовый план с подходами и отдыхом.' },
              ].map((item) => (
                <div key={item.step} className="flex gap-4">
                  <div className="text-amber-300 text-lg font-semibold">{item.step}</div>
                  <div>
                    <p className="font-semibold">{item.title}</p>
                    <p className="text-slate-300 text-sm">{item.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="rounded-3xl border border-amber-200 bg-amber-50 px-8 py-12 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold">Готовы тренироваться системно?</h2>
          <p className="mt-3 text-slate-700">
            Присоединяйтесь к pro100gym и получите план под себя уже сегодня.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-4">
            {hasToken ? (
              <Link
                to="/dashboard"
                className="px-6 py-3 rounded-full bg-slate-900 text-white font-semibold hover:bg-slate-800 transition"
              >
                Открыть кабинет
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="px-6 py-3 rounded-full bg-slate-900 text-white font-semibold hover:bg-slate-800 transition"
                >
                  Создать аккаунт
                </Link>
                <Link
                  to="/login"
                  className="px-6 py-3 rounded-full border border-slate-900 text-slate-900 font-semibold hover:bg-white transition"
                >
                  Уже есть аккаунт
                </Link>
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
