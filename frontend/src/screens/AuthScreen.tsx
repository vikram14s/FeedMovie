import { useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';

type AuthMode = 'login' | 'register';

export function AuthScreen() {
  const { login, register, error, isLoading, clearError } = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');

  // Form state
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const switchMode = useCallback(
    (newMode: AuthMode) => {
      setMode(newMode);
      setLocalError(null);
      clearError();
    },
    [clearError]
  );

  const handleLogin = useCallback(async () => {
    if (!email || !password) {
      setLocalError('Please fill in all fields');
      return;
    }
    setLocalError(null);
    await login(email, password);
  }, [email, password, login]);

  const handleRegister = useCallback(async () => {
    if (!username || !email || !password) {
      setLocalError('Please fill in all fields');
      return;
    }
    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters');
      return;
    }
    setLocalError(null);
    await register(username, email, password);
  }, [username, email, password, register]);

  const displayError = localError || error;

  return (
    <div className="auth-container">
      <div className="auth-logo">feedmovie</div>
      <p className="auth-tagline">Never let your food go cold because you couldn't pick a movie</p>

      <div className="auth-card">
        <h2 className="auth-title">
          {mode === 'login' ? 'Welcome back' : 'Create account'}
        </h2>

        {mode === 'register' && (
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text"
              className="form-input"
              placeholder="Choose a username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
        )}

        <div className="form-group">
          <label className="form-label">{mode === 'login' ? 'Email or Username' : 'Email'}</label>
          <input
            type={mode === 'login' ? 'text' : 'email'}
            className="form-input"
            placeholder={mode === 'login' ? 'Enter email or username' : 'you@example.com'}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <input
            type="password"
            className="form-input"
            placeholder={mode === 'login' ? 'Enter your password' : 'Create a password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                mode === 'login' ? handleLogin() : handleRegister();
              }
            }}
          />
        </div>

        {displayError ? (
          <p className="form-error visible">{displayError}</p>
        ) : null}

        <Button
          variant="primary"
          onClick={mode === 'login' ? handleLogin : handleRegister}
          disabled={isLoading}
          className="auth-btn"
          style={{ width: '100%' }}
        >
          {isLoading
            ? mode === 'login'
              ? 'Signing in...'
              : 'Creating account...'
            : mode === 'login'
              ? 'Sign In'
              : 'Create Account'}
        </Button>

        <p className="auth-switch">
          {mode === 'login' ? (
            <>
              Don't have an account?{' '}
              <span className="auth-switch-link" onClick={() => switchMode('register')}>
                Sign up
              </span>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <span className="auth-switch-link" onClick={() => switchMode('login')}>
                Sign in
              </span>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
