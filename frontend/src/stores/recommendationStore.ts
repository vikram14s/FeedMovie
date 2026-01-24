import { create } from 'zustand';
import type { Recommendation, MoodPreset } from '../types';
import { recommendationsApi } from '../api/client';

// Genre presets for filtering
export const moodPresets: MoodPreset[] = [
  { id: 'action', label: 'Action', icon: '💥', genres: ['Action'] },
  { id: 'comedy', label: 'Comedy', icon: '😂', genres: ['Comedy'] },
  { id: 'thriller', label: 'Thriller', icon: '🔪', genres: ['Thriller'] },
  { id: 'horror', label: 'Horror', icon: '👻', genres: ['Horror'] },
  { id: 'scifi', label: 'Sci-Fi', icon: '🚀', genres: ['Sci-Fi'] },
  { id: 'drama', label: 'Drama', icon: '🎭', genres: ['Drama'] },
];

export const allGenres = [
  'Action',
  'Comedy',
  'Drama',
  'Thriller',
  'Romance',
  'Sci-Fi',
  'Horror',
  'Documentary',
  'Animation',
  'Crime',
];

interface RecommendationState {
  recommendations: Recommendation[];
  currentIndex: number;
  totalUnshown: number;
  selectedGenres: string[];
  selectedMoods: string[];
  isLoading: boolean;
  generationTriggered: boolean;

  // Stats
  stats: {
    liked: number;
    skipped: number;
  };

  // Actions
  loadRecommendations: (genres?: string[]) => Promise<void>;
  swipeLeft: () => Promise<void>;
  swipeRight: () => Promise<void>;
  setSelectedGenres: (genres: string[]) => void;
  setSelectedMoods: (moods: string[]) => void;
  generateMore: () => Promise<void>;
  reset: () => void;
}

// Lazy init from localStorage
const getInitialGenres = (): string[] => {
  try {
    const saved = localStorage.getItem('feedmovie_genres');
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
};

export const useRecommendationStore = create<RecommendationState>((set, get) => ({
  recommendations: [],
  currentIndex: 0,
  totalUnshown: 0,
  selectedGenres: getInitialGenres(),
  selectedMoods: [],
  isLoading: false,
  generationTriggered: false,
  stats: { liked: 0, skipped: 0 },

  loadRecommendations: async (genres) => {
    set({ isLoading: true });
    try {
      const genresToUse = genres ?? get().selectedGenres;
      const data = await recommendationsApi.get({
        limit: 50,
        genres: genresToUse.length > 0 ? genresToUse : undefined
      });

      set({
        recommendations: data.recommendations,
        totalUnshown: data.total_unshown,
        currentIndex: 0,
        isLoading: false,
      });
    } catch (error) {
      console.error('Error loading recommendations:', error);
      set({ isLoading: false });
    }
  },

  swipeLeft: async () => {
    const { recommendations, currentIndex, totalUnshown, generationTriggered } = get();
    if (currentIndex >= recommendations.length) return;

    const movie = recommendations[currentIndex];

    try {
      await recommendationsApi.swipe(movie.tmdb_id, 'left');
    } catch (error) {
      console.error('Error recording swipe:', error);
    }

    // Functional setState (Vercel best practice: rerender-functional-setstate)
    set((state) => ({
      currentIndex: state.currentIndex + 1,
      stats: { ...state.stats, skipped: state.stats.skipped + 1 },
    }));

    // Check preemptive generation
    const remaining = totalUnshown - (currentIndex + 1);
    if (remaining < 10 && !generationTriggered) {
      set({ generationTriggered: true });
      recommendationsApi.generateMore().catch(console.error);
    }
  },

  swipeRight: async () => {
    const { recommendations, currentIndex, totalUnshown, generationTriggered } = get();
    if (currentIndex >= recommendations.length) return;

    const movie = recommendations[currentIndex];

    try {
      await recommendationsApi.swipe(movie.tmdb_id, 'right');
    } catch (error) {
      console.error('Error recording swipe:', error);
    }

    set((state) => ({
      currentIndex: state.currentIndex + 1,
      stats: { ...state.stats, liked: state.stats.liked + 1 },
    }));

    // Check preemptive generation
    const remaining = totalUnshown - (currentIndex + 1);
    if (remaining < 10 && !generationTriggered) {
      set({ generationTriggered: true });
      recommendationsApi.generateMore().catch(console.error);
    }
  },

  setSelectedGenres: (genres) => {
    localStorage.setItem('feedmovie_genres', JSON.stringify(genres));
    set({ selectedGenres: genres });
  },

  setSelectedMoods: (moods) => {
    // Convert moods to genres
    const genres = moods.flatMap((moodId) => {
      const preset = moodPresets.find((p) => p.id === moodId);
      return preset?.genres ?? [];
    });
    const uniqueGenres = [...new Set(genres)];

    localStorage.setItem('feedmovie_genres', JSON.stringify(uniqueGenres));
    set({ selectedMoods: moods, selectedGenres: uniqueGenres });
  },

  generateMore: async () => {
    set({ isLoading: true });
    try {
      await recommendationsApi.generateMore();

      // Poll for recommendations (AI generation can take 30-60 seconds)
      const maxAttempts = 20;
      const pollInterval = 3000; // 3 seconds between polls

      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await new Promise((resolve) => setTimeout(resolve, pollInterval));

        // Try to load recommendations
        const data = await recommendationsApi.get({ limit: 50 });

        if (data.recommendations && data.recommendations.length > 0) {
          set({
            recommendations: data.recommendations,
            totalUnshown: data.total_unshown,
            currentIndex: 0,
            isLoading: false,
          });
          return; // Success!
        }

        console.log(`Polling for recommendations... attempt ${attempt + 1}/${maxAttempts}`);
      }

      // After max attempts, just load whatever we have
      await get().loadRecommendations();
    } catch (error) {
      console.error('Error generating recommendations:', error);
      set({ isLoading: false });
    }
  },

  reset: () => {
    localStorage.removeItem('feedmovie_genres');
    set({
      recommendations: [],
      currentIndex: 0,
      totalUnshown: 0,
      selectedGenres: [],
      selectedMoods: [],
      isLoading: false,
      generationTriggered: false,
      stats: { liked: 0, skipped: 0 },
    });
  },
}));
