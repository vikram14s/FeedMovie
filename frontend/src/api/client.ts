// API client with auth headers

const API_URL = import.meta.env.VITE_API_URL || '/api';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = localStorage.getItem('feedmovie_token');

  const res = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    let message = text;
    try {
      const json = JSON.parse(text);
      message = json.error || json.message || text;
    } catch {
      // Keep raw text as message
    }
    throw new ApiError(message, res.status);
  }

  return res.json();
}

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<{ token: string; user: import('../types').User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (username: string, email: string, password: string) =>
    apiFetch<{ token: string; user: import('../types').User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    }),

  me: () => apiFetch<{ user: import('../types').User }>('/auth/me'),
};

// Onboarding API
export const onboardingApi = {
  getMovies: () =>
    apiFetch<{ success: boolean; movies: import('../types').Movie[] }>('/onboarding/movies'),

  submitLetterboxd: (letterboxd_username: string) =>
    apiFetch<{ success: boolean }>('/onboarding/letterboxd', {
      method: 'POST',
      body: JSON.stringify({ letterboxd_username }),
    }),

  submitSwipeRatings: (ratings: { tmdb_id: number; rating: number }[]) =>
    apiFetch<{ success: boolean }>('/onboarding/swipe-ratings', {
      method: 'POST',
      body: JSON.stringify({ ratings }),
    }),

  complete: () =>
    apiFetch<{ success: boolean }>('/onboarding/complete', { method: 'POST' }),
};

// Recommendations API
export const recommendationsApi = {
  get: (params?: { limit?: number; genres?: string[] }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.genres?.length) searchParams.set('genres', params.genres.join(','));
    const query = searchParams.toString();
    return apiFetch<{
      success: boolean;
      recommendations: import('../types').Recommendation[];
      total_unshown: number;
    }>(`/recommendations${query ? `?${query}` : ''}`);
  },

  swipe: (tmdb_id: number, action: 'left' | 'right') =>
    apiFetch<{ success: boolean }>('/swipe', {
      method: 'POST',
      body: JSON.stringify({ tmdb_id, action }),
    }),

  generateMore: () =>
    apiFetch<{ success: boolean }>('/generate-more', { method: 'POST' }),
};

// Watchlist API
export const watchlistApi = {
  get: () =>
    apiFetch<{ success: boolean; watchlist: import('../types').WatchlistItem[] }>('/watchlist'),

  remove: (tmdb_id: number) =>
    apiFetch<{ success: boolean }>(`/watchlist/${tmdb_id}`, { method: 'DELETE' }),

  markSeen: (tmdb_id: number, rating: number, review_text?: string) =>
    apiFetch<{ success: boolean }>(`/watchlist/${tmdb_id}/seen`, {
      method: 'POST',
      body: JSON.stringify({ rating, review_text }),
    }),
};

// Feed API
export const feedApi = {
  get: () =>
    apiFetch<{ success: boolean; activities: import('../types').FeedActivity[] }>('/feed'),

  toggleLike: (activityId: number) =>
    apiFetch<{ success: boolean }>(`/feed/${activityId}/like`, { method: 'POST' }),

  addToWatchlist: (tmdb_id: number) =>
    apiFetch<{ success: boolean }>(`/feed/${tmdb_id}/watchlist`, { method: 'POST' }),
};

// Profile API
export const profileApi = {
  get: () =>
    apiFetch<{ success: boolean; profile: import('../types').UserProfile }>('/profile'),

  update: (data: { bio?: string }) =>
    apiFetch<{ success: boolean }>('/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  getLibrary: () =>
    apiFetch<{ success: boolean; library: import('../types').Rating[] }>('/profile/library'),

  getFriends: () =>
    apiFetch<{ success: boolean; friends: import('../types').Friend[] }>('/profile/friends'),
};

// Taste Profiles API
export const tasteProfilesApi = {
  get: () =>
    apiFetch<{ success: boolean; profiles: import('../types').TasteProfile[] }>('/taste-profiles'),

  select: (profile_ids: string[]) =>
    apiFetch<{ success: boolean }>('/select-profile', {
      method: 'POST',
      body: JSON.stringify({ profile_ids }),
    }),
};

// Ratings API
export const ratingsApi = {
  add: (tmdb_id: number, title: string, year: number | undefined, rating: number, review_text?: string) =>
    apiFetch<{ success: boolean }>('/add-rating', {
      method: 'POST',
      body: JSON.stringify({ tmdb_id, title, year, rating, review_text }),
    }),

  addReview: (tmdb_id: number, rating: number, review_text?: string) =>
    apiFetch<{ success: boolean }>('/reviews', {
      method: 'POST',
      body: JSON.stringify({ tmdb_id, rating, review_text }),
    }),
};

// Search API
export const searchApi = {
  movies: (query: string) =>
    apiFetch<{ success: boolean; results: import('../types').Movie[] }>(
      `/movies/search?q=${encodeURIComponent(query)}`
    ),
};
