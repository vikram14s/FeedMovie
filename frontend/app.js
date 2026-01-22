// FeedMovie Frontend Logic

let recommendations = [];
let currentIndex = 0;
let stats = {
    liked: 0,
    skipped: 0
};
let selectedGenres = [];
let selectedProfiles = [];
let generationTriggered = false;
let totalUnshown = 0;

const API_URL = 'http://localhost:5000/api';

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    const savedGenres = localStorage.getItem('feedmovie_genres');
    const savedProfiles = localStorage.getItem('feedmovie_profiles');

    if (savedGenres) {
        selectedGenres = JSON.parse(savedGenres);
        if (savedProfiles) {
            selectedProfiles = JSON.parse(savedProfiles);
        }

        document.getElementById('change-genres-pill').style.display = 'inline-flex';
        document.getElementById('taste-profile-selection').style.display = 'none';
        document.getElementById('genre-selection').style.display = 'none';
        document.getElementById('loading').style.display = 'flex';
        document.getElementById('stats-bar').style.display = 'flex';

        loadRecommendations(selectedGenres);
    } else {
        const hasProfiles = localStorage.getItem('feedmovie_profiles_completed');

        if (!hasProfiles) {
            await loadTasteProfiles();
            document.getElementById('taste-profile-selection').style.display = 'block';
            document.getElementById('genre-selection').style.display = 'none';
        } else {
            document.getElementById('taste-profile-selection').style.display = 'none';
            document.getElementById('genre-selection').style.display = 'block';
        }

        document.getElementById('loading').style.display = 'none';
        document.getElementById('stats-bar').style.display = 'none';
    }

    setupKeyboardControls();
});

function changeGenres() {
    localStorage.removeItem('feedmovie_genres');
    selectedGenres = [];
    generationTriggered = false;
    location.reload();
}

// =============================================
// TASTE PROFILE FUNCTIONS
// =============================================

async function loadTasteProfiles() {
    try {
        const response = await fetch(`${API_URL}/taste-profiles`);
        const data = await response.json();

        if (data.success && data.profiles) {
            renderTasteProfiles(data.profiles);
        }
    } catch (error) {
        console.error('Error loading taste profiles:', error);
    }
}

function renderTasteProfiles(profiles) {
    const grid = document.getElementById('taste-profiles-grid');

    grid.innerHTML = profiles.map(profile => {
        const movies = profile.representative_movies
            .slice(0, 3)
            .map(m => m.title)
            .join(', ');

        return `
            <div class="profile-card" data-profile-id="${profile.id}" onclick="toggleTasteProfile('${profile.id}')">
                <div class="profile-icon">${profile.icon}</div>
                <div class="profile-name">${profile.name}</div>
                <div class="profile-desc">${profile.description}</div>
            </div>
        `;
    }).join('');
}

function toggleTasteProfile(profileId) {
    const card = document.querySelector(`[data-profile-id="${profileId}"]`);
    const index = selectedProfiles.indexOf(profileId);

    if (index > -1) {
        selectedProfiles.splice(index, 1);
        card.classList.remove('selected');
    } else {
        if (selectedProfiles.length < 2) {
            selectedProfiles.push(profileId);
            card.classList.add('selected');
        }
    }

    const saveBtn = document.getElementById('save-profiles-btn');
    const hint = document.getElementById('profile-hint');

    if (selectedProfiles.length > 0) {
        saveBtn.disabled = false;
        hint.textContent = `${selectedProfiles.length} profile${selectedProfiles.length > 1 ? 's' : ''} selected`;
    } else {
        saveBtn.disabled = true;
        hint.textContent = 'Select at least one profile';
    }
}

