import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api, Submission } from '../services/api';

const STATUS_LABELS: Record<string, string> = {
  pending_analysis: 'Pendente',
  analyzing: 'Analisando',
  analyzed: 'Analisado',
  approved: 'Aprovado',
  rejected: 'Reprovado',
  error: 'Erro',
};

const STATUS_BADGE: Record<string, string> = {
  pending_analysis: 'badge-pending',
  analyzing: 'badge-analyzing',
  analyzed: 'badge-analyzed',
  approved: 'badge-approved',
  rejected: 'badge-rejected',
  error: 'badge-error',
};

export default function DashboardPage() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    loadSubmissions();
  }, [filter]);

  const loadSubmissions = async () => {
    setLoading(true);
    try {
      const data = await api.listSubmissions(filter || undefined);
      setSubmissions(data);
    } catch (err: any) {
      if (err.message === 'Não autorizado') {
        navigate('/login');
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    total: submissions.length,
    analyzed: submissions.filter(s => s.status === 'analyzed').length,
    approved: submissions.filter(s => s.status === 'approved').length,
    rejected: submissions.filter(s => s.status === 'rejected').length,
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="page">
      <div style={{ marginBottom: '2rem' }}>
        <span className="label" style={{ display: 'inline-block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase' as const, letterSpacing: '0.15em', marginBottom: '0.75rem', padding: '6px 14px', background: 'var(--accent-bg)', borderRadius: '9999px' }}>
          Painel do Avaliador
        </span>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, marginBottom: '0.5rem', letterSpacing: '-0.02em' }}>
          Oportunidades
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Gerencie e avalie as oportunidades de negócio submetidas.
        </p>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Total</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.analyzed}</div>
          <div className="stat-label">Aguardando</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.approved}</div>
          <div className="stat-label">Aprovadas</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.rejected}</div>
          <div className="stat-label">Reprovadas</div>
        </div>
      </div>

      <div className="filters-row">
        {[
          { value: '', label: 'Todas' },
          { value: 'analyzed', label: 'Aguardando' },
          { value: 'approved', label: 'Aprovadas' },
          { value: 'rejected', label: 'Reprovadas' },
          { value: 'pending_analysis', label: 'Pendentes' },
        ].map(f => (
          <button
            key={f.value}
            className={`filter-btn ${filter === f.value ? 'active' : ''}`}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="message message-error">
          <span>!</span>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
          <span>Carregando submissões...</span>
        </div>
      ) : submissions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">○</div>
          <h3>Nenhuma submissão encontrada</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Novas oportunidades aparecerão aqui quando forem submetidas.</p>
        </div>
      ) : (
        <div className="submissions-grid">
          {submissions.map(sub => (
            <Link
              key={sub.id}
              to={`/avaliacao/${sub.id}`}
              className="submission-card"
            >
              <div className="submission-info">
                <h3>{sub.full_name}</h3>
                <p>
                  {sub.email} · {sub.original_filename} · {formatDate(sub.created_at)}
                </p>
              </div>
              <div className="submission-score">
                {sub.score ? `${sub.score}/30` : '—'}
              </div>
              <span className={`badge ${STATUS_BADGE[sub.status] || 'badge-pending'}`}>
                {STATUS_LABELS[sub.status] || sub.status}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
