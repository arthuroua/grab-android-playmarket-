import os, requests, zipfile
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path

# 🕒 Задайте timestamp архіву
timestamp = "20240907100524"
base_url = "http://android-playmarket.com/"
wayback = f"https://web.archive.org/web/{timestamp}/"
start_url = urljoin(wayback, base_url)

downloaded = set()
site_dir = Path("android-playmarket-site")
site_dir.mkdir(parents=True, exist_ok=True)

def save_file(url, content):
    parsed = urlparse(url)
    clean_path = parsed.netloc + parsed.path
    clean_path = clean_path.replace(":", "_")  # Windows-safe
    path = site_dir / clean_path.strip("/")
    if not path.suffix:
        path = path / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


def download(url):
    if url in downloaded: return
    downloaded.add(url)
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            save_file(url.replace(wayback, base_url), r.content)
    except Exception as e:
        print(f"Не вдалося завантажити {url}: {e}")

def rewrite_links(soup, tag, attr):
    for el in soup.find_all(tag):
        link = el.get(attr)
        if link and (link.startswith("/") or base_url in link):
            full = urljoin(wayback, link)
            download(full)
            new = link.replace(wayback, "").replace(base_url, "/")
            el[attr] = new

# Головна сторінка
resp = requests.get(start_url)
soup = BeautifulSoup(resp.content, "html.parser")

rewrite_links(soup, "link", "href")
rewrite_links(soup, "script", "src")
rewrite_links(soup, "img", "src")
rewrite_links(soup, "a", "href")

with open(site_dir / "index.html", "w", encoding="utf-8") as f:
    f.write(str(soup))

# ZIP-архів
with zipfile.ZipFile("android-playmarket.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, _, files in os.walk(site_dir):
        for file in files:
            path = Path(root) / file
            zipf.write(path, path.relative_to(site_dir))

print("🎉 Готово: android-playmarket.zip")
