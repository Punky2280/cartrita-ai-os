import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def download_docs(base_url, output_dir):
    """
    Downloads the Pydantic documentation from the given URL.

    Args:
        base_url: The base URL of the documentation to download.
        output_dir: The directory where the documentation will be saved.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    visited_urls = set()
    session = requests.Session()

    def scrape(url):
        if url in visited_urls:
            return
        visited_urls.add(url)

        try:
            response = session.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return

        soup = BeautifulSoup(response.content, "html.parser")

        # Save the current page
        parsed_url = urlparse(url)
        path = parsed_url.path.lstrip("/")
        if not path or path.endswith("/"):
            path += "index.html"

        file_path = os.path.join(output_dir, path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Saved {url} to {file_path}")

        # Find and follow links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(url, href)
            parsed_absolute_url = urlparse(absolute_url)

            # Follow links within the same domain
            if parsed_absolute_url.netloc == parsed_url.netloc:
                scrape(absolute_url)

    scrape(base_url)
    print("\nDocumentation download complete!")


if __name__ == "__main__":
    BASE_URL = "https://docs.pydantic.dev/2.11/"
    OUTPUT_DIR = "/home/robbie/cartrita-ai-os/docs/pydantic-v2.11"
    download_docs(BASE_URL, OUTPUT_DIR)
