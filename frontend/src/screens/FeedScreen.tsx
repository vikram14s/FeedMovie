import { useCallback } from 'react';
import { useFeed } from '../hooks/useFeed';
import { FeedItem } from '../components/cards/FeedItem';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import { useUIStore } from '../stores/uiStore';

export function FeedScreen() {
  const { activities, isLoading, loadFeed, toggleLike, addToWatchlist } = useFeed();
  const { setTab } = useUIStore();

  const handleAddToWatchlist = useCallback(
    async (tmdbId: number, title: string) => {
      const success = await addToWatchlist(tmdbId);
      if (success) {
        alert(`Added "${title}" to your watchlist!`);
      }
    },
    [addToWatchlist]
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
        <Button variant="primary" onClick={() => setTab('profile')}>
          Go to Profile
        </Button>
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
          />
        ))}
      </div>
    </>
  );
}
