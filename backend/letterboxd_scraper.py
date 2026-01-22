"""
Letterboxd Scraper - Scrape friend lists and ratings from Letterboxd.

Uses Playwright for browser automation to handle Letterboxd's bot protection.
"""

import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
import re


async def scrape_following_page(username: str, max_pages: int = 5) -> List[Dict[str, str]]:
    """
    Scrape the /following/ page for a Letterboxd user.

    Args:
        username: Letterboxd username
        max_pages: Maximum number of pages to scrape

    Returns:
        List of dicts with: username, display_name, avatar_url
    """
    friends = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        try:
            # Navigate to following page
            url = f"https://letterboxd.com/{username}/following/"
            print(f"   Fetching {url}...")
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait for content to load
            await page.wait_for_selector('.person-summary, .table-person', timeout=10000)

            page_num = 1
            while page_num <= max_pages:
                # Get page content
                html = await page.content()
                soup = BeautifulSoup(html, 'lxml')

                # Parse friend entries (try multiple selectors)
                person_elements = soup.select('.person-summary') or soup.select('.table-person')

                for person in person_elements:
                    # Get username from link
                    link = person.select_one('a[href*="letterboxd.com/"], a.name, a.avatar')
                    if link:
                        href = link.get('href', '')
                        # Extract username from URL like /username/ or https://letterboxd.com/username/
                        match = re.search(r'letterboxd\.com/([^/]+)/?', href) or re.search(r'^/([^/]+)/?$', href)
                        if match:
                            friend_username = match.group(1)
                        else:
                            # Try to get from href directly
                            friend_username = href.strip('/').split('/')[-1]

                        if friend_username and friend_username != username:
                            # Get display name
                            name_elem = person.select_one('.name, .title, h3 a, a.name')
                            display_name = name_elem.get_text(strip=True) if name_elem else friend_username

                            # Get avatar
                            avatar = person.select_one('img.avatar, img')
                            avatar_url = avatar.get('src') if avatar else None

                            # Avoid duplicates
                            if friend_username not in [f['username'] for f in friends]:
                                friends.append({
                                    'username': friend_username,
                                    'display_name': display_name,
                                    'avatar_url': avatar_url
                                })

                # Check for next page
                next_btn = await page.query_selector('.paginate-nextprev .next, a.next')
                if not next_btn or page_num >= max_pages:
                    break

                # Click next and wait
                await next_btn.click()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)  # Rate limiting
                page_num += 1

        except Exception as e:
            print(f"   Error scraping following page: {e}")

        await browser.close()

    return friends


async def scrape_user_ratings(username: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Scrape a user's film ratings from their /films/by/date/ page.

    Args:
        username: Letterboxd username
        limit: Maximum number of ratings to fetch

    Returns:
        List of dicts with: title, year, rating
    """
    ratings = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        try:
            # Go to rated films page (sorted by rating, highest first)
            url = f"https://letterboxd.com/{username}/films/ratings/"
            print(f"   Fetching {url}...")
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # Wait a bit for dynamic content
            await asyncio.sleep(2)

            # Wait for film posters to load (try multiple selectors)
            try:
                await page.wait_for_selector('.poster-container, .film-poster, .poster', timeout=15000)
            except Exception:
                # Page might have loaded but no posters yet, continue anyway
                pass

            page_num = 1
            while len(ratings) < limit:
                html = await page.content()
                soup = BeautifulSoup(html, 'lxml')

                # Find all film entries - Letterboxd uses .griditem for films on ratings page
                film_containers = (
                    soup.select('li.griditem') or
                    soup.select('.poster-container') or
                    soup.select('li.poster-container')
                )

                for container in film_containers:
                    if len(ratings) >= limit:
                        break

                    # Get film data from element with data attributes
                    # Letterboxd uses data-item-full-display-name or data-item-name
                    film_elem = (
                        container.select_one('[data-item-full-display-name]') or
                        container.select_one('[data-item-name]') or
                        container.select_one('[data-film-name]') or
                        container
                    )

                    # Get title from data-item-full-display-name (includes year)
                    # Format: "Movie Title (2024)"
                    full_name = (
                        film_elem.get('data-item-full-display-name', '') or
                        film_elem.get('data-item-name', '') or
                        film_elem.get('data-film-full-display-name', '')
                    )

                    title = ''
                    year_str = ''

                    if full_name:
                        # Parse "Movie Title (2024)" format
                        match = re.match(r'^(.+?)\s*\((\d{4})\)$', full_name)
                        if match:
                            title = match.group(1).strip()
                            year_str = match.group(2)
                        else:
                            title = full_name

                    # Fallback to other attributes
                    if not title:
                        title = film_elem.get('data-film-name', '')
                        year_str = film_elem.get('data-film-release-year', '')

                    # Try alt text if still no title (last resort)
                    if not title:
                        img = container.select_one('img')
                        if img:
                            alt = img.get('alt', '') or img.get('title', '')
                            # Remove "Poster for " prefix if present
                            if alt.startswith('Poster for '):
                                alt = alt[11:]
                            title = alt

                    # Get rating (Letterboxd uses rated-X class where X is rating * 2)
                    rating_span = container.select_one('span.rating, span[class*="rated-"]')
                    rating_val = None

                    if rating_span:
                        # Try to find rated-X class
                        classes = rating_span.get('class', [])
                        for cls in classes:
                            if cls.startswith('rated-'):
                                try:
                                    rating_num = int(cls.replace('rated-', ''))
                                    rating_val = rating_num / 2  # Convert to 0.5-5 scale
                                except ValueError:
                                    pass

                    # Only include if we have title and rating
                    if title and rating_val is not None:
                        ratings.append({
                            'title': title,
                            'year': int(year_str) if year_str and year_str.isdigit() else None,
                            'rating': rating_val
                        })

                # Check for next page
                next_btn = await page.query_selector('.paginate-nextprev .next, a.next')
                if not next_btn or len(film_containers) == 0:
                    break

                page_num += 1
                if page_num > 10:  # Safety limit
                    break

                await next_btn.click()
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"   Error scraping ratings for {username}: {e}")

        await browser.close()

    return ratings


def sync_scrape_following(username: str, max_pages: int = 5) -> List[Dict[str, str]]:
    """Synchronous wrapper for scrape_following_page."""
    return asyncio.run(scrape_following_page(username, max_pages))


def sync_scrape_ratings(username: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Synchronous wrapper for scrape_user_ratings."""
    return asyncio.run(scrape_user_ratings(username, limit))


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python letterboxd_scraper.py <username>")
        print("Example: python letterboxd_scraper.py vikram14s")
        sys.exit(1)

    username = sys.argv[1]

    print(f"\n🔍 Scraping Letterboxd data for {username}...")

    # Test following page
    print(f"\n📋 Fetching following list...")
    friends = sync_scrape_following(username, max_pages=2)
    print(f"   Found {len(friends)} friends")
    for f in friends[:5]:
        print(f"   - {f['display_name']} (@{f['username']})")
    if len(friends) > 5:
        print(f"   ... and {len(friends) - 5} more")

    # Test ratings
    print(f"\n🎬 Fetching ratings...")
    ratings = sync_scrape_ratings(username, limit=20)
    print(f"   Found {len(ratings)} ratings")
    for r in ratings[:5]:
        print(f"   - {r['title']} ({r.get('year', 'N/A')}) - {r['rating']}★")

    print("\n✅ Scraping test complete!")
