import asyncio
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import aiofiles
import aiohttp
from aiohttp import ClientTimeout

INPUT_FILE = "horus_heresy_card_images.txt"
FACTIONS_FILE = "factions.txt"
BASE_LOCAL_DIR = "./horus_heresy_images"
MAX_CONCURRENT = 8
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CardImageDownloader/1.0)"}

# Regex for valid characters
VALID_FILENAME_RE = re.compile(r"[^A-Za-z0-9\-.]+")


async def load_factions() -> list[str]:
    if not os.path.exists(FACTIONS_FILE):
        print(f"[!] Factions file not found: {FACTIONS_FILE}")
        sys.exit(1)

    async with aiofiles.open(FACTIONS_FILE, "r") as f:
        lines = await f.readlines()

    return [line.strip().lower() for line in lines if line.strip()]


def normalize_folder(raw_folder: str, factions: list[str]) -> str:
    raw_lower = raw_folder.lower()
    for faction in factions:
        if raw_lower.startswith(faction):
            return faction
    return raw_folder


def sanitize_filename(name: str) -> str:
    """Replace any character outside [A-Za-z0-9-.] with -"""
    return VALID_FILENAME_RE.sub("-", name)


async def download_image(
    session: aiohttp.ClientSession,
    url: str,
    sem: asyncio.Semaphore,
    factions: list[str],
):
    path_parts = urlparse(url).path.strip("/").split("/")

    try:
        gallery_index = path_parts.index("gallery")
        raw_folder = path_parts[gallery_index + 1]
        folder = normalize_folder(raw_folder, factions)
        raw_image_name = path_parts[gallery_index + 2]
        image_name = sanitize_filename(raw_image_name)
    except (ValueError, IndexError):
        print(f"[!] Skipping unexpected URL format: {url}")
        return

    local_folder = Path(BASE_LOCAL_DIR) / folder
    local_folder.mkdir(parents=True, exist_ok=True)
    local_path = local_folder / image_name

    if local_path.exists():
        print(f"[*] Already exists: {local_path}")
        return

    async with sem:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"[!] Failed ({resp.status}): {url}")
                    return
                content = await resp.read()
                async with aiofiles.open(local_path, "wb") as f:
                    await f.write(content)
            print(f"[✓] Saved {local_path}")
        except Exception as e:
            print(f"[!] Error downloading {url}: {e}")


async def main():
    factions = await load_factions()

    if not os.path.exists(INPUT_FILE):
        print(f"[!] Input file not found: {INPUT_FILE}")
        sys.exit(1)

    async with aiofiles.open(INPUT_FILE, "r") as f:
        urls = [line.strip() for line in await f.readlines() if line.strip()]

    print(f"[*] Found {len(urls)} images to download")
    print(f"[*] Using {len(factions)} canonical factions")

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    timeout = ClientTimeout(total=60)

    async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
        tasks = [download_image(session, url, sem, factions) for url in urls]
        await asyncio.gather(*tasks)

    print("[✓] All done!")


if __name__ == "__main__":
    asyncio.run(main())
