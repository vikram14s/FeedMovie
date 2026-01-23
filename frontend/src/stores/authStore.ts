import { create } from 'zustand';
import type { User } from '../types';
import { authApi, ApiError } from '../api/client';

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
  setUser: (user: User) => void;
  clearError: () => void;
}

// Lazy init from localStorage (Vercel best practice: rerender-lazy-state-init)
const getInitialToken = () => localStorage.getItem('feedmovie_token');

export const useAuthStore = create<AuthState>((set, get) => ({
  token: getInitialToken(),
  user: null,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authApi.login(email, password);
      localStorage.setItem('feedmovie_token', data.token);
      set({ token: data.token, user: data.user, isLoading: false });
      return true;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Login failed';
      set({ error: message, isLoading: false });
      return false;
    }
  },

  register: async (username, email, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authApi.register(username, email, password);
      localStorage.setItem('feedmovie_token', data.token);
      set({ token: data.token, user: data.user, isLoading: false });
      return true;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Registration failed';
      set({ error: message, isLoading: false });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('feedmovie_token');
    localStorage.removeItem('feedmovie_genres');
    localStorage.removeItem('feedmovie_profiles');
    localStorage.removeItem('feedmovie_profiles_completed');
    set({ token: null, user: null, error: null });
  },

  checkAuth: async () => {
    const { token } = get();
    if (!token) return false;

    set({ isLoading: true });
    try {
      const data = await authApi.me();
      set({ user: data.user, isLoading: false });
      return true;
    } catch {
      // Token invalid, clear it
      localStorage.removeItem('feedmovie_token');
      set({ token: null, user: null, isLoading: false });
      return false;
    }
  },

  setUser: (user) => set({ user }),

  clearError: () => set({ error: null }),
}));
