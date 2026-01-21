"""
Flask API for FeedMovie.

Endpoints:
- GET /api/recommendations - Get movie recommendations
- POST /api/swipe - Record swipe action
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import (get_top_recommendations, record_swipe, get_movie_by_tmdb_id,
                      add_movie, add_rating, get_watchlist, remove_from_watchlist, get_connection)
from datetime import datetime
import tmdb_client

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend


@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
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

        recommendations, total_unshown = get_top_recommendations(limit=limit, genres=genres)

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
def swipe():
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

        record_swipe(tmdb_id, action)

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
def add_rating_endpoint():
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

        # Add rating
        today = datetime.now().strftime('%Y-%m-%d')
        add_rating(movie_id, rating, watched_date=today)

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
def get_watchlist_endpoint():
    """
    Get user's watchlist (movies they've liked).
    """
    try:
        watchlist = get_watchlist()

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
def remove_from_watchlist_endpoint(tmdb_id):
    """
    Remove a movie from the watchlist.
    """
    try:
        remove_from_watchlist(tmdb_id)

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
def generate_more():
    """
    Generate more recommendations ONLY if running low (<15 unshown movies).
    Returns immediately with status.
    """
    try:
        import threading
        from recommender import generate_and_save_recommendations

        # Check how many unshown recommendations we have
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM recommendations WHERE shown_to_user = FALSE')
        unshown_count = cursor.fetchone()[0]
        conn.close()

        print(f"\n📊 Preemptive check: {unshown_count} unshown recommendations")

        # Only generate if running low
        if unshown_count < 15:
            print("⚠️  Running low on recommendations, generating more...")

            # Start generation in background thread
            def generate_async():
                try:
                    print("🔄 Starting background recommendation generation...")
                    generate_and_save_recommendations(count=50)  # Generate 50 for better coverage
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
