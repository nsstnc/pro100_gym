import { Link } from 'react-router-dom';
import type {FC} from 'react';

import { logoutUser } from '../api';

interface NavbarProps {
  hasToken: boolean;
}

const Navbar: FC<NavbarProps> = ({ hasToken }) => (
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
              <Link to="/connect" className="text-blue-600 hover:text-blue-800 font-medium flex items-center">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                </svg>
                Telegram
              </Link>
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
