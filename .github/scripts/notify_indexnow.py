"""Notify IndexNow of SOLACE's public sitemap after a successful deployment.

Uses only public URLs. Acceptance is not a promise of crawling or ranking.
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET

HOST = "solacemontana.com"
BASE = "https://" + HOST
KEY = "38c1e28a8539c38195bf2c72b71a6f13"
KEY_URL = BASE + "/" + KEY + ".txt"


def read_public(url):
    request = urllib.request.Request(url, headers={"User-Agent": "SOLACE-IndexNow/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.geturl() != url:
            raise RuntimeError("Unexpected redirect: " + url)
        return response.read().decode("utf-8")


def main():
    if read_public(KEY_URL).strip() != KEY:
        raise RuntimeError("The deployed IndexNow ownership file does not match.")
    sitemap = ET.fromstring(read_public(BASE + "/sitemap.xml"))
    urls = list(dict.fromkeys(
        loc.text.strip() for loc in sitemap.findall(
            "{http://www.sitemaps.org/schemas/sitemap/0.9}url/"
            "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        ) if loc.text
    ))
    if not urls or len(urls) > 100:
        raise RuntimeError("Unexpected public sitemap size.")
    for url in urls:
        if not url.startswith(BASE + "/") or "?" in url or "#" in url:
            raise RuntimeError("Unexpected sitemap URL: " + url)
        html = read_public(url)
        if re.search(r'<meta\b[^>]*\bcontent\s*=\s*["\'][^"\']*noindex', html, re.I):
            raise RuntimeError("Noindex page must not be submitted: " + url)
    payload = json.dumps({
        "host": HOST, "key": KEY, "keyLocation": KEY_URL, "urlList": urls
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8",
                 "User-Agent": "SOLACE-IndexNow/1.0"},
        method="POST"
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status not in (200, 202):
            raise RuntimeError("Unexpected IndexNow status: " + str(response.status))
        print("IndexNow accepted " + str(len(urls)) + " public URLs; HTTP "
              + str(response.status) + ". This does not confirm indexing.")


if __name__ == "__main__":
    main()
