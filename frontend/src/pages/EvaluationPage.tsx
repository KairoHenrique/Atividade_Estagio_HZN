import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, Submission } from '../services/api';

const STATUS_LABELS: Record<string, string> = {
  pending_analysis: 'Pendente de análise',
  analyzing: 'Analisando...',
  analyzed: 'Aguardando avaliação',
  approved: 'Aprovada',
  rejected: 'Reprovada',
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

export default function EvaluationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [showModal, setShowModal] = useState<'approve' | 'reject' | null>(null);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    loadSubmission();
  }, [id]);

  const loadSubmission = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await api.getSubmission(id);
      setSubmission(data);
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

  const handleVerdict = async (action: 'approve' | 'reject') => {
    if (!id) return;
    setActionLoading(true);
    try {
      const result = await api.setVerdict(id, action);
      setSuccessMsg(result.message);
      setShowModal(null);
      await loadSubmission();
    } catch (err: any) {
      setError(err.message);
      setShowModal(null);
    } finally {
      setActionLoading(false);
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

  if (loading) {
    return (
      <div className="loading-container" style={{ minHeight: '60vh' }}>
        <div className="spinner" />
        <span>Carregando submissão...</span>
      </div>
    );
  }

  if (error && !submission) {
    return (
      <div className="page">
        <div className="message message-error">
          <span>!</span>
          <span>{error}</span>
        </div>
        <button className="btn btn-outline" onClick={() => navigate('/dashboard')}>
          ← Voltar
        </button>
      </div>
    );
  }

  if (!submission) return null;

  const canEvaluate = submission.status === 'analyzed';

  return (
    <div className="page">
      <button
        className="btn btn-outline"
        onClick={() => navigate('/dashboard')}
        style={{ marginBottom: '1.5rem' }}
      >
        ← Voltar ao painel
      </button>

      {successMsg && (
        <div className="message message-success">
          <span>✓</span>
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div className="message message-error">
          <span>!</span>
          <span>{error}</span>
        </div>
      )}

      {/* Header */}
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase' as const, letterSpacing: '0.12em' }}>
              Avaliação de oportunidade
            </span>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 900, marginTop: '0.5rem', marginBottom: '0.75rem', letterSpacing: '-0.02em' }}>
              {submission.full_name}
            </h1>
            <span className={`badge ${STATUS_BADGE[submission.status] || 'badge-pending'}`}>
              {STATUS_LABELS[submission.status] || submission.status}
            </span>
          </div>

          {submission.score !== null && submission.score !== undefined && (
            <div className="score-display">
              <div style={{ textAlign: 'center' }}>
                <div className="score-circle">{submission.score}</div>
                <div className="score-label" style={{ marginTop: 6 }}>/30</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Details */}
      <div className="card" style={{ marginBottom: '1rem' }}>
        <h3 className="card-title" style={{ marginBottom: '1.25rem' }}>Dados do proponente</h3>
        <div className="detail-grid">
          <div className="detail-item">
            <div className="label">Nome completo</div>
            <div className="value">{submission.full_name}</div>
          </div>
          <div className="detail-item">
            <div className="label">E-mail</div>
            <div className="value">{submission.email}</div>
          </div>
          <div className="detail-item">
            <div className="label">Telefone</div>
            <div className="value">{submission.phone}</div>
          </div>
          <div className="detail-item">
            <div className="label">Documento</div>
            <div className="value">{submission.original_filename}</div>
          </div>
          <div className="detail-item">
            <div className="label">Data de submissão</div>
            <div className="value">{formatDate(submission.created_at)}</div>
          </div>
          {submission.verdict && (
            <div className="detail-item">
              <div className="label">Veredito IA</div>
              <div className="value">{submission.verdict}</div>
            </div>
          )}
        </div>

        {/* Download PDF Button */}
        <div style={{ marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)' }}>
          <button
            className="btn btn-outline"
            onClick={async () => {
              try {
                const token = localStorage.getItem('bpa_token');
                const res = await fetch(`/api/submissions/${id}/file`, {
                  headers: { Authorization: `Bearer ${token}` },
                });
                if (!res.ok) throw new Error('Erro ao baixar arquivo');
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                window.open(url, '_blank');
              } catch (err) {
                setError('Erro ao abrir o documento.');
              }
            }}
          >
            📄 Abrir documento original
          </button>
        </div>
      </div>

      {/* AI Analysis */}
      {submission.ai_analysis && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <h3 className="card-title" style={{ marginBottom: '1rem' }}>Análise da inteligência artificial</h3>
          <div className="analysis-container">
            {submission.ai_analysis}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {canEvaluate && (
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '0.5rem' }}>Decisão final</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
            Após revisar a análise, aprove ou reprove esta oportunidade.
          </p>
          <div className="action-buttons">
            <button
              className="btn btn-success"
              onClick={() => setShowModal('approve')}
              disabled={actionLoading}
            >
              Aprovar oportunidade
            </button>
            <button
              className="btn btn-danger"
              onClick={() => setShowModal('reject')}
              disabled={actionLoading}
            >
              Reprovar oportunidade
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>
              {showModal === 'approve'
                ? 'Confirmar aprovação'
                : 'Confirmar reprovação'}
            </h3>
            <p>
              {showModal === 'approve'
                ? `Tem certeza que deseja aprovar a oportunidade de ${submission.full_name}?`
                : `Tem certeza que deseja reprovar a oportunidade de ${submission.full_name}?`}
            </p>
            <div className="modal-actions">
              <button
                className="btn btn-outline"
                onClick={() => setShowModal(null)}
                disabled={actionLoading}
              >
                Cancelar
              </button>
              <button
                className={showModal === 'approve' ? 'btn btn-success' : 'btn btn-danger'}
                onClick={() => handleVerdict(showModal)}
                disabled={actionLoading}
              >
                {actionLoading ? (
                  <>
                    <span className="spinner spinner-sm" />
                    Processando...
                  </>
                ) : (
                  showModal === 'approve' ? 'Confirmar aprovação' : 'Confirmar reprovação'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
