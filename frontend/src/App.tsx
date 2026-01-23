import { useEffect, useState, useCallback, lazy, Suspense } from 'react';
import { useAuth } from './hooks/useAuth';
import { useUIStore } from './stores/uiStore';
import { useWatchlist } from './hooks/useWatchlist';
import { useRecommendations } from './hooks/useRecommendations';
import { useProfile } from './hooks/useProfile';
import { ratingsApi } from './api/client';

// Layout
import { AppShell } from './components/layout/AppShell';

// Screens
import { AuthScreen } from './screens/AuthScreen';
import { OnboardingScreen } from './screens/OnboardingScreen';
import { DiscoverScreen } from './screens/DiscoverScreen';
import { FeedScreen } from './screens/FeedScreen';
import { WatchlistScreen } from './screens/WatchlistScreen';
import { ProfileScreen } from './screens/ProfileScreen';

// Modals - dynamically imported (Vercel best practice: bundle-dynamic-imports)
const SearchModal = lazy(() =>
  import('./components/modals/SearchModal').then((m) => ({ default: m.SearchModal }))
);
const FiltersModal = lazy(() =>
  import('./components/modals/FiltersModal').then((m) => ({ default: m.FiltersModal }))
);
const RatingModal = lazy(() =>
  import('./components/modals/RatingModal').then((m) => ({ default: m.RatingModal }))
);
const EditBioModal = lazy(() =>
  import('./components/modals/EditBioModal').then((m) => ({ default: m.EditBioModal }))
);

import { Spinner } from './components/ui/Spinner';

function App() {
  const { user, isLoading: authLoading, isAuthenticated, checkAuth } = useAuth();
  const {
    activeTab,
    searchModalOpen,
    filtersModalOpen,
    ratingModal,
    markSeenModal,
    editBioModalOpen,
    closeSearchModal,
    closeFiltersModal,
    closeRatingModal,
    closeMarkSeenModal,
    closeEditBioModal,
    openRatingModal,
  } = useUIStore();

  const { watchlistCount, loadWatchlist, markAsSeen } = useWatchlist();
  const {
    selectedGenres,
    selectedMoods,
    setSelectedGenres,
    setSelectedMoods,
    loadRecommendations,
    swipeLeft,
  } = useRecommendations();
  const { profile, updateBio } = useProfile();

  const [initialCheckDone, setInitialCheckDone] = useState(false);

  // Initial auth check
  useEffect(() => {
    const doCheck = async () => {
      await checkAuth();
      setInitialCheckDone(true);
    };
    doCheck();
  }, [checkAuth]);

  // Handle movie selection from search
  const handleSearchSelectMovie = useCallback(
    (movie: import('./types').Movie) => {
      closeSearchModal();
      openRatingModal(movie as import('./types').Recommendation);
    },
    [closeSearchModal, openRatingModal]
  );

  // Handle rating submission from discover screen (already seen)
  const handleRatingSubmit = useCallback(
    async (rating: number, reviewText?: string) => {
      const movie = ratingModal.movie;
      if (!movie) return;

      await ratingsApi.add(
        movie.tmdb_id,
        movie.title,
        movie.year,
        rating,
        reviewText
      );

      closeRatingModal();
      swipeLeft(); // Move to next movie after rating
    },
    [ratingModal.movie, closeRatingModal, swipeLeft]
  );

  // Handle mark seen from watchlist
  const handleMarkSeenSubmit = useCallback(
    async (rating: number, reviewText?: string) => {
      const movie = markSeenModal.movie;
      if (!movie) return;

      await markAsSeen(movie.tmdb_id, rating, reviewText);
      closeMarkSeenModal();
      loadWatchlist();
    },
    [markSeenModal.movie, markAsSeen, closeMarkSeenModal, loadWatchlist]
  );

  // Handle filter apply
  const handleFiltersApply = useCallback(
    (genres: string[], moods: string[]) => {
      if (moods.includes('custom')) {
        setSelectedGenres(genres);
        setSelectedMoods(['custom']);
      } else {
        setSelectedMoods(moods);
      }
      loadRecommendations(genres);
    },
    [setSelectedGenres, setSelectedMoods, loadRecommendations]
  );

  // Handle bio update
  const handleBioUpdate = useCallback(
    async (bio: string) => {
      return updateBio(bio);
    },
    [updateBio]
  );

  // Show loading spinner during initial auth check
  if (!initialCheckDone || authLoading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <Spinner size="lg" />
      </div>
    );
  }

  // Not authenticated - show auth screen
  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  // Authenticated but onboarding not complete
  if (!user?.onboarding_completed) {
    return <OnboardingScreen />;
  }

  // Main app
  return (
    <>
      <AppShell watchlistCount={watchlistCount}>
        {activeTab === 'discover' ? <DiscoverScreen /> : null}
        {activeTab === 'feed' ? <FeedScreen /> : null}
        {activeTab === 'watchlist' ? <WatchlistScreen /> : null}
        {activeTab === 'profile' ? <ProfileScreen /> : null}
      </AppShell>

      {/* Modals */}
      <Suspense fallback={null}>
        {searchModalOpen ? (
          <SearchModal
            isOpen={searchModalOpen}
            onClose={closeSearchModal}
            onSelectMovie={handleSearchSelectMovie}
          />
        ) : null}

        {filtersModalOpen ? (
          <FiltersModal
            isOpen={filtersModalOpen}
            selectedGenres={selectedGenres}
            selectedMoods={selectedMoods}
            onClose={closeFiltersModal}
            onApply={handleFiltersApply}
          />
        ) : null}

        {ratingModal.open ? (
          <RatingModal
            isOpen={ratingModal.open}
            movie={ratingModal.movie}
            title="Rate this movie"
            onClose={closeRatingModal}
            onSubmit={handleRatingSubmit}
          />
        ) : null}

        {markSeenModal.open ? (
          <RatingModal
            isOpen={markSeenModal.open}
            movie={markSeenModal.movie}
            title="Mark as watched"
            onClose={closeMarkSeenModal}
            onSubmit={handleMarkSeenSubmit}
          />
        ) : null}

        {editBioModalOpen ? (
          <EditBioModal
            isOpen={editBioModalOpen}
            currentBio={profile?.bio || ''}
            onClose={closeEditBioModal}
            onSave={handleBioUpdate}
          />
        ) : null}
      </Suspense>
    </>
  );
}

export default App;
