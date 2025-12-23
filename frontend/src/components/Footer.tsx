const Footer = () => (
  <footer className="bg-gray-800 text-gray-300 py-10 px-4 sm:px-6 lg:px-8 text-center">
    <div className="max-w-7xl mx-auto">
      <p className="mb-4">&copy; {new Date().getFullYear()} pro100gym. Все права защищены.</p>
      <div className="flex justify-center space-x-6">
        <a href="#" className="text-gray-400 hover:text-white transition duration-300">Приватность</a>
        <a href="#" className="text-gray-400 hover:text-white transition duration-300">Условия</a>
      </div>
    </div>
  </footer>
);

export default Footer;
