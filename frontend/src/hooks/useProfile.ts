import { useState, useCallback, useEffect } from 'react';
import type { UserProfile, Rating, Friend } from '../types';
import { profileApi } from '../api/client';

export function useProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [library, setLibrary] = useState<Rating[]>([]);
  const [friends, setFriends] = useState<Friend[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Parallel fetch (Vercel best practice: async-parallel)
      const [profileRes, libraryRes, friendsRes] = await Promise.all([
        profileApi.get(),
        profileApi.getLibrary(),
        profileApi.getFriends(),
      ]);

      setProfile(profileRes.profile);
      setLibrary(libraryRes.library || []);
      setFriends(friendsRes.friends || []);
    } catch (err) {
      setError('Failed to load profile');
      console.error('Error loading profile:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateBio = useCallback(async (bio: string) => {
    try {
      await profileApi.update({ bio });
      setProfile((prev) => (prev ? { ...prev, bio } : null));
      return true;
    } catch (err) {
      console.error('Error updating bio:', err);
      return false;
    }
  }, []);

  // Load on mount
  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  return {
    profile,
    library,
    friends,
    isLoading,
    error,
    loadProfile,
    updateBio,
  };
}
