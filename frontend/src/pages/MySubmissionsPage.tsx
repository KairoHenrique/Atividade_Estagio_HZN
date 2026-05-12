import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api, Submission } from '../services/api';

const STATUS_LABELS: Record<string, string> = {
  pending_analysis: 'Pendente de análise',
  analyzing: 'Analisando...',
  analyzed: 'Análise concluída',
  approved: 'Aprovada',
  rejected: 'Reprovada',
  error: 'Erro no processamento',
};

const STATUS_BADGE: Record<string, string> = {
  pending_analysis: 'badge-pending',
  analyzing: 'badge-analyzing',
  analyzed: 'badge-analyzed',
  approved: 'badge-approved',
  rejected: 'badge-rejected',
  error: 'badge-error',
};

const STATUS_DESCRIPTIONS: Record<string, string> = {
  pending_analysis: 'Seu documento está na fila para análise pela nossa IA.',
  analyzing: 'Nossa IA está analisando seu documento neste momento.',
  analyzed: 'A análise foi concluída e está aguardando avaliação da equipe.',
  approved: 'Parabéns! Sua oportunidade foi aprovada pela equipe.',
  rejected: 'Sua oportunidade não foi aprovada neste momento.',
  error: 'Ocorreu um erro durante o processamento. Nossa equipe foi notificada.',
};

export default function MySubmissionsPage() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadSubmissions();
  }, []);

  const loadSubmissions = async () => {
    setLoading(true);
    try {
      const data = await api.listMySubmissions();
      setSubmissions(data);
    } catch (err: any) {
      if (err.message === 'Não autorizado') {
        navigate('/proponente');
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
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

  const handleLogout = () => {
    localStorage.removeItem('bpa_token');
    localStorage.removeItem('bpa_role');
    navigate('/proponente');
  };

  const selected = selectedId ? submissions.find(s => s.id === selectedId) : null;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <span style={{ display: 'inline-block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase' as const, letterSpacing: '0.15em', marginBottom: '0.75rem', padding: '6px 14px', background: 'var(--accent-bg)', borderRadius: '9999px' }}>
            Minhas Submissões
          </span>
          <h1 style={{ fontSize: '2rem', fontWeight: 900, marginBottom: '0.5rem', letterSpacing: '-0.02em' }}>
            Acompanhamento
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Veja o status e andamento das suas submissões.
          </p>
        </div>
        <button className="btn btn-outline" onClick={handleLogout}>Sair</button>
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
          <span>Carregando suas submissões...</span>
        </div>
      ) : submissions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">○</div>
          <h3>Nenhuma submissão encontrada</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            Você ainda não enviou nenhuma ideia de negócio com este e-mail.
          </p>
          <Link to="/" className="btn btn-primary">Submeter uma ideia →</Link>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {submissions.map(sub => (
            <div key={sub.id} className="card" style={{ cursor: 'pointer', padding: '1.5rem 2rem' }} onClick={() => setSelectedId(selectedId === sub.id ? null : sub.id)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                    {sub.project_title}
                  </h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Enviado em {formatDate(sub.created_at)}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span className={`badge ${STATUS_BADGE[sub.status] || 'badge-pending'}`}>
                    {STATUS_LABELS[sub.status] || sub.status}
                  </span>
                </div>
              </div>

              {selectedId === sub.id && (
                <div style={{ marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)' }}>
                  <div className={`message ${sub.status === 'rejected' ? 'message-error' : sub.status === 'approved' ? 'message-success' : 'message-info'}`} style={{ marginBottom: '1rem' }}>
                    <span>{sub.status === 'rejected' ? '!' : sub.status === 'approved' ? '✓' : 'ℹ'}</span>
                    <span>{STATUS_DESCRIPTIONS[sub.status] || 'Status desconhecido.'}</span>
                  </div>

                  <div className="detail-grid">
                    <div className="detail-item">
                      <div className="label">Status atual</div>
                      <div className="value">{STATUS_LABELS[sub.status]}</div>
                    </div>
                    <div className="detail-item">
                      <div className="label">Data de envio</div>
                      <div className="value">{formatDate(sub.created_at)}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
