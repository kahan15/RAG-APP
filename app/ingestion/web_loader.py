from typing import List, Optional
import aiohttp
from bs4 import BeautifulSoup
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from playwright.async_api import async_playwright
import asyncio
from urllib.parse import urljoin, urlparse

async def process_webpage(
    url: str,
    is_dynamic: bool = False,
    max_depth: int = 1,
    visited_urls: Optional[set] = None
) -> List[Document]:
    """
    Process a webpage and convert it to a list of Document objects.
    
    Args:
        url: The URL to process
        is_dynamic: Whether the page requires JavaScript rendering
        max_depth: Maximum depth for crawling internal links
        visited_urls: Set of already visited URLs
        
    Returns:
        List of Document objects
    """
    if visited_urls is None:
        visited_urls = set()
    
    if url in visited_urls:
        return []
    
    visited_urls.add(url)
    
    # Create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    try:
        if is_dynamic:
            html_content = await get_dynamic_content(url)
        else:
            html_content = await get_static_content(url)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        # Extract main content
        main_content = extract_main_content(soup)
        
        # Create metadata
        metadata = {
            "url": url,
            "title": get_page_title(soup),
            "is_dynamic": is_dynamic
        }
        
        # Split content into chunks
        chunks = text_splitter.split_text(main_content)
        
        # Create documents
        documents = [
            Document(
                page_content=chunk,
                metadata=metadata
            )
            for chunk in chunks if chunk.strip()
        ]
        
        # Process internal links if depth allows
        if max_depth > 1:
            internal_links = get_internal_links(soup, url)
            for link in internal_links:
                if link not in visited_urls:
                    sub_documents = await process_webpage(
                        url=link,
                        is_dynamic=is_dynamic,
                        max_depth=max_depth - 1,
                        visited_urls=visited_urls
                    )
                    documents.extend(sub_documents)
        
        return documents
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return []

async def get_static_content(url: str) -> str:
    """Fetch static webpage content."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def get_dynamic_content(url: str) -> str:
    """Fetch JavaScript-rendered webpage content using Playwright."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until='networkidle')
            # Wait for dynamic content to load
            await asyncio.sleep(2)
            content = await page.content()
            return content
        finally:
            await browser.close()

def extract_main_content(soup: BeautifulSoup) -> str:
    """Extract main content from webpage, prioritizing article and main tags."""
    # Try to find main content containers
    main_content = None
    for selector in ['article', 'main', '[role="main"]', '#content', '.content']:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    if not main_content:
        # Fallback to body if no main content container found
        main_content = soup.body
    
    # Extract text from paragraphs and headings
    text_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    return "\n\n".join([element.get_text(strip=True) for element in text_elements])

def get_page_title(soup: BeautifulSoup) -> str:
    """Extract page title."""
    title = soup.title
    return title.string.strip() if title else ""

def get_internal_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Extract internal links from the webpage."""
    base_domain = urlparse(base_url).netloc
    internal_links = set()
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        absolute_url = urljoin(base_url, href)
        
        # Check if link is internal
        if urlparse(absolute_url).netloc == base_domain:
            internal_links.add(absolute_url)
    
    return list(internal_links) 