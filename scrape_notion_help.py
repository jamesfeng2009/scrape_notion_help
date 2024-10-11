import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

# 定义要抓取的页面 URL 和保存文件的路径
base_url = "https://www.notion.so/help"
save_path = "/Users/fengyu/Downloads/myproject/workspace/crawlerLLM"

# 创建保存文件的目录
if not os.path.exists(save_path):
    os.makedirs(save_path)


# 获取帮助中心的页面内容
def get_page_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve the page: {url}")
        return None


# 从帮助中心主页获取所有文章链接
def get_all_article_links(content):
    soup = BeautifulSoup(content, "html.parser")
    article_links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        # 只保留 /help/ 路径下的链接，忽略 /help/guides 和 Notion Academy 的内容
        if href.startswith("/help/") and not href.startswith("/help/guides") and not href.startswith("#"):
            article_links.append(full_url)
    # 打印所有抓取到的链接
    print(f"All article links: {article_links}")
    return list(set(article_links))


# 将文章分割为小片段，确保标题和段落保存在一起
def split_article_text(article_text, max_length=750):
    paragraphs = article_text.split("\n")
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) > max_length:
            # 确保当前片段按语义完整保存上下文
            if len(paragraph) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                chunks.append(paragraph.strip())
                current_chunk = ""
            else:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n" + paragraph
            else:
                current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


# 提取每篇文章的标题和内容，并保存为 .txt 文件
def save_article(link):
    print(f"Processing: {link}")
    content = get_page_content(link)
    if content:
        soup = BeautifulSoup(content, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else "untitled"

        article_body = soup.find("body")

        if article_body:
            # 提取标题和内容组合在一起
            sections = article_body.find_all(["h2", "p", "span"])
            combined_sections = []
            current_title = ""
            current_content = ""

            for section in sections:
                if section.name == "h2" or (section.name == "span" and section.find_parent("h2")):
                    # 保存之前的内容块
                    if current_title or current_content:
                        combined_sections.append(f"{current_title}\n{current_content}".strip())
                    # 处理新的标题
                    current_title = section.get_text(strip=True)
                    current_content = ""
                elif section.name == "p":
                    current_content += section.get_text(strip=True) + "\n"

            # 保存最后一个内容块
            if current_title or current_content:
                combined_sections.append(f"{current_title}\n{current_content}".strip())

            article_text = "\n".join(combined_sections)

            # 去掉文章开头和结尾的无关内容
            EXCLUDE_PATTERNS = re.compile(
                r'Company|Download|Resources|Notion for|AI|Docs|Wikis|Projects|Calendar|Sites|Templates|Product|Personal|Request a demo|Log in|Get Notion free|Help Center|Reference'
            )

            lines = article_text.splitlines()
            cleaned_lines = [line for line in lines if not EXCLUDE_PATTERNS.search(line)]
            article_text = "\n".join(cleaned_lines).strip()

            # 分割文章为小片段，确保标题和段落保存在一起，允许片段长度超过750个字符以保留上下文
            chunks = split_article_text(article_text)

            # 保存每个片段为 .txt 文件
            for idx, chunk in enumerate(chunks):
                file_name = f"{title}_part_{idx + 1}.txt".replace("/", "-").replace("\\", "-").replace(":",
                                                                                                       "-")  # 替换不合法字符
                file_path = os.path.join(save_path, file_name)
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(chunk)
                print(f"Saved: {file_path}")
        else:
            print(f"No article content found for: {link}")


# 主函数
def main():
    main_page_content = get_page_content(base_url)
    if main_page_content:
        article_links = get_all_article_links(main_page_content)
        print(f"Found {len(article_links)} articles.")

        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(save_article, article_links)


if __name__ == "__main__":
    main()
