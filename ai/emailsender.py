# 기본 라이브러리 관련
from datetime import datetime

# Email 관련
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 프롬프트 관련
from prompts import (html_news_letter_body, 
                     html_news_letter_footer, 
                     html_news_letter_header)


# 이메일 발송
class EmailSender:
    def __init__(self, sender_email, sender_password):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp = smtplib.SMTP('smtp.gmail.com', 587)
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.login(self.sender_email, self.sender_password)
        self.msg = MIMEMultipart()

    # 이메일 발송
    def send_email(self, recipient_email, subject, news_list):
        self.msg['Subject'] = subject
        self.msg['From'] = self.sender_email
        self.msg['To'] = recipient_email
        # 이메일 본문 구성 - 헤더
        html_content = html_news_letter_header

        # 이메일 본문 구성 - 본문
        for i, news in enumerate(news_list, start=1):
            # 각 뉴스 기사 본문 구성
            html_content += html_news_letter_body.format(content=f"""
                <div class="article">
                    <h2 class="article-title">{i}. {news['title']}</h2>
                    <div class="article-meta">
                        {datetime.now().strftime("%Y-%m-%d")}
                    </div>
                    <img class="article-image" src="{news['img']}" alt="Article image">
                    <p class="article-excerpt">
                        {news['summary']}
                    </p>
                    <a href="{news['url']}" class="read-more">자세히 보기</a>
                </div>
            """)
        # 이메일 본문 구성 - 푸터
        html_content += html_news_letter_footer
        self.msg.attach(MIMEText(html_content, 'html'))
        
        # 이메일 발송
        self.smtp.sendmail(self.sender_email, recipient_email, self.msg.as_string())

    def close(self):
        self.smtp.quit()
