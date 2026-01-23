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
let watchlistCount = 0;

// Auth state
let authToken = null;
let currentUser = null;

// Onboarding state
let onboardingMovies = [];
let onboardingIndex = 0;
let onboardingRatings = [];

const API_URL = 'http://localhost:5000/api';

// =============================================
// AUTH HELPERS
// =============================================

function getAuthHeaders() {
    return authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
}

function saveToken(token) {
    authToken = token;
    localStorage.setItem('feedmovie_token', token);
}

function clearToken() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('feedmovie_token');
}

// =============================================
// INITIALIZATION
// =============================================

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Check for existing token
    const savedToken = localStorage.getItem('feedmovie_token');

    if (savedToken) {
        authToken = savedToken;
        const user = await checkAuth();

        if (user) {
            currentUser = user;

            if (!user.onboarding_completed) {
                // Show onboarding
                showOnboardingScreen();
            } else {
                // Show main app
                showMainApp();
            }
        } else {
            // Token invalid, show auth
            clearToken();
            showAuthScreen();
        }
    } else {
        // No token, show auth
        showAuthScreen();
    }

    setupKeyboardControls();
});

async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            return data.user;
        }
        return null;
    } catch (error) {
        console.error('Auth check failed:', error);
        return null;
    }
}

// =============================================
// SCREEN NAVIGATION
// =============================================

function showAuthScreen() {
    document.getElementById('auth-screen').style.display = 'flex';
    document.getElementById('onboarding-screen').style.display = 'none';
    document.getElementById('main-app').style.display = 'none';
}

function showOnboardingScreen() {
    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('onboarding-screen').style.display = 'block';
    document.getElementById('main-app').style.display = 'none';
    showOnboardingPath();
}

function showMainApp() {
    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('onboarding-screen').style.display = 'none';
    document.getElementById('main-app').style.display = 'block';
    initializeMainApp();
}

async function initializeMainApp() {
    // Fetch initial watchlist count
    try {
        const response = await fetch(`${API_URL}/watchlist`, { headers: getAuthHeaders() });
        const data = await response.json();
        if (data.success) {
            watchlistCount = data.watchlist.length;
            updateWatchlistBadge(watchlistCount);
        }
    } catch (e) { /* ignore */ }

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
}

// =============================================
// AUTH FORMS
// =============================================

function showLoginForm() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('login-error').classList.remove('visible');
}

function showRegisterForm() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.getElementById('register-error').classList.remove('visible');
}

async function handleLogin() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    const btn = document.getElementById('login-btn');

    if (!email || !password) {
        errorEl.textContent = 'Please fill in all fields';
        errorEl.classList.add('visible');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Signing in...';

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok && data.token) {
            saveToken(data.token);
            currentUser = data.user;

            if (!currentUser.onboarding_completed) {
                showOnboardingScreen();
            } else {
                showMainApp();
            }
        } else {
            errorEl.textContent = data.error || 'Login failed';
            errorEl.classList.add('visible');
        }
    } catch (error) {
        console.error('Login error:', error);
        errorEl.textContent = 'Connection error. Please try again.';
        errorEl.classList.add('visible');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign In';
    }
}

async function handleRegister() {
    const username = document.getElementById('register-username').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const errorEl = document.getElementById('register-error');
    const btn = document.getElementById('register-btn');

    if (!username || !email || !password) {
        errorEl.textContent = 'Please fill in all fields';
        errorEl.classList.add('visible');
        return;
    }

    if (password.length < 6) {
        errorEl.textContent = 'Password must be at least 6 characters';
        errorEl.classList.add('visible');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Creating account...';

    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok && data.token) {
            saveToken(data.token);
            currentUser = data.user;
            showOnboardingScreen();
        } else {
            errorEl.textContent = data.error || 'Registration failed';
            errorEl.classList.add('visible');
        }
    } catch (error) {
        console.error('Registration error:', error);
        errorEl.textContent = 'Connection error. Please try again.';
        errorEl.classList.add('visible');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Account';
    }
}

// =============================================
// ONBOARDING
// =============================================

function showOnboardingPath() {
    document.getElementById('onboarding-path').style.display = 'block';
    document.getElementById('onboarding-letterboxd').style.display = 'none';
    document.getElementById('onboarding-swipe').style.display = 'none';
    document.getElementById('onboarding-loading').style.display = 'none';
}

