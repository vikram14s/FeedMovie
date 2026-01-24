import { useEffect, useCallback, useState, useRef } from 'react';
import { X, Eye, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRecommendations } from '../hooks/useRecommendations';
import { useUIStore } from '../stores/uiStore';
import { MovieCard } from '../components/cards/MovieCard';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import { recommendationsApi } from '../api/client';

// Helper to check if user is on discover tab
const isOnDiscoverTab = () => {
  const { activeTab } = useUIStore.getState();
  return activeTab === 'discover';
};

// Generation status type
interface GenerationStatus {
  progress: number;
  stage: string;
  estimatedSecondsRemaining: number;
  estimatedTotalSeconds: number;
  isComplete: boolean;
  error?: string;
}

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

  const { openRatingModal, showNotification, setTab } = useUIStore();
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll for generation status
  const pollGenerationStatus = useCallback(async () => {
    try {
      const res = await recommendationsApi.getGenerationStatus();
      if (res.has_job && res.status === 'running') {
        setGenerationStatus({
          progress: res.progress,
          stage: res.stage || 'processing',
          estimatedSecondsRemaining: res.estimated_seconds_remaining,
          estimatedTotalSeconds: res.estimated_total_seconds,
          isComplete: false,
        });
      } else if (res.has_job && res.status === 'completed') {
        setGenerationStatus({
          progress: 100,
          stage: 'completed',
          estimatedSecondsRemaining: 0,
          estimatedTotalSeconds: res.estimated_total_seconds,
          isComplete: true,
        });
        // Stop polling and reload recommendations
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsGenerating(false);
        loadRecommendations();

        // Show notification if user is on another tab
        if (!isOnDiscoverTab()) {
          showNotification({
            message: 'Your personalized recommendations are ready!',
            type: 'success',
            action: {
              label: 'View',
              onClick: () => setTab('discover'),
            },
          });
        }
      } else if (res.has_job && res.status === 'failed') {
        setGenerationStatus({
          progress: 0,
          stage: 'failed',
          estimatedSecondsRemaining: 0,
          estimatedTotalSeconds: res.estimated_total_seconds,
          isComplete: false,
          error: res.error_message || 'Generation failed',
        });
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsGenerating(false);
      }
    } catch (error) {
      console.error('Error polling generation status:', error);
    }
  }, [loadRecommendations]);

  // Start polling when generating
  useEffect(() => {
    if (isGenerating && !pollIntervalRef.current) {
      // Poll immediately and then every 2 seconds
      pollGenerationStatus();
      pollIntervalRef.current = setInterval(pollGenerationStatus, 2000);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [isGenerating, pollGenerationStatus]);

  // Always load recommendations on mount
  useEffect(() => {
    loadRecommendations();
  }, []); // Only on mount

  // Auto-generate when empty (after onboarding or for new users)
  useEffect(() => {
    if (isEmpty && !isLoading && !isGenerating) {
      // Automatically start generating when there are no recommendations
      setIsGenerating(true);
      generateMore().finally(() => {
        // Don't set isGenerating to false here - wait for status poll to confirm completion
      });
    }
  }, [isEmpty, isLoading, isGenerating, generateMore]);

  // Manual generate button handler (fallback)
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

  // Helper to format stage names
  const formatStageName = (stage: string) => {
    const stageNames: Record<string, string> = {
      starting: 'Starting up...',
      loading_ratings: 'Analyzing your taste...',
      ai_recommendations: 'Consulting AI experts...',
      cf_recommendations: 'Finding similar users...',
      aggregating: 'Combining results...',
      enriching_tmdb: 'Fetching movie details...',
      genre_diversity: 'Ensuring variety...',
      saving: 'Saving recommendations...',
      completed: 'Done!',
      failed: 'Error occurred',
    };
    return stageNames[stage] || 'Processing...';
  };

  // Empty state - no recommendations yet (auto-generating)
  if (isEmpty && !hasMore) {
    // When empty, we auto-generate - show generating state with progress
    if (isGenerating) {
      const progress = generationStatus?.progress || 0;
      const stage = generationStatus?.stage || 'starting';
      const estimatedRemaining = generationStatus?.estimatedSecondsRemaining || 90;

      return (
        <div className="generating-state" style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '32px 24px',
          textAlign: 'center',
          minHeight: '300px'
        }}>
          <div style={{ marginBottom: '24px' }}>
            <Spinner />
          </div>

          <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '8px' }}>
            Creating Your Personalized Picks
          </h2>

          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '14px' }}>
            {formatStageName(stage)}
          </p>

          {/* Progress bar */}
          <div style={{
            width: '100%',
            maxWidth: '300px',
            height: '8px',
            backgroundColor: 'var(--bg-tertiary)',
            borderRadius: '4px',
            overflow: 'hidden',
            marginBottom: '12px'
          }}>
            <div style={{
              width: `${progress}%`,
              height: '100%',
              background: 'linear-gradient(90deg, var(--primary), var(--primary-hover))',
              borderRadius: '4px',
              transition: 'width 0.3s ease'
            }} />
          </div>

          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
            {progress}% complete {estimatedRemaining > 0 ? `• ~${Math.ceil(estimatedRemaining / 60)} min remaining` : ''}
          </p>

          {/* Explore suggestion */}
          <div style={{
            marginTop: '32px',
            padding: '16px',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: '12px',
            maxWidth: '320px'
          }}>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
              While you wait, explore your <strong>Feed</strong> to see what friends are watching,
              or check your <strong>Watchlist</strong>!
            </p>
          </div>
        </div>
      );
    }

    // Fallback button if auto-generate didn't start for some reason
    return (
      <div className="empty-state">
        <div className="empty-icon">🎬</div>
        <h2 className="empty-title">Ready to discover movies?</h2>
        <p className="empty-text">
          Click below to generate personalized recommendations based on your taste
        </p>
        <Button
          variant="primary"
          onClick={handleGenerateRecommendations}
          disabled={isGenerating}
          style={{ marginTop: '16px' }}
        >
          Generate Recommendations
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
