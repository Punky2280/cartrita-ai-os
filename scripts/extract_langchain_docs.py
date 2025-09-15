#!/usr/bin/env python3
"""
LangChain Documentation Extractor
Extracts comprehensive documentation from LangChain API reference
"""

import os
import re
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

class LangChainDocsExtractor:
    def __init__(self, base_url: str = "https://python.langchain.com/api_reference/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.visited_urls: Set[str] = set()
        self.docs_dir = Path("docs/langchain_extracted")
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def get_page_content(self, url: str) -> str:
        """Fetch page content with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return ""

    def extract_documentation_links(self, content: str, current_url: str) -> List[str]:
        """Extract all documentation links from a page"""
        soup = BeautifulSoup(content, 'html.parser')
        links = []

        # Find all links in the documentation
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)

            # Filter for LangChain documentation links
            if 'python.langchain.com' in full_url and full_url not in self.visited_urls:
                # Focus on API reference and important sections
                if any(section in full_url for section in [
                    '/api_reference/', '/docs/', '/langchain/',
                    '/community/', '/core/', '/openai/'
                ]):
                    links.append(full_url)

        return links

    def extract_page_documentation(self, url: str) -> Dict:
        """Extract documentation content from a page"""
        content = self.get_page_content(url)
        if not content:
            return {}

        soup = BeautifulSoup(content, 'html.parser')

        # Extract title
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else urlparse(url).path

        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')

        doc_data = {
            'url': url,
            'title': title_text,
            'sections': []
        }

        if main_content:
            # Extract code examples
            code_blocks = main_content.find_all(['pre', 'code'])
            doc_data['code_examples'] = [block.get_text(strip=True) for block in code_blocks]

            # Extract API signatures
            signatures = main_content.find_all(class_=re.compile(r'sig|signature|api'))
            doc_data['api_signatures'] = [sig.get_text(strip=True) for sig in signatures]

            # Extract parameters and returns
            params = main_content.find_all(class_=re.compile(r'param|parameter'))
            doc_data['parameters'] = [param.get_text(strip=True) for param in params]

            # Extract main text content
            for element in main_content.find_all(['h2', 'h3', 'p', 'li']):
                text = element.get_text(strip=True)
                if text and len(text) > 10:
                    doc_data['sections'].append({
                        'type': element.name,
                        'content': text
                    })

        return doc_data

    def save_documentation(self, doc_data: Dict, category: str = "general"):
        """Save extracted documentation to file"""
        if not doc_data:
            return

        # Create category directory
        category_dir = self.docs_dir / category
        category_dir.mkdir(exist_ok=True)

        # Generate filename from URL
        url_hash = hashlib.md5(doc_data['url'].encode()).hexdigest()[:8]
        filename = f"{doc_data['title'][:50].replace('/', '_')}_{url_hash}.json"
        filename = re.sub(r'[<>:"|?*]', '', filename)

        filepath = category_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)

        print(f"Saved: {filepath}")

    def categorize_url(self, url: str) -> str:
        """Categorize URL for organized storage"""
        if '/langchain_core/' in url or '/core/' in url:
            return 'core'
        elif '/langchain_community/' in url or '/community/' in url:
            return 'community'
        elif '/langchain_openai/' in url or '/openai/' in url:
            return 'openai'
        elif '/agents/' in url:
            return 'agents'
        elif '/chains/' in url:
            return 'chains'
        elif '/memory/' in url:
            return 'memory'
        elif '/prompts/' in url or '/prompt/' in url:
            return 'prompts'
        elif '/tools/' in url:
            return 'tools'
        elif '/callbacks/' in url:
            return 'callbacks'
        elif '/vectorstores/' in url:
            return 'vectorstores'
        elif '/llms/' in url:
            return 'llms'
        elif '/chat/' in url:
            return 'chat'
        elif '/retrievers/' in url:
            return 'retrievers'
        else:
            return 'general'

    def extract_all_documentation(self):
        """Main extraction process"""
        print(f"Starting extraction from {self.base_url}")

        # Start with main pages
        initial_urls = [
            f"{self.base_url}openai/index.html",
            f"{self.base_url}core/index.html",
            f"{self.base_url}community/index.html",
            f"{self.base_url}langchain/index.html",
        ]

        urls_to_visit = set(initial_urls)
        processed_count = 0
        max_pages = 500  # Limit to prevent infinite crawling

        while urls_to_visit and processed_count < max_pages:
            current_url = urls_to_visit.pop()

            if current_url in self.visited_urls:
                continue

            print(f"Processing ({processed_count + 1}/{max_pages}): {current_url}")
            self.visited_urls.add(current_url)

            # Extract documentation
            doc_data = self.extract_page_documentation(current_url)
            if doc_data:
                category = self.categorize_url(current_url)
                self.save_documentation(doc_data, category)

            # Get new links
            content = self.get_page_content(current_url)
            if content:
                new_links = self.extract_documentation_links(content, current_url)
                urls_to_visit.update(new_links)

            processed_count += 1

            # Be respectful to the server
            time.sleep(0.5)

        print(f"\nExtraction complete!")
        print(f"Total pages processed: {processed_count}")
        print(f"Documentation saved to: {self.docs_dir}")

        # Create summary
        self.create_summary()

    def create_summary(self):
        """Create a summary of extracted documentation"""
        summary = {
            'total_pages': len(self.visited_urls),
            'categories': {},
            'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        for category_dir in self.docs_dir.iterdir():
            if category_dir.is_dir():
                files = list(category_dir.glob('*.json'))
                summary['categories'][category_dir.name] = {
                    'file_count': len(files),
                    'files': [f.name for f in files[:10]]  # Sample files
                }

        summary_path = self.docs_dir / 'extraction_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary saved to: {summary_path}")

        # Create index
        self.create_documentation_index()

    def create_documentation_index(self):
        """Create an index of all extracted documentation"""
        index = {
            'agents': [],
            'chains': [],
            'llms': [],
            'tools': [],
            'memory': [],
            'prompts': [],
            'core_concepts': [],
            'examples': []
        }

        for category_dir in self.docs_dir.iterdir():
            if category_dir.is_dir():
                for json_file in category_dir.glob('*.json'):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            entry = {
                                'title': data.get('title', ''),
                                'url': data.get('url', ''),
                                'category': category_dir.name,
                                'file': str(json_file.relative_to(self.docs_dir)),
                                'has_code_examples': bool(data.get('code_examples')),
                                'has_api_signatures': bool(data.get('api_signatures'))
                            }

                            # Categorize for index
                            if 'agent' in data.get('title', '').lower():
                                index['agents'].append(entry)
                            elif 'chain' in data.get('title', '').lower():
                                index['chains'].append(entry)
                            elif 'llm' in data.get('title', '').lower():
                                index['llms'].append(entry)
                            elif 'tool' in data.get('title', '').lower():
                                index['tools'].append(entry)
                            elif 'memory' in data.get('title', '').lower():
                                index['memory'].append(entry)
                            elif 'prompt' in data.get('title', '').lower():
                                index['prompts'].append(entry)
                            elif data.get('code_examples'):
                                index['examples'].append(entry)
                            else:
                                index['core_concepts'].append(entry)
                        except json.JSONDecodeError:
                            print(f"Error reading {json_file}")

        index_path = self.docs_dir / 'documentation_index.json'
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)

        print(f"Index created: {index_path}")

if __name__ == "__main__":
    extractor = LangChainDocsExtractor()
    extractor.extract_all_documentation()