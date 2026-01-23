# FeedMovie Social Features Plan

## Overview
Add social features to FeedMovie: movie search & reviews, user profiles, and a friends activity feed.

---

## Features Summary

### 1. Add & Review Movies
- **Search any movie** from TMDB to rate/review
- **Mark watchlist movies as seen** with rating + review
- **Review modal** with star rating + optional text

### 2. Profile Page
- User stats (movies watched, avg rating, favorite genres)
- Recent activity
- Watchlist preview
- Edit profile (bio, preferences)

### 3. Friends Feed
- **Scrollable Instagram-style feed** of friend activity
- Activity types: ratings, watchlist adds, reviews
- **Like/add to watchlist** directly from feed items
- Show friend's rating, review text, movie poster

---

## Database Schema Changes

### New Tables

```sql
-- Reviews with optional text
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    rating REAL NOT NULL,
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (movie_id) REFERENCES movies(id),
    UNIQUE(user_id, movie_id)
);

-- Activity feed entries
CREATE TABLE activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,  -- 'rated', 'watchlist_add', 'reviewed'
    movie_id INTEGER NOT NULL,
    rating REAL,
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (movie_id) REFERENCES movies(id)
);

-- Feed likes (users liking friend activity)
CREATE TABLE activity_likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (activity_id) REFERENCES activity(id),
    UNIQUE(user_id, activity_id)
);
```

### Modify Users Table
```sql
ALTER TABLE users ADD COLUMN bio TEXT;
ALTER TABLE users ADD COLUMN profile_picture_url TEXT;
```

---

## New API Endpoints

### Movie Search
```
GET /api/movies/search?q={query}  - Search TMDB for movies
GET /api/movies/{tmdb_id}         - Get movie details
```

### Reviews
```
POST /api/reviews                  - Create/update review + rating
GET  /api/reviews/user/{user_id}   - Get user's reviews
GET  /api/reviews/movie/{tmdb_id}  - Get reviews for a movie
```

### Activity Feed
```
GET  /api/feed                     - Get friends' activity feed
POST /api/feed/{activity_id}/like  - Like an activity
DELETE /api/feed/{activity_id}/like - Unlike
POST /api/feed/{activity_id}/watchlist - Add movie to watchlist from feed
```

### Profile
```
GET  /api/profile                  - Get own profile with stats
GET  /api/profile/{username}       - Get user's public profile
PUT  /api/profile                  - Update own profile
```

### Watchlist Enhancement
```
POST /api/watchlist/{tmdb_id}/seen - Mark watchlist item as seen (with rating)
```

---

## Frontend Changes

### New Tabs (in header filter pills)
1. **Discover** (existing)
2. **Watchlist** (enhanced - add "Mark Seen" button)
3. **Feed** (new - friends activity)
4. **Profile** (new - user profile)

### New UI Components

#### Search Modal
- Search input with autocomplete
- Results list with poster, title, year
- Tap to open review modal

#### Review Modal (enhanced)
- Movie poster + title
- 5-star rating (existing)
- Text area for review (new)
- "Post" button

#### Feed View
```
┌─────────────────────────────┐
│ 👤 friend_name · 2h ago     │
│ ★★★★☆ rated                 │
│ ┌─────────────────────────┐ │
│ │  [Poster]  Title (2024) │ │
│ │            ★ 8.5 IMDb   │ │
│ │            Drama, Sci-Fi│ │
│ └─────────────────────────┘ │
│ "Great film, loved the..." │
│ ♡ 12 likes    [+ Watchlist] │
└─────────────────────────────┘
```

#### Profile View
```
┌─────────────────────────────┐
│     👤 username             │
│     @letterboxd_user        │
│     "Bio text here..."      │
│ ─────────────────────────── │
│  127      4.2      Drama    │
│ watched  avg rating  fav    │
│ ─────────────────────────── │
│ Recent Activity             │
│ • Rated Dune ★★★★★          │
│ • Added Tenet to watchlist  │
│ ─────────────────────────── │
│ [Edit Profile]              │
└─────────────────────────────┘
```

#### Watchlist Enhancement
- Add "Mark Seen" button on each watchlist item
- Opens review modal with movie pre-filled

---

## Files to Modify

### Backend
| File | Changes |
|------|---------|
| `backend/database.py` | Add reviews, activity, activity_likes tables; new query functions |
| `backend/app.py` | Add all new endpoints (search, reviews, feed, profile) |

### Frontend
| File | Changes |
|------|---------|
| `frontend/index.html` | Add Feed tab, Profile tab, search modal, review modal, feed UI, profile UI |
| `frontend/app.js` | Add feed logic, profile logic, search logic, enhanced watchlist |

---

## Implementation Order

### Phase 1: Database & Core APIs
1. Add new tables (reviews, activity, activity_likes)
2. Add bio/picture columns to users
3. Implement movie search endpoint (uses existing TMDB client)
4. Implement review creation (also creates activity entry)

### Phase 2: Enhanced Watchlist
1. Add "Mark Seen" button to watchlist items
2. Create review modal with text input
3. Implement watchlist-to-seen flow

### Phase 3: Activity Feed
1. Create activity logging on all actions
2. Implement feed endpoint (aggregate friend activity)
3. Build scrollable feed UI
4. Add like/watchlist buttons on feed items

### Phase 4: Profile Page
1. Implement profile endpoints
2. Build profile UI with stats
3. Show recent activity on profile
4. Add edit profile functionality

---

## Verification Plan

### Movie Search & Review
1. Search for "Inception" → see results
2. Tap result → review modal opens
3. Rate 5 stars, write "Amazing!" → submits
4. Check activity table has entry

### Watchlist Mark Seen
1. Add movie to watchlist via swipe
2. Go to Watchlist tab
3. Click "Mark Seen" on movie
4. Rate + review → movie moves from watchlist to seen

### Friends Feed
1. Have friend rate a movie
2. Go to Feed tab
3. See friend's activity with poster, rating, review
4. Like the activity → like count updates
5. Add to watchlist from feed → appears in watchlist

### Profile
1. Go to Profile tab
2. See stats (watched count, avg rating)
3. See recent activity
4. Edit bio → saves correctly

---

## Technical Notes

- **Activity logging**: Create activity entry whenever user rates, reviews, or adds to watchlist
- **Feed query**: Join activity with users (friends) and movies, ordered by created_at DESC
- **Search**: Use existing `search_movie()` from tmdb_client.py
- **Likes**: Simple toggle endpoint, count aggregated in feed query
