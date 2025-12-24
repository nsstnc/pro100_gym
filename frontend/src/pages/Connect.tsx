import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTelegramLink } from '../api';

const Connect = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Проверяем, авторизован ли пользователь
    const token = localStorage.getItem('accessToken');
    if (!token) {
      navigate('/login');
      return;
    }
  }, [navigate]);

  const handleConnectTelegram = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getTelegramLink();
      // Открываем Telegram бота в новой вкладке
      window.open(response.telegram_link, '_blank');
    } catch (err) {
      setError('Не удалось получить ссылку на Telegram бота. Попробуйте еще раз.');
      console.error('Error getting Telegram link:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Подключение Telegram
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Подключите свой Telegram аккаунт для быстрого входа и управления тренировками через бота
          </p>
        </div>

        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-4">
                Нажмите кнопку ниже, чтобы открыть Telegram бота и автоматически подключить аккаунт
              </p>

              <button
                onClick={handleConnectTelegram}
                disabled={isLoading}
                className="w-full flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <div className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Получение ссылки...
                  </div>
                ) : (
                  <div className="flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                    </svg>
                    Открыть Telegram бота
                  </div>
                )}
              </button>
            </div>

            <div className="border-t border-gray-200 pt-4">
              <p className="text-xs text-gray-500 text-center">
                Или авторизуйтесь в боте вручную, введя логин и пароль
              </p>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Вернуться в дашборд
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Connect;
