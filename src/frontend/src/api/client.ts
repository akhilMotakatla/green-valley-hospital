import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

const TOKEN_STORAGE_KEY = 'gvh_token';

let inMemoryToken: string | null = null;

export function setToken(token: string | null) {
  inMemoryToken = token;
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

export function getToken(): string | null {
  if (inMemoryToken) return inMemoryToken;
  const stored = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (stored) inMemoryToken = stored;
  return inMemoryToken;
}

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface ApiErrorShape {
  detail?: string | { msg: string; loc?: (string | number)[] }[];
}

export function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as ApiErrorShape | undefined;
    if (data?.detail) {
      if (typeof data.detail === 'string') return data.detail;
      if (Array.isArray(data.detail)) {
        return data.detail.map((d) => d.msg).join('; ');
      }
    }
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return 'Unexpected error';
}
