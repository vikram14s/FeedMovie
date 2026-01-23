import { useState, useCallback, useEffect } from 'react';
import { X } from 'lucide-react';
import { Button } from '../ui/Button';
import { moodPresets } from '../../stores/recommendationStore';

interface FiltersModalProps {
  isOpen: boolean;
  selectedGenres: string[];
  selectedMoods: string[];
  onClose: () => void;
  onApply: (genres: string[], moods: string[]) => void;
}

export function FiltersModal({
  isOpen,
  selectedMoods: initialMoods,
  onClose,
  onApply,
}: FiltersModalProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>(initialMoods);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedIds(initialMoods.length > 0 ? initialMoods : []);
    }
  }, [isOpen, initialMoods]);

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

  const toggleGenre = useCallback((id: string) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((g) => g !== id);
      }
      return [...prev, id];
    });
  }, []);

  const handleApply = useCallback(() => {
    // Convert selected IDs to genre names
    const genres = selectedIds.flatMap((id) => {
      const preset = moodPresets.find((p) => p.id === id);
      return preset?.genres ?? [];
    });
    onApply([...new Set(genres)], selectedIds);
    onClose();
  }, [selectedIds, onApply, onClose]);

  const handleSkip = useCallback(() => {
    onApply([], []);
    onClose();
  }, [onApply, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ maxWidth: '420px' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="modal-title">Filter by Genre</h2>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            aria-label="Close"
          >
            <X size={24} />
          </button>
        </div>

        <p className="modal-subtitle">Select genres to filter recommendations</p>

        {/* Genre Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '10px',
            marginBottom: '20px',
          }}
        >
          {moodPresets.map((preset) => (
            <button
              key={preset.id}
              onClick={() => toggleGenre(preset.id)}
              className={`genre-option ${selectedIds.includes(preset.id) ? 'selected' : ''}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '14px 12px',
              }}
            >
              <span style={{ fontSize: '18px' }}>{preset.icon}</span>
              <span style={{ fontSize: '14px', fontWeight: 500 }}>{preset.label}</span>
            </button>
          ))}
        </div>

        <div className="selection-actions" style={{ flexDirection: 'column', gap: '12px' }}>
          <Button
            variant="primary"
            onClick={handleApply}
            style={{ width: '100%' }}
          >
            Apply Filters
          </Button>
          <Button variant="link" onClick={handleSkip}>
            Show me everything
          </Button>
        </div>
      </div>
    </div>
  );
}
