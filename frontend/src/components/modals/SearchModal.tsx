import { useState, useCallback, useRef, useEffect } from 'react';
import { X, Film, Users } from 'lucide-react';
import { searchApi, usersApi } from '../../api/client';
import type { Movie } from '../../types';
import { Spinner } from '../ui/Spinner';

interface UserResult {
  id: number;
  username: string;
  bio?: string;
  ratings_count: number;
}

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectMovie: (movie: Movie) => void;
  onSelectUser?: (userId: number, username: string) => void;
}

export function SearchModal({ isOpen, onClose, onSelectMovie, onSelectUser }: SearchModalProps) {
  const [activeTab, setActiveTab] = useState<'movies' | 'users'>('movies');
  const [query, setQuery] = useState('');
  const [movieResults, setMovieResults] = useState<Movie[]>([]);
  const [userResults, setUserResults] = useState<UserResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const searchMovies = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setMovieResults([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await searchApi.movies(searchQuery);
      setMovieResults(data.results || []);
    } catch (err) {
      setError('Error searching. Try again.');
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const searchUsers = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setUserResults([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await usersApi.search(searchQuery);
      setUserResults(data.users || []);
    } catch (err) {
      setError('Error searching. Try again.');
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setQuery(value);

      // Debounce search
      if (searchTimeout.current) {
        clearTimeout(searchTimeout.current);
      }

      if (value.length < 2) {
        setMovieResults([]);
        setUserResults([]);
        return;
      }

      setIsLoading(true);
      searchTimeout.current = setTimeout(() => {
        if (activeTab === 'movies') {
          searchMovies(value);
        } else {
          searchUsers(value);
        }
      }, 300);
    },
    [activeTab, searchMovies, searchUsers]
  );

  // Re-search when tab changes
  const handleTabChange = useCallback((tab: 'movies' | 'users') => {
    setActiveTab(tab);
    setError(null);
    if (query.length >= 2) {
      setIsLoading(true);
      if (tab === 'movies') {
        searchMovies(query);
      } else {
        searchUsers(query);
      }
    }
  }, [query, searchMovies, searchUsers]);

  const handleSelectMovie = useCallback(
    (movie: Movie) => {
      onSelectMovie(movie);
      setQuery('');
      setMovieResults([]);
      setUserResults([]);
    },
    [onSelectMovie]
  );

  const handleSelectUser = useCallback(
    (user: UserResult) => {
      if (onSelectUser) {
        onSelectUser(user.id, user.username);
        setQuery('');
        setMovieResults([]);
        setUserResults([]);
      }
    },
    [onSelectUser]
  );

  if (!isOpen) return null;

  const placeholder = activeTab === 'movies' ? 'Search for movies...' : 'Search for users...';
  const emptyMessage = activeTab === 'movies' ? 'No movies found' : 'No users found';
  const defaultMessage = activeTab === 'movies' ? 'Start typing to search for movies' : 'Start typing to search for users';

  return (
    <div className="search-modal" onClick={onClose}>
      <div className="search-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="search-header">
          <input
            ref={inputRef}
            type="text"
            className="search-input"
            placeholder={placeholder}
            value={query}
            onChange={handleInputChange}
          />
          <button onClick={onClose} className="search-close-btn" aria-label="Close">
            <X size={24} />
          </button>
        </div>

        {/* Search Tabs */}
        <div className="search-tabs">
          <button
            className={`search-tab ${activeTab === 'movies' ? 'active' : ''}`}
            onClick={() => handleTabChange('movies')}
          >
            <Film size={16} />
            <span>Movies</span>
          </button>
          <button
            className={`search-tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => handleTabChange('users')}
          >
            <Users size={16} />
            <span>Users</span>
          </button>
        </div>

        <div className="search-results">
          {isLoading ? (
            <div className="search-loading">
              <Spinner size="sm" />
              <p>Searching...</p>
            </div>
          ) : error ? (
            <div className="search-empty">{error}</div>
          ) : activeTab === 'movies' && movieResults.length > 0 ? (
            movieResults.map((movie) => (
              <div
                key={movie.tmdb_id}
                className="search-result-item"
                onClick={() => handleSelectMovie(movie)}
              >
                <img
                  src={movie.poster_path || 'https://via.placeholder.com/48x72?text=?'}
                  alt={movie.title}
                  className="search-result-poster"
                />
                <div className="search-result-info">
                  <div className="search-result-title">{movie.title}</div>
                  <div className="search-result-year">{movie.year || ''}</div>
                </div>
              </div>
            ))
          ) : activeTab === 'users' && userResults.length > 0 ? (
            userResults.map((user) => (
              <div
                key={user.id}
                className="search-result-item"
                onClick={() => handleSelectUser(user)}
              >
                <div className="search-result-avatar">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <div className="search-result-info">
                  <div className="search-result-title">{user.username}</div>
                  <div className="search-result-meta">
                    {user.ratings_count} {user.ratings_count === 1 ? 'rating' : 'ratings'}
                  </div>
                </div>
              </div>
            ))
          ) : query.length > 0 && query.length < 2 ? (
            <div className="search-empty">Keep typing to search...</div>
          ) : query.length >= 2 ? (
            <div className="search-empty">{emptyMessage}</div>
          ) : (
            <div className="search-empty">{defaultMessage}</div>
          )}
        </div>
      </div>
    </div>
  );
}
