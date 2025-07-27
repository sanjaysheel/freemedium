# app.py
from flask import Flask, request, jsonify, render_template
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import hashlib
import os

app = Flask(__name__)
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def clean_filename(url):
    return hashlib.md5(url.encode()).hexdigest() + ".html"

def fetch_article(url):
    filename = os.path.join(CACHE_DIR, clean_filename(url))
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()

    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")

    # Attempt to extract readable content
    article = soup.find("article")
    if not article:
        article = soup.find("div", {"class": "postArticle-content"})

    title = soup.title.string if soup.title else "No title"
    content = article.prettify() if article else "<p>Content not found or blocked.</p>"
    full_html = f"""
    <html>
    <head><title>{title}</title></head>
    <body><h1>{title}</h1>{content}<hr><p><a href='{url}'>Original Source</a></p></body>
    </html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_html)

    return full_html

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/read", methods=["POST"])
def read():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided."}), 400

    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        return jsonify({"error": "Invalid URL."}), 400

    try:
        article_html = fetch_article(url)
        return jsonify({"html": article_html})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
