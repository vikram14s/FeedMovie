import { useEffect, useCallback } from 'react';
import { useAuthStore } from '../stores/authStore';

export function useAuth() {
  const { token, user, isLoading, error, checkAuth, login, register, logout, clearError, setUser } =
    useAuthStore();

  // Check auth on mount if token exists but no user
  useEffect(() => {
    if (token && !user && !isLoading) {
      checkAuth();
    }
  }, [token, user, isLoading, checkAuth]);

  // Stable callbacks (Vercel best practice: rerender-functional-setstate)
  const handleLogin = useCallback(
    async (email: string, password: string) => {
      return login(email, password);
    },
    [login]
  );

  const handleRegister = useCallback(
    async (username: string, email: string, password: string) => {
      return register(username, email, password);
    },
    [register]
  );

  const handleLogout = useCallback(() => {
    logout();
  }, [logout]);

  return {
    token,
    user,
    isLoading,
    error,
    isAuthenticated: !!token && !!user,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    checkAuth,
    clearError,
    setUser,
  };
}
