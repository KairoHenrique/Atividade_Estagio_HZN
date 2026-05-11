import React, { useState, useRef } from 'react';
import { api } from '../services/api';

export default function HomePage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!fullName.trim() || !email.trim() || !phone.trim() || !password.trim()) {
      setError('Por favor, preencha todos os campos.');
      return;
    }

    if (password.length < 4) {
      setError('A senha deve ter pelo menos 4 caracteres.');
      return;
    }

    if (!file) {
      setError('Por favor, selecione um documento.');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('full_name', fullName.trim());
      formData.append('email', email.trim());
      formData.append('phone', phone.trim());
      formData.append('password', password);
      formData.append('file', file);

      const result = await api.createSubmission(formData);
      setSuccess(result.message);
      setFullName('');
      setEmail('');
      setPhone('');
      setPassword('');
      setFile(null);
    } catch (err: any) {
      setError(err.message || 'Erro ao enviar submissão.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      const ext = selectedFile.name.split('.').pop()?.toLowerCase();
      if (!['pdf', 'doc', 'docx'].includes(ext || '')) {
        setError('Tipo de arquivo não suportado. Envie PDF, DOC ou DOCX.');
        return;
      }
      setFile(selectedFile);
      setError('');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      const ext = droppedFile.name.split('.').pop()?.toLowerCase();
      if (!['pdf', 'doc', 'docx'].includes(ext || '')) {
        setError('Tipo de arquivo não suportado. Envie PDF, DOC ou DOCX.');
        return;
      }
      setFile(droppedFile);
      setError('');
    }
  };

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div className="page-hero" style={{ textAlign: 'center', maxWidth: 640, margin: '0 auto' }}>
        <span className="label">Plataforma de Avaliação</span>
        <h1>Submeta sua ideia de negócio.</h1>
        <p>
          Envie seu documento para análise pela BPA Ventures.
          Utilizamos inteligência artificial para avaliar oportunidades
          de forma rápida, precisa e transparente.
        </p>
      </div>

      <div style={{ width: '100%', maxWidth: 580, margin: '0 auto' }}>
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Nova submissão</h2>
          </div>

          {success && (
            <div className="message message-success">
              <span>✓</span>
              <span>{success}</span>
            </div>
          )}

          {error && (
            <div className="message message-error">
              <span>!</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="fullName">Nome completo</label>
              <input
                id="fullName"
                type="text"
                className="form-input"
                placeholder="Digite seu nome completo"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="email">E-mail</label>
              <input
                id="email"
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
              <label className="form-label" htmlFor="phone">Telefone</label>
              <input
                id="phone"
                type="tel"
                className="form-input"
                placeholder="(11) 99999-9999"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="password">Senha de acesso</label>
              <input
                id="password"
                type="password"
                className="form-input"
                placeholder="Crie uma senha para acompanhar sua submissão"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                minLength={4}
                required
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                Use esta senha + seu e-mail para acompanhar o andamento.
              </p>
            </div>

            <div className="form-group">
              <label className="form-label">Documento</label>
              <div
                className={`file-upload ${dragOver ? 'dragover' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileChange}
                  disabled={loading}
                />
                <div className="file-upload-icon">↑</div>
                <p className="file-upload-text">
                  <strong>Clique para selecionar</strong> ou arraste aqui
                </p>
                <p className="file-upload-hint">PDF, DOC ou DOCX • Máximo 20MB</p>
              </div>

              {file && (
                <div className="file-selected">
                  <span className="file-icon">📄</span>
                  <span className="file-name">{file.name}</span>
                  <button
                    type="button"
                    className="file-remove"
                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-full btn-lg"
              disabled={loading || !fullName || !email || !phone || !password || !file}
            >
              {loading ? (
                <>
                  <span className="spinner spinner-sm" />
                  Enviando...
                </>
              ) : (
                'Enviar para avaliação →'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
