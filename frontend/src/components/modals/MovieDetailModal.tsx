import { useState, useEffect, useCallback } from 'react';
import { X, Star, Check, Bookmark, Users } from 'lucide-react';
import { Button } from '../ui/Button';
import { StarRating } from '../ui/StarRating';
import type { Movie, Recommendation, Review, FriendWatched } from '../../types';
import { apiFetch, moviesApi } from '../../api/client';
import { Spinner } from '../ui/Spinner';

interface MovieDetailModalProps {
  isOpen: boolean;
  movie: Movie | Recommendation | null;
  onClose: () => void;
  onAddToWatchlist?: (movie: Movie) => void;
  onUserClick?: (userId: number, username: string) => void;
}

export function MovieDetailModal({
  isOpen,
  movie,
  onClose,
  onAddToWatchlist,
  onUserClick,
}: MovieDetailModalProps) {
  const [fullMovie, setFullMovie] = useState<Movie | Recommendation | null>(null);
  const [isLoadingMovie, setIsLoadingMovie] = useState(false);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [friendsWatched, setFriendsWatched] = useState<FriendWatched[]>([]);
  const [isLoadingReviews, setIsLoadingReviews] = useState(false);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [userRating, setUserRating] = useState(0);
  const [reviewText, setReviewText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [addedToWatchlist, setAddedToWatchlist] = useState(false);

  // Load full movie details, reviews and friends when modal opens
  useEffect(() => {
    if (isOpen && movie) {
      // If the movie doesn't have overview, fetch full details
      if (!movie.overview) {
        loadFullMovieDetails();
      } else {
        setFullMovie(movie);
      }
      loadReviews();
      loadFriendsWatched();
    }
  }, [isOpen, movie]);

  const loadFullMovieDetails = async () => {
    if (!movie) return;
    setIsLoadingMovie(true);
    try {
      const data = await apiFetch<{ success: boolean; movie: Movie }>(
        `/movies/${movie.tmdb_id}`
      );
      if (data.movie) {
        setFullMovie({ ...movie, ...data.movie });
      } else {
        setFullMovie(movie);
      }
    } catch (err) {
      console.error('Error loading movie details:', err);
      setFullMovie(movie);
    } finally {
      setIsLoadingMovie(false);
    }
  };

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setFullMovie(null);
      setReviews([]);
      setFriendsWatched([]);
      setShowReviewForm(false);
      setUserRating(0);
      setReviewText('');
      setAddedToWatchlist(false);
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

  const loadReviews = async () => {
    if (!movie) return;
    setIsLoadingReviews(true);
    try {
      const data = await moviesApi.getReviews(movie.tmdb_id);
      setReviews(data.reviews || []);
    } catch (err) {
      console.error('Error loading reviews:', err);
    } finally {
      setIsLoadingReviews(false);
    }
  };

  const loadFriendsWatched = async () => {
    if (!movie) return;
    try {
      const data = await moviesApi.getFriendsWhoWatched(movie.tmdb_id);
      setFriendsWatched(data.friends || []);
    } catch (err) {
      console.error('Error loading friends who watched:', err);
    }
  };

  const handleSubmitReview = useCallback(async () => {
    if (!movie || userRating === 0) return;

    setIsSubmitting(true);
    try {
      await apiFetch('/reviews', {
        method: 'POST',
        body: JSON.stringify({
          tmdb_id: movie.tmdb_id,
          rating: userRating,
          review_text: reviewText.trim() || null,
        }),
      });

      // Reload reviews
      await loadReviews();

      // Reset form
      setShowReviewForm(false);
      setUserRating(0);
      setReviewText('');
    } catch (err) {
      console.error('Error submitting review:', err);
    } finally {
      setIsSubmitting(false);
    }
  }, [movie, userRating, reviewText]);

  const handleAddToWatchlist = useCallback(() => {
    if (movie && onAddToWatchlist) {
      onAddToWatchlist(movie);
      setAddedToWatchlist(true);
    }
  }, [movie, onAddToWatchlist]);

  if (!isOpen || !movie) return null;

  // Use fullMovie for details if available, otherwise fall back to movie
  const displayMovie = fullMovie || movie;

  const genres = typeof displayMovie.genres === 'string'
    ? JSON.parse(displayMovie.genres)
    : displayMovie.genres || [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal movie-detail-modal"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '600px', maxHeight: '90vh', overflow: 'auto' }}
      >
        {/* Header */}
        <div className="movie-detail-header">
          <button onClick={onClose} className="modal-close-btn" aria-label="Close">
            <X size={24} />
          </button>
        </div>

        {/* Movie Info */}
        <div className="movie-detail-content">
          <div className="movie-detail-poster-row">
            {displayMovie.poster_path ? (
              <img
                src={displayMovie.poster_path}
                alt={displayMovie.title}
                className="movie-detail-poster"
              />
            ) : (
              <div className="movie-detail-poster-placeholder">No Poster</div>
            )}
            <div className="movie-detail-info">
              <h2 className="movie-detail-title">{displayMovie.title}</h2>
              <p className="movie-detail-year">{displayMovie.year}</p>

              {genres.length > 0 && (
                <div className="movie-detail-genres">
                  {genres.slice(0, 3).map((genre: string) => (
                    <span key={genre} className="genre-tag">{genre}</span>
                  ))}
                </div>
              )}

              {'tmdb_rating' in displayMovie && displayMovie.tmdb_rating ? (
                <div className="movie-detail-rating">
                  <Star size={16} fill="var(--gold)" stroke="var(--gold)" />
                  <span>{displayMovie.tmdb_rating.toFixed(1)}</span>
                </div>
              ) : null}
            </div>
          </div>

          {/* Friends Who Watched - Social Context */}
          {friendsWatched.length > 0 ? (
            <div className="friends-watched-section">
              <div className="friends-watched-header">
                <Users size={16} />
                <span>Friends who watched</span>
              </div>
              <div className="friends-watched-list">
                {friendsWatched.slice(0, 5).map((friend) => (
                  <div
                    key={friend.id}
                    className="friend-watched-item"
                    onClick={() => onUserClick?.(friend.id, friend.username)}
                    style={{ cursor: onUserClick ? 'pointer' : 'default' }}
                  >
                    <div className="friend-watched-avatar">
                      {friend.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="friend-watched-info">
                      <span className="friend-watched-name">{friend.username}</span>
                      <span className="friend-watched-rating">
                        {'★'.repeat(Math.floor(friend.rating))}
                        {'☆'.repeat(5 - Math.floor(friend.rating))}
                      </span>
                    </div>
                  </div>
                ))}
                {friendsWatched.length > 5 ? (
                  <div className="friends-watched-more">
                    +{friendsWatched.length - 5} more
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}

          {/* Overview */}
          {isLoadingMovie ? (
            <div className="movie-detail-overview" style={{ textAlign: 'center', padding: '20px' }}>
              <Spinner size="sm" />
            </div>
          ) : displayMovie.overview ? (
            <div className="movie-detail-overview">
              <p>{displayMovie.overview}</p>
            </div>
          ) : null}

          {/* AI Reasoning (if available) */}
          {'reasoning' in displayMovie && displayMovie.reasoning ? (
            <div className="movie-detail-reasoning">
              <p className="reasoning-label">Why you might like it:</p>
              <p className="reasoning-text">"{String(displayMovie.reasoning)}"</p>
            </div>
          ) : null}

          {/* Action Buttons */}
          <div className="movie-detail-actions">
            <Button
              variant={addedToWatchlist ? 'secondary' : 'primary'}
              onClick={handleAddToWatchlist}
              disabled={addedToWatchlist}
            >
              {addedToWatchlist ? (
                <>
                  <Check size={18} /> Added
                </>
              ) : (
                <>
                  <Bookmark size={18} /> Add to Watchlist
                </>
              )}
            </Button>
            <Button variant="secondary" onClick={() => setShowReviewForm(!showReviewForm)}>
              <Star size={18} /> Write Review
            </Button>
          </div>

          {/* Review Form */}
          {showReviewForm ? (
            <div className="review-form">
              <h3>Your Review</h3>
              <div className="review-rating">
                <span>Rating:</span>
                <StarRating rating={userRating} onChange={setUserRating} size="md" />
              </div>
              <textarea
                className="review-textarea"
                placeholder="What did you think? (optional)"
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                rows={3}
              />
              <div className="review-form-actions">
                <Button
                  variant="primary"
                  onClick={handleSubmitReview}
                  disabled={userRating === 0 || isSubmitting}
                >
                  {isSubmitting ? 'Posting...' : 'Post Review'}
                </Button>
                <Button variant="link" onClick={() => setShowReviewForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : null}

          {/* Reviews Section */}
          <div className="movie-detail-reviews">
            <h3>Reviews {reviews.length > 0 ? `(${reviews.length})` : ''}</h3>
            {isLoadingReviews ? (
              <p className="reviews-loading">Loading reviews...</p>
            ) : reviews.length > 0 ? (
              <div className="reviews-list">
                {reviews.map((review) => (
                  <div
                    key={review.id}
                    className="review-item"
                    onClick={() => onUserClick?.(review.user.id, review.user.username)}
                    style={{ cursor: onUserClick ? 'pointer' : 'default' }}
                  >
                    <div className="review-header">
                      <span className="review-username">{review.user.username}</span>
                      <span className="review-rating">
                        {'★'.repeat(Math.floor(review.rating))}
                        {'☆'.repeat(5 - Math.floor(review.rating))}
                      </span>
                    </div>
                    {review.review_text ? (
                      <p className="review-text">{review.review_text}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-reviews">No reviews yet. Be the first!</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
