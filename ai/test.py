import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from tavily import TavilyClient, MissingAPIKeyError, InvalidAPIKeyError, UsageLimitExceededError
from datetime import datetime


load_dotenv()


class NewsScraper:
    def __init__(self):
        try:
            self.client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        except MissingAPIKeyError:
            print("API key 오류")
            raise

    def fetch_latest_news(self, query, max_results=5):
        try:
            response = self.client.search(query, max_results=max_results, topic="news")
            sorted_news = sorted(response['results'], key=lambda x: x.get('views', 0), reverse=True)
            return sorted_news
        except InvalidAPIKeyError:
            print("Invalid API key 오류")
        except UsageLimitExceededError:
            print("Usage limit exceeded 오류")
        except Exception as e:
            print(f"예기치 않은 오류 발생: {e}")


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


news_scraper = NewsScraper()
latest_news = news_scraper.fetch_latest_news("latest news")
news_list = []
for news in latest_news:
    print(f"제목: {news['title']}")
    print(f"URL: {news['url']}")
    print(f"내용: {news['content']}\n")
    print("==========================================")
    news_list.append(news)


email_sender = EmailSender()

recipient_email = 'lyh19990326@gmail.com'
subject = 'TSUKI News Letter - ' + datetime.now().strftime("%Y-%m-%d") + ' - Test'
body = ''
for news in news_list:
    body += f"제목: {news['title']}\nURL: {news['url']}\n내용: {news['content']}\n\n==========================================\n"

email_sender.send_email(recipient_email, subject, body)
email_sender.close()