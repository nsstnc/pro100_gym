import { Link } from 'react-router-dom';

import { logoutUser } from '../api';

interface NavbarProps {
  hasToken: boolean;
}

const Navbar = ({ hasToken }: NavbarProps) => (
  <nav className="bg-white shadow-sm sticky top-0 z-50">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between h-16">
        <div className="flex">
          <div className="flex-shrink-0 flex items-center">
            <Link to="/" className="text-2xl font-bold text-indigo-600">pro100gym</Link>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {!hasToken && (
            <>
              <Link to="/register" className="text-gray-600 hover:text-indigo-600 font-medium">Регистрация</Link>
              <Link to="/login" className="text-gray-600 hover:text-indigo-600 font-medium">Вход</Link>
            </>
          )}
          {hasToken && (
            <>
              <Link to="/onboarding" className="text-gray-600 hover:text-indigo-600 font-medium">Онбординг</Link>
              <Link to="/dashboard" className="text-gray-600 hover:text-indigo-600 font-medium">Панель управления</Link>
              <button
                type="button"
                onClick={async () => {
                  try {
                    await logoutUser();
                  } catch {
                    // ignore
                  } finally {
                    try {
                      localStorage.removeItem('accessToken');
                    } catch {
                      // ignore
                    }
                    window.location.href = '/login';
                  }
                }}
                className="text-gray-600 hover:text-indigo-600 font-medium"
              >
                Выйти
              </button>
            </>
          )}
          <Link to="/about" className="text-gray-600 hover:text-indigo-600 font-medium">О нас</Link>
        </div>
      </div>
    </div>
  </nav>
);

export default Navbar;
