import { useState, useCallback, useRef, useEffect } from 'react';
import { X } from 'lucide-react';
import { searchApi } from '../../api/client';
import type { Movie } from '../../types';
import { Spinner } from '../ui/Spinner';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectMovie: (movie: Movie) => void;
}

export function SearchModal({ isOpen, onClose, onSelectMovie }: SearchModalProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Movie[]>([]);
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
      setResults([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await searchApi.movies(searchQuery);
      setResults(data.results || []);
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
        setResults([]);
        return;
      }

      setIsLoading(true);
      searchTimeout.current = setTimeout(() => {
        searchMovies(value);
      }, 300);
    },
    [searchMovies]
  );

  const handleSelectMovie = useCallback(
    (movie: Movie) => {
      onSelectMovie(movie);
      setQuery('');
      setResults([]);
    },
    [onSelectMovie]
  );

  if (!isOpen) return null;

  return (
    <div className="search-modal" onClick={onClose}>
      <div className="search-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="search-header">
          <input
            ref={inputRef}
            type="text"
            className="search-input"
            placeholder="Search for a movie..."
            value={query}
            onChange={handleInputChange}
          />
          <button onClick={onClose} className="search-close-btn" aria-label="Close">
            <X size={24} />
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
          ) : results.length > 0 ? (
            results.map((movie) => (
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
          ) : query.length > 0 && query.length < 2 ? (
            <div className="search-empty">Keep typing to search...</div>
          ) : query.length >= 2 ? (
            <div className="search-empty">No movies found</div>
          ) : (
            <div className="search-empty">Start typing to search for movies</div>
          )}
        </div>
      </div>
    </div>
  );
}
