import { useState, useCallback, useEffect } from 'react';
import type { WatchlistItem } from '../types';
import { watchlistApi } from '../api/client';

export function useWatchlist() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadWatchlist = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await watchlistApi.get();
      // Filter out already watched items
      const unwatched = (data.watchlist || []).filter(
        (item: WatchlistItem & { already_watched?: boolean }) => !item.already_watched
      );
      setWatchlist(unwatched);
    } catch (err) {
      setError('Failed to load watchlist');
      console.error('Error loading watchlist:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const removeFromWatchlist = useCallback(async (tmdbId: number) => {
    try {
      await watchlistApi.remove(tmdbId);
      setWatchlist((prev) => prev.filter((m) => m.tmdb_id !== tmdbId));
    } catch (err) {
      console.error('Error removing from watchlist:', err);
    }
  }, []);

  const markAsSeen = useCallback(
    async (tmdbId: number, rating: number, reviewText?: string) => {
      try {
        await watchlistApi.markSeen(tmdbId, rating, reviewText);
        setWatchlist((prev) => prev.filter((m) => m.tmdb_id !== tmdbId));
        return true;
      } catch (err) {
        console.error('Error marking as seen:', err);
        return false;
      }
    },
    []
  );

  // Load on mount
  useEffect(() => {
    loadWatchlist();
  }, [loadWatchlist]);

  return {
    watchlist,
    watchlistCount: watchlist.length,
    isLoading,
    error,
    loadWatchlist,
    removeFromWatchlist,
    markAsSeen,
  };
}
