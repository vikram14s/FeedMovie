import { motion } from 'framer-motion';
import type { Recommendation } from '../../types';

interface MovieCardProps {
  movie: Recommendation;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
}

function formatAwards(awards?: string): string {
  if (!awards) return '';

  const oscarMatch = awards.match(/Won (\d+) Oscar/i);
  if (oscarMatch) {
    return `${oscarMatch[1]} Oscar${parseInt(oscarMatch[1]) > 1 ? 's' : ''}`;
  }

  const nomMatch = awards.match(/Nominated for (\d+) Oscar/i);
  if (nomMatch) {
    return `${nomMatch[1]} Nom`;
  }

  const winMatch = awards.match(/(\d+) win/i);
  if (winMatch && parseInt(winMatch[1]) >= 5) {
    return `${winMatch[1]} Wins`;
  }

  return '';
}

export function MovieCard({ movie, onSwipeLeft, onSwipeRight }: MovieCardProps) {
  const posterUrl = movie.poster_path || 'https://via.placeholder.com/140x210?text=No+Poster';
  const matchScore = movie.score ? Math.round(movie.score * 100) : null;
  const genres = (movie.genres || []).slice(0, 3);
  const directors = movie.directors || [];
  const cast = movie.cast || [];
  const awards = formatAwards(movie.awards);
  const overview = movie.overview || '';
  const reasoning = movie.reasoning || 'Recommended based on your taste';
  const sources = [...new Set(movie.sources || [])];
  const isFriendRec =
    reasoning.toLowerCase().includes('friend') ||
    sources.some((s) => s.toLowerCase().includes('friend'));

  // Streaming providers
  const streamingProviders = movie.streaming_providers || {};
  const subscription = streamingProviders.subscription || [];
  const rent = streamingProviders.rent || [];
  const allProviders = [...subscription, ...rent.slice(0, 3)];

  const handleDragEnd = (
    _: MouseEvent | TouchEvent | PointerEvent,
    info: { offset: { x: number }; velocity: { x: number } }
  ) => {
    const swipeThreshold = 100;
    const velocityThreshold = 500;

    if (info.offset.x > swipeThreshold || info.velocity.x > velocityThreshold) {
      onSwipeRight?.();
    } else if (info.offset.x < -swipeThreshold || info.velocity.x < -velocityThreshold) {
      onSwipeLeft?.();
    }
  };

  return (
    <motion.div
      className="movie-card"
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.8}
      onDragEnd={handleDragEnd}
      whileDrag={{ scale: 1.02 }}
      style={{ cursor: 'grab' }}
    >
      <div className="card-top">
        {matchScore !== null ? <span className="match-badge">{matchScore}% match</span> : null}
        {isFriendRec ? <span className="friend-rec-badge">friend rec</span> : null}

        <div className="poster-container">
          <img src={posterUrl} alt={movie.title} className="movie-poster" />
          {movie.already_watched ? <span className="watched-badge">SEEN</span> : null}
          {awards ? <div className="awards-badge">🏆 {awards}</div> : null}
        </div>

        <div className="card-info">
          <h2 className="movie-title">{movie.title}</h2>
          <div className="movie-subtitle">
            <span className="movie-year">{movie.year || 'Unknown'}</span>
            {movie.imdb_rating ? (
              <span className="rating-badge rating-imdb">★ {movie.imdb_rating}</span>
            ) : null}
            {movie.rt_rating ? (
              <span className="rating-badge rating-rt">🍅 {movie.rt_rating}</span>
            ) : null}
            {!movie.imdb_rating && movie.tmdb_rating ? (
              <span className="rating-badge rating-tmdb">★ {movie.tmdb_rating}</span>
            ) : null}
          </div>

          <div className="movie-meta">
            {genres.map((g) => (
              <span key={g} className="genre-tag">
                {g}
              </span>
            ))}
          </div>

          {directors.length > 0 || cast.length > 0 ? (
            <div className="credits-compact">
              {directors.length > 0 ? (
                <>
                  <strong>Director:</strong> {directors[0]}
                  <br />
                </>
              ) : null}
              {cast.length > 0 ? (
                <>
                  <strong>Cast:</strong> {cast.slice(0, 2).join(', ')}
                </>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      <div className="card-details">
        {overview ? (
          <div className="movie-synopsis">
            <div className="section-label">Synopsis</div>
            <p className="synopsis-text">{overview}</p>
          </div>
        ) : null}

        <div className="movie-reasoning">
          <div className="section-label">Why You'll Love It</div>
          <p className="reasoning-text">"{reasoning}"</p>
        </div>

        {allProviders.length > 0 ? (
          <div className="streaming-section">
            <div className="section-label">Available On</div>
            <div className="streaming-row">
              {allProviders.slice(0, 5).map((p) =>
                p.logo ? (
                  <img
                    key={p.name}
                    src={p.logo}
                    alt={p.name}
                    className="streaming-logo"
                    title={p.name}
                  />
                ) : null
              )}
            </div>
          </div>
        ) : null}

        {sources.length > 0 ? (
          <div className="source-section">
            <div className="section-label">Recommended By</div>
            <div className="source-badges">
              {sources.map((s) => {
                const label = s.toLowerCase();
                const displayName =
                  label === 'claude'
                    ? 'Claude'
                    : label === 'gemini'
                      ? 'Gemini'
                      : label === 'chatgpt'
                        ? 'ChatGPT'
                        : s;
                return (
                  <span key={s} className="source-badge">
                    <span className={`source-dot ${label}`}></span>
                    {displayName}
                  </span>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>
    </motion.div>
  );
}
