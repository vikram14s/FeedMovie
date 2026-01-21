// FeedMovie Frontend Logic

let recommendations = [];
let currentIndex = 0;
let stats = {
    liked: 0,
    skipped: 0
};
let selectedGenres = [];
let generationTriggered = false; // Track if we've triggered background generation
let totalUnshown = 0; // Total unshown movies in database

// API URL
const API_URL = 'http://localhost:5000/api';

// Load recommendations on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if we have saved genres from previous session
    const savedGenres = localStorage.getItem('feedmovie_genres');

    if (savedGenres) {
        // Auto-load with saved genres
        selectedGenres = JSON.parse(savedGenres);
        console.log(`Auto-loading with saved genres: ${selectedGenres.join(', ')}`);

        // Show change genres button
        document.getElementById('change-genres-btn').style.display = 'block';

        // Hide genre selection, show loading
        document.getElementById('genre-selection').style.display = 'none';
        document.getElementById('loading').style.display = 'block';
        document.getElementById('stats').style.display = 'block';

        // Load recommendations
        loadRecommendations(selectedGenres);
    } else {
        // Show genre selection for first time
        document.getElementById('genre-selection').style.display = 'block';
        document.getElementById('loading').style.display = 'none';
        document.getElementById('stats').style.display = 'none';
    }

    setupKeyboardControls();
});

// Change genres function
function changeGenres() {
    // Clear saved genres
    localStorage.removeItem('feedmovie_genres');
    selectedGenres = [];

    // Reset generation flag
    generationTriggered = false;

    // Reload page to show genre selection
    location.reload();
}

// Genre Selection Functions
function toggleGenre(genre) {
    const btn = document.querySelector(`[data-genre="${genre}"]`);

    if (selectedGenres.includes(genre)) {
        // Remove genre
        selectedGenres = selectedGenres.filter(g => g !== genre);
        btn.classList.remove('selected');
    } else {
        // Add genre
        selectedGenres.push(genre);
        btn.classList.add('selected');
    }

    // Update start button
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
    if (selectedGenres.length === 0) return;

    // Save selected genres to localStorage
    localStorage.setItem('feedmovie_genres', JSON.stringify(selectedGenres));

    // Show change genres button
    document.getElementById('change-genres-btn').style.display = 'block';

    // Hide genre selection
    document.getElementById('genre-selection').style.display = 'none';

    // Show loading and stats
    document.getElementById('loading').style.display = 'block';
    document.getElementById('stats').style.display = 'block';

    // Load recommendations with selected genres
    loadRecommendations(selectedGenres);
}

