import requests
from bs4 import BeautifulSoup
import re
import os
from concurrent.futures import ThreadPoolExecutor


# 爬取网页内容的函数
def scrape_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch {url}, status code: {response.status_code}")
        return None


# 解析帮助中心主页，获取所有文章链接
def get_all_links(base_url):
    page_content = scrape_page(base_url)
    if not page_content:
        return []
    soup = BeautifulSoup(page_content, 'html.parser')
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('/help/') and 'notion-academy' not in href.lower() and 'guides' not in href.lower():
            full_url = f"https://www.notion.so{href}"
            if full_url not in links:
                links.append(full_url)
    return links


# 从文章页面提取核心内容
def extract_core_content(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    content = []
    current_section = []

    # 提取标题和段落
    for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol']):
        text = element.get_text(strip=True)
        if not re.search(
                r'Company|Download|Resources|Notion for|AI|Docs|Wikis|Projects|Calendar|Sites|Templates|Product|Personal|Request a demo|Log in|Get Notion free|Help Center|Reference',
                text):
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

    i = 0
    while i < len(content):
        part = content[i]
        # 确保标题和其后的段落保持在一起
        if current_length + len(part) + 1 > max_length and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(part)
        current_length += len(part) + 1

        i += 1

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return '\n\n\n'.join(chunks)


# 多线程抓取网页内容并保存
def scrape_and_save(link, output_directory):
    print(f"Scraping {link}")
    page_content = scrape_page(link)
    if page_content:
        core_content = extract_core_content(page_content)
        split_core_content = split_content(core_content)
        # 使用标题作为文件名，去除不合法的文件名字符
        title = core_content[0].split('\n')[0] if core_content else "Untitled"
        file_name = re.sub(r'[^a-zA-Z0-9-_ ]', '', title) + '.txt'
        file_path = os.path.join(output_directory, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(split_core_content)


# 主函数，抓取所有帮助文章
def scrape_notion_help():
    base_url = "https://www.notion.so/help"
    all_links = get_all_links(base_url)

    output_directory = "/Users/fengyu/Downloads/myproject/workspace/crawlerLLM"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # 使用线程池来进行多线程抓取
    with ThreadPoolExecutor(max_workers=10) as executor:
        for link in all_links:
            executor.submit(scrape_and_save, link, output_directory)
    print("处理完毕!")


if __name__ == "__main__":
    scrape_notion_help()
