import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { login } from '../api';

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      setIsSubmitting(true);
      setError(null);
      const token = await login(username, password);
      localStorage.setItem('accessToken', token.access_token);
      navigate('/onboarding');
    } catch {
      setError('Не удалось выполнить вход. Проверьте логин и пароль.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 text-gray-900 px-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm p-8">
        <h2 className="text-2xl font-extrabold mb-6 text-center">Вход</h2>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="login-username">
              Логин
            </label>
            <input
              id="login-username"
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="login-password">
              Пароль
            </label>
            <input
              id="login-password"
              type="password"
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={isSubmitting}
            className={`w-full px-4 py-2 rounded-md text-sm font-semibold ${
              isSubmitting ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-indigo-600 text-white'
            }`}
          >
            {isSubmitting ? 'Входим...' : 'Войти'}
          </button>
        </form>
        <p className="mt-4 text-sm text-gray-600 text-center">
          Нет аккаунта?{' '}
          <Link to="/register" className="text-indigo-600 hover:text-indigo-700 font-medium">
            Зарегистрироваться
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
