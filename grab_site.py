import os
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pathlib import Path

# Налаштування
start_url = "https://web.archive.org/web/20240907100524/http://android-playmarket.com/"
site_dir = Path("android-playmarket-site")
site_dir.mkdir(exist_ok=True)

# Завантажити HTML
r = requests.get(start_url, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")

# Список розширень, які обробляємо
extensions = [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot"]

def clean_filename(url: str) -> Path:
    """
    Генерує коректний шлях для збереження файлу з URL,
    вирізаючи префікс Wayback Machine і замінюючи всі заборонені символи.
    """
    m = re.match(r"https?://web\.archive\.org/web/\d+[a-z_]*?/(https?://.+)", url)
    if m:
        url = m.group(1)

    parsed = urlparse(url)
    # Створюємо базовий шлях без заборонених символів
    clean_path = parsed.netloc + parsed.path
    clean_path = re.sub(r"[<>:\"/\\|?*]", "_", clean_path)

    # Додаємо розширення, якщо його нема
    if not os.path.splitext(clean_path)[1]:
        clean_path += ".html"

    return site_dir / clean_path

def download(url):
    filename = clean_filename(url)
    try:
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True, exist_ok=True)

        if not filename.exists():
            r = requests.get(url, timeout=10)
            with open(filename, "wb") as f:
                f.write(r.content)
            print(f"✅ Завантажено: {url}")
    except Exception as e:
        print(f"Не вдалося завантажити {url}: {e}")

def rewrite_links(soup, tag, attr):
    for el in soup.find_all(tag):
        link = el.get(attr)
        if not link or not any(ext in link for ext in extensions):
            continue
        full = urljoin(start_url, link)
        download(full)
        local_path = clean_filename(full).relative_to(site_dir).as_posix()
        el[attr] = local_path

# Обробка CSS, JS, зображень
rewrite_links(soup, "link", "href")
rewrite_links(soup, "script", "src")
rewrite_links(soup, "img", "src")

# Збереження HTML
main_file = site_dir / "index.html"
with open(main_file, "w", encoding="utf-8") as f:
    f.write(str(soup))

print("📁 Сайт збережено в:", main_file)
