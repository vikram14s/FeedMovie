"""
Flask API for FeedMovie.

Multi-user movie recommendation platform.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import (
    get_top_recommendations, record_swipe, get_movie_by_tmdb_id,
    add_movie, add_rating, get_watchlist, remove_from_watchlist, get_connection,
    create_user, get_user_by_email, get_user_by_id, update_user_onboarding,
    get_onboarding_movies, init_database
)
from auth import hash_password, verify_password, create_token, require_auth, optional_auth
from datetime import datetime
import json
import tmdb_client
from taste_profiles import get_all_profiles, get_profile, build_profile_prompt_context
from swipe_analytics import get_swipe_patterns, get_swipe_summary

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
            'user_id': user_id,
            'username': username,
            'email': email,
            'token': token,
            'onboarding_completed': False
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
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'token': token,
            'onboarding_completed': bool(user['onboarding_completed']),
            'onboarding_type': user['onboarding_type'],
            'letterboxd_username': user['letterboxd_username']
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
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'onboarding_completed': bool(user['onboarding_completed']),
            'onboarding_type': user['onboarding_type'],
            'letterboxd_username': user['letterboxd_username'],
            'genre_preferences': json.loads(user['genre_preferences']) if user['genre_preferences'] else []
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

        # Trigger recommendation generation in background
        import threading
        from recommender import generate_and_save_recommendations

        def generate_async():
            try:
                print(f"Generating initial recommendations for user {user_id}...")
                generate_and_save_recommendations(count=50, user_id=user_id)
                print(f"Initial recommendations generated for user {user_id}")
            except Exception as e:
                print(f"Error generating recommendations: {e}")

        thread = threading.Thread(target=generate_async)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Onboarding complete! Generating your personalized recommendations...'
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
        recommendations, total_unshown = get_top_recommendations(limit=limit, genres=genres, user_id=user_id)

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
    Returns immediately with status.
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

            # Start generation in background thread
            def generate_async():
                try:
                    print(f"🔄 Starting background recommendation generation for user {user_id}...")
                    generate_and_save_recommendations(count=50, user_id=user_id)
                    print("✅ Background generation complete!")
                except Exception as e:
                    print(f"❌ Background generation error: {e}")

            thread = threading.Thread(target=generate_async)
            thread.daemon = True
            thread.start()

            return jsonify({
                'success': True,
                'generating': True,
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


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@app.route('/')
def index():
    """Serve the frontend."""
    from flask import send_from_directory
    return send_from_directory('../frontend', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files."""
    from flask import send_from_directory
    return send_from_directory('../frontend', path)


if __name__ == '__main__':
    print("\n🎬 Starting FeedMovie API server...")
    print("🌐 Frontend: http://localhost:5000")
    print("📡 API: http://localhost:5000/api/recommendations")
    print("\n✨ Happy movie hunting!\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
