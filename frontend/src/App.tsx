import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

// Компоненты-заглушки
const Home = () => (
  <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 text-gray-900">
    <h2 className="text-4xl font-extrabold mb-4">Добро пожаловать в pro100gym!</h2>
    <p className="text-lg text-gray-600">Ваш персональный тренер в кармане.</p>
  </div>
);

const About = () => (
  <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 text-gray-900">
    <h2 className="text-4xl font-extrabold mb-4">О нас</h2>
    <p className="text-lg text-gray-600">Мы помогаем вам достигать фитнес-целей.</p>
  </div>
);

const Dashboard = () => (
  <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 text-gray-900">
    <h2 className="text-4xl font-extrabold mb-4">Панель управления</h2>
    <p className="text-lg text-gray-600">Здесь будет ваша статистика и тренировки.</p>
  </div>
);

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
        {/* Навигационная панель */}
        <nav className="bg-white shadow-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <Link to="/" className="text-2xl font-bold text-indigo-600">pro100gym</Link>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Link to="/about" className="text-gray-600 hover:text-indigo-600 font-medium">О нас</Link>
                <Link to="/dashboard" className="text-gray-600 hover:text-indigo-600 font-medium">Панель управления</Link>
              </div>
            </div>
          </div>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>

        {/* Футер */}
        <footer className="bg-gray-800 text-gray-300 py-10 px-4 sm:px-6 lg:px-8 text-center">
          <div className="max-w-7xl mx-auto">
            <p className="mb-4">&copy; {new Date().getFullYear()} pro100gym. Все права защищены.</p>
            <div className="flex justify-center space-x-6">
              <a href="#" className="text-gray-400 hover:text-white transition duration-300">Приватность</a>
              <a href="#" className="text-gray-400 hover:text-white transition duration-300">Условия</a>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