async function loadRecommendations(genres = []) {
    try {
        const genresParam = genres.length > 0 ? `&genres=${genres.join(',')}` : '';
        const response = await fetch(`${API_URL}/recommendations?limit=10${genresParam}`);
        const data = await response.json();

        if (data.success) {
            recommendations = data.recommendations;
            totalUnshown = data.total_unshown;
            currentIndex = 0; // Reset index
            generationTriggered = false; // Reset generation flag for new batch
            console.log(`Loaded ${recommendations.length} recommendations (${totalUnshown} total unshown in database)`);

            // Hide loading, show card container
            document.getElementById('loading').style.display = 'none';
            document.getElementById('card-container').style.display = 'block';
            document.getElementById('actions').style.display = 'flex';

            // Update stats
            updateStats();

            // Show first card
            showCurrentCard();
        } else {
            showError('Failed to load recommendations');
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        showError('Failed to connect to server. Make sure backend is running.');
    }
}

function showCurrentCard() {
    if (currentIndex >= recommendations.length) {
        showNoMore();
        return;
    }

    const movie = recommendations[currentIndex];
    const container = document.getElementById('card-container');

    // Clear container
    container.innerHTML = '';

    // Create card
    const card = createMovieCard(movie);
    container.appendChild(card);

    // Update stats
    updateStats();
}

function createMovieCard(movie) {
    const card = document.createElement('div');
    card.className = 'movie-card rounded-2xl shadow-2xl absolute inset-0';

    // Poster or placeholder
    const posterUrl = movie.poster_path || 'https://via.placeholder.com/500x750?text=No+Poster';

    // Streaming badges
    const streamingHTML = createStreamingBadges(movie.streaming_providers || {});

    // Genres
    const genresHTML = movie.genres ?
        movie.genres.slice(0, 3).map(g => `<span class="badge">${g}</span>`).join('') :
        '';

    // Movie overview/description
    const overview = movie.overview || 'No description available.';

    // Reasoning (full text, not truncated)
    let reasoning = movie.reasoning || 'Recommended for you';

    // Sources (deduplicate just in case)
    const sources = [...new Set(movie.sources || [])];
    const sourceBadges = sources.map(s => {
        const label = s.toUpperCase();
        return `<span class="badge badge-source">${label}</span>`;
    }).join('');

    card.innerHTML = `
        <div class="poster-container relative overflow-hidden rounded-t-2xl">
            <img src="${posterUrl}" alt="${movie.title}" class="w-full object-cover" style="height: 450px;">
            <div class="absolute top-5 right-5 flex flex-col gap-2 items-end">
                <span class="match-badge">
                    ${movie.score ? (movie.score * 100).toFixed(0) : '??'}% MATCH
                </span>
                ${movie.already_watched ? `
                    <span class="badge badge-rewatch">
                        ALREADY WATCHED
                    </span>
                ` : ''}
            </div>
        </div>
        <div class="p-8 pb-10">
            <h2 class="text-3xl font-bold mb-2">${movie.title}</h2>
            <div class="flex items-center gap-4 mb-2">
                <p class="text-gray-500 text-sm">
                    ${movie.year || 'Unknown'}
                    ${movie.user_rating ? ` • Rated ${movie.user_rating}★` : ''}
                </p>
                ${movie.tmdb_rating && movie.tmdb_rating > 0 ? `
                    <div class="flex items-center gap-1.5 bg-[rgba(245,197,24,0.15)] px-2.5 py-1 rounded-lg border border-[rgba(245,197,24,0.3)]">
                        <span class="text-[#F5C518] text-lg">★</span>
                        <span class="text-[#F5C518] font-semibold text-sm">${movie.tmdb_rating.toFixed(1)}</span>
                        <span class="text-gray-500 text-xs">IMDb</span>
                    </div>
                ` : ''}
                ${movie.rt_rating ? `
                    <div class="flex items-center gap-1.5 bg-[rgba(250,82,82,0.15)] px-2.5 py-1 rounded-lg border border-[rgba(250,82,82,0.3)]">
                        <span class="text-[#FA5252] text-lg">🍅</span>
                        <span class="text-[#FA5252] font-semibold text-sm">${movie.rt_rating}</span>
                        <span class="text-gray-500 text-xs">RT</span>
                    </div>
                ` : ''}
            </div>

            <div class="mb-6">
                ${genresHTML}
            </div>

            ${streamingHTML ? `
                <div class="mb-6">
                    <div class="section-divider"></div>
                    <p class="section-header">Available On</p>
                    <div class="flex flex-wrap gap-4 items-center">
                        ${streamingHTML}
                    </div>
                </div>
            ` : ''}

            <div class="mb-6">
                <div class="section-divider"></div>
                <p class="section-header">Synopsis</p>
                <p class="text-gray-300 text-sm leading-relaxed">${overview}</p>
            </div>

            <div class="mb-6">
                <div class="section-divider"></div>
                <p class="section-header">Why You'll Love It</p>
                <p class="text-gray-300 text-sm leading-relaxed">${reasoning}</p>
            </div>

            ${sourceBadges ? `
                <div class="mt-6 pt-5" style="border-top: 1px solid rgba(255, 255, 255, 0.1);">
                    <p class="text-xs text-gray-600 uppercase tracking-wider mb-3">Recommended By</p>
                    ${sourceBadges}
                </div>
            ` : ''}
        </div>
    `;

    return card;
}

// Map streaming service names to local logo files
function getLocalLogo(serviceName) {
    const normalizedName = serviceName.toLowerCase();

    // Map provider names to local logo files
    if (normalizedName.includes('netflix')) {
        return 'logos/Netflix.png';
    } else if (normalizedName.includes('prime') || normalizedName.includes('amazon')) {
        return 'logos/Amazon-Prime-Video-Icon.png';
    } else if (normalizedName.includes('apple')) {
        return 'logos/AppleTVLogo.png';
    } else if (normalizedName.includes('hulu')) {
        return 'logos/Hulu.png';
    } else if (normalizedName.includes('youtube')) {
        return 'logos/Youtube_logo.png';
    } else if (normalizedName.includes('fandango')) {
        return 'logos/Fandango.svg';
    } else if (normalizedName.includes('google play')) {
        return 'logos/google-play-movies-tv-logo.png';
    }

    return null; // No local logo available
}

// Normalize service name for deduplication
function normalizeServiceName(name) {
    return name.toLowerCase().replace(/\s+/g, '').replace(/[^a-z]/g, '');
}

function createStreamingBadges(providers) {
    const badges = [];
    const seenServices = new Set();
    const rentalOnly = new Set();

    // Filter out unwanted services
    const filterService = (name) => {
        const lower = name.toLowerCase();
        return !lower.includes('flixfling');
    };

    // Track which services are subscription vs rental-only
    const subscriptionServices = new Set();
    if (providers.subscription && providers.subscription.length > 0) {
        providers.subscription.forEach(service => {
            const serviceName = typeof service === 'string' ? service : service.name;
            if (filterService(serviceName)) {
                subscriptionServices.add(normalizeServiceName(serviceName));
            }
        });
    }

    // Mark rental-only services (not in subscription)
    if (providers.rent && providers.rent.length > 0) {
        providers.rent.forEach(service => {
            const serviceName = typeof service === 'string' ? service : service.name;
            const normalized = normalizeServiceName(serviceName);
            if (filterService(serviceName) && !subscriptionServices.has(normalized)) {
                rentalOnly.add(normalized);
            }
        });
    }

    // Add subscription services
    if (providers.subscription && providers.subscription.length > 0) {
        providers.subscription.forEach(service => {
            const serviceName = typeof service === 'string' ? service : service.name;
            const normalized = normalizeServiceName(serviceName);

            if (!filterService(serviceName) || seenServices.has(normalized)) return;
            seenServices.add(normalized);

            const localLogo = getLocalLogo(serviceName);
            if (localLogo) {
                badges.push(`<div class="streaming-service"><img src="${localLogo}" alt="${serviceName}" class="streaming-logo" title="${serviceName}"></div>`);
            } else if (typeof service === 'object' && service.logo) {
                badges.push(`<div class="streaming-service"><img src="${service.logo}" alt="${serviceName}" class="streaming-logo" title="${serviceName}"></div>`);
            } else {
                const badgeClass = getBadgeClass(serviceName);
                badges.push(`<span class="badge ${badgeClass}">${serviceName}</span>`);
            }
        });
    }

    // Add rental-only services with $ indicator
    if (providers.rent && providers.rent.length > 0) {
        providers.rent.forEach(service => {
            const serviceName = typeof service === 'string' ? service : service.name;
            const normalized = normalizeServiceName(serviceName);

            if (!filterService(serviceName) || seenServices.has(normalized)) return;
            if (!rentalOnly.has(normalized)) return; // Skip if also in subscription
            seenServices.add(normalized);

            const localLogo = getLocalLogo(serviceName);
            if (localLogo) {
                badges.push(`<div class="streaming-service"><img src="${localLogo}" alt="Rent on ${serviceName}" class="streaming-logo" title="Rent on ${serviceName}"><div class="rental-indicator">$</div></div>`);
            } else if (typeof service === 'object' && service.logo) {
                badges.push(`<div class="streaming-service"><img src="${service.logo}" alt="Rent on ${serviceName}" class="streaming-logo" title="Rent on ${serviceName}"><div class="rental-indicator">$</div></div>`);
            } else {
                badges.push(`<span class="badge badge-default">${serviceName}</span>`);
            }
        });
    }

    return badges.join('');
}

function getBadgeClass(service) {
    const lower = service.toLowerCase();
    if (lower.includes('netflix')) return 'badge-netflix';
    if (lower.includes('prime')) return 'badge-prime';
    if (lower.includes('hbo')) return 'badge-hbo';
    if (lower.includes('disney')) return 'badge-disney';
    if (lower.includes('hulu')) return 'badge-hulu';
    return 'badge-default';
}

async function swipeLeft() {
    await recordSwipe('left');
    animateSwipe('left');
}

async function swipeRight() {
    await recordSwipe('right');
    animateSwipe('right');
}

async function recordSwipe(action) {
    const movie = recommendations[currentIndex];

    try {
        await fetch(`${API_URL}/swipe`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tmdb_id: movie.tmdb_id,
                action: action
            })
        });

        // Update stats
        if (action === 'right') {
            stats.liked++;
            // Update watchlist count badge
            const watchlistCount = document.getElementById('watchlist-count');
            watchlistCount.textContent = parseInt(watchlistCount.textContent) + 1;
        } else {
            stats.skipped++;
        }

        // Decrement total unshown count since we've now shown this movie
        totalUnshown = Math.max(0, totalUnshown - 1);

        // Note: Swipes are saved to database for future model improvements
        // To retrain the model with your feedback, run: python backend/recommender.py
        console.log(`Swipe ${action} recorded for "${movie.title}" (${totalUnshown} unshown remaining)`);

    } catch (error) {
        console.error('Error recording swipe:', error);
    }
}

