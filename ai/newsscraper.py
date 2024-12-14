# 기본 라이브러리 관련
import os
import requests
import time

# 크롤링 관련
from bs4 import BeautifulSoup

# LangChain 관련
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# 진행 상황 표시 관련
from tqdm import tqdm

# 프롬프트 관련
from prompts import summarize_news_prompt


# 뉴스 크롤링 및 요약
class NewsScraper:
    def __init__(self, openai_api_key):
        self.base_url = "https://news.naver.com/section/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }
        self.llm = ChatOpenAI(model='gpt-4o', openai_api_key=openai_api_key)

    def fetch_article_links(self, sid, max_results=2):
        try:
            url = f"{self.base_url}{sid}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            a_tags = soup.find_all("a")

            tag_list = []
            for a in a_tags:
                if "href" in a.attrs and "article" in a["href"] and not any(x in a["href"] for x in ["RANKING", "comment"]):
                    tag_list.append(a["href"])

            return list(set(tag_list))[:max_results]
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching article links for sid {sid}: {e}")
            return []

    def fetch_article_content(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            # 요청 간격 설정
            time.sleep(1)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            title_selector = "#title_area > span"
            date_selector = "#ct > div.media_end_head.go_trans > div.media_end_head_info.nv_notrans > div.media_end_head_info_datestamp > div:nth-child(1) > span"
            main_selector = "#dic_area"
            image_selector = "#img1"  # 이미지 선택자

            title = soup.select_one(title_selector).get_text(strip=True)
            date = soup.select_one(date_selector).get_text(strip=True)
            main = soup.select_one(main_selector).get_text(strip=True)
            image = soup.select_one(image_selector)

            image_url = image['data-src'] if image else None

            return {"title": title, "date": date, "main": main, "image_url": image_url}
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching article content: {e}")
            return {}
        except AttributeError:
            print("Could not find the article content.")
            return {}

    def scrape_articles(self):
        all_articles = []
        # 섹션 매핑
        sid_mapping = {
            100: '정치',
            101: '경제',
            102: '사회',
            103: '생활/문화',
            104: '세계',
            105: 'IT/과학'
        }

        for sid in range(100, 106):
        # for sid in [100]:
            # 섹션 이름 가져오기(default: 기타)
            category = sid_mapping.get(sid, '기타')
            # 뉴스 내용 크롤링
            article_links = self.fetch_article_links(sid)

            for link in tqdm(article_links, desc=f"Scraping {category}"):
                # 기사 내용 추출
                article_content = self.fetch_article_content(link)
                if article_content:
                    article_content["url"] = link
                    article_content["section"] = sid
                    all_articles.append(article_content)
        return all_articles

    def summarize_news(self, news_list):
        # 프롬프트 템플릿 정의
        prompt_template = PromptTemplate.from_template(
            summarize_news_prompt
        )

        # Chain 구성
        chain = prompt_template | self.llm

        summaries = []
        for news in tqdm(news_list):
            # 각 뉴스 기사의 본문을 요약
            summary = chain.invoke({"content": news['main']})

            # 제목 및 이미지, 링크, 요약 저장
            summaries.append({
                'title': news['title'],
                'url': news['url'],
                'summary': summary.content,
                'img': news['image_url'],
            })
        return summaries