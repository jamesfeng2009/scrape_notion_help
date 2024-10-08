import requests
from bs4 import BeautifulSoup
import re
import os
from concurrent.futures import ThreadPoolExecutor

# 常量设置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
EXCLUDE_PATTERNS = re.compile(
    r'Company|Download|Resources|Notion for|AI|Docs|Wikis|Projects|Calendar|Sites|Templates|Product|Personal|Request a demo|Log in|Get Notion free|Help Center|Reference')
OUTPUT_DIRECTORY = "/Users/fengyu/Downloads/myproject/workspace/crawlerLLM"
BASE_URL = "https://www.notion.so/help"


# 爬取网页内容的函数
def scrape_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}, error: {e}")
        return None


# 解析帮助中心主页，获取所有文章链接
def get_all_links(base_url):
    page_content = scrape_page(base_url)
    if not page_content:
        return []
    soup = BeautifulSoup(page_content, 'html.parser')
    links = set(
        f"https://www.notion.so{a_tag['href']}"
        for a_tag in soup.find_all('a', href=True)
        if
        a_tag['href'].startswith('/help/') and 'notion-academy' not in a_tag['href'].lower() and 'guides' not in a_tag[
            'href'].lower()
    )
    return list(links)


# 从文章页面提取核心内容
def extract_core_content(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    content = []
    current_section = []

    # 尝试提取所有相关标签的内容
    for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'div', 'span']):
        text = element.get_text(strip=True)
        if not EXCLUDE_PATTERNS.search(text):
            # 如果遇到标题，且当前段落不为空，则先保存当前段落
            if element.name in ['h1', 'h2', 'h3'] and current_section:
                content.append('\n'.join(current_section))
                current_section = []
            current_section.append(text)

    if current_section:
        content.append('\n'.join(current_section))

    return content


# 将内容分割为较小部分，确保标题和相关段落保持在一起
def split_content(content, max_length=750):
    chunks = []
    current_chunk = []
    current_length = 0

    for part in content:
        if current_length + len(part) + 1 > max_length and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(part)
        current_length += len(part) + 1

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return '\n\n\n'.join(chunks)


# 多线程抓取网页内容并保存
def scrape_and_save(link, output_directory):
    print(f"Scraping {link}")
    page_content = scrape_page(link)
    if page_content:
        core_content = extract_core_content(page_content)

        # 验证抓取是否完整
        if len(core_content) == 0:
            print(f"Warning: No content extracted from {link}")
            return

        split_core_content = split_content(core_content)
        title = core_content[0].split('\n')[0] if core_content else "Untitled"
        file_name = re.sub(r'[^a-zA-Z0-9-_ ]', '', title)[:50] + '.txt'  # 限制文件名长度，避免过长
        file_path = os.path.join(output_directory, file_name)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(split_core_content)
        except OSError as e:
            print(f"Failed to write to file {file_path}, error: {e}")


# 主函数，抓取所有帮助文章
def scrape_notion_help():
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)

    all_links = get_all_links(BASE_URL)

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(lambda link: scrape_and_save(link, OUTPUT_DIRECTORY), all_links)


if __name__ == "__main__":
    scrape_notion_help()