function animateSwipe(direction) {
    const card = document.querySelector('.movie-card');
    if (!card) return;

    card.classList.add(`swipe-${direction}`);

    setTimeout(() => {
        currentIndex++;
        showCurrentCard();
    }, 300);
}

function updateStats() {
    const remaining = recommendations.length - currentIndex;
    document.getElementById('remaining-count').textContent = remaining;
    document.getElementById('liked-count').textContent = stats.liked;
    document.getElementById('skipped-count').textContent = stats.skipped;

    // Preemptively trigger generation when total unshown in database is low
    // Trigger when we have fewer than 15 unshown movies total
    if (totalUnshown < 15 && !generationTriggered) {
        console.log(`🔄 Preemptively generating more (only ${totalUnshown} unshown movies left)...`);
        generationTriggered = true;
        triggerBackgroundGeneration();
    }
}

async function triggerBackgroundGeneration() {
    try {
        console.log('📡 Triggering background generation...');
        await fetch(`${API_URL}/generate-more`, {
            method: 'POST'
        });
        console.log('✅ Background generation started');
    } catch (error) {
        console.error('Error triggering background generation:', error);
    }
}

function showNoMore() {
    document.getElementById('card-container').style.display = 'none';
    document.getElementById('actions').style.display = 'none';
    document.getElementById('no-more').style.display = 'block';

    // Update the hint text with selected genres
    if (selectedGenres && selectedGenres.length > 0) {
        const genreText = selectedGenres.join(', ');
        document.getElementById('see-more-hint').textContent = `Loading more ${genreText} movies`;
    }
}

