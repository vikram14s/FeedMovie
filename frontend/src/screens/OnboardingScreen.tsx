import { useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { onboardingApi, profileApi, searchApi } from '../api/client';
import type { Movie } from '../types';
import { Button } from '../components/ui/Button';
import { StarRating } from '../components/ui/StarRating';
import { Spinner } from '../components/ui/Spinner';
import { moodPresets, useRecommendationStore } from '../stores/recommendationStore';
import { useUIStore } from '../stores/uiStore';

type OnboardingStep = 'path' | 'letterboxd' | 'swipe' | 'search' | 'profiles' | 'curators' | 'genres';

const SWIPE_MOVIE_COUNT = 10; // Number of movies to swipe through
const MAX_SEARCH_ADDITIONS = 5; // Number of movies user can add via search

// Curators/tastemakers that new users can follow
const curatorProfiles = [
  {
    id: 'film_critic',
    name: 'The Film Critic',
    avatar: '🎭',
    bio: 'Award-season expert, loves prestige cinema',
    recentPicks: ['Oppenheimer', 'Past Lives', 'The Holdovers'],
  },
  {
    id: 'popcorn_fan',
    name: 'Popcorn Pete',
    avatar: '🍿',
    bio: 'Blockbuster enthusiast, here for the fun',
    recentPicks: ['Dune: Part Two', 'Top Gun: Maverick', 'Spider-Man'],
  },
  {
    id: 'horror_host',
    name: 'Scary Sarah',
    avatar: '🧛',
    bio: 'Horror aficionado, loves a good scare',
    recentPicks: ['Talk to Me', 'Smile', 'Barbarian'],
  },
  {
    id: 'indie_hunter',
    name: 'Indie Ian',
    avatar: '🎸',
    bio: 'Discovers hidden gems before they trend',
    recentPicks: ['Aftersun', 'The Worst Person in the World', 'Drive My Car'],
  },
  {
    id: 'classic_lover',
    name: 'Classic Clara',
    avatar: '📽️',
    bio: 'Old Hollywood expert, timeless taste',
    recentPicks: ['Casablanca', '12 Angry Men', 'Sunset Boulevard'],
  },
  {
    id: 'global_cinema',
    name: 'World Cinema Wes',
    avatar: '🌍',
    bio: 'Explores films from every corner of the globe',
    recentPicks: ['Parasite', 'City of God', 'Amélie'],
  },
];

// Starter taste profiles for new users
const tasteProfiles = [
  {
    id: 'cinephile',
    icon: '🎬',
    name: 'The Cinephile',
    desc: 'Appreciates critically acclaimed films and auteur directors',
    genres: ['Drama', 'Documentary'],
    examples: ['Parasite', 'There Will Be Blood', 'In the Mood for Love'],
  },
  {
    id: 'blockbuster',
    icon: '💥',
    name: 'The Blockbuster Fan',
    desc: 'Lives for epic action, superheroes, and big spectacles',
    genres: ['Action', 'Sci-Fi'],
    examples: ['The Dark Knight', 'Avengers: Endgame', 'Top Gun: Maverick'],
  },
  {
    id: 'horror',
    icon: '👻',
    name: 'The Horror Buff',
    desc: 'Loves scares, suspense, and things that go bump in the night',
    genres: ['Horror', 'Thriller'],
    examples: ['Hereditary', 'Get Out', 'The Conjuring'],
  },
  {
    id: 'comedy',
    icon: '😂',
    name: 'The Comedy Lover',
    desc: 'Always looking for a good laugh and feel-good vibes',
    genres: ['Comedy'],
    examples: ['Superbad', 'The Grand Budapest Hotel', 'Bridesmaids'],
  },
  {
    id: 'romantic',
    icon: '💕',
    name: 'The Romantic',
    desc: 'Swoons for love stories and emotional connections',
    genres: ['Romance', 'Drama'],
    examples: ['Pride & Prejudice', 'La La Land', 'Before Sunrise'],
  },
  {
    id: 'scifi',
    icon: '🚀',
    name: 'The Explorer',
    desc: 'Fascinated by sci-fi worlds, fantasy realms, and imagination',
    genres: ['Sci-Fi', 'Animation'],
    examples: ['Interstellar', 'Blade Runner 2049', 'Spirited Away'],
  },
];

// Search result item component with quick rating
function SearchResultItem({
  movie,
  onAdd,
}: {
  movie: Movie;
  onAdd: (rating: number) => void;
}) {
  const [selectedRating, setSelectedRating] = useState(0);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '10px 12px',
        background: 'var(--bg-secondary)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
      }}
    >
      {movie.poster_path ? (
        <img
          src={movie.poster_path}
          alt={movie.title}
          style={{ width: '40px', height: '60px', borderRadius: '4px', objectFit: 'cover' }}
        />
      ) : (
        <div
          style={{
            width: '40px',
            height: '60px',
            borderRadius: '4px',
            background: 'var(--bg-tertiary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            color: 'var(--text-muted)',
          }}
        >
          🎬
        </div>
      )}

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 500, fontSize: '14px', marginBottom: '2px' }}>
          {movie.title}
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          {movie.year || ''}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '4px' }}>
        {[1, 2, 3, 4, 5].map((rating) => (
          <button
            key={rating}
            onClick={() => {
              setSelectedRating(rating);
              onAdd(rating);
            }}
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '4px',
              border: selectedRating === rating ? '2px solid var(--accent)' : '1px solid var(--border)',
              background: selectedRating === rating ? 'var(--accent)' : 'var(--bg-primary)',
              color: selectedRating === rating ? 'white' : 'var(--text-primary)',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 500,
            }}
          >
            {rating}
          </button>
        ))}
      </div>
    </div>
  );
}

