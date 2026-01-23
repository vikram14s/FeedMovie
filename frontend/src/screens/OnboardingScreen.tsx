import { useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { onboardingApi } from '../api/client';
import type { Movie } from '../types';
import { Button } from '../components/ui/Button';
import { StarRating } from '../components/ui/StarRating';
import { Spinner } from '../components/ui/Spinner';
import { moodPresets, useRecommendationStore } from '../stores/recommendationStore';

type OnboardingStep = 'path' | 'letterboxd' | 'swipe' | 'profiles' | 'curators' | 'genres';

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

export function OnboardingScreen() {
  const { user, setUser } = useAuth();
  const { setSelectedGenres, setSelectedMoods } = useRecommendationStore();

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
      setOnboardingMovies(data.movies || []);
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
      finishSwipeOnboarding();
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

  const finishSwipeOnboarding = async () => {
    setIsLoading(true);
    setLoadingText('Saving your ratings...');

    try {
      const ratings = Object.entries(onboardingRatings).map(([tmdb_id, rating]) => ({
        tmdb_id: parseInt(tmdb_id),
        rating,
      }));

      if (ratings.length > 0) {
        await onboardingApi.submitSwipeRatings(ratings);
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

  const saveCurators = useCallback(async () => {
    // In a real implementation, this would save the selected curators as friends
    // For now, we'll just proceed to genres
    // TODO: Call API to add curators as friends
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
    setLoadingText('Generating your personalized recommendations...');

    try {
      await onboardingApi.complete();
      if (user) {
        setUser({ ...user, onboarding_completed: true, onboarding_type: type });
      }
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
                Rate 20 popular movies to help us learn your taste
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
              Show me everything
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
