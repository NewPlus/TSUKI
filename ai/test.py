import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

class EmailSender:
    def __init__(self):
        load_dotenv()
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

# 사용 예시
email_sender = EmailSender()

recipient_email = 'lyh19990326@gmail.com'
subject = '제목: 파이썬으로 gmail 보내기'
body = '내용 : 본문 내용'

email_sender.send_email(recipient_email, subject, body)
email_sender.close()