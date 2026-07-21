import { apiClient } from './client';
import type { LoginResponse, User } from '../types';

export interface SignupPayload {
  email: string;
  password: string;
  full_name: string;
  phone: string;
  date_of_birth: string;
}

export function signup(payload: SignupPayload) {
  return apiClient.post<User>('/auth/signup', payload).then((r) => r.data);
}

export function login(email: string, password: string) {
  return apiClient.post<LoginResponse>('/auth/login', { email, password }).then((r) => r.data);
}

export function fetchMe() {
  return apiClient.get<User>('/auth/me').then((r) => r.data);
}