async function saveTasteProfiles() {
    try {
        await fetch(`${API_URL}/select-profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_ids: selectedProfiles })
        });

        localStorage.setItem('feedmovie_profiles', JSON.stringify(selectedProfiles));
        localStorage.setItem('feedmovie_profiles_completed', 'true');

        document.getElementById('taste-profile-selection').style.display = 'none';
        document.getElementById('genre-selection').style.display = 'block';
    } catch (error) {
        console.error('Error saving profiles:', error);
    }
}

function skipTasteProfiles() {
    localStorage.setItem('feedmovie_profiles_completed', 'true');
    document.getElementById('taste-profile-selection').style.display = 'none';
    document.getElementById('genre-selection').style.display = 'block';
}

// =============================================
// GENRE SELECTION
// =============================================

function toggleGenre(genre) {
    const btn = document.querySelector(`[data-genre="${genre}"]`);
    const index = selectedGenres.indexOf(genre);

    if (index > -1) {
        selectedGenres.splice(index, 1);
        btn.classList.remove('selected');
    } else {
        selectedGenres.push(genre);
        btn.classList.add('selected');
    }

    const startBtn = document.getElementById('start-btn');
    const hint = document.getElementById('genre-hint');

    if (selectedGenres.length > 0) {
        startBtn.disabled = false;
        hint.textContent = `${selectedGenres.length} genre${selectedGenres.length > 1 ? 's' : ''} selected`;
    } else {
        startBtn.disabled = true;
        hint.textContent = 'Select at least one genre';
    }
}

function startRecommendations() {
    localStorage.setItem('feedmovie_genres', JSON.stringify(selectedGenres));

    document.getElementById('genre-selection').style.display = 'none';
    document.getElementById('loading').style.display = 'flex';
    document.getElementById('stats-bar').style.display = 'flex';
    document.getElementById('change-genres-pill').style.display = 'inline-flex';

    loadRecommendations(selectedGenres);
}

function skipGenreSelection() {
    // Load all recommendations without genre filter
    selectedGenres = [];
    localStorage.setItem('feedmovie_genres', JSON.stringify([]));

    document.getElementById('genre-selection').style.display = 'none';
    document.getElementById('loading').style.display = 'flex';
    document.getElementById('stats-bar').style.display = 'flex';
    document.getElementById('change-genres-pill').style.display = 'inline-flex';

    loadRecommendations([]);
}

// =============================================
// RECOMMENDATIONS
// =============================================

async function loadRecommendations(genres = []) {
    try {
        const genreParam = genres.length > 0 ? `&genres=${genres.join(',')}` : '';
        const response = await fetch(`${API_URL}/recommendations?limit=50${genreParam}`);
        const data = await response.json();

        if (data.success) {
            recommendations = data.recommendations;
            totalUnshown = data.total_unshown;
            currentIndex = 0;

            document.getElementById('loading').style.display = 'none';

            if (recommendations.length === 0) {
                showNoMore();
            } else {
                showCards();
            }

            updateStats();
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
    }
}

function showCards() {
    const container = document.getElementById('card-container');
    container.innerHTML = '';
    container.style.display = 'block';
    document.getElementById('actions').style.display = 'flex';
    document.getElementById('keyboard-hints').style.display = 'block';
    document.getElementById('no-more').style.display = 'none';

    // Show current card
    if (currentIndex < recommendations.length) {
        const card = createMovieCard(recommendations[currentIndex]);
        container.appendChild(card);
    }
}

function createMovieCard(movie) {
    const card = document.createElement('div');
    card.className = 'movie-card';

    const posterUrl = movie.poster_path || 'https://via.placeholder.com/140x210?text=No+Poster';
    const matchScore = movie.score ? Math.round(movie.score * 100) : '?';
    const genres = (movie.genres || []).slice(0, 3);
    const directors = movie.directors || [];
    const cast = movie.cast || [];
    const awards = movie.awards;
    const overview = movie.overview || '';
    const reasoning = movie.reasoning || 'Recommended based on your taste';
    const sources = [...new Set(movie.sources || [])];

    // Ratings
    const imdbRating = movie.imdb_rating;
    const tmdbRating = movie.tmdb_rating;
    const rtRating = movie.rt_rating;

    // Streaming providers
    const streamingProviders = movie.streaming_providers || {};
    const subscription = streamingProviders.subscription || [];
    const rent = streamingProviders.rent || [];
    const allProviders = [...subscription, ...rent.slice(0, 3)];

    card.innerHTML = `
        <div class="card-top">
            <span class="match-badge">${matchScore}% match</span>
            <div class="poster-container">
                <img src="${posterUrl}" alt="${movie.title}" class="movie-poster">
                ${movie.already_watched ? '<span class="watched-badge">SEEN</span>' : ''}
                ${awards && formatAwards(awards) ? `<div class="awards-badge">🏆 ${formatAwards(awards)}</div>` : ''}
            </div>

            <div class="card-info">
                <h2 class="movie-title">${movie.title}</h2>
                <div class="movie-subtitle">
                    <span class="movie-year">${movie.year || 'Unknown'}</span>
                    ${imdbRating ? `<span class="rating-badge rating-imdb">★ ${imdbRating}</span>` : ''}
                    ${rtRating ? `<span class="rating-badge rating-rt">🍅 ${rtRating}</span>` : ''}
                    ${!imdbRating && tmdbRating ? `<span class="rating-badge rating-tmdb">★ ${tmdbRating}</span>` : ''}
                </div>

                <div class="movie-meta">
                    ${genres.map(g => `<span class="genre-tag">${g}</span>`).join('')}
                </div>

                ${directors.length > 0 || cast.length > 0 ? `
                    <div class="credits-compact">
                        ${directors.length > 0 ? `<strong>Director:</strong> ${directors[0]}<br>` : ''}
                        ${cast.length > 0 ? `<strong>Cast:</strong> ${cast.slice(0, 2).join(', ')}` : ''}
                    </div>
                ` : ''}
            </div>
        </div>

        <div class="card-details">
            ${overview ? `
                <div class="movie-synopsis">
                    <div class="section-label">Synopsis</div>
                    <p class="synopsis-text">${overview}</p>
                </div>
            ` : ''}

            <div class="movie-reasoning">
                <div class="section-label">Why You'll Love It</div>
                <p class="reasoning-text">"${reasoning}"</p>
            </div>

            ${allProviders.length > 0 ? `
                <div class="streaming-section">
                    <div class="section-label">Available On</div>
                    <div class="streaming-row">
                        ${allProviders.slice(0, 5).map(p =>
                            p.logo ? `<img src="${p.logo}" alt="${p.name}" class="streaming-logo" title="${p.name}">` : ''
                        ).join('')}
                    </div>
                </div>
            ` : ''}

            ${sources.length > 0 ? `
                <div class="source-section">
                    <div class="section-label">Recommended By</div>
                    <div class="source-badges">
                        ${sources.map(s => {
                            const label = s.toLowerCase();
                            const displayName = label === 'claude' ? 'Claude' : label === 'gemini' ? 'Gemini' : label === 'chatgpt' ? 'ChatGPT' : s;
                            return `<span class="source-badge"><span class="source-dot ${label}"></span>${displayName}</span>`;
                        }).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;

    return card;
}

function formatAwards(awards) {
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

// =============================================
// SWIPE ACTIONS
// =============================================

async function swipeLeft() {
    if (currentIndex >= recommendations.length) return;

    const movie = recommendations[currentIndex];
    const card = document.querySelector('.movie-card');

    if (card) {
        card.classList.add('swipe-left');
    }

    try {
        await fetch(`${API_URL}/swipe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tmdb_id: movie.tmdb_id, action: 'left' })
        });
    } catch (error) {
        console.error('Error recording swipe:', error);
    }

    stats.skipped++;
    currentIndex++;

    setTimeout(() => {
        if (currentIndex < recommendations.length) {
            showCards();
        } else {
            showNoMore();
        }
        updateStats();
        checkPreemptiveGeneration();
    }, 400);
}