function showError(message) {
    const loading = document.getElementById('loading');
    loading.innerHTML = `
        <div class="text-red-400 text-lg mb-6">${message}</div>
        <button onclick="location.reload()" class="btn green-btn px-8 py-4 rounded-xl font-bold">
            Retry
        </button>
    `;
}

function setupKeyboardControls() {
    document.addEventListener('keydown', (e) => {
        if (currentIndex >= recommendations.length) return;

        // Don't intercept if modal is open
        const modal = document.getElementById('already-seen-modal');
        if (modal.style.display === 'flex') return;

        if (e.key === 'ArrowLeft' || e.key === 'x' || e.key === 'X') {
            swipeLeft();
        } else if (e.key === 'ArrowRight' || e.key === 'v' || e.key === 'V' || e.key === '✓') {
            swipeRight();
        } else if (e.key === 's' || e.key === 'S') {
            showAlreadySeenModal();
        }
    });
}

// Already Seen Modal Functions
let selectedRating = null;

function showAlreadySeenModal() {
    const movie = recommendations[currentIndex];
    if (!movie) return;

    // Set movie title
    document.getElementById('modal-movie-title').textContent = `${movie.title} (${movie.year})`;

    // Reset rating
    selectedRating = null;
    document.getElementById('selected-rating').textContent = '-';
    document.getElementById('submit-rating-btn').disabled = true;

    // Clear all selected stars
    document.querySelectorAll('.star-wrapper').forEach(wrapper => {
        wrapper.classList.remove('filled', 'half-filled');
    });

    // Show modal
    document.getElementById('already-seen-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('already-seen-modal').style.display = 'none';
}

function handleStarClick(event, starNumber) {
    const wrapper = event.currentTarget;
    const rect = wrapper.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const halfWidth = rect.width / 2;

    // Determine if click was on left half (0.5) or right half (1.0)
    const isHalf = clickX < halfWidth;
    const rating = isHalf ? starNumber - 0.5 : starNumber;

    setRating(rating);
}

function setRating(rating) {
    selectedRating = rating;
    document.getElementById('selected-rating').textContent = rating.toFixed(1);
    document.getElementById('submit-rating-btn').disabled = false;

    // Update star display
    const wrappers = document.querySelectorAll('.star-wrapper');
    wrappers.forEach((wrapper, index) => {
        const starNumber = index + 1;
        wrapper.classList.remove('filled', 'half-filled');

        if (starNumber < rating) {
            // Full star
            wrapper.classList.add('filled');
        } else if (starNumber === Math.ceil(rating) && rating % 1 !== 0) {
            // Half star
            wrapper.classList.add('half-filled');
        }
    });
}

async function submitRating() {
    if (!selectedRating) return;

    const movie = recommendations[currentIndex];

    try {
        const response = await fetch(`${API_URL}/add-rating`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tmdb_id: movie.tmdb_id,
                title: movie.title,
                year: movie.year,
                rating: selectedRating
            })
        });

        const data = await response.json();

        if (data.success) {
            console.log(`Added rating ${selectedRating} for "${movie.title}"`);
            closeModal();
            // Move to next movie
            animateSwipe('right');
        } else {
            alert('Failed to save rating. Please try again.');
        }
    } catch (error) {
        console.error('Error saving rating:', error);
        alert('Failed to save rating. Please try again.');
    }
}