function selectOnboardingPath(path) {
    if (path === 'letterboxd') {
        document.getElementById('onboarding-path').style.display = 'none';
        document.getElementById('onboarding-letterboxd').style.display = 'block';
    } else {
        startSwipeOnboarding();
    }
}

async function importLetterboxd() {
    const username = document.getElementById('letterboxd-username').value.trim();
    const errorEl = document.getElementById('letterboxd-error');
    const btn = document.getElementById('import-btn');

    if (!username) {
        errorEl.textContent = 'Please enter your Letterboxd username';
        errorEl.classList.add('visible');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Importing...';

    try {
        const response = await fetch(`${API_URL}/onboarding/letterboxd`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({ letterboxd_username: username })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            await completeOnboarding();
        } else {
            errorEl.textContent = data.error || 'Import failed. Check your username.';
            errorEl.classList.add('visible');
        }
    } catch (error) {
        console.error('Letterboxd import error:', error);
        errorEl.textContent = 'Connection error. Please try again.';
        errorEl.classList.add('visible');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Import Ratings';
    }
}

async function startSwipeOnboarding() {
    document.getElementById('onboarding-path').style.display = 'none';
    document.getElementById('onboarding-loading').style.display = 'block';
    document.getElementById('onboarding-loading-text').textContent = 'Loading popular movies...';

    try {
        const response = await fetch(`${API_URL}/onboarding/movies`, {
            headers: getAuthHeaders()
        });

        const data = await response.json();

        if (data.success && data.movies) {
            onboardingMovies = data.movies;
            onboardingIndex = 0;
            onboardingRatings = [];

            document.getElementById('onboarding-loading').style.display = 'none';
            document.getElementById('onboarding-swipe').style.display = 'block';

            renderOnboardingProgress();
            renderOnboardingCard();
        }
    } catch (error) {
        console.error('Error loading onboarding movies:', error);
    }
}

function renderOnboardingProgress() {
    const container = document.getElementById('onboarding-progress');
    const total = onboardingMovies.length;

    container.innerHTML = Array.from({ length: total }, (_, i) => {
        let className = 'progress-dot';
        if (i < onboardingIndex) className += ' completed';
        if (i === onboardingIndex) className += ' active';
        return `<div class="${className}"></div>`;
    }).join('');

    document.getElementById('onboarding-counter').textContent =
        `Movie ${onboardingIndex + 1} of ${total}`;
}

// Store ratings by tmdb_id so we can update them
let onboardingRatingsMap = {};
let currentOnboardingRating = 0;

function renderOnboardingCard() {
    if (onboardingIndex >= onboardingMovies.length) {
        finishSwipeOnboarding();
        return;
    }

    const movie = onboardingMovies[onboardingIndex];
    const container = document.getElementById('onboarding-card-container');

    // Check if we already have a rating for this movie
    currentOnboardingRating = onboardingRatingsMap[movie.tmdb_id] || 0;

    container.innerHTML = `
        <div class="onboarding-card">
            <img src="${movie.poster_path || 'https://via.placeholder.com/160x240?text=No+Poster'}"
                 alt="${movie.title}"
                 class="onboarding-movie-poster">
            <h3 class="onboarding-movie-title">${movie.title}</h3>
            <p class="onboarding-movie-year">${movie.year || ''}</p>
            <div class="onboarding-stars" id="onboarding-stars-container">
                ${[1, 2, 3, 4, 5].map(star => `
                    <span class="onboarding-star" data-star="${star}">★</span>
                `).join('')}
            </div>
            <div class="onboarding-rating-display" id="onboarding-rating-display">
                ${currentOnboardingRating > 0 ? currentOnboardingRating + ' / 5' : 'Tap stars to rate (supports half stars)'}
            </div>
            <div class="onboarding-nav">
                <button class="onboarding-nav-btn" onclick="prevOnboardingMovie()" ${onboardingIndex === 0 ? 'disabled' : ''}>
                    ← Back
                </button>
                <button class="onboarding-skip-btn" onclick="skipOnboardingMovie()">Haven't seen it</button>
                <button class="onboarding-nav-btn primary" onclick="nextOnboardingMovie()">
                    Next →
                </button>
            </div>
        </div>
    `;

    // Add click handlers for half-star support
    setupOnboardingStarHandlers();
    updateOnboardingStarDisplay();
}

function setupOnboardingStarHandlers() {
    const stars = document.querySelectorAll('.onboarding-star');
    stars.forEach((star, index) => {
        star.addEventListener('click', (e) => {
            const rect = star.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const isLeftHalf = clickX < rect.width / 2;

            // Left half = x.5, right half = x.0
            const rating = isLeftHalf ? index + 0.5 : index + 1;
            setOnboardingRating(rating);
        });
    });
}

function setOnboardingRating(rating) {
    const movie = onboardingMovies[onboardingIndex];
    currentOnboardingRating = rating;
    onboardingRatingsMap[movie.tmdb_id] = rating;

    updateOnboardingStarDisplay();

    // Update rating display
    document.getElementById('onboarding-rating-display').textContent = rating + ' / 5';
}

function updateOnboardingStarDisplay() {
    const stars = document.querySelectorAll('.onboarding-star');
    stars.forEach((star, i) => {
        const starNum = i + 1;
        star.classList.remove('filled', 'half');

        if (currentOnboardingRating >= starNum) {
            star.classList.add('filled');
        } else if (currentOnboardingRating >= starNum - 0.5) {
            star.classList.add('half');
        }
    });
}

function nextOnboardingMovie() {
    onboardingIndex++;
    if (onboardingIndex >= onboardingMovies.length) {
        finishSwipeOnboarding();
        return;
    }
    renderOnboardingProgress();
    renderOnboardingCard();
}

function prevOnboardingMovie() {
    if (onboardingIndex > 0) {
        onboardingIndex--;
        renderOnboardingProgress();
        renderOnboardingCard();
    }
}

function skipOnboardingMovie() {
    // Remove any rating for this movie
    const movie = onboardingMovies[onboardingIndex];
    delete onboardingRatingsMap[movie.tmdb_id];

    nextOnboardingMovie();
}

async function finishSwipeOnboarding() {
    document.getElementById('onboarding-swipe').style.display = 'none';
    document.getElementById('onboarding-loading').style.display = 'block';
    document.getElementById('onboarding-loading-text').textContent = 'Saving your ratings...';

    try {
        // Convert ratings map to array
        const ratings = Object.entries(onboardingRatingsMap).map(([tmdb_id, rating]) => ({
            tmdb_id: parseInt(tmdb_id),
            rating: rating
        }));

        // Save ratings if any
        if (ratings.length > 0) {
            await fetch(`${API_URL}/onboarding/swipe-ratings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify({ ratings })
            });
        }

        await completeOnboarding();
    } catch (error) {
        console.error('Error saving onboarding ratings:', error);
    }
}

async function completeOnboarding() {
    document.getElementById('onboarding-loading').style.display = 'block';
    document.getElementById('onboarding-loading-text').textContent = 'Generating your personalized recommendations...';

    try {
        await fetch(`${API_URL}/onboarding/complete`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        // Update user state
        if (currentUser) {
            currentUser.onboarding_completed = true;
        }

        // Show main app
        showMainApp();
    } catch (error) {
        console.error('Error completing onboarding:', error);
    }
}

function changeGenres() {
    localStorage.removeItem('feedmovie_genres');
    selectedGenres = [];
    generationTriggered = false;

    // Show genre selection without full reload
    document.getElementById('card-container').style.display = 'none';
    document.getElementById('actions').style.display = 'none';
    document.getElementById('keyboard-hints').style.display = 'none';
    document.getElementById('no-more').style.display = 'none';
    document.getElementById('stats-bar').style.display = 'none';
    document.getElementById('genre-selection').style.display = 'block';
}

// =============================================
// TASTE PROFILE FUNCTIONS
// =============================================

async function loadTasteProfiles() {
    try {
        const response = await fetch(`${API_URL}/taste-profiles`, {
            headers: getAuthHeaders()
        });
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
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
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
        const response = await fetch(`${API_URL}/recommendations?limit=50${genreParam}`, {
            headers: getAuthHeaders()
        });
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
    const isFriendRec = reasoning.toLowerCase().includes('friend') || sources.some(s => s.toLowerCase().includes('friend'));

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
            ${isFriendRec ? '<span class="friend-rec-badge">friend rec</span>' : ''}
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
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
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
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
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
        watchlistCount++;
        updateWatchlistBadge(watchlistCount);
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
    // Get all pills
    const pills = ['discover', 'feed', 'watchlist', 'profile'];
    pills.forEach(p => {
        const pill = document.getElementById(`${p}-pill`);
        if (pill) {
            pill.classList.remove('active');
        }
    });

    // Activate selected pill
    const activePill = document.getElementById(`${tab}-pill`);
    if (activePill) {
        activePill.classList.add('active');
    }

    // Hide all views
    document.getElementById('card-container').style.display = 'none';
    document.getElementById('actions').style.display = 'none';
    document.getElementById('keyboard-hints').style.display = 'none';
    document.getElementById('no-more').style.display = 'none';
    document.getElementById('stats-bar').style.display = 'none';
    document.getElementById('watchlist-view').style.display = 'none';
    document.getElementById('feed-view').style.display = 'none';
    document.getElementById('profile-view').style.display = 'none';
    document.getElementById('taste-profile-selection').style.display = 'none';
    document.getElementById('genre-selection').style.display = 'none';

    if (tab === 'discover') {
        document.getElementById('stats-bar').style.display = 'flex';

        if (recommendations.length > 0 && currentIndex < recommendations.length) {
            document.getElementById('card-container').style.display = 'block';
            document.getElementById('actions').style.display = 'flex';
            document.getElementById('keyboard-hints').style.display = 'block';
        } else if (recommendations.length > 0) {
            document.getElementById('no-more').style.display = 'block';
        } else {
            // No recommendations loaded yet - show genre selection if needed
            const savedGenres = localStorage.getItem('feedmovie_genres');
            if (!savedGenres) {
                document.getElementById('genre-selection').style.display = 'block';
            }
        }
    } else if (tab === 'feed') {
        document.getElementById('feed-view').style.display = 'block';
        loadFeed();
    } else if (tab === 'watchlist') {
        document.getElementById('watchlist-view').style.display = 'block';
        loadWatchlist();
    } else if (tab === 'profile') {
        document.getElementById('profile-view').style.display = 'block';
        loadProfile();
    }
}

async function loadWatchlist() {
    try {
        const response = await fetch(`${API_URL}/watchlist`, {
            headers: getAuthHeaders()
        });
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

            watchlistCount = data.watchlist.length;
            updateWatchlistBadge(watchlistCount);
        }
    } catch (error) {
        console.error('Error loading watchlist:', error);
    }
}

function createWatchlistItem(movie) {
    const posterUrl = movie.poster_path || 'https://via.placeholder.com/80x120?text=No+Poster';
    const streamingProviders = movie.streaming_providers || {};
    const allProviders = [...(streamingProviders.subscription || []), ...(streamingProviders.rent || [])];
    const escapedTitle = movie.title.replace(/'/g, "\\'");

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
            <div class="watchlist-actions">
                <button class="mark-seen-btn" onclick="openMarkSeenModal(${movie.tmdb_id}, '${escapedTitle}')" title="Mark as watched">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                    </svg>
                    Watched
                </button>
                <button class="remove-btn" onclick="removeFromWatchlist(${movie.tmdb_id})" title="Remove">
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        </div>
    `;
}

async function removeFromWatchlist(tmdbId) {
    try {
        await fetch(`${API_URL}/watchlist/${tmdbId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
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
    const reviewText = document.getElementById('review-text').value.trim();

    try {
        await fetch(`${API_URL}/add-rating`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                tmdb_id: movie.tmdb_id,
                title: movie.title,
                year: movie.year,
                rating: selectedRating,
                review_text: reviewText
            })
        });

        // Clear review text for next use
        document.getElementById('review-text').value = '';
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
        // Handle ESC for all modals
        if (e.key === 'Escape') {
            if (document.getElementById('already-seen-modal').style.display === 'flex') {
                closeModal();
                return;
            }
            if (document.getElementById('search-modal').style.display === 'flex') {
                closeSearchModal();
                return;
            }
            if (document.getElementById('edit-bio-modal').style.display === 'flex') {
                closeEditBioModal();
                return;
            }
            if (document.getElementById('rate-search-modal').style.display === 'flex') {
                closeRateSearchModal();
                return;
            }
            if (document.getElementById('mark-seen-modal').style.display === 'flex') {
                closeMarkSeenModal();
                return;
            }
        }

        // Don't handle swipe keys if any modal is open or if we're in an input
        if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') {
            return;
        }

        if (document.getElementById('already-seen-modal').style.display === 'flex' ||
            document.getElementById('search-modal').style.display === 'flex' ||
            document.getElementById('edit-bio-modal').style.display === 'flex' ||
            document.getElementById('rate-search-modal').style.display === 'flex' ||
            document.getElementById('mark-seen-modal').style.display === 'flex') {
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
        fetch(`${API_URL}/generate-more`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
    }
}

async function generateMoreRecommendations() {
    document.getElementById('no-more').style.display = 'none';
    document.getElementById('loading').style.display = 'flex';

    try {
        await fetch(`${API_URL}/generate-more`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        setTimeout(() => {
            loadRecommendations(selectedGenres);
        }, 3000);
    } catch (error) {
        console.error('Error generating recommendations:', error);
    }
}

// =============================================
// LOGOUT
// =============================================

function logout() {
    clearToken();

    // Clear all localStorage items for this app
    localStorage.removeItem('feedmovie_genres');
    localStorage.removeItem('feedmovie_profiles');
    localStorage.removeItem('feedmovie_profiles_completed');

    // Reset all cached data
    profileData = null;
    feedItems = [];
    recommendations = [];
    watchlistCount = 0;
    currentIndex = 0;
    stats = { liked: 0, skipped: 0 };
    selectedGenres = [];
    selectedProfiles = [];
    totalUnshown = 0;
    generationTriggered = false;

    // Reset onboarding data
    onboardingMovies = [];
    onboardingRatings = [];
    if (typeof onboardingRatingsMap !== 'undefined') {
        onboardingRatingsMap = {};
    }
    onboardingIndex = 0;
    if (typeof currentOnboardingRating !== 'undefined') {
        currentOnboardingRating = 0;
    }

    // Clear UI elements
    const elementsToEmpty = [
        'profile-activity-list', 'profile-friends-list', 'profile-library-grid',
        'feed-list', 'watchlist-grid', 'card-container'
    ];
    elementsToEmpty.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });

    showAuthScreen();
}

// =============================================
// FEED
// =============================================

let feedItems = [];

async function loadFeed() {
    document.getElementById('feed-loading').style.display = 'flex';
    document.getElementById('feed-empty').style.display = 'none';
    document.getElementById('feed-list').innerHTML = '';

    try {
        const response = await fetch(`${API_URL}/feed`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        document.getElementById('feed-loading').style.display = 'none';

        if (data.success && data.activities && data.activities.length > 0) {
            feedItems = data.activities;
            renderFeed(feedItems);
        } else {
            document.getElementById('feed-empty').style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading feed:', error);
        document.getElementById('feed-loading').style.display = 'none';
        document.getElementById('feed-empty').style.display = 'block';
    }
}

function renderFeed(items) {
    const container = document.getElementById('feed-list');
    container.innerHTML = items.map(item => createFeedItem(item)).join('');
}

function createFeedItem(item) {
    const posterUrl = item.movie?.poster_path || 'https://via.placeholder.com/80x120?text=No+Poster';
    const avatar = item.user?.username?.charAt(0).toUpperCase() || '?';
    const username = item.user?.username || 'Unknown';
    const timeAgo = formatTimeAgo(item.created_at);
    const rating = item.rating || 0;
    const reviewText = item.review_text || '';
    const movieTitle = item.movie?.title || 'Unknown Movie';
    const movieYear = item.movie?.year || '';
    const genres = (item.movie?.genres || []).slice(0, 2).join(', ');
    const likeCount = item.like_count || 0;
    const isLiked = item.is_liked || false;

    const starsHtml = Array.from({ length: 5 }, (_, i) =>
        `<span class="star ${i < rating ? '' : 'empty'}">★</span>`
    ).join('');

    return `
        <div class="feed-item" data-activity-id="${item.id}">
            <div class="feed-header">
                <div class="feed-avatar">${avatar}</div>
                <div class="feed-user-info">
                    <div class="feed-username">${username}</div>
                    <div class="feed-action-text">rated a movie</div>
                </div>
                <div class="feed-time">${timeAgo}</div>
            </div>
            <div class="feed-movie">
                <img src="${posterUrl}" alt="${movieTitle}" class="feed-movie-poster">
                <div class="feed-movie-info">
                    <div class="feed-movie-title">${movieTitle}</div>
                    <div class="feed-movie-meta">${movieYear}${genres ? ' • ' + genres : ''}</div>
                    <div class="feed-rating">${starsHtml}</div>
                    ${reviewText ? `<div class="feed-review-text">"${reviewText}"</div>` : ''}
                </div>
            </div>
            <div class="feed-actions">
                <button class="feed-action-btn ${isLiked ? 'liked' : ''}" onclick="toggleFeedLike(${item.id})">
                    <svg fill="${isLiked ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                    </svg>
                    ${likeCount > 0 ? likeCount : ''}
                </button>
                <button class="feed-action-btn" onclick="addFeedMovieToWatchlist(${item.movie?.tmdb_id}, '${movieTitle.replace(/'/g, "\\'")}')">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                    </svg>
                    Watchlist
                </button>
            </div>
        </div>
    `;
}

function formatTimeAgo(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
}

async function toggleFeedLike(activityId) {
    try {
        await fetch(`${API_URL}/feed/${activityId}/like`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        // Reload feed to get updated like status
        loadFeed();
    } catch (error) {
        console.error('Error toggling like:', error);
    }
}

async function addFeedMovieToWatchlist(tmdbId, title) {
    try {
        await fetch(`${API_URL}/feed/${tmdbId}/watchlist`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            }
        });
        alert(`Added "${title}" to your watchlist!`);
        watchlistCount++;
        updateWatchlistBadge(watchlistCount);
    } catch (error) {
        console.error('Error adding to watchlist:', error);
    }
}

// =============================================
// PROFILE
// =============================================

let profileData = null;

async function loadProfile() {
    try {
        // Load profile, library, and friends in parallel
        const [profileRes, libraryRes, friendsRes] = await Promise.all([
            fetch(`${API_URL}/profile`, { headers: getAuthHeaders() }),
            fetch(`${API_URL}/profile/library`, { headers: getAuthHeaders() }),
            fetch(`${API_URL}/profile/friends`, { headers: getAuthHeaders() })
        ]);

        const profileData = await profileRes.json();
        const libraryData = await libraryRes.json();
        const friendsData = await friendsRes.json();

        if (profileData.success && profileData.profile) {
            renderProfile(profileData.profile);
        }

        if (libraryData.success) {
            renderLibrary(libraryData.library);
        }

        if (friendsData.success) {
            renderFriends(friendsData.friends);
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

function renderProfile(profile) {
    const username = profile.username || currentUser?.username || 'User';
    const initial = username.charAt(0).toUpperCase();

    document.getElementById('profile-avatar').textContent = initial;
    document.getElementById('profile-username').textContent = username;
    document.getElementById('profile-bio').textContent = profile.bio || 'Add a bio to tell others about your taste';

    // Stats from profile.stats
    const stats = profile.stats || {};
    document.getElementById('profile-watched-count').textContent = stats.movies_watched || 0;
    document.getElementById('profile-avg-rating').textContent = stats.avg_rating ? stats.avg_rating.toFixed(1) : '-';
    document.getElementById('profile-fav-genre').textContent = stats.favorite_genres?.[0] || '-';

    // Store for later
    profileData = profile;

    // Recent activity
    const activityList = document.getElementById('profile-activity-list');
    const activityEmpty = document.getElementById('profile-activity-empty');

    if (profile.recent_activity && profile.recent_activity.length > 0) {
        activityEmpty.style.display = 'none';
        activityList.innerHTML = profile.recent_activity.map(activity => {
            const movie = activity.movie || {};
            const posterUrl = movie.poster_path || 'https://via.placeholder.com/48x72?text=?';
            const stars = '★'.repeat(Math.floor(activity.rating || 0)) + '☆'.repeat(5 - Math.floor(activity.rating || 0));
            return `
                <div class="profile-activity-item">
                    <img src="${posterUrl}" alt="${movie.title}" class="profile-activity-poster">
                    <div class="profile-activity-info">
                        <div class="profile-activity-title">${movie.title || 'Unknown'}</div>
                        <div class="profile-activity-detail">${stars} • ${formatTimeAgo(activity.created_at)}</div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        activityList.innerHTML = '';
        activityEmpty.style.display = 'block';
    }
}

function renderLibrary(library) {
    const libraryGrid = document.getElementById('profile-library-grid');
    const libraryEmpty = document.getElementById('profile-library-empty');

    if (library && library.length > 0) {
        libraryEmpty.style.display = 'none';
        libraryGrid.innerHTML = library.slice(0, 20).map(item => {
            const movie = item.movie || {};
            const posterUrl = movie.poster_path || 'https://via.placeholder.com/80x120?text=?';
            return `
                <div class="library-item">
                    <img src="${posterUrl}" alt="${movie.title}" class="library-poster" title="${movie.title} (${movie.year})">
                    <div class="library-rating">★ ${item.rating}</div>
                </div>
            `;
        }).join('');
    } else {
        libraryGrid.innerHTML = '';
        libraryEmpty.style.display = 'block';
    }
}

function renderFriends(friends) {
    const friendsList = document.getElementById('profile-friends-list');
    const friendsEmpty = document.getElementById('profile-friends-empty');

    if (friends && friends.length > 0) {
        friendsEmpty.style.display = 'none';
        friendsList.innerHTML = '<div class="friends-list">' + friends.map(friend => {
            const initial = (friend.name || 'F').charAt(0).toUpperCase();
            const score = friend.compatibility_score ? `${Math.round(friend.compatibility_score * 100)}%` : '';
            return `
                <div class="friend-item">
                    <div class="friend-avatar">${initial}</div>
                    <span class="friend-name">${friend.name}</span>
                    ${score ? `<span class="friend-score">${score}</span>` : ''}
                </div>
            `;
        }).join('') + '</div>';
    } else {
        friendsList.innerHTML = '';
        friendsEmpty.style.display = 'block';
    }
}

function openEditBioModal() {
    document.getElementById('bio-input').value = profileData?.bio || '';
    document.getElementById('edit-bio-modal').style.display = 'flex';
}

function closeEditBioModal() {
    document.getElementById('edit-bio-modal').style.display = 'none';
}

async function saveBio() {
    const bio = document.getElementById('bio-input').value.trim();

    try {
        await fetch(`${API_URL}/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({ bio })
        });

        if (profileData) {
            profileData.bio = bio;
        }
        document.getElementById('profile-bio').textContent = bio || 'Add a bio to tell others about your taste';
        closeEditBioModal();
    } catch (error) {
        console.error('Error saving bio:', error);
    }
}

// =============================================
// SEARCH
// =============================================

let searchTimeout = null;
let searchSelectedMovie = null;
let searchRating = 0;

function openSearchModal() {
    document.getElementById('search-modal').style.display = 'flex';
    document.getElementById('search-input').value = '';
    document.getElementById('search-results').innerHTML = '<div class="search-empty">Start typing to search for movies</div>';
    document.getElementById('search-input').focus();
}

function closeSearchModal() {
    document.getElementById('search-modal').style.display = 'none';
}

function handleSearchInput(event) {
    const query = event.target.value.trim();

    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }

    if (query.length < 2) {
        document.getElementById('search-results').innerHTML = '<div class="search-empty">Start typing to search for movies</div>';
        return;
    }

    document.getElementById('search-results').innerHTML = '<div class="search-loading"><div class="spinner"></div><p>Searching...</p></div>';

    searchTimeout = setTimeout(() => {
        searchMovies(query);
    }, 300);
}

async function searchMovies(query) {
    try {
        const response = await fetch(`${API_URL}/movies/search?q=${encodeURIComponent(query)}`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        if (data.success && data.movies && data.movies.length > 0) {
            renderSearchResults(data.movies);
        } else {
            document.getElementById('search-results').innerHTML = '<div class="search-empty">No movies found</div>';
        }
    } catch (error) {
        console.error('Error searching movies:', error);
        document.getElementById('search-results').innerHTML = '<div class="search-empty">Error searching. Try again.</div>';
    }
}

function renderSearchResults(movies) {
    const container = document.getElementById('search-results');
    container.innerHTML = movies.map(movie => {
        const posterUrl = movie.poster_path || 'https://via.placeholder.com/48x72?text=?';
        return `
            <div class="search-result-item" onclick="selectSearchMovie(${movie.tmdb_id}, '${movie.title.replace(/'/g, "\\'")}', ${movie.year || 'null'}, '${posterUrl.replace(/'/g, "\\'")}')">
                <img src="${posterUrl}" alt="${movie.title}" class="search-result-poster">
                <div class="search-result-info">
                    <div class="search-result-title">${movie.title}</div>
                    <div class="search-result-year">${movie.year || ''}</div>
                </div>
            </div>
        `;
    }).join('');
}

function selectSearchMovie(tmdbId, title, year, posterPath) {
    searchSelectedMovie = { tmdb_id: tmdbId, title, year, poster_path: posterPath };
    searchRating = 0;

    document.getElementById('rate-search-movie-title').textContent = title;
    document.getElementById('search-selected-rating').textContent = '-';
    document.getElementById('search-review-text').value = '';
    document.getElementById('submit-search-rating-btn').disabled = true;

    // Reset stars
    const stars = document.querySelectorAll('#rate-search-stars .star');
    stars.forEach(star => star.classList.remove('filled'));

    closeSearchModal();
    document.getElementById('rate-search-modal').style.display = 'flex';
}

function handleSearchRatingClick(rating) {
    searchRating = rating;
    document.getElementById('search-selected-rating').textContent = rating;
    document.getElementById('submit-search-rating-btn').disabled = false;

    const stars = document.querySelectorAll('#rate-search-stars .star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('filled');
        } else {
            star.classList.remove('filled');
        }
    });
}

function closeRateSearchModal() {
    document.getElementById('rate-search-modal').style.display = 'none';
    searchSelectedMovie = null;
    searchRating = 0;
}

async function submitSearchRating() {
    if (!searchSelectedMovie || searchRating === 0) return;

    const reviewText = document.getElementById('search-review-text').value.trim();

    try {
        await fetch(`${API_URL}/reviews`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                tmdb_id: searchSelectedMovie.tmdb_id,
                rating: searchRating,
                review_text: reviewText
            })
        });

        closeRateSearchModal();
        alert(`Rated "${searchSelectedMovie.title}"!`);
    } catch (error) {
        console.error('Error submitting search rating:', error);
    }
}

// =============================================
// MARK SEEN (WATCHLIST)
// =============================================

let markSeenMovie = null;
let markSeenRating = 0;

function openMarkSeenModal(tmdbId, title) {
    markSeenMovie = { tmdb_id: tmdbId, title };
    markSeenRating = 0;

    document.getElementById('mark-seen-movie-title').textContent = title;
    document.getElementById('mark-seen-rating').textContent = '-';
    document.getElementById('mark-seen-review-text').value = '';
    document.getElementById('submit-mark-seen-btn').disabled = true;

    // Reset stars
    const stars = document.querySelectorAll('#mark-seen-stars .star');
    stars.forEach(star => star.classList.remove('filled'));

    document.getElementById('mark-seen-modal').style.display = 'flex';
}

function closeMarkSeenModal() {
    document.getElementById('mark-seen-modal').style.display = 'none';
    markSeenMovie = null;
    markSeenRating = 0;
}

function handleMarkSeenRatingClick(rating) {
    markSeenRating = rating;
    document.getElementById('mark-seen-rating').textContent = rating;
    document.getElementById('submit-mark-seen-btn').disabled = false;

    const stars = document.querySelectorAll('#mark-seen-stars .star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('filled');
        } else {
            star.classList.remove('filled');
        }
    });
}

async function submitMarkSeen() {
    if (!markSeenMovie || markSeenRating === 0) return;

    const reviewText = document.getElementById('mark-seen-review-text').value.trim();

    try {
        await fetch(`${API_URL}/watchlist/${markSeenMovie.tmdb_id}/seen`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                rating: markSeenRating,
                review_text: reviewText
            })
        });

        closeMarkSeenModal();
        loadWatchlist(); // Refresh watchlist
    } catch (error) {
        console.error('Error marking as seen:', error);
    }
}