async function swipeRight() {
    if (currentIndex >= recommendations.length) return;

    const movie = recommendations[currentIndex];
    const card = document.querySelector('.movie-card');

    if (card) {
        card.classList.add('swipe-right');
    }

    try {
        await fetch(`${API_URL}/swipe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tmdb_id: movie.tmdb_id, action: 'right' })
        });
    } catch (error) {
        console.error('Error recording swipe:', error);
    }

    stats.liked++;
    currentIndex++;

    setTimeout(() => {
        if (currentIndex < recommendations.length) {
            showCards();
        } else {
            showNoMore();
        }
        updateStats();
        checkPreemptiveGeneration();
        updateWatchlistBadge();
    }, 400);
}

function updateStats() {
    document.getElementById('liked-count').textContent = stats.liked;
    document.getElementById('skipped-count').textContent = stats.skipped;

    const remaining = recommendations.length - currentIndex;
    document.getElementById('remaining-count').textContent = remaining;
}

function showNoMore() {
    document.getElementById('card-container').style.display = 'none';
    document.getElementById('actions').style.display = 'none';
    document.getElementById('keyboard-hints').style.display = 'none';
    document.getElementById('no-more').style.display = 'block';
}

// =============================================
// TAB SWITCHING
// =============================================

function switchTab(tab) {
    const discoverPill = document.getElementById('discover-pill');
    const watchlistPill = document.getElementById('watchlist-pill');

    if (tab === 'discover') {
        discoverPill.classList.add('active');
        watchlistPill.classList.remove('active');

        document.getElementById('watchlist-view').style.display = 'none';
        document.getElementById('stats-bar').style.display = 'flex';

        if (recommendations.length > 0 && currentIndex < recommendations.length) {
            document.getElementById('card-container').style.display = 'block';
            document.getElementById('actions').style.display = 'flex';
            document.getElementById('keyboard-hints').style.display = 'block';
        } else if (recommendations.length > 0) {
            document.getElementById('no-more').style.display = 'block';
        }
    } else if (tab === 'watchlist') {
        discoverPill.classList.remove('active');
        watchlistPill.classList.add('active');

        document.getElementById('card-container').style.display = 'none';
        document.getElementById('actions').style.display = 'none';
        document.getElementById('keyboard-hints').style.display = 'none';
        document.getElementById('no-more').style.display = 'none';
        document.getElementById('stats-bar').style.display = 'none';

        document.getElementById('watchlist-view').style.display = 'block';
        loadWatchlist();
    }
}

async function loadWatchlist() {
    try {
        const response = await fetch(`${API_URL}/watchlist`);
        const data = await response.json();

        if (data.success) {
            const grid = document.getElementById('watchlist-grid');
            const empty = document.getElementById('watchlist-empty');

            if (data.watchlist.length === 0) {
                grid.innerHTML = '';
                empty.style.display = 'block';
            } else {
                empty.style.display = 'none';
                grid.innerHTML = data.watchlist.map(movie => createWatchlistItem(movie)).join('');
            }

            updateWatchlistBadge(data.watchlist.length);
        }
    } catch (error) {
        console.error('Error loading watchlist:', error);
    }
}

function createWatchlistItem(movie) {
    const posterUrl = movie.poster_path || 'https://via.placeholder.com/80x120?text=No+Poster';
    const streamingProviders = movie.streaming_providers || {};
    const allProviders = [...(streamingProviders.subscription || []), ...(streamingProviders.rent || [])];

    return `
        <div class="watchlist-item">
            <img src="${posterUrl}" alt="${movie.title}" class="watchlist-poster">
            <div class="watchlist-info">
                <h3 class="watchlist-title">${movie.title}</h3>
                <p class="watchlist-meta">${movie.year} • ${(movie.genres || []).slice(0, 2).join(', ')}</p>
                <div class="watchlist-streaming">
                    ${allProviders.slice(0, 3).map(p =>
                        p.logo ? `<img src="${p.logo}" alt="${p.name}" title="${p.name}">` : ''
                    ).join('')}
                </div>
            </div>
            <button class="remove-btn" onclick="removeFromWatchlist(${movie.tmdb_id})" title="Remove">
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
}

async function removeFromWatchlist(tmdbId) {
    try {
        await fetch(`${API_URL}/watchlist/${tmdbId}`, { method: 'DELETE' });
        loadWatchlist();
    } catch (error) {
        console.error('Error removing from watchlist:', error);
    }
}

function updateWatchlistBadge(count) {
    const badge = document.getElementById('watchlist-badge');
    if (count && count > 0) {
        badge.textContent = count;
        badge.style.display = 'inline';
    } else {
        badge.style.display = 'none';
    }
}

// =============================================
// ALREADY SEEN MODAL
// =============================================

let selectedRating = 0;

function showAlreadySeenModal() {
    if (currentIndex >= recommendations.length) return;

    const movie = recommendations[currentIndex];
    document.getElementById('modal-movie-title').textContent = movie.title;
    document.getElementById('already-seen-modal').style.display = 'flex';

    selectedRating = 0;
    updateStarDisplay();
    document.getElementById('selected-rating').textContent = '-';
    document.getElementById('submit-rating-btn').disabled = true;
}

function closeModal() {
    document.getElementById('already-seen-modal').style.display = 'none';
}

function handleStarClick(event, star) {
    const rect = event.target.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const isHalf = x < rect.width / 2;

    selectedRating = isHalf ? star - 0.5 : star;
    updateStarDisplay();
    document.getElementById('selected-rating').textContent = selectedRating.toFixed(1);
    document.getElementById('submit-rating-btn').disabled = false;
}

function updateStarDisplay() {
    const stars = document.querySelectorAll('.star');
    stars.forEach((star, index) => {
        const starValue = index + 1;
        if (selectedRating >= starValue) {
            star.classList.add('filled');
        } else {
            star.classList.remove('filled');
        }
    });
}

async function submitRating() {
    if (selectedRating === 0) return;

    const movie = recommendations[currentIndex];

    try {
        await fetch(`${API_URL}/add-rating`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tmdb_id: movie.tmdb_id,
                title: movie.title,
                year: movie.year,
                rating: selectedRating
            })
        });

        closeModal();
        swipeLeft();
    } catch (error) {
        console.error('Error submitting rating:', error);
    }
}

// =============================================
// KEYBOARD CONTROLS
// =============================================

function setupKeyboardControls() {
    document.addEventListener('keydown', (e) => {
        if (document.getElementById('already-seen-modal').style.display === 'flex') {
            if (e.key === 'Escape') closeModal();
            return;
        }

        if (e.key === 'ArrowLeft') swipeLeft();
        else if (e.key === 'ArrowRight') swipeRight();
        else if (e.key === 's' || e.key === 'S') showAlreadySeenModal();
    });
}

// =============================================
// GENERATION
// =============================================

function checkPreemptiveGeneration() {
    const remaining = totalUnshown - currentIndex;
    if (remaining < 10 && !generationTriggered) {
        generationTriggered = true;
        fetch(`${API_URL}/generate-more`, { method: 'POST' });
    }
}

async function generateMoreRecommendations() {
    document.getElementById('no-more').style.display = 'none';
    document.getElementById('loading').style.display = 'flex';

    try {
        await fetch(`${API_URL}/generate-more`, { method: 'POST' });
        setTimeout(() => {
            loadRecommendations(selectedGenres);
        }, 3000);
    } catch (error) {
        console.error('Error generating recommendations:', error);
    }
}