// Tab Switching
function switchTab(tab) {
    const discoverTab = document.getElementById('discover-tab');
    const watchlistTab = document.getElementById('watchlist-tab');
    const changeGenresBtn = document.getElementById('change-genres-btn');
    const genreSelection = document.getElementById('genre-selection');
    const stats = document.getElementById('stats');
    const loading = document.getElementById('loading');
    const cardContainer = document.getElementById('card-container');
    const noMore = document.getElementById('no-more');
    const actions = document.getElementById('actions');
    const keyboardHints = document.getElementById('keyboard-hints');
    const watchlistView = document.getElementById('watchlist-view');

    if (tab === 'discover') {
        // Activate discover tab
        discoverTab.classList.add('active');
        watchlistTab.classList.remove('active');

        // Show change genres button if genres are selected
        if (selectedGenres && selectedGenres.length > 0) {
            changeGenresBtn.style.display = 'block';
        }

        // Show discover content
        watchlistView.style.display = 'none';

        // Show appropriate discover view based on state
        if (recommendations.length === 0) {
            genreSelection.style.display = 'block';
            stats.style.display = 'none';
            loading.style.display = 'none';
            cardContainer.style.display = 'none';
            actions.style.display = 'none';
            keyboardHints.style.display = 'none';
            noMore.style.display = 'none';
        } else if (currentIndex >= recommendations.length) {
            genreSelection.style.display = 'none';
            stats.style.display = 'block';
            loading.style.display = 'none';
            cardContainer.style.display = 'none';
            actions.style.display = 'none';
            keyboardHints.style.display = 'block';
            noMore.style.display = 'block';
        } else {
            genreSelection.style.display = 'none';
            stats.style.display = 'block';
            loading.style.display = 'none';
            cardContainer.style.display = 'block';
            actions.style.display = 'flex';
            keyboardHints.style.display = 'block';
            noMore.style.display = 'none';
        }
    } else if (tab === 'watchlist') {
        // Activate watchlist tab
        discoverTab.classList.remove('active');
        watchlistTab.classList.add('active');

        // Hide change genres button on watchlist
        changeGenresBtn.style.display = 'none';

        // Hide discover content
        genreSelection.style.display = 'none';
        stats.style.display = 'none';
        loading.style.display = 'none';
        cardContainer.style.display = 'none';
        noMore.style.display = 'none';
        actions.style.display = 'none';
        keyboardHints.style.display = 'none';

        // Show watchlist
        watchlistView.style.display = 'block';
        loadWatchlist();
    }
}

