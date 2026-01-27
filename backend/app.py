"""
Flask API for FeedMovie.

Multi-user movie recommendation platform.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import (
    get_top_recommendations, record_swipe, get_movie_by_tmdb_id,
    add_movie, add_rating, get_watchlist, remove_from_watchlist, get_connection,
    create_user, get_user_by_email, get_user_by_id, get_user_by_username,
    update_user_onboarding, get_onboarding_movies, init_database,
    get_all_friends, get_user_library, add_friend,
    # Social features
    create_or_update_review, get_user_reviews, get_movie_reviews,
    create_activity, get_friends_activity, get_user_activity,
    like_activity, unlike_activity, update_user_profile, get_user_stats,
    # User discovery
    search_users, get_suggested_users,
    # Generation tracking
    create_generation_job, update_generation_job, get_generation_job, get_average_generation_time
)
from auth import hash_password, verify_password, create_token, require_auth, optional_auth
from datetime import datetime
import json
import tmdb_client
from taste_profiles import get_all_profiles, get_profile, build_profile_prompt_context
from swipe_analytics import get_swipe_patterns, get_swipe_summary
from populate_onboarding import populate_onboarding_movies
from curators import ensure_curators_exist

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend


# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new user.

    Body:
    {
        "email": "user@example.com",
        "password": "securepassword",
        "username": "moviefan"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        username = data.get('username', '').strip()

        # Validation
        if not email or not password or not username:
            return jsonify({
                'success': False,
                'error': 'Email, password, and username are required'
            }), 400

        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400

        if len(username) < 2:
            return jsonify({
                'success': False,
                'error': 'Username must be at least 2 characters'
            }), 400

        # Hash password and create user
        password_hash = hash_password(password)
        user_id = create_user(email, password_hash, username)

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Email or username already exists'
            }), 409

        # Create token
        token = create_token(user_id, email, username)

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'onboarding_completed': False,
                'onboarding_type': None,
                'letterboxd_username': None
            }
        })

    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login and get JWT token.

    Body:
    {
        "email": "user@example.com",
        "password": "securepassword"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400

        # Get user
        user = get_user_by_email(email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401

        # Verify password
        if not verify_password(password, user['password_hash']):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401

        # Create token
        token = create_token(user['id'], user['email'], user['username'])

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'onboarding_completed': bool(user['onboarding_completed']),
                'onboarding_type': user['onboarding_type'],
                'letterboxd_username': user['letterboxd_username']
            }
        })

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """Get current user info."""
    try:
        user = get_user_by_id(current_user['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'onboarding_completed': bool(user['onboarding_completed']),
                'onboarding_type': user['onboarding_type'],
                'letterboxd_username': user['letterboxd_username'],
                'genre_preferences': json.loads(user['genre_preferences']) if user['genre_preferences'] else []
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# ONBOARDING ENDPOINTS
# ============================================================

@app.route('/api/onboarding/movies', methods=['GET'])
def get_onboarding_movies_endpoint():
    """Get popular movies for swipe onboarding."""
    try:
        limit = int(request.args.get('limit', 20))
        movies = get_onboarding_movies(limit=limit)

        return jsonify({
            'success': True,
            'count': len(movies),
            'movies': movies
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/onboarding/swipe-ratings', methods=['POST'])
@require_auth
def save_swipe_ratings(current_user):
    """
    Save batch of ratings from swipe onboarding.

    Body:
    {
        "ratings": [
            {"tmdb_id": 123, "rating": 4.5},
            {"tmdb_id": 456, "rating": 3.0}
        ]
    }
    """
    try:
        data = request.get_json()
        ratings = data.get('ratings', [])
        user_id = current_user['user_id']

        saved_count = 0
        for r in ratings:
            tmdb_id = r.get('tmdb_id')
            rating = r.get('rating')

            if not tmdb_id or not rating:
                continue

            # Get or fetch movie
            movie = get_movie_by_tmdb_id(tmdb_id)
            if not movie:
                # Fetch from TMDB
                tmdb_data = tmdb_client.get_movie_details(tmdb_id)
                if tmdb_data:
                    movie_id = add_movie(
                        tmdb_id=tmdb_data['tmdb_id'],
                        title=tmdb_data['title'],
                        year=tmdb_data['year'],
                        genres=tmdb_data.get('genres', []),
                        poster_path=tmdb_data.get('poster_path'),
                        streaming_providers=tmdb_data.get('streaming_providers', {}),
                        overview=tmdb_data.get('overview', '')
                    )
                else:
                    continue
            else:
                movie_id = movie['id']

            # Add rating with user_id
            add_rating(movie_id, rating, user_id=user_id)
            saved_count += 1

        # Mark onboarding type
        update_user_onboarding(user_id, onboarding_type='swipe')

        return jsonify({
            'success': True,
            'ratings_saved': saved_count
        })

    except Exception as e:
        print(f"Error saving swipe ratings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/onboarding/letterboxd', methods=['POST'])
@require_auth
def import_letterboxd(current_user):
    """
    Import ratings from Letterboxd username.

    Body:
    {
        "letterboxd_username": "moviefan123"
    }
    """
    try:
        data = request.get_json()
        letterboxd_username = data.get('letterboxd_username', '').strip()
        user_id = current_user['user_id']

        if not letterboxd_username:
            return jsonify({
                'success': False,
                'error': 'Letterboxd username is required'
            }), 400

        # Import ratings using scraper
        from letterboxd_scraper import sync_scrape_ratings

        print(f"Scraping ratings for {letterboxd_username}...")
        ratings = sync_scrape_ratings(letterboxd_username, limit=200)

        if not ratings:
            return jsonify({
                'success': False,
                'error': 'Could not fetch ratings. Make sure the username is correct and profile is public.'
            }), 404

        # Save ratings
        saved_count = 0
        for r in ratings:
            title = r.get('title')
            year = r.get('year')
            rating = r.get('rating')

            if not title or not rating:
                continue

            # Search TMDB for movie
            tmdb_data = tmdb_client.search_movie(title, year)
            if not tmdb_data:
                continue

            # Add movie to database
            movie_id = add_movie(
                tmdb_id=tmdb_data['tmdb_id'],
                title=tmdb_data['title'],
                year=tmdb_data['year'],
                genres=tmdb_data.get('genres', []),
                poster_path=tmdb_data.get('poster_path'),
                streaming_providers=tmdb_data.get('streaming_providers', {}),
                overview=tmdb_data.get('overview', '')
            )

            # Add rating with user_id
            add_rating(movie_id, rating, user_id=user_id)
            saved_count += 1

        # Update user
        update_user_onboarding(
            user_id,
            onboarding_type='letterboxd',
            letterboxd_username=letterboxd_username
        )

        return jsonify({
            'success': True,
            'ratings_imported': saved_count,
            'total_found': len(ratings),
            'message': f'Imported {saved_count} ratings from Letterboxd'
        })

    except Exception as e:
        print(f"Letterboxd import error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/onboarding/genre-preferences', methods=['POST'])
@require_auth
def save_genre_preferences(current_user):
    """
    Save user's genre preferences.

    Body:
    {
        "genres": ["Action", "Sci-Fi", "Thriller"]
    }
    """
    try:
        data = request.get_json()
        genres = data.get('genres', [])
        user_id = current_user['user_id']

        update_user_onboarding(user_id, genre_preferences=genres)

        return jsonify({
            'success': True,
            'genres': genres
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/onboarding/complete', methods=['POST'])
@require_auth
def complete_onboarding(current_user):
    """Mark onboarding as complete and trigger initial recommendation generation."""
    try:
        user_id = current_user['user_id']

        # Mark onboarding complete
        update_user_onboarding(user_id, onboarding_completed=True)

        # Create a generation job for progress tracking
        job_id = create_generation_job(user_id)
        avg_time = get_average_generation_time()

        # Trigger recommendation generation in background
        import threading
        from recommender import generate_and_save_recommendations

        def generate_async():
            try:
                print(f"Generating initial recommendations for user {user_id} (job {job_id})...")
                generate_and_save_recommendations(count=50, user_id=user_id, job_id=job_id)
                print(f"Initial recommendations generated for user {user_id}")
            except Exception as e:
                print(f"Error generating recommendations: {e}")
                update_generation_job(job_id, status='failed', error_message=str(e))

        thread = threading.Thread(target=generate_async)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Onboarding complete! Generating your personalized recommendations...',
            'job_id': job_id,
            'estimated_seconds': avg_time
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# EXISTING ENDPOINTS (updated for multi-user)
# ============================================================


@app.route('/api/recommendations', methods=['GET'])
@optional_auth
def get_recommendations(current_user):
    """
    Get top recommendations from database.

    Query params:
    - limit: Number of recommendations (default: 50)
    - genres: Comma-separated list of genres to filter by
    """
    try:
        limit = int(request.args.get('limit', 50))
        genres_param = request.args.get('genres', '')
        genres = [g.strip() for g in genres_param.split(',') if g.strip()] if genres_param else None

        user_id = current_user['user_id'] if current_user else None
        print(f"📽️ Recommendations request for user {user_id}")

        recommendations, total_unshown = get_top_recommendations(limit=limit, genres=genres, user_id=user_id)
        print(f"   → Found {len(recommendations)} recommendations, {total_unshown} total unshown")

        return jsonify({
            'success': True,
            'count': len(recommendations),
            'total_unshown': total_unshown,
            'recommendations': recommendations,
            'filtered_by_genres': genres if genres else []
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/swipe', methods=['POST'])
@optional_auth
def swipe(current_user):
    """
    Record a swipe action.

    Body:
    {
        "tmdb_id": 123,
        "action": "left" | "right"
    }
    """
    try:
        data = request.get_json()
        tmdb_id = data.get('tmdb_id')
        action = data.get('action')

        if not tmdb_id or action not in ['left', 'right']:
            return jsonify({
                'success': False,
                'error': 'Invalid request. Provide tmdb_id and action (left/right)'
            }), 400

        user_id = current_user['user_id'] if current_user else None
        record_swipe(tmdb_id, action, user_id=user_id)

        return jsonify({
            'success': True,
            'message': f'Recorded swipe {action} for movie {tmdb_id}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/add-rating', methods=['POST'])
@optional_auth
def add_rating_endpoint(current_user):
    """
    Add a rating for a movie the user has already watched.

    Body:
    {
        "tmdb_id": 123,
        "title": "Movie Title",
        "year": 2023,
        "rating": 4.5
    }
    """
    try:
        data = request.get_json()
        tmdb_id = data.get('tmdb_id')
        title = data.get('title')
        year = data.get('year')
        rating = data.get('rating')

        if not tmdb_id or not rating:
            return jsonify({
                'success': False,
                'error': 'Invalid request. Provide tmdb_id and rating'
            }), 400

        # Check if rating is valid (0.5 to 5.0)
        if rating < 0.5 or rating > 5.0:
            return jsonify({
                'success': False,
                'error': 'Rating must be between 0.5 and 5.0'
            }), 400

        # Check if movie exists in database
        movie = get_movie_by_tmdb_id(tmdb_id)

        # If movie doesn't exist, fetch from TMDB and add it
        if not movie:
            print(f"Movie {title} not in database, fetching from TMDB...")
            tmdb_data = tmdb_client.search_movie(title, year)

            if not tmdb_data:
                return jsonify({
                    'success': False,
                    'error': 'Movie not found in TMDB'
                }), 404

            # Add movie to database
            movie_id = add_movie(
                tmdb_id=tmdb_data['tmdb_id'],
                title=tmdb_data['title'],
                year=tmdb_data['year'],
                genres=tmdb_data['genres'],
                poster_path=tmdb_data['poster_path'],
                streaming_providers=tmdb_data['streaming_providers'],
                overview=tmdb_data['overview']
            )
        else:
            movie_id = movie['id']

        # Add rating with user_id
        today = datetime.now().strftime('%Y-%m-%d')
        user_id = current_user['user_id'] if current_user else None
        add_rating(movie_id, rating, watched_date=today, user_id=user_id)

        return jsonify({
            'success': True,
            'message': f'Added rating {rating} for {title}'
        })

    except Exception as e:
        print(f"Error adding rating: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/watchlist', methods=['GET'])
@optional_auth
def get_watchlist_endpoint(current_user):
    """
    Get user's watchlist (movies they've liked).
    """
    try:
        user_id = current_user['user_id'] if current_user else None
        watchlist = get_watchlist(user_id=user_id)

        return jsonify({
            'success': True,
            'count': len(watchlist),
            'watchlist': watchlist
        })

    except Exception as e:
        print(f"Error fetching watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/watchlist/<int:tmdb_id>', methods=['DELETE'])
@optional_auth
def remove_from_watchlist_endpoint(tmdb_id, current_user):
    """
    Remove a movie from the watchlist.
    """
    try:
        user_id = current_user['user_id'] if current_user else None
        remove_from_watchlist(tmdb_id, user_id=user_id)

        return jsonify({
            'success': True,
            'message': f'Removed movie {tmdb_id} from watchlist'
        })

    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-more', methods=['POST'])
@optional_auth
def generate_more(current_user):
    """
    Generate more recommendations ONLY if running low (<15 unshown movies).
    Returns immediately with status and job info for progress tracking.
    """
    try:
        import threading
        from recommender import generate_and_save_recommendations

        user_id = current_user['user_id'] if current_user else None

        # Check how many unshown recommendations we have for this user
        conn = get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute('SELECT COUNT(*) FROM recommendations WHERE shown_to_user = FALSE AND user_id = ?', (user_id,))
        else:
            cursor.execute('SELECT COUNT(*) FROM recommendations WHERE shown_to_user = FALSE AND user_id IS NULL')
        unshown_count = cursor.fetchone()[0]
        conn.close()

        print(f"\n📊 Preemptive check: {unshown_count} unshown recommendations for user {user_id}")

        # Only generate if running low
        if unshown_count < 15:
            print("⚠️  Running low on recommendations, generating more...")

            # Create a generation job for progress tracking
            job_id = create_generation_job(user_id) if user_id else None
            avg_time = get_average_generation_time()

            # Start generation in background thread
            def generate_async():
                try:
                    print(f"🔄 Starting background recommendation generation for user {user_id}...")
                    generate_and_save_recommendations(count=50, user_id=user_id, job_id=job_id)
                    print("✅ Background generation complete!")
                except Exception as e:
                    print(f"❌ Background generation error: {e}")
                    if job_id:
                        update_generation_job(job_id, status='failed', error_message=str(e))

            thread = threading.Thread(target=generate_async)
            thread.daemon = True
            thread.start()

            return jsonify({
                'success': True,
                'generating': True,
                'job_id': job_id,
                'estimated_seconds': avg_time,
                'message': f'Generating more recommendations ({unshown_count} remaining)...'
            })
        else:
            print(f"✓ Sufficient recommendations available ({unshown_count}), skipping generation")
            return jsonify({
                'success': True,
                'generating': False,
                'message': f'{unshown_count} recommendations available'
            })

    except Exception as e:
        print(f"Error checking generation status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/taste-profiles', methods=['GET'])
def get_taste_profiles():
    """
    Get available taste profiles for onboarding.
    """
    try:
        profiles = get_all_profiles()
        return jsonify({
            'success': True,
            'profiles': profiles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/select-profile', methods=['POST'])
@optional_auth
def select_taste_profile(current_user):
    """
    Save user's selected taste profile(s).

    Body:
    {
        "profile_ids": ["nolan_epic_fan", "a24_indie_lover"]
    }
    """
    try:
        data = request.get_json()
        profile_ids = data.get('profile_ids', [])
        user_id = current_user['user_id'] if current_user else None

        if not profile_ids:
            return jsonify({
                'success': False,
                'error': 'No profiles selected'
            }), 400

        # Validate profiles exist
        valid_profiles = []
        for pid in profile_ids:
            profile = get_profile(pid)
            if profile:
                valid_profiles.append(pid)

        if not valid_profiles:
            return jsonify({
                'success': False,
                'error': 'No valid profiles found'
            }), 400

        # Save to database
        conn = get_connection()
        cursor = conn.cursor()

        # Clear existing profile selections for this user
        if user_id:
            cursor.execute('DELETE FROM user_taste_profiles WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('DELETE FROM user_taste_profiles WHERE user_id IS NULL')

        # Insert new selections
        for pid in valid_profiles:
            cursor.execute(
                'INSERT INTO user_taste_profiles (profile_id, user_id) VALUES (?, ?)',
                (pid, user_id)
            )

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Saved {len(valid_profiles)} taste profile(s)',
            'profiles': valid_profiles
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/user-profiles', methods=['GET'])
@optional_auth
def get_user_profiles(current_user):
    """
    Get user's selected taste profiles.
    """
    try:
        user_id = current_user['user_id'] if current_user else None

        conn = get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute('SELECT profile_id FROM user_taste_profiles WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('SELECT profile_id FROM user_taste_profiles WHERE user_id IS NULL')

        rows = cursor.fetchall()
        conn.close()

        profile_ids = [row['profile_id'] for row in rows]
        return jsonify({
            'success': True,
            'profile_ids': profile_ids
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/swipe-analytics', methods=['GET'])
def get_swipe_analytics():
    """
    Get swipe pattern analytics.
    """
    try:
        patterns = get_swipe_patterns()
        summary = get_swipe_summary()

        return jsonify({
            'success': True,
            'patterns': patterns,
            'summary': summary
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# MOVIE SEARCH
# ============================================================

@app.route('/api/movies/search', methods=['GET'])
@require_auth
def search_movies(current_user):
    """
    Search for movies via TMDB.

    Query params:
    - q: Search query (required)
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400

        # Search TMDB
        results = tmdb_client.search_movies(query, limit=20)

        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })

    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/movies/<int:tmdb_id>', methods=['GET'])
