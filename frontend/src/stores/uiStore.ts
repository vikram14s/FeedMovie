import { create } from 'zustand';
import type { Tab, Movie, Recommendation } from '../types';

interface UIState {
  // Navigation
  activeTab: Tab;
  setTab: (tab: Tab) => void;

  // Modals
  searchModalOpen: boolean;
  filtersModalOpen: boolean;
  ratingModal: { open: boolean; movie: Movie | null };
  markSeenModal: { open: boolean; movie: Movie | null };
  editBioModalOpen: boolean;

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
}

export const useUIStore = create<UIState>((set) => ({
  // Navigation
  activeTab: 'discover',
  setTab: (tab) => set({ activeTab: tab }),

  // Modals
  searchModalOpen: false,
  filtersModalOpen: false,
  ratingModal: { open: false, movie: null },
  markSeenModal: { open: false, movie: null },
  editBioModalOpen: false,

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
}));