// Watchlist Functions
async function loadWatchlist() {
    try {
        const response = await fetch(`${API_URL}/watchlist`);
        const data = await response.json();

        if (data.success) {
            const watchlist = data.watchlist;
            const watchlistGrid = document.getElementById('watchlist-grid');
            const watchlistEmpty = document.getElementById('watchlist-empty');
            const watchlistCount = document.getElementById('watchlist-count');

            // Update count badge
            watchlistCount.textContent = watchlist.length;

            if (watchlist.length === 0) {
                watchlistEmpty.style.display = 'block';
                watchlistGrid.style.display = 'none';
            } else {
                watchlistEmpty.style.display = 'none';
                watchlistGrid.style.display = 'grid';

                // Render watchlist items
                watchlistGrid.innerHTML = watchlist.map(movie => createWatchlistItem(movie)).join('');
            }
        }
    } catch (error) {
        console.error('Error loading watchlist:', error);
    }
}

function createWatchlistItem(movie) {
    const posterUrl = movie.poster_path || 'https://via.placeholder.com/120x180?text=No+Poster';
    const streamingBadges = createStreamingBadges(movie.streaming_providers || {});

    return `
        <div class="watchlist-item">
            <img src="${posterUrl}" alt="${movie.title}" class="watchlist-poster">
            <div class="flex-1">
                <h3 class="text-2xl font-bold mb-1">${movie.title}</h3>
                <p class="text-gray-500 text-sm mb-3">${movie.year || 'Unknown'}</p>

                <div class="mb-3 flex flex-wrap gap-1">
                    ${movie.genres.slice(0, 3).map(g => `<span class="badge text-xs">${g}</span>`).join('')}
                </div>

                ${streamingBadges ? `
                    <div class="mb-4">
                        <p class="section-header text-xs">Available On</p>
                        <div class="flex flex-wrap gap-2">
                            ${streamingBadges}
                        </div>
                    </div>
                ` : ''}

                <div class="flex gap-3 mt-4">
                    <button onclick="removeFromWatchlist(${movie.tmdb_id})" class="btn dark-btn px-5 py-2 rounded-xl text-xs font-semibold">
                        Remove
                    </button>
                    <button onclick="markAsWatched(${movie.tmdb_id}, '${movie.title.replace(/'/g, "\\'")}', ${movie.year})" class="btn green-btn px-5 py-2 rounded-xl text-xs font-semibold">
                        Mark Watched
                    </button>
                </div>
            </div>
        </div>
    `;
}

