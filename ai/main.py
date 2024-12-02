from fastapi import FastAPI
import tavily
from langchain import LLMChain
from langchain.llms import OpenAI
from whisper import Whisper
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio

app = FastAPI()

# 뉴스 수집을 위한 엔드포인트
@app.get("/collect-news")
async def collect_news():
    # tavily 라이브러리를 사용하여 뉴스 수집
    news_data = tavily.scrape_news(
        sources=["New York Times", "BBC"],  # 뉴스 소스
        time_range="24h"  # 지난 24시간 동안의 뉴스
    )
    
    # 수집된 뉴스 데이터를 반환
    return {"news": news_data}

# 텍스트 뉴스레터 작성 기능
@app.post("/generate-newsletter")
async def generate_newsletter(news_data: dict):
    # GPT-4 모델을 사용하여 뉴스 요약 및 뉴스레터 작성
    llm = OpenAI(model="gpt-4o")
    chain = LLMChain(llm=llm, prompt="뉴스 데이터를 요약하여 뉴스레터를 작성하세요.")
    
    # 뉴스 데이터를 요약하여 뉴스레터 생성
    newsletter = chain.run(news_data)
    
    # 생성된 뉴스레터 반환
    return {"newsletter": newsletter}

# 음성 변환 및 이메일 전송 기능
@app.post("/send-newsletter")
async def send_newsletter(newsletter: str, recipient_email: str):
    # Whisper 모델을 사용하여 텍스트를 음성으로 변환
    whisper = Whisper()
    audio_data = whisper.text_to_speech(newsletter)
    
    # 이메일 설정
    sender_email = "your_email@example.com"
    password = "your_password"
    
    # 이메일 메시지 생성
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Your Daily AI Voice Newsletter"
    
    # 텍스트와 음성 파일 첨부
    msg.attach(MIMEText(newsletter, 'plain'))
    msg.attach(MIMEAudio(audio_data, 'wav'))
    
    # 이메일 전송
    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
    
    return {"status": "Newsletter sent successfully"}
