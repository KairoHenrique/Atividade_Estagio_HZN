const API_BASE = '/api';

interface RequestOptions {
  method?: string;
  body?: FormData | string;
  headers?: Record<string, string>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const token = localStorage.getItem('bpa_token');

  const headers: Record<string, string> = { ...options.headers };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: options.method || 'GET',
    headers,
    body: options.body,
  });

  // Handle auth errors — redirect only for protected route access
  if (response.status === 403) {
    const isProponentRoute = window.location.pathname.startsWith('/minha');
    if (isProponentRoute) {
      localStorage.removeItem('bpa_token');
      localStorage.removeItem('bpa_role');
      window.location.href = '/proponente';
    } else if (window.location.pathname !== '/login' && window.location.pathname !== '/proponente') {
      localStorage.removeItem('bpa_token');
      localStorage.removeItem('bpa_role');
      window.location.href = '/login';
    }
    throw new Error('Não autorizado');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
    throw new Error(error.detail || `Erro ${response.status}`);
  }

  return response.json();
}

export interface Submission {
  id: string;
  project_title: string;
  full_name: string;
  email: string;
  phone: string;
  original_filename: string;
  status: string;
  ai_analysis?: string;
  score?: number;
  verdict?: string;
  created_at: string;
  updated_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface MessageResponse {
  message: string;
  submission_id?: string;
}

export const api = {
  // Auth — Evaluator
  login: (email: string, password: string) =>
    request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  // Auth — Proponent
  proponentLogin: (email: string, password: string) =>
    request<LoginResponse>('/auth/proponent-login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  // Submissions — Public
  createSubmission: (formData: FormData) =>
    request<MessageResponse>('/submissions/', {
      method: 'POST',
      body: formData,
    }),

  // Submissions — Evaluator
  listSubmissions: (statusFilter?: string) => {
    const params = statusFilter ? `?status_filter=${statusFilter}` : '';
    return request<Submission[]>(`/submissions/${params}`);
  },

  getSubmission: (id: string) =>
    request<Submission>(`/submissions/${id}`),

  setVerdict: (id: string, action: 'approve' | 'reject') =>
    request<MessageResponse>(`/submissions/${id}/verdict`, {
      method: 'PATCH',
      body: JSON.stringify({ action }),
    }),

  getFileUrl: (id: string) => {
    const token = localStorage.getItem('bpa_token');
    return `/api/submissions/${id}/file?token=${token}`;
  },

  // Submissions — Proponent
  listMySubmissions: () =>
    request<Submission[]>('/submissions/my'),

  getMySubmission: (id: string) =>
    request<Submission>(`/submissions/my/${id}`),
};
