import { Heart, Plus } from 'lucide-react';
import type { FeedActivity, Movie } from '../../types';
import { formatTimeAgo } from '../../utils/time';

interface FeedItemProps {
  activity: FeedActivity;
  onLike: (activityId: number) => void;
  onAddToWatchlist: (tmdbId: number, title: string) => void;
  onUserClick?: (userId: number, username: string) => void;
  onMovieClick?: (movie: Movie) => void;
}

export function FeedItem({ activity, onLike, onAddToWatchlist, onUserClick, onMovieClick }: FeedItemProps) {
  const posterUrl = activity.movie?.poster_path || 'https://via.placeholder.com/80x120?text=No+Poster';
  const avatar = activity.user?.username?.charAt(0).toUpperCase() || '?';
  const username = activity.user?.username || 'Unknown';
  const userId = activity.user?.id;
  const timeAgo = formatTimeAgo(activity.created_at);
  const rating = activity.rating || 0;
  const reviewText = activity.review_text || '';
  const movieTitle = activity.movie?.title || 'Unknown Movie';
  const movieYear = activity.movie?.year || '';
  const genres = (activity.movie?.genres || []).slice(0, 2).join(', ');

  const handleUserClick = () => {
    if (onUserClick && userId) {
      onUserClick(userId, username);
    }
  };

  const handleMovieClick = () => {
    if (onMovieClick && activity.movie) {
      onMovieClick(activity.movie as Movie);
    }
  };

  return (
    <div className="feed-item" data-activity-id={activity.id}>
      <div className="feed-header">
        <div
          className="feed-avatar"
          onClick={handleUserClick}
          style={{ cursor: onUserClick ? 'pointer' : 'default' }}
        >
          {avatar}
        </div>
        <div className="feed-user-info">
          <div
            className={`feed-username ${onUserClick ? 'clickable' : ''}`}
            onClick={handleUserClick}
          >
            {username}
          </div>
          <div className="feed-action-text">rated a movie</div>
        </div>
        <div className="feed-time">{timeAgo}</div>
      </div>

      <div className="feed-movie">
        <img
          src={posterUrl}
          alt={movieTitle}
          className={`feed-movie-poster ${onMovieClick ? 'clickable' : ''}`}
          onClick={handleMovieClick}
        />
        <div className="feed-movie-info">
          <div
            className="feed-movie-title"
            onClick={handleMovieClick}
            style={{ cursor: onMovieClick ? 'pointer' : 'default' }}
          >
            {movieTitle}
          </div>
          <div className="feed-movie-meta">
            {movieYear}
            {genres ? ` • ${genres}` : ''}
          </div>
          <div className="feed-rating">
            {[1, 2, 3, 4, 5].map((star) => (
              <span key={star} className={`star ${star <= rating ? '' : 'empty'}`}>
                ★
              </span>
            ))}
          </div>
          {reviewText ? <div className="feed-review-text">"{reviewText}"</div> : null}
        </div>
      </div>

      <div className="feed-actions">
        <button
          className={`feed-action-btn ${activity.is_liked ? 'liked' : ''}`}
          onClick={() => onLike(activity.id)}
        >
          <Heart size={18} fill={activity.is_liked ? 'currentColor' : 'none'} />
          {activity.like_count > 0 ? activity.like_count : ''}
        </button>
        <button
          className="feed-action-btn"
          onClick={() => onAddToWatchlist(activity.movie.tmdb_id, movieTitle)}
        >
          <Plus size={18} />
          Watchlist
        </button>
      </div>
    </div>
  );
}
