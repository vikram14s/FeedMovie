import { useCallback } from 'react';
import { useFeed } from '../hooks/useFeed';
import { FeedItem } from '../components/cards/FeedItem';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import { useUIStore } from '../stores/uiStore';
import type { Movie } from '../types';

export function FeedScreen() {
  const { activities, isLoading, loadFeed, toggleLike, addToWatchlist } = useFeed();
  const { setTab, openUserProfileModal, openMovieDetailModal, openAddFriendsModal } = useUIStore();

  const handleAddToWatchlist = useCallback(
    async (tmdbId: number, title: string) => {
      const success = await addToWatchlist(tmdbId);
      if (success) {
        alert(`Added "${title}" to your watchlist!`);
      }
    },
    [addToWatchlist]
  );

  const handleUserClick = useCallback(
    (userId: number, username: string) => {
      openUserProfileModal(userId, username);
    },
    [openUserProfileModal]
  );

  const handleMovieClick = useCallback(
    (movie: Movie) => {
      openMovieDetailModal(movie);
    },
    [openMovieDetailModal]
  );

  if (isLoading) {
    return (
      <div className="loading">
        <Spinner />
        <p className="loading-text">Loading feed...</p>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">👥</div>
        <h2 className="empty-title">No activity yet</h2>
        <p className="empty-text">Add friends to see their movie activity</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', alignItems: 'center' }}>
          <Button variant="primary" onClick={openAddFriendsModal}>
            Find Friends
          </Button>
          <Button variant="secondary" onClick={() => setTab('profile')}>
            Go to Profile
          </Button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="section-header">
        <span className="section-title">Friend Activity</span>
        <button onClick={loadFeed} className="section-link" style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
          Refresh
        </button>
      </div>

      <div className="feed-view">
        {activities.map((activity) => (
          <FeedItem
            key={activity.id}
            activity={activity}
            onLike={toggleLike}
            onAddToWatchlist={handleAddToWatchlist}
            onUserClick={handleUserClick}
            onMovieClick={handleMovieClick}
          />
        ))}
      </div>
    </>
  );
}
