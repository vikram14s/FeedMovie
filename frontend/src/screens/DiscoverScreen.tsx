import { useEffect, useCallback, useState } from 'react';
import { X, Eye, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRecommendations } from '../hooks/useRecommendations';
import { useUIStore } from '../stores/uiStore';
import { MovieCard } from '../components/cards/MovieCard';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';

export function DiscoverScreen() {
  const {
    currentMovie,
    remainingCount,
    hasMore,
    isEmpty,
    isLoading,
    stats,
    swipeLeft,
    swipeRight,
    loadRecommendations,
    generateMore,
  } = useRecommendations();

  const { openRatingModal } = useUIStore();
  const [isGenerating, setIsGenerating] = useState(false);

  // Always load recommendations on mount
  useEffect(() => {
    loadRecommendations();
  }, []); // Only on mount

  // Auto-generate for new users with no recommendations
  const handleGenerateRecommendations = useCallback(async () => {
    setIsGenerating(true);
    try {
      await generateMore();
    } finally {
      setIsGenerating(false);
    }
  }, [generateMore]);

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle if in input/textarea
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }

      // Check if any modal is open
      const modalOpen = document.querySelector('.modal-overlay');
      if (modalOpen) return;

      if (e.key === 'ArrowLeft') {
        swipeLeft();
      } else if (e.key === 'ArrowRight') {
        swipeRight();
      } else if (e.key === 's' || e.key === 'S') {
        if (currentMovie) {
          openRatingModal(currentMovie);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [swipeLeft, swipeRight, currentMovie, openRatingModal]);

  const handleSwipeLeft = useCallback(() => {
    swipeLeft();
  }, [swipeLeft]);

  const handleSwipeRight = useCallback(() => {
    swipeRight();
  }, [swipeRight]);

  const handleAlreadySeen = useCallback(() => {
    if (currentMovie) {
      openRatingModal(currentMovie);
    }
  }, [currentMovie, openRatingModal]);

  // Loading state
  if (isLoading) {
    return (
      <div className="loading">
        <Spinner />
        <p className="loading-text">Finding perfect movies for you...</p>
      </div>
    );
  }

  // Empty state - no recommendations yet
  if (isEmpty && !hasMore) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🎬</div>
        <h2 className="empty-title">Ready to discover movies?</h2>
        <p className="empty-text">
          {isGenerating
            ? 'Our AI is finding perfect movies for you...'
            : 'Click below to generate personalized recommendations based on your taste'}
        </p>
        <Button
          variant="primary"
          onClick={handleGenerateRecommendations}
          disabled={isGenerating}
          style={{ marginTop: '16px' }}
        >
          {isGenerating ? 'Generating...' : 'Generate Recommendations'}
        </Button>
      </div>
    );
  }

  // All caught up state
  if (!hasMore && !isLoading) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🎉</div>
        <h2 className="empty-title">All caught up!</h2>
        <p className="empty-text">You've reviewed all recommendations</p>
        <Button variant="primary" onClick={generateMore}>
          Load More Movies
        </Button>
      </div>
    );
  }

  return (
    <>
      {/* Stats Bar */}
      <div className="stats-bar">
        <div className="stat-item">
          <div className="stat-value">{remainingCount}</div>
          <div className="stat-label">Remaining</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{stats.liked}</div>
          <div className="stat-label">Liked</div>
        </div>
        <div className="stat-item">
          <div className="stat-value" style={{ color: 'var(--text-muted)' }}>
            {stats.skipped}
          </div>
          <div className="stat-label">Skipped</div>
        </div>
      </div>

      {/* Movie Card Stack */}
      <div className="card-stack">
        <AnimatePresence mode="wait">
          {currentMovie ? (
            <motion.div
              key={currentMovie.tmdb_id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <MovieCard
                movie={currentMovie}
                onSwipeLeft={handleSwipeLeft}
                onSwipeRight={handleSwipeRight}
              />
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button
          onClick={handleSwipeLeft}
          className="action-btn btn-skip"
          title="Skip (←)"
          aria-label="Skip"
        >
          <X size={28} />
        </button>

        <button
          onClick={handleAlreadySeen}
          className="action-btn btn-seen"
          title="Already Seen (S)"
          aria-label="Already Seen"
        >
          <Eye size={28} />
        </button>

        <button
          onClick={handleSwipeRight}
          className="action-btn btn-like"
          title="Add to Watchlist (→)"
          aria-label="Add to Watchlist"
        >
          <Check size={28} strokeWidth={2.5} />
        </button>
      </div>

      {/* Keyboard Hints */}
      <div className="keyboard-hints">← Skip • S Already Seen • → Add to Watchlist</div>
    </>
  );
}
