import { useCallback } from 'react';

interface StarRatingProps {
  rating: number;
  onChange?: (rating: number) => void;
  readonly?: boolean;
  size?: 'sm' | 'md' | 'lg';
  allowHalf?: boolean;
}

export function StarRating({
  rating,
  onChange,
  readonly = false,
  size = 'md',
  allowHalf = true,
}: StarRatingProps) {
  const fontSize = {
    sm: '16px',
    md: '32px',
    lg: '36px',
  }[size];

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLSpanElement>, starIndex: number) => {
      if (readonly || !onChange) return;

      if (allowHalf) {
        const rect = e.currentTarget.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const isLeftHalf = clickX < rect.width / 2;
        const newRating = isLeftHalf ? starIndex + 0.5 : starIndex + 1;
        onChange(newRating);
      } else {
        onChange(starIndex + 1);
      }
    },
    [readonly, onChange, allowHalf]
  );

  return (
    <div className="star-rating" style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
      {[0, 1, 2, 3, 4].map((i) => {
        const starNum = i + 1;
        const isFilled = rating >= starNum;
        const isHalf = !isFilled && rating >= starNum - 0.5;

        return (
          <span
            key={i}
            onClick={(e) => handleClick(e, i)}
            style={{
              fontSize,
              color: isFilled ? 'var(--teal)' : 'var(--border)',
              cursor: readonly ? 'default' : 'pointer',
              transition: 'color 0.2s, transform 0.1s',
              position: 'relative',
              userSelect: 'none',
            }}
            className={`star ${isFilled ? 'filled' : ''} ${isHalf ? 'half' : ''}`}
          >
            ★
            {isHalf && (
              <span
                style={{
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  width: '50%',
                  overflow: 'hidden',
                  color: 'var(--teal)',
                }}
              >
                ★
              </span>
            )}
          </span>
        );
      })}
    </div>
  );
}
