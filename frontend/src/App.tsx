import {useEffect, useState, type FC, type JSX} from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';

import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import About from './pages/About';
import Login from './pages/Login';
import Register from './pages/Register';
import Onboarding from './pages/Onboarding';
import DashboardLayout from './pages/dashboard/DashboardLayout';
import DashboardHome from './pages/dashboard/DashboardHome';
import DashboardWorkout from './pages/dashboard/DashboardWorkout';
import DashboardStats from './pages/dashboard/DashboardStats';
import Connect from './pages/Connect';

const getHasToken = () => {
  try {
    return Boolean(localStorage.getItem('accessToken'));
  } catch {
    return false;
  }
};

const getPageTitle = (pathname: string) => {
  switch (pathname) {
    case '/':
      return 'Главная';
    case '/register':
      return 'Регистрация';
    case '/login':
      return 'Вход';
    case '/about':
      return 'О нас';
    case '/connect':
      return 'Подключение Telegram';
    case '/dashboard':
      return 'Дашборд';
    case '/dashboard/workout':
      return 'Текущая тренировка';
    case '/dashboard/statistics':
      return 'Статистика';
    case '/onboarding':
      return 'Онбординг';
    default:
      return 'pro100gym';
  }
};

const AppShell: FC = () => {
  const location = useLocation();
  const [hasToken, setHasToken] = useState(getHasToken);

  useEffect(() => {
    setHasToken(getHasToken());
    const sectionTitle = getPageTitle(location.pathname);
    document.title = `pro100gym — ${sectionTitle}`;
  }, [location.pathname]);

  useEffect(() => {
    const handleStorage = () => {
      setHasToken(getHasToken());
    };

    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
      <Navbar hasToken={hasToken} />

      <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/about" element={<About />} />
            <Route path="/connect" element={<Connect />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/dashboard" element={<DashboardLayout />}>
              <Route index element={<DashboardHome />} />
              <Route path="workout" element={<DashboardWorkout />} />
              <Route path="statistics" element={<DashboardStats />} />
            </Route>
          </Routes>
        </main>

      <Footer />
    </div>
  );
};

function App(): JSX.Element {
  return (
    <Router>
      <AppShell />
    </Router>
  );
}

export default App;
