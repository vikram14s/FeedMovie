import { Search, SlidersHorizontal } from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';

export function Header() {
  const { activeTab, openSearchModal, openFiltersModal } = useUIStore();

  return (
    <header className="header">
      <div className="header-top">
        <div className="logo">feedmovie</div>
        <div className="header-icons">
          <button
            onClick={openSearchModal}
            className="header-icon"
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            aria-label="Search"
          >
            <Search size={24} />
          </button>
          {activeTab === 'discover' && (
            <button
              onClick={openFiltersModal}
              className="header-icon"
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
              aria-label="Filters"
            >
              <SlidersHorizontal size={24} />
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
