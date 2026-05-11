import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function ProponentLoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await api.proponentLogin(email, password);
      localStorage.setItem('bpa_token', result.access_token);
      localStorage.setItem('bpa_role', 'proponent');
      navigate('/minhas-submissoes');
    } catch (err: any) {
      setError(err.message || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="card login-card">
        <div className="card-header">
          <div className="login-icon">✉</div>
          <h2 className="card-title">Área do proponente</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '-0.5rem' }}>
            Entre com o e-mail e a senha que você cadastrou ao submeter seu projeto
          </p>
        </div>

        {error && (
          <div className="message message-error">
            <span>!</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="proponent-email">E-mail</label>
            <input
              id="proponent-email"
              type="email"
              className="form-input"
              placeholder="seu@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="proponent-password">Senha</label>
            <input
              id="proponent-password"
              type="password"
              className="form-input"
              placeholder="A senha que você criou ao submeter"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-full btn-lg"
            disabled={loading || !email || !password}
          >
            {loading ? (
              <>
                <span className="spinner spinner-sm" />
                Entrando...
              </>
            ) : (
              'Entrar →'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
