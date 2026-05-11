import { BrowserRouter, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import ProponentLoginPage from './pages/ProponentLoginPage';
import DashboardPage from './pages/DashboardPage';
import EvaluationPage from './pages/EvaluationPage';
import MySubmissionsPage from './pages/MySubmissionsPage';

function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem('bpa_token');
  const role = localStorage.getItem('bpa_role');
  const isEvaluator = token && role !== 'proponent';
  const isProponent = token && role === 'proponent';

  const handleLogout = () => {
    localStorage.removeItem('bpa_token');
    localStorage.removeItem('bpa_role');
    navigate('/');
  };

  return (
    <header className="header">
      <Link to="/" className="header-logo">
        <div className="logo-icon">⚡</div>
        <span>BPA Ventures</span>
      </Link>
      <nav className="header-nav">
        <Link to="/">Submeter Ideia</Link>
        {isProponent ? (
          <>
            <Link to="/minhas-submissoes">Minhas Submissões</Link>
            <button className="btn-logout" onClick={handleLogout}>Sair</button>
          </>
        ) : isEvaluator ? (
          <>
            <Link to="/dashboard">Dashboard</Link>
            <button className="btn-logout" onClick={handleLogout}>Sair</button>
          </>
        ) : (
          <>
            <Link to="/proponente">Acompanhar Submissão</Link>
            <Link to="/login">Avaliador</Link>
          </>
        )}
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/proponente" element={<ProponentLoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/avaliacao/:id" element={<EvaluationPage />} />
        <Route path="/minhas-submissoes" element={<MySubmissionsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