@optional_auth
def get_movie_details(tmdb_id, current_user):
    """Get detailed movie info."""
    try:
        # Check local DB first
        movie = get_movie_by_tmdb_id(tmdb_id)

        if not movie:
            # Fetch from TMDB
            movie_data = tmdb_client.get_movie_details(tmdb_id)
            if not movie_data:
                return jsonify({
                    'success': False,
                    'error': 'Movie not found'
                }), 404

            # Save to DB for future
            movie_id = add_movie(
                tmdb_id=movie_data['tmdb_id'],
                title=movie_data['title'],
                year=movie_data['year'],
                genres=movie_data.get('genres', []),
                poster_path=movie_data.get('poster_path'),
                streaming_providers=movie_data.get('streaming_providers', {}),
                overview=movie_data.get('overview', ''),
                tmdb_rating=movie_data.get('tmdb_rating')
            )
            movie = get_movie_by_tmdb_id(tmdb_id)

        return jsonify({
            'success': True,
            'movie': movie
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# REVIEWS
# ============================================================

@app.route('/api/reviews', methods=['POST'])
@require_auth
def create_review(current_user):
    """
    Create or update a review for a movie.
    Also creates activity entry.

    Body:
    {
        "tmdb_id": 123,
        "rating": 4.5,
        "review_text": "Great movie!" (optional)
    }
    """
    try:
        data = request.get_json()
        tmdb_id = data.get('tmdb_id')
        rating = data.get('rating')
        review_text = data.get('review_text', '').strip() or None
        user_id = current_user['user_id']

        if not tmdb_id or rating is None:
            return jsonify({
                'success': False,
                'error': 'tmdb_id and rating are required'
            }), 400

        if rating < 0.5 or rating > 5.0:
            return jsonify({
                'success': False,
                'error': 'Rating must be between 0.5 and 5.0'
            }), 400

        # Get or create movie in database
        movie = get_movie_by_tmdb_id(tmdb_id)
        if not movie:
            # Fetch from TMDB
            movie_data = tmdb_client.get_movie_details(tmdb_id)
            if not movie_data:
                return jsonify({
                    'success': False,
                    'error': 'Movie not found'
                }), 404

            movie_id = add_movie(
                tmdb_id=movie_data['tmdb_id'],
                title=movie_data['title'],
                year=movie_data['year'],
                genres=movie_data.get('genres', []),
                poster_path=movie_data.get('poster_path'),
                streaming_providers=movie_data.get('streaming_providers', {}),
                overview=movie_data.get('overview', ''),
                tmdb_rating=movie_data.get('tmdb_rating')
            )
        else:
            movie_id = movie['id']

        # Create/update review
        review_id = create_or_update_review(user_id, movie_id, rating, review_text)

        # Create activity entry
        action_type = 'reviewed' if review_text else 'rated'
        create_activity(user_id, action_type, movie_id, rating, review_text)

        # Also add to ratings table for recommendation engine
        today = datetime.now().strftime('%Y-%m-%d')
        add_rating(movie_id, rating, watched_date=today, user_id=user_id)

        return jsonify({
            'success': True,
            'review_id': review_id,
            'message': f'Review saved for movie {tmdb_id}'
        })

    except Exception as e:
        print(f"Error creating review: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reviews/user/<int:user_id>', methods=['GET'])
@optional_auth
def get_reviews_by_user(user_id, current_user):
    """Get reviews by a specific user."""
    try:
        limit = int(request.args.get('limit', 50))
        reviews = get_user_reviews(user_id, limit)

        return jsonify({
            'success': True,
            'count': len(reviews),
            'reviews': reviews
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reviews/movie/<int:tmdb_id>', methods=['GET'])
@optional_auth
def get_reviews_for_movie(tmdb_id, current_user):
    """Get reviews for a specific movie."""
    try:
        movie = get_movie_by_tmdb_id(tmdb_id)
        if not movie:
            return jsonify({
                'success': True,
                'count': 0,
                'reviews': []
            })

        limit = int(request.args.get('limit', 50))
        reviews = get_movie_reviews(movie['id'], limit)

        return jsonify({
            'success': True,
            'count': len(reviews),
            'reviews': reviews
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# ACTIVITY FEED
# ============================================================

@app.route('/api/feed', methods=['GET'])
@require_auth
def get_feed(current_user):
    """
    Get activity feed from friends.

    Query params:
    - limit: Number of items (default: 50)
    - offset: Pagination offset (default: 0)
    """
    try:
        user_id = current_user['user_id']
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        # Debug: check user's friends
        friends = get_all_friends(user_id)
        print(f"📋 Feed request for user {user_id}: has {len(friends)} friends")
        for f in friends[:5]:  # Log first 5
            print(f"   Friend: {f.get('name')} (username: {f.get('letterboxd_username')})")

        activities = get_friends_activity(user_id, limit, offset)
        print(f"   → Found {len(activities)} activities")

        return jsonify({
            'success': True,
            'count': len(activities),
            'activities': activities
        })

    except Exception as e:
        print(f"Feed error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/feed/<int:activity_id>/like', methods=['POST'])
@require_auth
def like_activity_endpoint(activity_id, current_user):
    """Like an activity."""
    try:
        user_id = current_user['user_id']
        success = like_activity(user_id, activity_id)

        return jsonify({
            'success': True,
            'liked': success,
            'message': 'Activity liked' if success else 'Already liked'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/feed/<int:activity_id>/like', methods=['DELETE'])
@require_auth
def unlike_activity_endpoint(activity_id, current_user):
    """Unlike an activity."""
    try:
        user_id = current_user['user_id']
        success = unlike_activity(user_id, activity_id)

        return jsonify({
            'success': True,
            'unliked': success
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/feed/<int:activity_id>/watchlist', methods=['POST'])
@require_auth
def add_to_watchlist_from_feed(activity_id, current_user):
    """Add a movie from a feed activity to user's watchlist."""
    try:
        user_id = current_user['user_id']

        # Get the activity to find the movie
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT movie_id FROM activity WHERE id = ?
        ''', (activity_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({
                'success': False,
                'error': 'Activity not found'
            }), 404

        movie_id = row['movie_id']

        # Get movie tmdb_id
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT tmdb_id, title FROM movies WHERE id = ?', (movie_id,))
        movie = cursor.fetchone()
        conn.close()

        if not movie:
            return jsonify({
                'success': False,
                'error': 'Movie not found'
            }), 404

        # Add recommendation entry with swipe_action = 'right' to add to watchlist
        from database import add_recommendation
        add_recommendation(movie_id, 'feed', 0.8, 'Added from friend activity', user_id)
        record_swipe(movie['tmdb_id'], 'right', user_id)

        # Create activity for this action
        create_activity(user_id, 'watchlist_add', movie_id)

        return jsonify({
            'success': True,
            'message': f'Added {movie["title"]} to watchlist'
        })

    except Exception as e:
        print(f"Error adding to watchlist from feed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# USER PROFILE
# ============================================================

@app.route('/api/profile', methods=['GET'])
@require_auth
def get_own_profile(current_user):
    """Get current user's profile with stats."""
    try:
        user_id = current_user['user_id']
        user = get_user_by_id(user_id)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        stats = get_user_stats(user_id)
        recent_activity = get_user_activity(user_id, limit=10)

        return jsonify({
            'success': True,
            'profile': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'bio': user.get('bio'),
                'profile_picture_url': user.get('profile_picture_url'),
                'letterboxd_username': user.get('letterboxd_username'),
                'stats': stats,
                'recent_activity': recent_activity
            }
        })

    except Exception as e:
        print(f"Profile error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/<username>', methods=['GET'])
@optional_auth
def get_user_profile(username, current_user):
    """Get a user's public profile."""
    try:
        user = get_user_by_username(username)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        stats = get_user_stats(user['id'])
        recent_activity = get_user_activity(user['id'], limit=10)

        return jsonify({
            'success': True,
            'profile': {
                'id': user['id'],
                'username': user['username'],
                'bio': user.get('bio'),
                'profile_picture_url': user.get('profile_picture_url'),
                'letterboxd_username': user.get('letterboxd_username'),
                'stats': stats,
                'recent_activity': recent_activity
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile', methods=['PUT'])
@require_auth
def update_profile(current_user):
    """
    Update current user's profile.

    Body:
    {
        "bio": "Movie enthusiast...",
        "profile_picture_url": "https://..."
    }
    """
    try:
        user_id = current_user['user_id']
        data = request.get_json()

        bio = data.get('bio')
        profile_picture_url = data.get('profile_picture_url')

        update_user_profile(user_id, bio=bio, profile_picture_url=profile_picture_url)

        return jsonify({
            'success': True,
            'message': 'Profile updated'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/library', methods=['GET'])
@require_auth
def get_profile_library(current_user):
    """Get user's rated movies (Letterboxd library)."""
    try:
        user_id = current_user['user_id']
        limit = int(request.args.get('limit', 100))

        library = get_user_library(user_id, limit)

        return jsonify({
            'success': True,
            'count': len(library),
            'library': library
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/friends', methods=['GET'])
@require_auth
def get_profile_friends(current_user):
    """Get user's friends list."""
    try:
        user_id = current_user['user_id']
        friends = get_all_friends(user_id)

        return jsonify({
            'success': True,
            'count': len(friends),
            'friends': friends
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/friends', methods=['POST'])
@require_auth
def add_profile_friend(current_user):
    """Add a friend/curator to follow."""
    try:
        user_id = current_user['user_id']
        data = request.get_json()
        name = data.get('name', '').strip()

        if not name:
            return jsonify({
                'success': False,
                'error': 'Friend name is required'
            }), 400

        # Check if this is a curator (system account)
        from curators import CURATORS
        curator_username = None
        if name in CURATORS:
            curator_username = CURATORS[name]["username"]

        # Add friend with curator username if applicable
        friend_id = add_friend(name, curator_username=curator_username, user_id=user_id)

        return jsonify({
            'success': True,
            'friend_id': friend_id,
            'message': f'Added {name} as a friend'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# USER DISCOVERY
# ============================================================

@app.route('/api/users/search', methods=['GET'])
@require_auth
def api_search_users(current_user):
    """Search users by username."""
    try:
        user_id = current_user['user_id']
        query = request.args.get('q', '').strip()

        if not query:
            return jsonify({
                'success': True,
                'users': []
            })

        users = search_users(query, user_id)

        return jsonify({
            'success': True,
            'users': users
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/users/suggested', methods=['GET'])
@require_auth
def api_suggested_users(current_user):
    """Get suggested users to follow."""
    try:
        user_id = current_user['user_id']
        limit = request.args.get('limit', 10, type=int)

        users = get_suggested_users(user_id, limit)

        return jsonify({
            'success': True,
            'users': users
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# WATCHLIST MARK SEEN
# ============================================================

@app.route('/api/watchlist/<int:tmdb_id>/seen', methods=['POST'])
@require_auth
def mark_watchlist_seen(tmdb_id, current_user):
    """
    Mark a watchlist movie as seen with rating and optional review.

    Body:
    {
        "rating": 4.5,
        "review_text": "Finally watched it!" (optional)
    }
    """
    try:
        data = request.get_json()
        rating = data.get('rating')
        review_text = data.get('review_text', '').strip() or None
        user_id = current_user['user_id']

        if rating is None:
            return jsonify({
                'success': False,
                'error': 'Rating is required'
            }), 400

        if rating < 0.5 or rating > 5.0:
            return jsonify({
                'success': False,
                'error': 'Rating must be between 0.5 and 5.0'
            }), 400

        # Get movie from database
        movie = get_movie_by_tmdb_id(tmdb_id)
        if not movie:
            return jsonify({
                'success': False,
                'error': 'Movie not found'
            }), 404

        movie_id = movie['id']

        # Create review
        create_or_update_review(user_id, movie_id, rating, review_text)

        # Create activity entry
        action_type = 'reviewed' if review_text else 'rated'
        create_activity(user_id, action_type, movie_id, rating, review_text)

        # Add rating for recommendation engine
        today = datetime.now().strftime('%Y-%m-%d')
        add_rating(movie_id, rating, watched_date=today, user_id=user_id)

        # Remove from watchlist (set swipe_action to null)
        remove_from_watchlist(tmdb_id, user_id)

        return jsonify({
            'success': True,
            'message': f'Marked {movie["title"]} as seen with rating {rating}'
        })

    except Exception as e:
        print(f"Error marking watchlist seen: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generation-status', methods=['GET'])
@require_auth
def get_generation_status(current_user):
    """
    Get the current recommendation generation status for a user.
    Returns progress, estimated time remaining, and completion status.
    """
    try:
        user_id = current_user['user_id']
        job = get_generation_job(user_id)

        if not job:
            return jsonify({
                'success': True,
                'has_job': False,
                'status': 'none',
                'message': 'No generation job found'
            })

        # Calculate estimated time remaining
        avg_time = get_average_generation_time()
        progress = job['progress'] or 0
        elapsed = None

        if job['started_at']:
            from datetime import datetime
            started = datetime.fromisoformat(job['started_at'].replace('Z', '+00:00')) if isinstance(job['started_at'], str) else job['started_at']
            elapsed = (datetime.now() - started.replace(tzinfo=None)).total_seconds()

        # Estimate remaining time based on progress
        if progress > 0 and elapsed:
            estimated_total = elapsed / (progress / 100)
            estimated_remaining = max(0, estimated_total - elapsed)
        else:
            estimated_remaining = avg_time * (1 - progress / 100)

        return jsonify({
            'success': True,
            'has_job': True,
            'status': job['status'],
            'stage': job['stage'],
            'progress': progress,
            'estimated_seconds_remaining': round(estimated_remaining),
            'estimated_total_seconds': round(avg_time),
            'is_complete': job['status'] == 'completed',
            'error_message': job.get('error_message')
        })

    except Exception as e:
        print(f"Error getting generation status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


# ============================================================
# STATIC FILE SERVING (Frontend)
# ============================================================

import os

# In production, serve from the built frontend/dist folder
# In development, serve from frontend/ (source files)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
if not os.path.exists(FRONTEND_DIR):
    # Fallback to dev mode (source files)
    FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')


@app.route('/')
def index():
    """Serve the frontend."""
    from flask import send_from_directory
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files, with SPA fallback for client-side routing."""
    from flask import send_from_directory

    # Try to serve the file directly
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)

    # For SPA: return index.html for any non-file routes (client-side routing)
    return send_from_directory(FRONTEND_DIR, 'index.html')


def run_startup_tasks():
    """Run startup tasks in background thread."""
    import time
    time.sleep(2)  # Wait for server to be ready
    try:
        print("🔧 Running startup tasks...")
        print("  → Populating onboarding movies...")
        populate_onboarding_movies()
        print("  → Creating curator accounts...")
        curators_created = ensure_curators_exist()
        print(f"  → Curators created: {curators_created}")
        print("✅ Startup tasks complete!")
    except Exception as e:
        import traceback
        print(f"⚠️ Startup task error: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    # Initialize database tables on startup (fast)
    init_database()

    # Run population tasks in background thread (slow, shouldn't block startup)
    import threading
    startup_thread = threading.Thread(target=run_startup_tasks, daemon=True)
    startup_thread.start()

    # Use PORT from environment (Railway sets this) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PRODUCTION')

    print("\n🎬 Starting FeedMovie API server...")
    print(f"🌐 Server: http://localhost:{port}")
    print(f"📡 API: http://localhost:{port}/api/recommendations")
    print(f"🔧 Mode: {'Production' if is_production else 'Development'}")
    print("\n✨ Happy movie hunting!\n")

    app.run(
        debug=not is_production,
        host='0.0.0.0',
        port=port
    )
