import { useState, useCallback, useEffect } from 'react';
import type { Movie } from '../../types';
import { StarRating } from '../ui/StarRating';
import { Button } from '../ui/Button';

interface RatingModalProps {
  isOpen: boolean;
  movie: Movie | null;
  title?: string;
  onClose: () => void;
  onSubmit: (rating: number, reviewText?: string) => Promise<void>;
}

export function RatingModal({
  isOpen,
  movie,
  title = 'Rate this movie',
  onClose,
  onSubmit,
}: RatingModalProps) {
  const [rating, setRating] = useState(0);
  const [reviewText, setReviewText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setRating(0);
      setReviewText('');
    }
  }, [isOpen]);

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

  const handleSubmit = useCallback(async () => {
    if (rating === 0) return;

    setIsSubmitting(true);
    try {
      await onSubmit(rating, reviewText.trim() || undefined);
      onClose();
    } catch (error) {
      console.error('Error submitting rating:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [rating, reviewText, onSubmit, onClose]);

  if (!isOpen || !movie) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal-title">{title}</h2>
        <p className="modal-subtitle">{movie.title}</p>

        <StarRating rating={rating} onChange={setRating} size="lg" allowHalf />

        <div className="rating-display">
          <span className="rating-value">{rating > 0 ? rating.toFixed(1) : '-'}</span>
          <span className="rating-max">/ 5</span>
        </div>

        <p className="review-optional">Write a review (optional)</p>
        <textarea
          className="review-textarea"
          placeholder="What did you think of this movie?"
          value={reviewText}
          onChange={(e) => setReviewText(e.target.value)}
        />

        <div className="modal-actions">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={rating === 0 || isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </Button>
        </div>
      </div>
    </div>
  );
}