async function removeFromWatchlist(tmdbId) {
    try {
        const response = await fetch(`${API_URL}/watchlist/${tmdbId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            console.log(`Removed movie ${tmdbId} from watchlist`);
            loadWatchlist(); // Reload the watchlist
        } else {
            alert('Failed to remove from watchlist');
        }
    } catch (error) {
        console.error('Error removing from watchlist:', error);
        alert('Failed to remove from watchlist');
    }
}

function markAsWatched(tmdbId, title, year) {
    // Reuse the existing rating modal
    document.getElementById('modal-movie-title').textContent = `${title} (${year})`;

    // Reset rating
    selectedRating = null;
    document.getElementById('selected-rating').textContent = '-';
    document.getElementById('submit-rating-btn').disabled = true;

    // Store tmdb_id, title, year for submission
    document.getElementById('submit-rating-btn').setAttribute('data-tmdb-id', tmdbId);
    document.getElementById('submit-rating-btn').setAttribute('data-title', title);
    document.getElementById('submit-rating-btn').setAttribute('data-year', year);
    document.getElementById('submit-rating-btn').setAttribute('data-from-watchlist', 'true');

    // Clear all selected stars
    document.querySelectorAll('.star-wrapper').forEach(wrapper => {
        wrapper.classList.remove('filled', 'half-filled');
    });

    // Show modal
    document.getElementById('already-seen-modal').style.display = 'flex';
}

// Update submitRating to handle watchlist
async function submitRatingFromWatchlist() {
    if (!selectedRating) return;

    const submitBtn = document.getElementById('submit-rating-btn');
    const tmdbId = submitBtn.getAttribute('data-tmdb-id');
    const title = submitBtn.getAttribute('data-title');
    const year = submitBtn.getAttribute('data-year');
    const fromWatchlist = submitBtn.getAttribute('data-from-watchlist');

    try {
        const response = await fetch(`${API_URL}/add-rating`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tmdb_id: parseInt(tmdbId),
                title: title,
                year: parseInt(year),
                rating: selectedRating
            })
        });

        const data = await response.json();

        if (data.success) {
            console.log(`Added rating ${selectedRating} for "${title}"`);

            // Remove from watchlist after rating
            await removeFromWatchlist(parseInt(tmdbId));

            closeModal();

            // Clean up attributes
            submitBtn.removeAttribute('data-tmdb-id');
            submitBtn.removeAttribute('data-title');
            submitBtn.removeAttribute('data-year');
            submitBtn.removeAttribute('data-from-watchlist');

            // Reload watchlist if we're on watchlist tab
            if (fromWatchlist === 'true') {
                loadWatchlist();
            }
        } else {
            alert('Failed to save rating. Please try again.');
        }
    } catch (error) {
        console.error('Error saving rating:', error);
        alert('Failed to save rating. Please try again.');
    }
}

// Update original submitRating to check if it's from watchlist
const originalSubmitRating = submitRating;
submitRating = async function() {
    const submitBtn = document.getElementById('submit-rating-btn');
    if (submitBtn.getAttribute('data-from-watchlist')) {
        await submitRatingFromWatchlist();
    } else {
        await originalSubmitRating();
    }
};

// Load watchlist count on page load
document.addEventListener('DOMContentLoaded', () => {
    fetch(`${API_URL}/watchlist`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById('watchlist-count').textContent = data.count;
            }
        })
        .catch(err => console.error('Error loading watchlist count:', err));
});

// Generate More Recommendations
async function generateMoreRecommendations() {
    const seeMoreBtn = document.getElementById('see-more-btn');

    // Show loading state
    seeMoreBtn.disabled = true;
    seeMoreBtn.textContent = 'Loading...';

    // If we haven't triggered generation yet, do it now
    if (!generationTriggered) {
        console.log('🔄 Triggering generation now...');
        generationTriggered = true;
        await triggerBackgroundGeneration();
        // Wait a moment for generation to start
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Reload to fetch new recommendations from database
    console.log('🔄 Reloading to fetch new movies...');
    location.reload();
}

// Debugging
console.log('FeedMovie frontend loaded');
