from typing import List, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.horusheresylegions.com"
START_URL = f"{BASE_URL}/legions-card-list/"


HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CardImageScraper/1.0)"}


def fetch(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def extract_expansion_urls(soup: BeautifulSoup) -> Set[str]:
    """
    Extract expansion URLs from:
    <ul class="sub-menu">
        <a href="$expansion">
    """
    urls = set()

    for ul in soup.select("ul.sub-menu"):
        for a in ul.select("a[href]"):
            href = a["href"]
            urls.add(urljoin(BASE_URL, href))

    return urls


def extract_album_urls(soup: BeautifulSoup) -> Set[str]:
    """
    Extract nggallery album URLs:
    /nggallery/album/<albumName>
    """
    albums = set()

    for a in soup.select("a[href]"):
        href = a["href"]
        if "/nggallery/album/" in href:
            albums.add(urljoin(BASE_URL, href))

    return albums


def extract_image_urls(soup: BeautifulSoup) -> Set[str]:
    """
    Extract image URLs from:
    data-src="https://www.horusheresylegions.com/wp-content/gallery/..."
    """
    images = set()

    for tag in soup.select("[data-src]"):
        src = tag.get("data-src")
        if src and "/wp-content/gallery/" in src:
            images.add(src)

    return images


def scrape_all_images() -> List[str]:
    print("[*] Fetching main card list...")
    main_soup = fetch(START_URL)

    expansions = extract_expansion_urls(main_soup)
    print(f"[*] Found {len(expansions)} expansions")

    album_urls: Set[str] = set()
    image_urls: Set[str] = set()

    for exp_url in expansions:
        print(f"  [+] Expansion: {exp_url}")
        exp_soup = fetch(exp_url)

        albums = extract_album_urls(exp_soup)
        album_urls.update(albums)

    print(f"[*] Found {len(album_urls)} unique albums")

    for album_url in album_urls:
        print(f"  [+] Album: {album_url}")
        album_soup = fetch(album_url)

        images = extract_image_urls(album_soup)
        image_urls.update(images)

    print(f"[*] Total images collected: {len(image_urls)}")

    return sorted(image_urls)


if __name__ == "__main__":
    images = scrape_all_images()

    # Save to file (optional)
    with open("horus_heresy_card_images.txt", "w") as f:
        for img in images:
            f.write(img + "\n")

    print("[✓] Image URL list saved to horus_heresy_card_images.txt")
