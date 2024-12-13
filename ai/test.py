import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from tavily import TavilyClient, MissingAPIKeyError, InvalidAPIKeyError, UsageLimitExceededError
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from prompts import summarize_news_prompt
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


load_dotenv()


class NewsScraper:
    def __init__(self):
        self.base_url = "https://news.naver.com/section/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }

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
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            title_selector = "#title_area > span"
            date_selector = "#ct > div.media_end_head.go_trans > div.media_end_head_info.nv_notrans > div.media_end_head_info_datestamp > div:nth-child(1) > span"
            main_selector = "#dic_area"

            title = soup.select_one(title_selector).get_text(strip=True)
            date = soup.select_one(date_selector).get_text(strip=True)
            main = soup.select_one(main_selector).get_text(strip=True)

            return {"title": title, "date": date, "main": main}
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching article content: {e}")
            return {}
        except AttributeError:
            print("Could not find the article content.")
            return {}

    def scrape_articles(self):
        all_articles = []
        sid_mapping = {
            100: '정치',
            101: '경제',
            102: '사회',
            103: '생활/문화',
            104: '세계',
            105: 'IT/과학'
        }
        for sid in range(100, 106):
            category = sid_mapping.get(sid, '기타')  # 기본값 '기타'
            article_links = self.fetch_article_links(sid)
            for link in tqdm(article_links, desc=f"Scraping {category}"):
                article_content = self.fetch_article_content(link)
                if article_content:
                    article_content["url"] = link
                    article_content["section"] = sid
                    all_articles.append(article_content)
        return all_articles

    def summarize_news(self, news_list, api_key):
        llm = ChatOpenAI(model='gpt-4o', openai_api_key=api_key)
        summaries = []
        for news in tqdm(news_list):
            # 요약 프롬프트 생성
            prompt = summarize_news_prompt.format(content=news['main'])
            summary = llm.invoke(prompt)
            summaries.append({
                'title': news['title'],
                'url': news['url'],
                'summary': summary.content
            })
        return summaries


class EmailSender:
    def __init__(self):
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.password = os.getenv("SENDER_PASSWORD")
        self.smtp = smtplib.SMTP('smtp.gmail.com', 587)
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.login(self.sender_email, self.password)

    def send_email(self, recipient_email, subject, body):
        msg = MIMEText(body)
        msg['Subject'] = subject
        self.smtp.sendmail(self.sender_email, recipient_email, msg.as_string())

    def close(self):
        self.smtp.quit()


news_scraper = NewsScraper()  # 예: 경제 섹션
articles = news_scraper.scrape_articles()
summarized_news = news_scraper.summarize_news(articles, os.getenv("OPENAI_API_KEY"))
news_list = []
for news in summarized_news:
    print(f"제목: {news['title']}")
    print(f"URL: {news['url']}")
    print(f"내용: {news['summary']}\n")
    print("==========================================")
    news_list.append(news)


email_sender = EmailSender()

recipient_email = 'lyh19990326@gmail.com'
subject = 'TSUKI News Letter - ' + datetime.now().strftime("%Y-%m-%d") + ' - Test'
body = ''
for news in news_list:
    body += f"제목: {news['title']}\nURL: {news['url']}\n내용: {news['summary']}\n\n==========================================\n"

email_sender.send_email(recipient_email, subject, body)
email_sender.close()