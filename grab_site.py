import os
import re
import requests
from pathlib import Path
from urllib.parse import urlparse
import hashlib
from bs4 import BeautifulSoup

BASE_DIR = Path("android-playmarket-site")

def sanitize_filename(url):
    # Парсимо URL
    parsed = urlparse(url)
    netloc = parsed.netloc.replace(":", "_")
    path = parsed.path.replace(":", "_")
    # Хешуємо повну URL для унікальності
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    # Формуємо шлях
    filepath = BASE_DIR / netloc / path.lstrip("/")
    if filepath.name == "":
        filepath = filepath / "index.html"
    return filepath.with_name(f"{filepath.name}_{url_hash[:8]}")

def download(url):
    try:
        filepath = sanitize_filename(url)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if not filepath.exists():
            print(f"⬇️ Завантаження: {url}")
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(r.content)
        return filepath
    except Exception as e:
        print(f"❌ Не вдалося завантажити {url}: {e}")
        return None

def grab_page(url):
    filepath = download(url)
    if filepath is None:
        return

    try:
        with open(filepath, "rb") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        tags_attrs = {
            "link": "href",
            "script": "src",
            "img": "src",
        }

        for tag, attr in tags_attrs.items():
            for element in soup.find_all(tag):
                resource_url = element.get(attr)
                if resource_url and not resource_url.startswith("data:") and not resource_url.startswith("#"):
                    full_url = requests.compat.urljoin(url, resource_url)
                    res_path = download(full_url)
                    if res_path:
                        element[attr] = str(res_path.relative_to(BASE_DIR)).replace("\\", "/")

        with open(filepath, "wb") as f:
            f.write(soup.prettify("utf-8"))

        print(f"✅ Збережено: {filepath}")
    except Exception as e:
        print(f"⚠️ Не вдалося обробити HTML {url}: {e}")

if __name__ == "__main__":
    target_url = "https://web.archive.org/web/20240907100524cs_/http://android-playmarket.com/"
    grab_page(target_url)
