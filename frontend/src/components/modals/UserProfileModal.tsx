import { useState, useEffect, useCallback } from 'react';
import { X, UserPlus, UserCheck } from 'lucide-react';
import { Button } from '../ui/Button';
import { apiFetch, profileApi } from '../../api/client';

interface UserProfile {
  id: number;
  username: string;
  bio?: string;
  stats: {
    movies_watched: number;
    avg_rating: number | null;
    favorite_genres: string[];
  };
  recent_activity: Array<{
    movie: {
      tmdb_id: number;
      title: string;
      poster_path: string;
    };
    rating: number;
    created_at: string;
  }>;
}

interface UserProfileModalProps {
  isOpen: boolean;
  userId: number | null;
  username: string | null;
  onClose: () => void;
  onViewMovie?: (tmdbId: number) => void;
}

export function UserProfileModal({
  isOpen,
  userId,
  username,
  onClose,
  onViewMovie,
}: UserProfileModalProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isFriend, setIsFriend] = useState(false);
  const [isAddingFriend, setIsAddingFriend] = useState(false);

  // Load user profile
  useEffect(() => {
    if (isOpen && userId) {
      loadProfile();
    }
  }, [isOpen, userId]);

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const loadProfile = async () => {
    if (!userId) return;
    setIsLoading(true);
    try {
      const data = await apiFetch<{ success: boolean; profile: UserProfile; is_friend: boolean }>(
        `/users/${userId}/profile`
      );
      setProfile(data.profile);
      setIsFriend(data.is_friend);
    } catch (err) {
      console.error('Error loading user profile:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddFriend = useCallback(async () => {
    if (!username) return;
    setIsAddingFriend(true);
    try {
      await profileApi.addFriend(username);
      setIsFriend(true);
    } catch (err) {
      console.error('Error adding friend:', err);
    } finally {
      setIsAddingFriend(false);
    }
  }, [username]);

  if (!isOpen) return null;

  const initial = (username || 'U').charAt(0).toUpperCase();

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal user-profile-modal"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '480px' }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
          <button onClick={onClose} className="modal-close-btn" aria-label="Close">
            <X size={24} />
          </button>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p>Loading profile...</p>
          </div>
        ) : profile ? (
          <div className="user-profile-content">
            {/* Avatar and Name */}
            <div className="user-profile-header">
              <div className="profile-avatar-large">{initial}</div>
              <h2 className="user-profile-name">{profile.username}</h2>
              {profile.bio ? (
                <p className="user-profile-bio">{profile.bio}</p>
              ) : null}
            </div>

            {/* Add Friend Button */}
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <Button
                variant={isFriend ? 'secondary' : 'primary'}
                onClick={handleAddFriend}
                disabled={isFriend || isAddingFriend}
              >
                {isFriend ? (
                  <>
                    <UserCheck size={18} /> Following
                  </>
                ) : (
                  <>
                    <UserPlus size={18} /> {isAddingFriend ? 'Adding...' : 'Follow'}
                  </>
                )}
              </Button>
            </div>

            {/* Stats */}
            <div className="user-profile-stats">
              <div className="profile-stat">
                <div className="profile-stat-value">{profile.stats.movies_watched}</div>
                <div className="profile-stat-label">Watched</div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat-value">
                  {profile.stats.avg_rating ? profile.stats.avg_rating.toFixed(1) : '-'}
                </div>
                <div className="profile-stat-label">Avg Rating</div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat-value">
                  {profile.stats.favorite_genres?.[0] || '-'}
                </div>
                <div className="profile-stat-label">Fav Genre</div>
              </div>
            </div>

            {/* Recent Activity */}
            {profile.recent_activity && profile.recent_activity.length > 0 ? (
              <div className="user-profile-activity">
                <h3>Recent Activity</h3>
                <div className="activity-grid">
                  {profile.recent_activity.slice(0, 6).map((activity, idx) => (
                    <div
                      key={idx}
                      className="activity-movie"
                      onClick={() => onViewMovie?.(activity.movie.tmdb_id)}
                      style={{ cursor: onViewMovie ? 'pointer' : 'default' }}
                    >
                      <img
                        src={activity.movie.poster_path || 'https://via.placeholder.com/60x90?text=?'}
                        alt={activity.movie.title}
                        className="activity-poster"
                      />
                      <div className="activity-rating">★ {activity.rating}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                No activity yet
              </p>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p>Profile not found</p>
          </div>
        )}
      </div>
    </div>
  );
}
