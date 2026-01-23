import { useCallback } from 'react';
import { useWatchlist } from '../hooks/useWatchlist';
import { useUIStore } from '../stores/uiStore';
import { WatchlistItem } from '../components/cards/WatchlistItem';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import type { WatchlistItem as WatchlistItemType } from '../types';

export function WatchlistScreen() {
  const { watchlist, isLoading, removeFromWatchlist } = useWatchlist();
  const { openMarkSeenModal, setTab } = useUIStore();

  const handleMarkSeen = useCallback(
    (movie: WatchlistItemType) => {
      openMarkSeenModal(movie);
    },
    [openMarkSeenModal]
  );

  if (isLoading) {
    return (
      <div className="loading">
        <Spinner />
        <p className="loading-text">Loading watchlist...</p>
      </div>
    );
  }

  if (watchlist.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📋</div>
        <h2 className="empty-title">No movies saved yet</h2>
        <p className="empty-text">Movies you like will appear here</p>
        <Button variant="primary" onClick={() => setTab('discover')}>
          Discover Movies
        </Button>
      </div>
    );
  }

  return (
    <>
      <div className="section-header">
        <span className="section-title">Your Watchlist</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
          {watchlist.length} movies
        </span>
      </div>

      <div className="watchlist">
        {watchlist.map((movie) => (
          <WatchlistItem
            key={movie.tmdb_id}
            movie={movie}
            onRemove={removeFromWatchlist}
            onMarkSeen={handleMarkSeen}
          />
        ))}
      </div>
    </>
  );
}
