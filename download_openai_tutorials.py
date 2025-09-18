#!/usr/bin/env python3
"""
OpenAI Tutorials Downloader
Downloads comprehensive tutorial content from OpenAI Platform documentation.

Target: https://platform.openai.com/docs/tutorials/
Output: /home/robbie/cartrita-ai-os/docs/open-ai-docs/tutorials/
"""

import os
import json
import asyncio
import aiohttp
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re


class OpenAITutorialsDownloader:
    def __init__(self):
        self.base_url = "https://platform.openai.com"
        self.tutorials_url = "https://platform.openai.com/docs/tutorials"
        self.output_dir = Path(
            "/home/robbie/cartrita-ai-os/docs/open-ai-docs/tutorials"
        )
        self.session = None
        self.downloaded_urls = set()

        # Comprehensive tutorial targets
        self.tutorial_targets = [
            "web-qa",  # Web crawl tutorial
            "meeting-minutes",  # Meeting minutes tutorial
            "how-to-build-an-ai-that-can-answer-questions-about-your-website",
            "how-to-answer-questions-using-embeddings-based-search",
            "semantic-search",
            "question-answering",
            "file-q-and-a",
            "website-q-and-a",
            "summarization",
            "text-generation",
            "embeddings",
            "fine-tuning",
            "vision",
            "audio",
            "assistants",
            "function-calling",
        ]

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> tuple[str, str]:
        """Fetch page content with error handling."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"✓ Downloaded: {url}")
                    return content, ""
                else:
                    error = f"HTTP {response.status}"
                    print(f"✗ Failed: {url} - {error}")
                    return "", error
        except Exception as e:
            error = str(e)
            print(f"✗ Error: {url} - {error}")
            return "", error

    def clean_filename(self, name: str) -> str:
        """Clean filename for filesystem compatibility."""
        # Remove/replace invalid characters
        cleaned = re.sub(r'[<>:"/\\|?*]', "-", name)
        cleaned = re.sub(r"\s+", "-", cleaned)
        cleaned = cleaned.strip("-")
        return cleaned[:100]  # Limit length

    def extract_content(self, html: str, url: str) -> dict:
        """Extract structured content from HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        content = {
            "url": url,
            "title": "",
            "description": "",
            "content": "",
            "code_examples": [],
            "sections": [],
            "navigation": [],
        }

        # Extract title
        title_tag = soup.find("h1") or soup.find("title")
        if title_tag:
            content["title"] = title_tag.get_text().strip()

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            content["description"] = meta_desc["content"]

        # Extract main content
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_="content")
        )
        if not main_content:
            main_content = soup.find("body")

        if main_content:
            # Extract sections
            sections = main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
            for section in sections:
                level = int(section.name[1])
                text = section.get_text().strip()
                if text:
                    content["sections"].append(
                        {"level": level, "title": text, "anchor": section.get("id", "")}
                    )

            # Extract code examples
            code_blocks = main_content.find_all(["pre", "code"])
            for i, code in enumerate(code_blocks):
                code_text = code.get_text().strip()
                if len(code_text) > 20:  # Only substantial code blocks
                    language = ""
                    # Try to detect language from class
                    if code.get("class"):
                        for cls in code["class"]:
                            if cls.startswith("language-"):
                                language = cls.replace("language-", "")
                                break

                    content["code_examples"].append(
                        {"index": i, "language": language, "code": code_text}
                    )

            # Extract clean text content
            content["content"] = main_content.get_text().strip()

        # Extract navigation/TOC
        nav_elements = soup.find_all(["nav", "aside"])
        for nav in nav_elements:
            links = nav.find_all("a", href=True)
            for link in links:
                href = link["href"]
                if href.startswith("/docs/"):
                    content["navigation"].append(
                        {"text": link.get_text().strip(), "href": href}
                    )

        return content

    def save_content(self, content: dict, filename: str):
        """Save content to markdown file."""
        filepath = self.output_dir / f"{filename}.md"

        markdown_content = f"""# {content['title']}

**Source:** {content['url']}

**Description:** {content['description']}

---

{content['content']}

"""

        # Add code examples section
        if content["code_examples"]:
            markdown_content += "\n## Code Examples\n\n"
            for i, example in enumerate(content["code_examples"]):
                markdown_content += f"### Example {i+1}\n\n"
                if example["language"]:
                    markdown_content += f"```{example['language']}\n"
                else:
                    markdown_content += "```\n"
                markdown_content += f"{example['code']}\n```\n\n"

        # Add sections outline
        if content["sections"]:
            markdown_content += "\n## Sections Outline\n\n"
            for section in content["sections"]:
                indent = "  " * (section["level"] - 1)
                markdown_content += f"{indent}- {section['title']}\n"

        # Save markdown file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Save JSON metadata
        json_filepath = self.output_dir / f"{filename}.json"
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved: {filepath}")

    async def discover_tutorial_urls(self) -> list[str]:
        """Discover all tutorial URLs from the main tutorials page."""
        print("🔍 Discovering tutorial URLs...")

        urls = []

        # Direct tutorial URLs
        for target in self.tutorial_targets:
            url = f"{self.tutorials_url}/{target}"
            urls.append(url)

        # Fetch main tutorials page to discover more
        main_content, error = await self.fetch_page(self.tutorials_url)
        if main_content:
            soup = BeautifulSoup(main_content, "html.parser")

            # Find all tutorial links
            links = soup.find_all("a", href=True)
            for link in links:
                href = link["href"]
                if "/docs/tutorials/" in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in urls:
                        urls.append(full_url)

        # Remove duplicates and sort
        urls = list(set(urls))
        urls.sort()

        print(f"🎯 Found {len(urls)} tutorial URLs")
        return urls

    async def download_tutorial(self, url: str):
        """Download and process a single tutorial."""
        if url in self.downloaded_urls:
            return

        self.downloaded_urls.add(url)

        # Fetch content
        html, error = await self.fetch_page(url)
        if not html:
            return

        # Extract content
        content = self.extract_content(html, url)

        # Generate filename
        url_path = urlparse(url).path
        filename = url_path.replace("/docs/tutorials/", "").replace("/", "-")
        if not filename:
            filename = "index"
        filename = self.clean_filename(filename)

        # Save content
        self.save_content(content, filename)

        # Small delay to be respectful
        await asyncio.sleep(0.5)

    async def download_all_tutorials(self):
        """Download all tutorials."""
        print("🚀 Starting OpenAI Tutorials download...")
        start_time = time.time()

        # Discover tutorial URLs
        urls = await self.discover_tutorial_urls()

        # Download tutorials with concurrency limit
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests

        async def download_with_semaphore(url):
            async with semaphore:
                await self.download_tutorial(url)

        # Execute downloads
        tasks = [download_with_semaphore(url) for url in urls]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Create comprehensive index
        await self.create_tutorials_index()

        elapsed = time.time() - start_time
        print(f"✅ Download completed in {elapsed:.1f} seconds")
        print(f"📁 Files saved to: {self.output_dir}")

    async def create_tutorials_index(self):
        """Create comprehensive index of all downloaded tutorials."""
        print("📋 Creating tutorials index...")

        index_content = """# OpenAI Tutorials Documentation

This directory contains comprehensive tutorials from OpenAI Platform documentation.

**Source:** https://platform.openai.com/docs/tutorials/

## Available Tutorials

"""

        # List all downloaded files
        md_files = sorted(self.output_dir.glob("*.md"))

        for md_file in md_files:
            if md_file.name == "README.md":
                continue

            # Read title from file
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if first_line.startswith("# "):
                        title = first_line[2:]
                    else:
                        title = md_file.stem
            except:
                title = md_file.stem

            index_content += f"- [{title}]({md_file.name})\n"

        index_content += f"""

## Download Information

- **Downloaded:** {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Total Files:** {len(md_files)}
- **Target URL:** https://platform.openai.com/docs/tutorials/

## File Types

- `.md` files: Human-readable markdown documentation
- `.json` files: Structured metadata and content

## Key Tutorials

### Web Crawling & Q&A
- Web crawl tutorial with embeddings
- Website Q&A implementation
- Question answering with embeddings-based search

### Meeting Minutes
- Meeting minutes processing and summarization
- Audio transcription workflows

### Q&A Systems
- File-based Q&A systems
- Semantic search implementation
- Embeddings-based question answering

## Usage

Each tutorial includes:
- Complete step-by-step instructions
- Code examples with syntax highlighting
- Implementation details and best practices
- Links to related resources

"""

        # Save index
        index_path = self.output_dir / "README.md"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)

        print(f"✓ Index created: {index_path}")


async def main():
    """Main execution function."""
    async with OpenAITutorialsDownloader() as downloader:
        await downloader.download_all_tutorials()


if __name__ == "__main__":
    asyncio.run(main())
