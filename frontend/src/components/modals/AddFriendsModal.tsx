import { useState, useEffect, useCallback } from 'react';
import { X, Search, UserPlus, UserCheck } from 'lucide-react';
import { Button } from '../ui/Button';
import { apiFetch, profileApi } from '../../api/client';

interface UserResult {
  id: number;
  username: string;
  bio?: string;
  movies_watched: number;
  is_friend: boolean;
}

interface AddFriendsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFriendAdded?: () => void;
}

export function AddFriendsModal({
  isOpen,
  onClose,
  onFriendAdded,
}: AddFriendsModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<UserResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [addingIds, setAddingIds] = useState<Set<number>>(new Set());

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

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSearchQuery('');
      setResults([]);
    }
  }, [isOpen]);

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const data = await apiFetch<{ success: boolean; users: UserResult[] }>(
        `/users/search?q=${encodeURIComponent(searchQuery.trim())}`
      );
      setResults(data.users || []);
    } catch (err) {
      console.error('Error searching users:', err);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery]);

  const handleAddFriend = useCallback(async (user: UserResult) => {
    setAddingIds((prev) => new Set(prev).add(user.id));
    try {
      await profileApi.addFriend(user.username);
      // Update the result to show as friend
      setResults((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, is_friend: true } : u))
      );
      onFriendAdded?.();
    } catch (err) {
      console.error('Error adding friend:', err);
    } finally {
      setAddingIds((prev) => {
        const next = new Set(prev);
        next.delete(user.id);
        return next;
      });
    }
  }, [onFriendAdded]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal add-friends-modal"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '480px' }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 className="modal-title">Find Friends</h2>
          <button onClick={onClose} className="modal-close-btn" aria-label="Close">
            <X size={24} />
          </button>
        </div>

        {/* Search Input */}
        <div className="search-input-container" style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search by username..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSearch();
              }}
              style={{ flex: 1 }}
            />
            <Button variant="primary" onClick={handleSearch} disabled={isSearching}>
              <Search size={18} />
            </Button>
          </div>
        </div>

        {/* Results */}
        <div className="search-results">
          {isSearching ? (
            <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
              Searching...
            </p>
          ) : results.length > 0 ? (
            <div className="user-results-list">
              {results.map((user) => {
                const initial = user.username.charAt(0).toUpperCase();
                const isAdding = addingIds.has(user.id);

                return (
                  <div key={user.id} className="user-result-item">
                    <div className="user-result-avatar">{initial}</div>
                    <div className="user-result-info">
                      <div className="user-result-name">{user.username}</div>
                      <div className="user-result-stats">
                        {user.movies_watched} movies watched
                      </div>
                    </div>
                    <Button
                      variant={user.is_friend ? 'secondary' : 'primary'}
                      onClick={() => handleAddFriend(user)}
                      disabled={user.is_friend || isAdding}
                      style={{ padding: '8px 16px', fontSize: '13px' }}
                    >
                      {user.is_friend ? (
                        <>
                          <UserCheck size={16} /> Following
                        </>
                      ) : isAdding ? (
                        'Adding...'
                      ) : (
                        <>
                          <UserPlus size={16} /> Follow
                        </>
                      )}
                    </Button>
                  </div>
                );
              })}
            </div>
          ) : searchQuery ? (
            <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
              No users found
            </p>
          ) : (
            <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
              Search for users by username
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
