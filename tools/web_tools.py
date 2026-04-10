from pathlib import Path
from urllib.parse import quote_plus, urlparse
import webbrowser

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


def _normalize_url(url):
    cleaned_url = url.strip()
    parsed_url = urlparse(cleaned_url)
    if parsed_url.scheme:
        return cleaned_url
    return f"https://{cleaned_url}"


def _format_search_results(results):
    lines = []
    for index, item in enumerate(results, start=1):
        title = item.get("title") or "Untitled"
        link = item.get("href") or item.get("url") or ""
        snippet = item.get("body") or item.get("snippet") or ""
        block = f"{index}. {title}"
        if link:
            block += f"\n{link}"
        if snippet:
            block += f"\n{snippet}"
        lines.append(block)
    return "\n\n".join(lines) if lines else "No results found."


def _require_requests():
    if requests is None:
        return "requests is not installed"
    return None


def search_web(query):
    if DDGS is None:
        return "duckduckgo-search is not installed"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        return _format_search_results(results)
    except Exception as e:
        return str(e)


def search_images(query):
    if DDGS is None:
        return "duckduckgo-search is not installed"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=5))
        return _format_search_results(results)
    except Exception as e:
        return str(e)


def open_url(url):
    try:
        normalized_url = _normalize_url(url)
        opened = webbrowser.open(normalized_url)
        if opened:
            return f"Opened: {normalized_url}"
        return f"Browser could not open: {normalized_url}"
    except Exception as e:
        return str(e)


def fetch_page(url):
    missing_dependency = _require_requests()
    if missing_dependency:
        return missing_dependency

    try:
        normalized_url = _normalize_url(url)
        response = requests.get(normalized_url, timeout=10)
        response.raise_for_status()
        if BeautifulSoup is None:
            return response.text[:4000]

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.stripped_strings)
        return text[:4000] or "No readable text found."
    except Exception as e:
        return str(e)


def get_weather(city):
    missing_dependency = _require_requests()
    if missing_dependency:
        return missing_dependency

    try:
        response = requests.get(f"https://wttr.in/{quote_plus(city)}?format=j1", timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data["current_condition"][0]
        description = current["weatherDesc"][0]["value"]
        temperature = current["temp_C"]
        feels_like = current["FeelsLikeC"]
        humidity = current["humidity"]
        return (
            f"Weather in {city}:\n"
            f"Condition: {description}\n"
            f"Temperature: {temperature} C\n"
            f"Feels like: {feels_like} C\n"
            f"Humidity: {humidity}%"
        )
    except Exception as e:
        return str(e)


def get_news(topic):
    if DDGS is None:
        return "duckduckgo-search is not installed"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(topic, max_results=5))
        return _format_search_results(results)
    except Exception:
        return search_web(f"{topic} latest news")


def download_file(url, path):
    missing_dependency = _require_requests()
    if missing_dependency:
        return missing_dependency

    try:
        normalized_url = _normalize_url(url)
        target_path = Path(path).expanduser()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(normalized_url, timeout=30)
        response.raise_for_status()
        target_path.write_bytes(response.content)
        return f"Downloaded file to: {target_path}"
    except Exception as e:
        return str(e)


def check_internet():
    missing_dependency = _require_requests()
    if missing_dependency:
        return missing_dependency

    try:
        response = requests.get("https://example.com", timeout=5)
        response.raise_for_status()
        return "Internet is working."
    except Exception as e:
        return f"Internet check failed: {e}"


def get_public_ip():
    missing_dependency = _require_requests()
    if missing_dependency:
        return missing_dependency

    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        return str(e)