export function OnboardingScreen() {
  const { user, setUser } = useAuth();
  const { setSelectedGenres, setSelectedMoods } = useRecommendationStore();
  const { resetToDiscover } = useUIStore();

  const [step, setStep] = useState<OnboardingStep>('path');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Letterboxd state
  const [letterboxdUsername, setLetterboxdUsername] = useState('');

  // Swipe onboarding state
  const [onboardingMovies, setOnboardingMovies] = useState<Movie[]>([]);
  const [onboardingIndex, setOnboardingIndex] = useState(0);
  const [onboardingRatings, setOnboardingRatings] = useState<Record<number, number>>({});
  const [currentRating, setCurrentRating] = useState(0);

  // Genre/mood selection state
  const [selectedMoods, setSelectedMoodsLocal] = useState<string[]>([]);

  // Taste profile selection state
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);

  // Curator selection state
  const [selectedCurators, setSelectedCurators] = useState<string[]>([]);

  // Track onboarding type for conditional taste profiles
  const [onboardingType, setOnboardingType] = useState<'letterboxd' | 'swipe' | null>(null);

  // Search step state (for adding more movies after swipe)
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Movie[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [addedMovies, setAddedMovies] = useState<Movie[]>([]);
  const [addedMovieRatings, setAddedMovieRatings] = useState<Record<number, number>>({});

  const selectPath = useCallback((path: 'letterboxd' | 'swipe') => {
    setOnboardingType(path);
    if (path === 'letterboxd') {
      setStep('letterboxd');
    } else {
      startSwipeOnboarding();
    }
  }, []);

  const startSwipeOnboarding = async () => {
    setIsLoading(true);
    setLoadingText('Loading popular movies...');

    try {
      const data = await onboardingApi.getMovies();
      // Limit to SWIPE_MOVIE_COUNT movies
      const limitedMovies = (data.movies || []).slice(0, SWIPE_MOVIE_COUNT);
      setOnboardingMovies(limitedMovies);
      setOnboardingIndex(0);
      setOnboardingRatings({});
      setCurrentRating(0);
      setIsLoading(false);
      setStep('swipe');
    } catch (err) {
      console.error('Error loading onboarding movies:', err);
      setError('Failed to load movies. Please try again.');
      setIsLoading(false);
    }
  };

  const importLetterboxd = async () => {
    if (!letterboxdUsername.trim()) {
      setError('Please enter your Letterboxd username');
      return;
    }

    setIsLoading(true);
    setLoadingText('Importing ratings...');
    setError(null);

    try {
      await onboardingApi.submitLetterboxd(letterboxdUsername.trim());
      // Letterboxd users skip taste profiles (they have taste data) but see curators
      setIsLoading(false);
      setStep('curators');
    } catch (err) {
      console.error('Letterboxd import error:', err);
      setError('Import failed. Check your username.');
      setIsLoading(false);
    }
  };

  const handleOnboardingRating = useCallback((rating: number) => {
    setCurrentRating(rating);
    const movie = onboardingMovies[onboardingIndex];
    if (movie) {
      setOnboardingRatings((prev) => ({ ...prev, [movie.tmdb_id]: rating }));
    }
  }, [onboardingMovies, onboardingIndex]);

  const nextOnboardingMovie = useCallback(() => {
    if (onboardingIndex >= onboardingMovies.length - 1) {
      // After swipe movies, go to search step
      setStep('search');
    } else {
      setOnboardingIndex((i) => i + 1);
      const nextMovie = onboardingMovies[onboardingIndex + 1];
      setCurrentRating(onboardingRatings[nextMovie?.tmdb_id] || 0);
    }
  }, [onboardingIndex, onboardingMovies, onboardingRatings]);

  const prevOnboardingMovie = useCallback(() => {
    if (onboardingIndex > 0) {
      setOnboardingIndex((i) => i - 1);
      const prevMovie = onboardingMovies[onboardingIndex - 1];
      setCurrentRating(onboardingRatings[prevMovie?.tmdb_id] || 0);
    }
  }, [onboardingIndex, onboardingMovies, onboardingRatings]);

  const skipOnboardingMovie = useCallback(() => {
    const movie = onboardingMovies[onboardingIndex];
    if (movie) {
      setOnboardingRatings((prev) => {
        const newRatings = { ...prev };
        delete newRatings[movie.tmdb_id];
        return newRatings;
      });
    }
    nextOnboardingMovie();
  }, [onboardingMovies, onboardingIndex, nextOnboardingMovie]);

  // Search functions for adding more movies
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    try {
      const data = await searchApi.movies(searchQuery.trim());
      // Filter out movies already added
      const addedIds = new Set(addedMovies.map((m) => m.tmdb_id));
      const filteredResults = (data.results || []).filter(
        (m) => !addedIds.has(m.tmdb_id)
      );
      setSearchResults(filteredResults.slice(0, 5)); // Show top 5 results
    } catch (err) {
      console.error('Search error:', err);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }, [searchQuery, addedMovies]);

  const addMovieFromSearch = useCallback((movie: Movie, rating: number) => {
    if (addedMovies.length >= MAX_SEARCH_ADDITIONS) return;

    setAddedMovies((prev) => [...prev, movie]);
    setAddedMovieRatings((prev) => ({ ...prev, [movie.tmdb_id]: rating }));
    // Remove from search results
    setSearchResults((prev) => prev.filter((m) => m.tmdb_id !== movie.tmdb_id));
  }, [addedMovies]);

  const removeAddedMovie = useCallback((tmdb_id: number) => {
    setAddedMovies((prev) => prev.filter((m) => m.tmdb_id !== tmdb_id));
    setAddedMovieRatings((prev) => {
      const newRatings = { ...prev };
      delete newRatings[tmdb_id];
      return newRatings;
    });
  }, []);

  const finishSwipeOnboarding = async () => {
    setIsLoading(true);
    setLoadingText('Saving your ratings...');

    try {
      // Combine swipe ratings and search-added movie ratings
      const swipeRatings = Object.entries(onboardingRatings).map(([tmdb_id, rating]) => ({
        tmdb_id: parseInt(tmdb_id),
        rating,
      }));

      const searchRatings = Object.entries(addedMovieRatings).map(([tmdb_id, rating]) => ({
        tmdb_id: parseInt(tmdb_id),
        rating,
      }));

      const allRatings = [...swipeRatings, ...searchRatings];

      if (allRatings.length > 0) {
        await onboardingApi.submitSwipeRatings(allRatings);
      }

      // "Start Fresh" users see taste profiles
      setIsLoading(false);
      setStep('profiles');
    } catch (err) {
      console.error('Error saving ratings:', err);
      setError('Failed to save ratings. Please try again.');
      setIsLoading(false);
    }
  };

  const skipTasteProfiles = useCallback(() => {
    setStep('curators');
  }, []);

  const toggleProfile = useCallback((profileId: string) => {
    setSelectedProfiles((prev) => {
      if (prev.includes(profileId)) {
        return prev.filter((p) => p !== profileId);
      }
      // Allow up to 2 profiles
      if (prev.length >= 2) {
        return [prev[1], profileId];
      }
      return [...prev, profileId];
    });
  }, []);

  const saveTasteProfiles = useCallback(() => {
    // Extract genres from selected profiles and pre-select them
    if (selectedProfiles.length > 0) {
      const profileGenres = selectedProfiles.flatMap((profileId) => {
        const profile = tasteProfiles.find((p) => p.id === profileId);
        return profile?.genres ?? [];
      });
      const uniqueGenres = [...new Set(profileGenres)];

      // Map genres to mood preset IDs
      const moodIds = moodPresets
        .filter((preset) => preset.genres.some((g) => uniqueGenres.includes(g)))
        .map((preset) => preset.id);

      setSelectedMoodsLocal(moodIds);
    }
    setStep('curators');
  }, [selectedProfiles]);

  const toggleCurator = useCallback((curatorId: string) => {
    setSelectedCurators((prev) => {
      if (prev.includes(curatorId)) {
        return prev.filter((c) => c !== curatorId);
      }
      return [...prev, curatorId];
    });
  }, []);

  const skipCurators = useCallback(() => {
    setStep('genres');
  }, []);

  const saveCurators = useCallback(() => {
    // Save selected curators as friends (fire and forget - don't block UI)
    if (selectedCurators.length > 0) {
      Promise.all(
        selectedCurators.map((curatorId) => {
          const curator = curatorProfiles.find((c) => c.id === curatorId);
          if (curator) {
            return profileApi.addFriend(curator.name).catch(() => {
              // Ignore individual errors
            });
          }
          return Promise.resolve();
        })
      ).catch((err) => {
        console.error('Error adding curators as friends:', err);
      });
    }
    // Always advance to next step immediately
    setStep('genres');
  }, [selectedCurators]);

  const toggleMood = useCallback((moodId: string) => {
    setSelectedMoodsLocal((prev) => {
      if (prev.includes(moodId)) {
        return prev.filter((m) => m !== moodId);
      }
      return [...prev, moodId];
    });
  }, []);

  const completeOnboarding = async (type: 'letterboxd' | 'swipe') => {
    setIsLoading(true);
    setLoadingText('Setting up your account...');

    try {
      // Trigger recommendation generation on backend
      await onboardingApi.complete();

      // Mark onboarding as complete and go to Discover
      // The Discover screen will auto-generate if no recommendations
      setIsLoading(false);
      if (user) {
        setUser({ ...user, onboarding_completed: true, onboarding_type: type });
      }
      resetToDiscover();
    } catch (err) {
      console.error('Error completing onboarding:', err);
      setError('Failed to complete setup. Please try again.');
      setIsLoading(false);
    }
  };

  const startDiscovering = useCallback(() => {
    // Convert selected genre IDs to genre names
    const genres = selectedMoods.flatMap((moodId) => {
      const preset = moodPresets.find((p) => p.id === moodId);
      return preset?.genres ?? [];
    });
    setSelectedGenres([...new Set(genres)]);
    setSelectedMoods(selectedMoods);

    completeOnboarding(onboardingType || 'swipe');
  }, [selectedMoods, setSelectedGenres, setSelectedMoods, onboardingType]);

  const skipGenreSelection = useCallback(() => {
    setSelectedGenres([]);
    setSelectedMoods([]);
    completeOnboarding(onboardingType || 'swipe');
  }, [setSelectedGenres, setSelectedMoods, onboardingType]);

  // Loading screen
  if (isLoading) {
    return (
      <div className="container">
        <div className="loading">
          <Spinner />
          <p className="loading-text">{loadingText}</p>
        </div>
      </div>
    );
  }

  // Path selection
  if (step === 'path') {
    return (
      <div className="container">
        <div className="selection-card">
          <h2 className="selection-title">Let's personalize your experience</h2>
          <p className="selection-subtitle">How would you like to get started?</p>

          <div className="onboarding-option" onClick={() => selectPath('letterboxd')}>
            <div className="onboarding-icon">🎬</div>
            <div className="onboarding-option-content">
              <div className="onboarding-option-title">I have Letterboxd</div>
              <div className="onboarding-option-desc">
                Import your ratings automatically for instant personalized recommendations
              </div>
            </div>
          </div>

          <div className="onboarding-option" onClick={() => selectPath('swipe')}>
            <div className="onboarding-icon">✨</div>
            <div className="onboarding-option-content">
              <div className="onboarding-option-title">Start Fresh</div>
              <div className="onboarding-option-desc">
                Rate popular movies and add your favorites to help us learn your taste
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Letterboxd import
  if (step === 'letterboxd') {
    return (
      <div className="container">
        <div className="selection-card">
          <h2 className="selection-title">Import from Letterboxd</h2>
          <p className="selection-subtitle">Enter your Letterboxd username to import your ratings</p>

          <div className="form-group">
            <label className="form-label">Letterboxd Username</label>
            <input
              type="text"
              className="form-input"
              placeholder="your-username"
              value={letterboxdUsername}
              onChange={(e) => setLetterboxdUsername(e.target.value)}
            />
          </div>

          {error ? <p className="form-error visible">{error}</p> : null}

          <div className="selection-actions">
            <Button variant="primary" onClick={importLetterboxd}>
              Import Ratings
            </Button>
            <Button variant="link" onClick={() => setStep('path')}>
              Go back
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Swipe onboarding
  if (step === 'swipe') {
    const currentMovie = onboardingMovies[onboardingIndex];

    return (
      <div className="container">
        <header className="header">
          <div className="header-top">
            <div className="logo">feedmovie</div>
          </div>
        </header>

        <div className="onboarding-progress">
          {onboardingMovies.map((_, i) => (
            <div
              key={i}
              className={`progress-dot ${i < onboardingIndex ? 'completed' : ''} ${
                i === onboardingIndex ? 'active' : ''
              }`}
            />
          ))}
        </div>

        {currentMovie ? (
          <div className="onboarding-card">
            <img
              src={currentMovie.poster_path || 'https://via.placeholder.com/160x240?text=No+Poster'}
              alt={currentMovie.title}
              className="onboarding-movie-poster"
            />
            <h3 className="onboarding-movie-title">{currentMovie.title}</h3>
            <p className="onboarding-movie-year">{currentMovie.year || ''}</p>

            <StarRating rating={currentRating} onChange={handleOnboardingRating} size="lg" />

            <div className="onboarding-rating-display">
              {currentRating > 0 ? `${currentRating} / 5` : 'Tap stars to rate (supports half stars)'}
            </div>

            <div className="onboarding-nav">
              <button
                className="onboarding-nav-btn"
                onClick={prevOnboardingMovie}
                disabled={onboardingIndex === 0}
              >
                ← Back
              </button>
              <button className="onboarding-skip-btn" onClick={skipOnboardingMovie}>
                Haven't seen it
              </button>
              <button className="onboarding-nav-btn primary" onClick={nextOnboardingMovie}>
                Next →
              </button>
            </div>
          </div>
        ) : null}

        <p className="onboarding-counter">
          Movie {onboardingIndex + 1} of {onboardingMovies.length}
        </p>
      </div>
    );
  }

  // Search step - add more movies by searching
  if (step === 'search') {
    const canAddMore = addedMovies.length < MAX_SEARCH_ADDITIONS;
    const ratedCount = Object.keys(onboardingRatings).length + addedMovies.length;

    return (
      <div className="container">
        <div className="selection-card" style={{ maxWidth: '500px' }}>
          <h2 className="selection-title">Add your favorites</h2>
          <p className="selection-subtitle">
            Search for movies you love ({addedMovies.length}/{MAX_SEARCH_ADDITIONS} added)
          </p>

          {/* Search input */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search for a movie..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              style={{ flex: 1 }}
            />
            <Button variant="secondary" onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? '...' : 'Search'}
            </Button>
          </div>

          {/* Search results */}
          {searchResults.length > 0 && canAddMore && (
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                Tap a rating to add the movie
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {searchResults.map((movie) => (
                  <SearchResultItem
                    key={movie.tmdb_id}
                    movie={movie}
                    onAdd={(rating) => addMovieFromSearch(movie, rating)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Added movies */}
          {addedMovies.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                Your added movies
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {addedMovies.map((movie) => (
                  <div
                    key={movie.tmdb_id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      background: 'var(--bg-secondary)',
                      borderRadius: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 500 }}>{movie.title}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                        ({movie.year})
                      </span>
                      <span style={{ color: 'var(--accent)', fontSize: '13px' }}>
                        ★ {addedMovieRatings[movie.tmdb_id]}
                      </span>
                    </div>
                    <button
                      onClick={() => removeAddedMovie(movie.tmdb_id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '4px',
                      }}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="selection-actions">
            <Button variant="primary" onClick={finishSwipeOnboarding}>
              Continue ({ratedCount} movies rated)
            </Button>
            <Button variant="link" onClick={finishSwipeOnboarding}>
              Skip adding more
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Taste profiles (only for "Start Fresh" users)
  if (step === 'profiles') {
    return (
      <div className="container">
        <div className="selection-card">
          <h2 className="selection-title">What kind of viewer are you?</h2>
          <p className="selection-subtitle">Pick 1-2 profiles that match your taste</p>

          <div className="taste-profile-grid">
            {tasteProfiles.map((profile) => {
              const isSelected = selectedProfiles.includes(profile.id);
              return (
                <button
                  key={profile.id}
                  onClick={() => toggleProfile(profile.id)}
                  className={`taste-profile-card ${isSelected ? 'selected' : ''}`}
                >
                  <div className="taste-profile-icon">{profile.icon}</div>
                  <div className="taste-profile-name">{profile.name}</div>
                  <div className="taste-profile-desc">{profile.desc}</div>
                  <div className="taste-profile-examples">
                    {profile.examples.slice(0, 2).join(' • ')}
                  </div>
                  {isSelected ? <div className="taste-profile-check">✓</div> : null}
                </button>
              );
            })}
          </div>

          <div className="selection-actions">
            <Button
              variant="primary"
              onClick={saveTasteProfiles}
              disabled={selectedProfiles.length === 0}
            >
              Continue {selectedProfiles.length > 0 ? `(${selectedProfiles.length} selected)` : ''}
            </Button>
            <Button variant="link" onClick={skipTasteProfiles}>
              Skip for now
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Curators/tastemakers to follow
  if (step === 'curators') {
    return (
      <div className="container">
        <div className="selection-card">
          <h2 className="selection-title">Follow some tastemakers</h2>
          <p className="selection-subtitle">
            Their activity will appear in your feed
          </p>

          <div className="curator-grid">
            {curatorProfiles.map((curator) => {
              const isSelected = selectedCurators.includes(curator.id);
              return (
                <button
                  key={curator.id}
                  onClick={() => toggleCurator(curator.id)}
                  className={`curator-card ${isSelected ? 'selected' : ''}`}
                >
                  <div className="curator-avatar">{curator.avatar}</div>
                  <div className="curator-info">
                    <div className="curator-name">{curator.name}</div>
                    <div className="curator-bio">{curator.bio}</div>
                    <div className="curator-picks">
                      Recent: {curator.recentPicks.slice(0, 2).join(', ')}
                    </div>
                  </div>
                  {isSelected ? <div className="curator-check">✓</div> : null}
                </button>
              );
            })}
          </div>

          <div className="selection-actions">
            <Button
              variant="primary"
              onClick={saveCurators}
            >
              {selectedCurators.length > 0
                ? `Follow ${selectedCurators.length} curator${selectedCurators.length > 1 ? 's' : ''}`
                : 'Continue'}
            </Button>
            <Button variant="link" onClick={skipCurators}>
              Skip for now
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Genre selection
  if (step === 'genres') {
    return (
      <div className="container">
        <div className="selection-card">
          <h2 className="selection-title">What do you want to watch?</h2>
          <p className="selection-subtitle">Select genres to get started</p>

          {/* Genre Presets */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '10px',
              marginBottom: '20px',
            }}
          >
            {moodPresets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => toggleMood(preset.id)}
                className={`genre-option ${selectedMoods.includes(preset.id) ? 'selected' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '14px 12px',
                }}
              >
                <span style={{ fontSize: '18px' }}>{preset.icon}</span>
                <span style={{ fontSize: '14px', fontWeight: 500 }}>{preset.label}</span>
              </button>
            ))}
          </div>

          <div className="selection-actions">
            <Button
              variant="primary"
              onClick={startDiscovering}
            >
              Start Discovering
            </Button>
            <Button variant="link" onClick={skipGenreSelection}>
              Just pick for me
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
