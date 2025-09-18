import os
import time
import random
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# The complete list of OpenAI documentation pages to download
URLS_TO_DOWNLOAD = [
    "https://platform.openai.com/docs/introduction",
    "https://platform.openai.com/docs/quickstart",
    "https://platform.openai.com/docs/tutorials/assistant-intro",
    "https://platform.openai.com/docs/api-reference/authentication",
    "https://platform.openai.com/docs/api-reference/assistants",
    "https://platform.openai.com/docs/api-reference/audio",
    "https://platform.openai.com/docs/api-reference/chat",
    "https://platform.openai.com/docs/api-reference/embeddings",
    "https://platform.openai.com/docs/api-reference/files",
    "https://platform.openai.com/docs/api-reference/fine-tuning",
    "https://platform.openai.com/docs/api-reference/images",
    "https://platform.openai.com/docs/api-reference/models",
    "https://platform.openai.com/docs/api-reference/moderations",
    "https://platform.openai.com/docs/api-reference/making-requests",
    "https://platform.openai.com/docs/api-reference/error-codes",
    "https://platform.openai.com/docs/models",
    "https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo",
    "https://platform.openai.com/docs/models/gpt-3-5-turbo",
    "https://platform.openai.com/docs/models/embeddings",
    "https://platform.openai.com/docs/models/dall-e",
    "https://platform.openai.com/docs/models/tts",
    "https://platform.openai.com/docs/models/whisper",
    "https://platform.openai.com/docs/deprecations",
    "https://platform.openai.com/docs/assistants/overview",
    "https://platform.openai.com/docs/assistants/how-it-works",
    "https://platform.openai.com/docs/assistants/tools",
    "https://platform.openai.com/docs/guides/text-generation",
    "https://platform.openai.com/docs/guides/function-calling",
    "https://platform.openai.com/docs/guides/text-generation/json-mode",
    "https://platform.openai.com/docs/guides/text-generation/reproducible-outputs",
    "https://platform.openai.com/docs/guides/text-generation/log-probabilities",
    "https://platform.openai.com/docs/guides/embeddings",
    "https://platform.openai.com/docs/guides/fine-tuning",
    "https://platform.openai.com/docs/guides/images",
    "https://platform.openai.com/docs/guides/speech-to-text",
    "https://platform.openai.com/docs/guides/text-to-speech",
    "https://platform.openai.com/docs/guides/moderation",
    "https://platform.openai.com/docs/guides/rate-limits",
    "https://platform.openai.com/docs/guides/error-mitigation",
    "https://platform.openai.com/docs/guides/safety-best-practices",
    "https://platform.openai.com/docs/guides/production-best-practices",
    "https://platform.openai.com/docs/libraries/python-library",
    "https://platform.openai.com/docs/libraries/node-js-library",
    "https://platform.openai.com/docs/libraries/azure-openai-support",
    "https://platform.openai.com/docs/billing/overview",
    "https://platform.openai.com/docs/billing/usage-tracking",
    "https://platform.openai.com/docs/billing/limits",
]


def download_with_playwright(urls, output_dir):
    """
    Downloads pages from a list of URLs using Playwright to bypass bot detection.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with sync_playwright() as p:
        # Launch a headless browser (it runs in the background)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in urls:
            try:
                # Add a polite, random delay to mimic human behavior
                delay = random.uniform(2, 5)
                print(f"Waiting for {delay:.2f} seconds...")
                time.sleep(delay)

                print(f"Navigating to {url}...")
                # Go to the page and wait for the network to be idle, ensuring all resources are loaded
                page.goto(url, timeout=60000, wait_until="networkidle")

                # Get the page's final HTML content after JavaScript has run
                content = page.content()

            except PlaywrightTimeoutError:
                print(f"❌ Timeout error when trying to load {url}")
                continue
            except Exception as e:
                print(f"❌ An unexpected error occurred for {url}: {e}")
                continue

            # --- The file saving logic is the same as before ---
            parsed_url = urlparse(url)
            path = parsed_url.path.lstrip("/")

            if not os.path.splitext(path)[1]:
                path = os.path.join(path, "index.html")

            file_path = os.path.join(output_dir, path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Saved {url} to {file_path}")

        browser.close()
    print("\n🚀 Documentation download complete!")


if __name__ == "__main__":
    OUTPUT_DIR = "/home/robbie/cartrita-ai-os/docs/open-ai-docs"
    download_with_playwright(URLS_TO_DOWNLOAD, OUTPUT_DIR)
