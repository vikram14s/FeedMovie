import { create } from 'zustand';
import type { Tab, Movie, Recommendation } from '../types';

interface UIState {
  // Navigation
  activeTab: Tab;
  setTab: (tab: Tab) => void;
  resetToDiscover: () => void;

  // Modals
  searchModalOpen: boolean;
  filtersModalOpen: boolean;
  ratingModal: { open: boolean; movie: Movie | null };
  markSeenModal: { open: boolean; movie: Movie | null };
  editBioModalOpen: boolean;
  addFriendsModalOpen: boolean;
  movieDetailModal: { open: boolean; movie: Movie | Recommendation | null };
  userProfileModal: { open: boolean; userId: number | null; username: string | null };

  // Modal controls
  openSearchModal: () => void;
  closeSearchModal: () => void;
  openFiltersModal: () => void;
  closeFiltersModal: () => void;
  openRatingModal: (movie: Recommendation) => void;
  closeRatingModal: () => void;
  openMarkSeenModal: (movie: Movie) => void;
  closeMarkSeenModal: () => void;
  openEditBioModal: () => void;
  closeEditBioModal: () => void;
  openAddFriendsModal: () => void;
  closeAddFriendsModal: () => void;
  openMovieDetailModal: (movie: Movie | Recommendation) => void;
  closeMovieDetailModal: () => void;
  openUserProfileModal: (userId: number, username: string) => void;
  closeUserProfileModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  // Navigation
  activeTab: 'discover',
  setTab: (tab) => set({ activeTab: tab }),
  resetToDiscover: () => set({ activeTab: 'discover' }),

  // Modals
  searchModalOpen: false,
  filtersModalOpen: false,
  ratingModal: { open: false, movie: null },
  markSeenModal: { open: false, movie: null },
  editBioModalOpen: false,
  addFriendsModalOpen: false,
  movieDetailModal: { open: false, movie: null },
  userProfileModal: { open: false, userId: null, username: null },

  // Modal controls
  openSearchModal: () => set({ searchModalOpen: true }),
  closeSearchModal: () => set({ searchModalOpen: false }),
  openFiltersModal: () => set({ filtersModalOpen: true }),
  closeFiltersModal: () => set({ filtersModalOpen: false }),
  openRatingModal: (movie) => set({ ratingModal: { open: true, movie } }),
  closeRatingModal: () => set({ ratingModal: { open: false, movie: null } }),
  openMarkSeenModal: (movie) => set({ markSeenModal: { open: true, movie } }),
  closeMarkSeenModal: () => set({ markSeenModal: { open: false, movie: null } }),
  openEditBioModal: () => set({ editBioModalOpen: true }),
  closeEditBioModal: () => set({ editBioModalOpen: false }),
  openAddFriendsModal: () => set({ addFriendsModalOpen: true }),
  closeAddFriendsModal: () => set({ addFriendsModalOpen: false }),
  openMovieDetailModal: (movie) => set({ movieDetailModal: { open: true, movie } }),
  closeMovieDetailModal: () => set({ movieDetailModal: { open: false, movie: null } }),
  openUserProfileModal: (userId, username) => set({ userProfileModal: { open: true, userId, username } }),
  closeUserProfileModal: () => set({ userProfileModal: { open: false, userId: null, username: null } }),
}));
