import asyncio
from typing import List, Set
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup

BASE_URL = "https://www.horusheresylegions.com"
START_URL = f"{BASE_URL}/legions-card-list/"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CardImageScraper/1.0)"}
MAX_CONCURRENT = 8


async def fetch(
    session: aiohttp.ClientSession, url: str, sem: asyncio.Semaphore
) -> BeautifulSoup:
    async with sem:
        async with session.get(url) as resp:
            resp.raise_for_status()
            text = await resp.text()
            return BeautifulSoup(text, "html.parser")


def extract_expansion_urls(soup: BeautifulSoup) -> Set[str]:
    urls = set()
    for ul in soup.select("ul.sub-menu"):
        for a in ul.select("a[href]"):
            urls.add(urljoin(BASE_URL, a["href"]))
    return urls


def extract_album_urls(soup: BeautifulSoup) -> Set[str]:
    albums = set()
    for a in soup.select("a[href]"):
        href = a["href"]
        if "/nggallery/album/" in href:
            albums.add(urljoin(BASE_URL, href))
    return albums


def extract_image_urls(soup: BeautifulSoup) -> Set[str]:
    images = set()
    for tag in soup.select("[data-src]"):
        src = tag.get("data-src")
        if src and "/wp-content/gallery/" in src:
            images.add(src)
    return images


async def scrape_all_images() -> List[str]:
    timeout = ClientTimeout(total=60)
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
        print("[*] Fetching main card list...")
        main_soup = await fetch(session, START_URL, sem)

        expansions = extract_expansion_urls(main_soup)
        print(f"[*] Found {len(expansions)} expansions")

        # --- Fetch all expansions concurrently ---
        async def fetch_expansion(url: str) -> Set[str]:
            print(f"  [+] Expansion: {url}")
            soup = await fetch(session, url, sem)
            return extract_album_urls(soup)

        expansion_tasks = [fetch_expansion(url) for url in expansions]
        album_sets = await asyncio.gather(*expansion_tasks)

        album_urls: Set[str] = set().union(*album_sets)
        print(f"[*] Found {len(album_urls)} unique albums")

        # --- Fetch all albums concurrently ---
        async def fetch_album(url: str) -> Set[str]:
            print(f"  [+] Album: {url}")
            soup = await fetch(session, url, sem)
            return extract_image_urls(soup)

        album_tasks = [fetch_album(url) for url in album_urls]
        image_sets = await asyncio.gather(*album_tasks)

        image_urls: Set[str] = set().union(*image_sets)
        print(f"[*] Total images collected: {len(image_urls)}")

        return sorted(image_urls)


async def main():
    images = await scrape_all_images()

    with open("horus_heresy_card_images.txt", "w", encoding="utf-8") as f:
        for img in images:
            f.write(img + "\n")

    print("[✓] Image URL list saved to horus_heresy_card_images.txt")


if __name__ == "__main__":
    asyncio.run(main())
