# 기본 라이브러리 관련
import os
from dotenv import load_dotenv
from datetime import datetime

# 커스텀 클래스 관련
from newsscraper import NewsScraper
from emailsender import EmailSender


if __name__=='__main__':
    load_dotenv()

    # 뉴스 크롤링 및 요약
    news_scraper = NewsScraper(openai_api_key=os.getenv("OPENAI_API_KEY"))
    # 이메일 발송
    email_sender = EmailSender(sender_email=os.getenv("SENDER_EMAIL"), 
                              sender_password=os.getenv("SENDER_PASSWORD"))

    # 뉴스 크롤링
    articles = news_scraper.scrape_articles()

    # 뉴스 요약
    summarized_news = news_scraper.summarize_news(articles)

    # 뉴스 요약 출력
    for news in summarized_news:
        print(f"제목: {news['title']}")
        print(f"URL: {news['url']}")
        print(f"내용: {news['summary']}\n")
        print(f"이미지: {news['img']}\n")
        print("==========================================")

    # 이메일 발송 정보 - 발신자, 제목 등
    recipient_email = 'lyh19990326@gmail.com'
    subject = 'TSUKI News Letter - ' + datetime.now().strftime("%Y-%m-%d") + ' - Test'
    email_sender.send_email(recipient_email, subject, summarized_news)
    email_sender.close()
