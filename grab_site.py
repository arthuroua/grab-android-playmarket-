import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import os
import re

# Основна URL-адреса сторінки з Wayback Machine
base_url = "https://web.archive.org/web/20240907100524/http://android-playmarket.com/"
site_dir = Path("android-playmarket-site")
site_dir.mkdir(exist_ok=True)

def clean_filename(url):
    # Витягуємо оригінальний URL, якщо це Wayback Machine
    match = re.search(r'/web/\d+(?:[a-z_]*)/(http.*)', url)
    if match:
        url = match.group(1)

    parsed = urlparse(url)
    filepath = parsed.netloc + parsed.path

    # Заборонені символи Windows
    filepath = re.sub(r'[<>:"\\|?*]', "_", filepath)
    if filepath.endswith("/"):
        filepath += "index.html"
    return site_dir / filepath

def download(url):
    try:
        print(f"⬇ Завантаження: {url}")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        save_path = clean_filename(url)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"❌ Не вдалося завантажити {url}: {e}")

def rewrite_links(soup, tag, attr):
    for el in soup.find_all(tag):
        if el.has_attr(attr):
            original = el[attr]
            full = urljoin(base_url, original)
            el[attr] = clean_filename(full).relative_to(site_dir).as_posix()
            download(full)

# 1. Завантажити HTML-сторінку
try:
    print(f"🌐 Завантаження головної сторінки: {base_url}")
    res = requests.get(base_url, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 2. Переписати посилання та завантажити ресурси
    rewrite_links(soup, "link", "href")
    rewrite_links(soup, "script", "src")
    rewrite_links(soup, "img", "src")

    # 3. Зберегти HTML
    index_path = site_dir / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print(f"✅ Сайт збережено в: {index_path.resolve()}")
except Exception as e:
    print(f"❌ Помилка при завантаженні сайту: {e}")
