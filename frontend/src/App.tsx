import { useEffect, useState, useCallback, lazy, Suspense } from 'react';
import { useAuth } from './hooks/useAuth';
import { useUIStore } from './stores/uiStore';
import { useWatchlist } from './hooks/useWatchlist';
import { useRecommendations } from './hooks/useRecommendations';
import { useProfile } from './hooks/useProfile';
import { useFeed } from './hooks/useFeed';
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
const MovieDetailModal = lazy(() =>
  import('./components/modals/MovieDetailModal').then((m) => ({ default: m.MovieDetailModal }))
);
const UserProfileModal = lazy(() =>
  import('./components/modals/UserProfileModal').then((m) => ({ default: m.UserProfileModal }))
);
const AddFriendsModal = lazy(() =>
  import('./components/modals/AddFriendsModal').then((m) => ({ default: m.AddFriendsModal }))
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
    addFriendsModalOpen,
    movieDetailModal,
    userProfileModal,
    closeSearchModal,
    closeFiltersModal,
    closeRatingModal,
    closeMarkSeenModal,
    closeEditBioModal,
    closeAddFriendsModal,
    closeMovieDetailModal,
    closeUserProfileModal,
    openRatingModal,
    openUserProfileModal,
  } = useUIStore();

  const { watchlistCount, loadWatchlist, markAsSeen, addToWatchlist } = useWatchlist();
  const {
    selectedGenres,
    selectedMoods,
    setSelectedGenres,
    setSelectedMoods,
    loadRecommendations,
    swipeLeft,
  } = useRecommendations();
  const { profile, updateBio } = useProfile();
  const { loadFeed } = useFeed();

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

  // Handle user selection from search
  const handleSearchSelectUser = useCallback(
    (userId: number, username: string) => {
      closeSearchModal();
      openUserProfileModal(userId, username);
    },
    [closeSearchModal, openUserProfileModal]
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

  // Handle add to watchlist from movie detail modal
  const handleAddToWatchlistFromDetail = useCallback(
    async (movie: import('./types').Movie) => {
      await addToWatchlist(movie.tmdb_id);
      loadWatchlist();
    },
    [addToWatchlist, loadWatchlist]
  );

  // Handle friend added - reload feed
  const handleFriendAdded = useCallback(() => {
    loadFeed();
  }, [loadFeed]);

  // Handle view movie from user profile modal
  const handleViewMovieFromProfile = useCallback(
    (tmdbId: number) => {
      // Close user profile modal and open movie detail
      // We'd need to fetch the movie details first
      closeUserProfileModal();
      // For now, we'll just log it - the movie detail modal requires a full movie object
      console.log('View movie:', tmdbId);
    },
    [closeUserProfileModal]
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
            onSelectUser={handleSearchSelectUser}
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

        {movieDetailModal.open ? (
          <MovieDetailModal
            isOpen={movieDetailModal.open}
            movie={movieDetailModal.movie}
            onClose={closeMovieDetailModal}
            onAddToWatchlist={handleAddToWatchlistFromDetail}
            onUserClick={(userId, username) => {
              closeMovieDetailModal();
              openUserProfileModal(userId, username);
            }}
          />
        ) : null}

        {userProfileModal.open ? (
          <UserProfileModal
            isOpen={userProfileModal.open}
            userId={userProfileModal.userId}
            username={userProfileModal.username}
            onClose={closeUserProfileModal}
            onViewMovie={handleViewMovieFromProfile}
          />
        ) : null}

        {addFriendsModalOpen ? (
          <AddFriendsModal
            isOpen={addFriendsModalOpen}
            onClose={closeAddFriendsModal}
            onFriendAdded={handleFriendAdded}
          />
        ) : null}
      </Suspense>
    </>
  );
}

export default App;
