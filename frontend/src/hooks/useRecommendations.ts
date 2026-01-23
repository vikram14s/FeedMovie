import { useCallback } from 'react';
import { useRecommendationStore } from '../stores/recommendationStore';

export function useRecommendations() {
  const {
    recommendations,
    currentIndex,
    totalUnshown,
    selectedGenres,
    selectedMoods,
    isLoading,
    stats,
    loadRecommendations,
    swipeLeft,
    swipeRight,
    setSelectedGenres,
    setSelectedMoods,
    generateMore,
    reset,
  } = useRecommendationStore();

  // Derived state
  const currentMovie = recommendations[currentIndex] ?? null;
  const remainingCount = recommendations.length - currentIndex;
  const hasMore = currentIndex < recommendations.length;
  const isEmpty = recommendations.length === 0 && !isLoading;

  // Stable callbacks
  const handleSwipeLeft = useCallback(async () => {
    await swipeLeft();
  }, [swipeLeft]);

  const handleSwipeRight = useCallback(async () => {
    await swipeRight();
  }, [swipeRight]);

  const handleLoadRecommendations = useCallback(
    async (genres?: string[]) => {
      await loadRecommendations(genres);
    },
    [loadRecommendations]
  );

  return {
    recommendations,
    currentMovie,
    currentIndex,
    remainingCount,
    totalUnshown,
    hasMore,
    isEmpty,
    isLoading,
    stats,
    selectedGenres,
    selectedMoods,
    swipeLeft: handleSwipeLeft,
    swipeRight: handleSwipeRight,
    loadRecommendations: handleLoadRecommendations,
    setSelectedGenres,
    setSelectedMoods,
    generateMore,
    reset,
  };
}
