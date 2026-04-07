import axios from 'axios';
import type { Repository, Scan, Document, SearchResponse, Token } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired, logout user
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (username: string, password: string): Promise<Token> => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },
  
  register: async (email: string, username: string, password: string) => {
    const response = await api.post('/auth/register', { email, username, password });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Repository API
export const repositoryApi = {
  list: async (): Promise<Repository[]> => {
    const response = await api.get('/scans/');
    return response.data;
  },
  
  get: async (id: number): Promise<Repository> => {
    const response = await api.get(`/scans/${id}`);
    return response.data;
  },
  
  create: async (data: Partial<Repository>): Promise<Repository> => {
    const response = await api.post('/scans/', data);
    return response.data;
  },
  
  update: async (id: number, data: Partial<Repository>): Promise<Repository> => {
    const response = await api.put(`/scans/${id}`, data);
    return response.data;
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/scans/${id}`);
  },
};

// Scan API
export const scanApi = {
  trigger: async (repositoryId: number, triggerType: 'manual' | 'scheduled' | 'webhook' = 'manual'): Promise<Scan> => {
    const response = await api.post(`/scans/${repositoryId}/scans`, { trigger_type: triggerType });
    return response.data;
  },
  
  list: async (repositoryId: number): Promise<Scan[]> => {
    const response = await api.get(`/scans/${repositoryId}/scans`);
    return response.data;
  },
  
  get: async (repositoryId: number, scanId: number): Promise<Scan> => {
    const response = await api.get(`/scans/${repositoryId}/scans/${scanId}`);
    return response.data;
  },
};

// Document API
export const documentApi = {
  list: async (params?: { repository_id?: number; doc_type?: string }): Promise<Document[]> => {
    const response = await api.get('/docs/', { params });
    return response.data;
  },
  
  get: async (id: number): Promise<Document> => {
    const response = await api.get(`/docs/${id}`);
    return response.data;
  },
  
  getBySlug: async (slug: string, repository_id?: number): Promise<Document> => {
    const response = await api.get(`/docs/slug/${slug}`, { params: { repository_id } });
    return response.data;
  },
};

// Search API
export const searchApi = {
  search: async (query: string, options?: { 
    repository_ids?: number[]; 
    doc_types?: string[]; 
    languages?: string[];
    limit?: number;
    offset?: number;
  }): Promise<SearchResponse> => {
    const response = await api.post('/search/', {
      query,
      ...options,
    });
    return response.data;
  },
  
  suggestions: async (q: string, limit: number = 10): Promise<string[]> => {
    const response = await api.get('/search/suggestions', { params: { q, limit } });
    return response.data;
  },
};

export default api;
