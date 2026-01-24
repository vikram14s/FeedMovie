// Core domain types

export interface User {
  id: number;
  username: string;
  email: string;
  bio?: string;
  onboarding_completed: boolean;
  onboarding_type?: 'letterboxd' | 'swipe';
}

export interface Movie {
  tmdb_id: number;
  title: string;
  year?: number;
  poster_path?: string;
  overview?: string;
  genres?: string[];
  directors?: string[];
  cast?: string[];
  imdb_rating?: number;
  tmdb_rating?: number;
  rt_rating?: string;
  awards?: string;
  streaming_providers?: {
    subscription?: StreamingProvider[];
    rent?: StreamingProvider[];
  };
}

export interface StreamingProvider {
  name: string;
  logo?: string;
}

export interface Recommendation extends Movie {
  score?: number;
  reasoning?: string;
  sources?: string[];
  already_watched?: boolean;
}

export interface WatchlistItem extends Movie {
  added_at?: string;
}

export interface Rating {
  tmdb_id: number;
  rating: number;
  review_text?: string;
  created_at?: string;
  movie?: Movie;
}

export interface FeedActivity {
  id: number;
  user: {
    id: number;
    username: string;
    avatar?: string;
  };
  movie: Movie;
  rating: number;
  review_text?: string;
  created_at: string;
  like_count: number;
  is_liked: boolean;
}

export interface TasteProfile {
  id: string;
  name: string;
  icon: string;
  description: string;
  representative_movies: Movie[];
}

export interface ProfileStats {
  movies_watched: number;
  avg_rating?: number;
  favorite_genres?: string[];
}

export interface UserProfile {
  username: string;
  bio?: string;
  stats: ProfileStats;
  recent_activity: Rating[];
}

export interface Friend {
  id: number;
  name: string;
  compatibility_score?: number;
}

export interface Review {
  id: number;
  user: {
    id: number;
    username: string;
  };
  rating: number;
  review_text?: string;
  created_at: string;
}

export interface FriendWatched {
  id: number;
  username: string;
  rating: number;
  review_text?: string;
  watched_at: string;
}

export type Tab = 'discover' | 'feed' | 'watchlist' | 'profile';

export interface MoodPreset {
  id: string;
  label: string;
  icon: string;
  genres: string[];
}
