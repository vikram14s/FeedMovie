import { useCallback, useState } from 'react';
import { Edit2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useProfile } from '../hooks/useProfile';
import { useAuth } from '../hooks/useAuth';
import { useUIStore } from '../stores/uiStore';
import { Spinner } from '../components/ui/Spinner';
import { formatTimeAgo } from '../utils/time';

const ITEMS_PER_PAGE = 16;

export function ProfileScreen() {
  const { profile, library, friends, isLoading } = useProfile();
  const { user, logout } = useAuth();
  const { openEditBioModal } = useUIStore();
  const [libraryPage, setLibraryPage] = useState(0);

  const handleLogout = useCallback(() => {
    logout();
  }, [logout]);

  const totalPages = Math.ceil(library.length / ITEMS_PER_PAGE);
  const paginatedLibrary = library.slice(
    libraryPage * ITEMS_PER_PAGE,
    (libraryPage + 1) * ITEMS_PER_PAGE
  );

  const goToPrevPage = useCallback(() => {
    setLibraryPage((p) => Math.max(0, p - 1));
  }, []);

  const goToNextPage = useCallback(() => {
    setLibraryPage((p) => Math.min(totalPages - 1, p + 1));
  }, [totalPages]);

  if (isLoading && !profile) {
    return (
      <div className="loading">
        <Spinner />
        <p className="loading-text">Loading profile...</p>
      </div>
    );
  }

  const username = profile?.username || user?.username || 'User';
  const initial = username.charAt(0).toUpperCase();
  const bio = profile?.bio || 'Add a bio to tell others about your taste';
  const stats = profile?.stats || { movies_watched: 0, avg_rating: null, favorite_genres: [] };

  return (
    <div className="profile-view">
      {/* Profile Header */}
      <div className="profile-header">
        <div className="profile-avatar-large">{initial}</div>
        <div className="profile-username">{username}</div>
        <div className="profile-bio">{bio}</div>

        <button onClick={openEditBioModal} className="edit-bio-btn">
          <Edit2 size={14} />
          Edit Bio
        </button>

        <div className="profile-stats">
          <div className="profile-stat">
            <div className="profile-stat-value">{stats.movies_watched}</div>
            <div className="profile-stat-label">Watched</div>
          </div>
          <div className="profile-stat">
            <div className="profile-stat-value">
              {stats.avg_rating ? stats.avg_rating.toFixed(1) : '-'}
            </div>
            <div className="profile-stat-label">Avg Rating</div>
          </div>
          <div className="profile-stat">
            <div className="profile-stat-value">{stats.favorite_genres?.[0] || '-'}</div>
            <div className="profile-stat-label">Fav Genre</div>
          </div>
        </div>
      </div>

      {/* Friends Section */}
      <div className="profile-section">
        <div className="profile-section-title">Friends</div>
        {friends.length > 0 ? (
          <div className="friends-list">
            {friends.map((friend) => {
              const friendInitial = (friend.name || 'F').charAt(0).toUpperCase();
              const score = friend.compatibility_score
                ? `${Math.round(friend.compatibility_score * 100)}%`
                : '';

              return (
                <div key={friend.id} className="friend-item">
                  <div className="friend-avatar">{friendInitial}</div>
                  <span className="friend-name">{friend.name}</span>
                  {score ? <span className="friend-score">{score}</span> : null}
                </div>
              );
            })}
          </div>
        ) : (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
            No friends added yet
          </p>
        )}
      </div>

      {/* Library Section */}
      <div className="profile-section">
        <div className="profile-section-header">
          <div className="profile-section-title">My Library</div>
          {totalPages > 1 ? (
            <div className="library-pagination">
              <button
                onClick={goToPrevPage}
                disabled={libraryPage === 0}
                className="pagination-btn"
                aria-label="Previous page"
              >
                <ChevronLeft size={20} />
              </button>
              <span className="pagination-info">
                {libraryPage + 1} / {totalPages}
              </span>
              <button
                onClick={goToNextPage}
                disabled={libraryPage >= totalPages - 1}
                className="pagination-btn"
                aria-label="Next page"
              >
                <ChevronRight size={20} />
              </button>
            </div>
          ) : null}
        </div>
        {library.length > 0 ? (
          <div className="library-grid">
            {paginatedLibrary.map((item) => {
              const movie = item.movie;
              const posterUrl = movie?.poster_path || 'https://via.placeholder.com/80x120?text=?';

              return (
                <div key={item.tmdb_id} className="library-item">
                  <img
                    src={posterUrl}
                    alt={movie?.title || 'Unknown'}
                    className="library-poster"
                    title={`${movie?.title || 'Unknown'} (${movie?.year || ''})`}
                  />
                  <div className="library-rating">★ {item.rating}</div>
                </div>
              );
            })}
          </div>
        ) : (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
            No movies rated yet
          </p>
        )}
      </div>

      {/* Recent Activity Section */}
      <div className="profile-section">
        <div className="profile-section-title">Recent Activity</div>
        {profile?.recent_activity && profile.recent_activity.length > 0 ? (
          <div>
            {profile.recent_activity.map((activity, index) => {
              const movie = activity.movie;
              const posterUrl = movie?.poster_path || 'https://via.placeholder.com/48x72?text=?';
              const stars =
                '★'.repeat(Math.floor(activity.rating || 0)) +
                '☆'.repeat(5 - Math.floor(activity.rating || 0));

              return (
                <div key={index} className="profile-activity-item">
                  <img src={posterUrl} alt={movie?.title || 'Unknown'} className="profile-activity-poster" />
                  <div className="profile-activity-info">
                    <div className="profile-activity-title">{movie?.title || 'Unknown'}</div>
                    <div className="profile-activity-detail">
                      {stars} • {formatTimeAgo(activity.created_at)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
            No activity yet
          </p>
        )}
      </div>

      {/* Logout Button */}
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <button onClick={handleLogout} className="btn-link" style={{ color: 'var(--coral)' }}>
          Sign Out
        </button>
      </div>
    </div>
  );
}
