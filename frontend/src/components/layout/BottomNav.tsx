import { Compass, Users, Bookmark, User } from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';
import type { Tab } from '../../types';

interface NavItem {
  id: Tab;
  icon: typeof Compass;
  label: string;
}

const tabs: NavItem[] = [
  { id: 'discover', icon: Compass, label: 'Discover' },
  { id: 'feed', icon: Users, label: 'Feed' },
  { id: 'watchlist', icon: Bookmark, label: 'Watchlist' },
  { id: 'profile', icon: User, label: 'Profile' },
];

interface BottomNavProps {
  watchlistCount?: number;
}

export function BottomNav({ watchlistCount = 0 }: BottomNavProps) {
  const { activeTab, setTab } = useUIStore();

  return (
    <nav className="bottom-nav">
      {tabs.map(({ id, icon: Icon, label }) => (
        <button
          key={id}
          className={`nav-item ${activeTab === id ? 'active' : ''}`}
          onClick={() => setTab(id)}
          aria-label={label}
        >
          <div style={{ position: 'relative' }}>
            <Icon size={24} />
            {id === 'watchlist' && watchlistCount > 0 ? (
              <span className="nav-badge">{watchlistCount}</span>
            ) : null}
          </div>
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
}
