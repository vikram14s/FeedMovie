import { useState, useCallback, useEffect } from 'react';
import type { FeedActivity } from '../types';
import { feedApi } from '../api/client';

export function useFeed() {
  const [activities, setActivities] = useState<FeedActivity[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFeed = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await feedApi.get();
      setActivities(data.activities || []);
    } catch (err) {
      setError('Failed to load feed');
      console.error('Error loading feed:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const toggleLike = useCallback(async (activityId: number) => {
    try {
      await feedApi.toggleLike(activityId);
      // Optimistic update
      setActivities((prev) =>
        prev.map((a) =>
          a.id === activityId
            ? {
                ...a,
                is_liked: !a.is_liked,
                like_count: a.is_liked ? a.like_count - 1 : a.like_count + 1,
              }
            : a
        )
      );
    } catch (err) {
      console.error('Error toggling like:', err);
      // Reload to get correct state
      loadFeed();
    }
  }, [loadFeed]);

  const addToWatchlist = useCallback(async (tmdbId: number) => {
    try {
      await feedApi.addToWatchlist(tmdbId);
      return true;
    } catch (err) {
      console.error('Error adding to watchlist:', err);
      return false;
    }
  }, []);

  // Load on mount
  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  return {
    activities,
    isLoading,
    error,
    loadFeed,
    toggleLike,
    addToWatchlist,
  };
}
