import { X, Eye } from 'lucide-react';
import type { WatchlistItem as WatchlistItemType } from '../../types';

interface WatchlistItemProps {
  movie: WatchlistItemType;
  onRemove: (tmdbId: number) => void;
  onMarkSeen: (movie: WatchlistItemType) => void;
}

export function WatchlistItem({ movie, onRemove, onMarkSeen }: WatchlistItemProps) {
  const posterUrl = movie.poster_path || 'https://via.placeholder.com/80x120?text=No+Poster';
  const streamingProviders = movie.streaming_providers || {};
  const allProviders = [
    ...(streamingProviders.subscription || []),
    ...(streamingProviders.rent || []),
  ];

  return (
    <div className="watchlist-item">
      <img src={posterUrl} alt={movie.title} className="watchlist-poster" />
      <div className="watchlist-info">
        <h3 className="watchlist-title">{movie.title}</h3>
        <p className="watchlist-meta">
          {movie.year} • {(movie.genres || []).slice(0, 2).join(', ')}
        </p>
        <div className="watchlist-streaming">
          {allProviders.slice(0, 3).map((p) =>
            p.logo ? <img key={p.name} src={p.logo} alt={p.name} title={p.name} /> : null
          )}
        </div>
      </div>
      <div className="watchlist-actions">
        <button
          className="mark-seen-btn"
          onClick={() => onMarkSeen(movie)}
          title="Mark as watched"
        >
          <Eye size={14} />
          Watched
        </button>
        <button
          className="remove-btn"
          onClick={() => onRemove(movie.tmdb_id)}
          title="Remove"
        >
          <X size={20} />
        </button>
      </div>
    </div>
  );
}
