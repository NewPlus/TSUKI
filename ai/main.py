from fastapi import FastAPI, BackgroundTasks
import tavily
from langchain import LLMChain
from langchain.llms import OpenAI
from whisper import Whisper
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["SENDER_EMAIL"] = os.getenv("SENDER_EMAIL")
os.environ["SENDER_PASSWORD"] = os.getenv("SENDER_PASSWORD")

app = FastAPI()

# 동기 뉴스 수집
@app.get("/collect-news")
async def collect_news():
    news_data = await tavily.scrape_news_async(
        sources=["New York Times", "BBC"],
        time_range="24h"
    )
    return {"news": news_data}

# 비동기 뉴스레터 생성
@app.post("/generate-newsletter")
async def generate_newsletter(news_data: dict):
    llm = OpenAI(model="gpt-4o")
    chain = LLMChain(llm=llm, prompt="뉴스 데이터를 요약하여 뉴스레터를 작성하세요.")
    newsletter = await chain.run_async(news_data)
    return {"newsletter": newsletter}

# 비동기 음성 변환 및 이메일 전송
@app.post("/send-newsletter")
async def send_newsletter(newsletter: str, recipient_email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(convert_and_send_email, newsletter, recipient_email)
    return {"status": "Newsletter processing started"}

async def convert_and_send_email(newsletter: str, recipient_email: str):
    whisper = Whisper()
    audio_data = await whisper.text_to_speech_async(newsletter)
    
    sender_email = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Your Daily AI Voice Newsletter"
    
    msg.attach(MIMEText(newsletter, 'plain'))
    msg.attach(MIMEAudio(audio_data, 'wav'))
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
