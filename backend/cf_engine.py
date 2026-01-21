"""
Collaborative Filtering engine using scikit-surprise SVD.

Simple implementation: just basic SVD, no complex tuning.
Provides 20% of recommendations.
"""

import pandas as pd
from typing import List, Dict, Any
from surprise import SVD, Dataset, Reader
from surprise.model_selection import cross_validate
from database import get_all_ratings, get_watched_movie_ids
from tmdb_client import get_popular_movies


def train_cf_model(ratings: List[Dict[str, Any]]):
    """
    Train a simple SVD model on ratings data.

    Args:
        ratings: List of rating dicts with 'tmdb_id', 'title', 'rating'

    Returns:
        Trained SVD model
    """
    if not ratings or len(ratings) < 5:
        print("⚠️  Not enough ratings for collaborative filtering (need at least 5)")
        return None

    print(f"\n📊 Training CF model on {len(ratings)} ratings...")

    # Convert to DataFrame
    df = pd.DataFrame(ratings)
    df['user_id'] = 'vikram14s'  # Single user for now

    # Create surprise dataset
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(df[['user_id', 'tmdb_id', 'rating']], reader)

    # Train SVD with default parameters (simple!)
    trainset = data.build_full_trainset()
    algo = SVD()
    algo.fit(trainset)

    print("   ✓ CF model trained successfully")

    # Optional: Quick cross-validation to see accuracy
    # cv_results = cross_validate(SVD(), data, measures=['RMSE'], cv=3, verbose=False)
    # print(f"   RMSE: {cv_results['test_rmse'].mean():.2f}")

    return algo


def get_cf_recommendations(model, ratings: List[Dict[str, Any]],
                          count: int = 15) -> List[Dict[str, Any]]:
    """
    Get movie recommendations using collaborative filtering.

    Args:
        model: Trained SVD model
        ratings: User's existing ratings
        count: Number of recommendations to return

    Returns:
        List of dicts with 'title', 'year', 'tmdb_id', 'score', 'reasoning'
    """
    if model is None:
        print("⚠️  No CF model available, skipping CF recommendations")
        return []

    print(f"\n📊 Generating {count} CF recommendations...")

    # Get movies user has already watched
    watched_ids = {r['tmdb_id'] for r in ratings}
    print(f"   User has watched {len(watched_ids)} movies")

    # Get candidate movies (popular movies as a starting point)
    # In production, this would be a much larger database
    print("   Fetching candidate movies from TMDB popular...")
    candidates = get_popular_movies(page=1) + get_popular_movies(page=2)

    # Filter out watched movies
    unwatched = [m for m in candidates if m['tmdb_id'] not in watched_ids]
    print(f"   Found {len(unwatched)} unwatched candidates")

    if not unwatched:
        print("   ⚠️  No unwatched candidates found")
        return []

    # Predict ratings for unwatched movies
    predictions = []
    for movie in unwatched:
        pred = model.predict('vikram14s', movie['tmdb_id'])
        predictions.append({
            'title': movie['title'],
            'year': movie['year'],
            'tmdb_id': movie['tmdb_id'],
            'score': pred.est,
            'reasoning': f"Predicted rating: {pred.est:.1f}/5.0 based on your preferences"
        })

    # Sort by predicted rating
    predictions.sort(key=lambda x: x['score'], reverse=True)

    top_predictions = predictions[:count]
    print(f"   ✓ Generated {len(top_predictions)} CF recommendations")
    print(f"   Top prediction: {top_predictions[0]['title']} ({top_predictions[0]['score']:.2f})")

    return top_predictions


def generate_cf_recommendations(count: int = 15) -> List[Dict[str, Any]]:
    """
    End-to-end: Load ratings, train model, generate recommendations.
    """
    print("\n🎯 Collaborative Filtering Engine")
    print("=" * 50)

    # Load ratings from database
    ratings = get_all_ratings()

    if not ratings:
        print("⚠️  No ratings found in database")
        print("   Run letterboxd_import.py first to import your ratings")
        return []

    print(f"Loaded {len(ratings)} ratings from database")

    # Train model
    model = train_cf_model(ratings)

    if model is None:
        return []

    # Generate recommendations
    recommendations = get_cf_recommendations(model, ratings, count)

    return recommendations


if __name__ == '__main__':
    # Test CF engine
    print("Testing Collaborative Filtering engine...")
    recommendations = generate_cf_recommendations(count=10)

    if recommendations:
        print("\n📋 Top CF Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"{i}. {rec['title']} ({rec['year']}) - Score: {rec['score']:.2f}")
            print(f"   {rec['reasoning']}\n")
    else:
        print("\n⚠️  No recommendations generated")
        print("Make sure you've imported your Letterboxd data first!")
