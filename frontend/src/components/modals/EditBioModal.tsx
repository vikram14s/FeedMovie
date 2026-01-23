import { useState, useCallback, useEffect } from 'react';
import { Button } from '../ui/Button';

interface EditBioModalProps {
  isOpen: boolean;
  currentBio: string;
  onClose: () => void;
  onSave: (bio: string) => Promise<boolean>;
}

export function EditBioModal({ isOpen, currentBio, onClose, onSave }: EditBioModalProps) {
  const [bio, setBio] = useState(currentBio);
  const [isSaving, setIsSaving] = useState(false);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setBio(currentBio);
    }
  }, [isOpen, currentBio]);

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

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    const success = await onSave(bio.trim());
    setIsSaving(false);
    if (success) {
      onClose();
    }
  }, [bio, onSave, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal-title">Edit Bio</h2>
        <p className="modal-subtitle">Tell others about your movie taste</p>

        <textarea
          className="bio-textarea"
          placeholder="I love sci-fi and indie dramas..."
          value={bio}
          onChange={(e) => setBio(e.target.value)}
        />

        <div className="modal-actions">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>
    </div>
  );
}
