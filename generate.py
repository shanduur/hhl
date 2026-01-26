from pathlib import Path

BASE_DIR = Path("./horus_heresy_images")
OUTPUT_FILE = BASE_DIR / "index.html"

HTML_HEAD = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Horus Heresy Card Gallery</title>
<style>
body { font-family: Arial, sans-serif; background: #111; color: #fff; margin: 0; padding: 0; }
h2 { margin-left: 20px; }

/* Sticky search bar */
#search-container {
    position: sticky;
    top: 0;
    background: #111;
    padding: 10px 20px;
    border-bottom: 2px solid #444;
    z-index: 100;
}
#search-input {
    width: 300px;
    padding: 5px 10px;
    font-size: 16px;
    border: 1px solid #444;
    border-radius: 4px;
    background: #222;
    color: #fff;
}

/* Gallery */
.gallery { display: flex; flex-wrap: wrap; gap: 10px; padding: 10px; }
.gallery img { max-width: 200px; max-height: 280px; object-fit: contain; border: 2px solid #444; background: #222; padding: 2px; cursor: pointer; transition: transform 0.2s; }
.gallery img:hover { transform: scale(1.05); }

/* Lightbox overlay */
#lightbox-overlay {
    position: fixed;
    display: none;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0,0,0,0.9);
    justify-content: center;
    align-items: center;
    z-index: 1000;
}
#lightbox-overlay img {
    max-width: 90%;
    max-height: 90%;
    box-shadow: 0 0 20px #000;
    border: 3px solid #fff;
    object-fit: contain;
    cursor: pointer;
}
.faction-section { margin-bottom: 40px; }
</style>
</head>
<body>

<div id="search-container">
    <label for="search-input">Search cards: </label>
    <input type="text" id="search-input" placeholder="Type to filter cards...">
</div>

<h1 style="margin-left: 20px;">Horus Heresy Card Gallery</h1>

<div id="lightbox-overlay" onclick="this.style.display='none'"><img id="lightbox-img"></div>
"""

HTML_FOOT = """
<script>
// Lightbox functionality
document.querySelectorAll('.gallery img').forEach(img => {
    img.addEventListener('click', () => {
        const overlay = document.getElementById('lightbox-overlay');
        const lightboxImg = document.getElementById('lightbox-img');
        lightboxImg.src = img.src;
        overlay.style.display = 'flex';
    });
});

// Search/filter functionality
const searchInput = document.getElementById('search-input');
searchInput.addEventListener('input', () => {
    const query = searchInput.value.toLowerCase();
    document.querySelectorAll('.faction-section').forEach(section => {
        let visibleImages = 0;
        section.querySelectorAll('.gallery img').forEach(img => {
            const filename = img.alt.toLowerCase();
            const faction = section.querySelector('h2').innerText.toLowerCase();
            if (filename.includes(query) || faction.includes(query)) {
                img.style.display = '';
                visibleImages += 1;
            } else {
                img.style.display = 'none';
            }
        });
        // Hide entire section if no images match
        section.style.display = visibleImages > 0 ? '' : 'none';
    });
});
</script>
</body>
</html>
"""


def generate_gallery_html():
    content = [HTML_HEAD]

    for faction_folder in sorted(BASE_DIR.iterdir()):
        if not faction_folder.is_dir():
            continue
        images = sorted(faction_folder.glob("*.*"))
        if not images:
            continue

        content.append(
            f'<div class="faction-section"><h2>{faction_folder.name}</h2><div class="gallery">'
        )
        for img in images:
            img_path = img.relative_to(BASE_DIR)
            content.append(f'<img src="{img_path}" alt="{img.name}">')
        content.append("</div></div>")

    content.append(HTML_FOOT)
    return "\n".join(content)


def main():
    html_content = generate_gallery_html()
    OUTPUT_FILE.write_text(html_content, encoding="utf-8")
    print(f"[✓] Gallery page generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
