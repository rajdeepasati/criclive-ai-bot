import os, time, smtplib, feedparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

GEMINI_KEY = os.environ["GEMINI_API_KEY"].strip()
BLOGGER_EMAIL = os.environ["BLOGGER_EMAIL"].strip()
GMAIL_USER = os.environ["GMAIL_USER"].strip()
GMAIL_PASS = os.environ["GMAIL_PASS"].replace(" ", "").strip()

FEEDS = [
    "https://espncricinfo.com",
    "https://bbci.co.uk"
]

def get_news():
    items = []
    for u in FEEDS:
        f = feedparser.parse(u)
        for e in f.entries[:3]:
            items.append(f"- {e.title}: {e.get('summary', '')[:200]}")
    return "\n".join(items) if items else "Latest International Cricket Updates"

def write_post(news):
    client = genai.Client(api_key=GEMINI_KEY)
    prompt = f"""
    You are a top Indian cricket analyst & sports blogger. Analyze these latest cricket updates:
    {news}

    Write a 500-word SEO cricket news & fantasy analysis article in natural, engaging HINGLISH (Hindi written in English script, like Indian sports websites use).
    Use clean HTML tags (<p>, <h2>, <ul>, <li>, <strong> only; NO <html>, <body>, or markdown backticks).
    First line MUST start with 'TITLE: ' followed by a catchy Hinglish SEO headline.
    Include:
    1. Breaking Match / News Update in Hinglish
    2. Pitch Report & Key Player Stats
    3. Today's Fantasy 11 & Captain/Vice-Captain Suggestion
    """
    
    models = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash"]
    raw = ""
    for m in models:
        for attempt in range(3):
            try:
                res = client.models.generate_content(model=m, contents=prompt)
                if res.text:
                    raw = res.text
                    break
            except Exception as e:
                print(f"Retrying {m}...", e)
                time.sleep(5)
        if raw:
            break

    if not raw:
        raise Exception("All models busy, skipping empty post.")

    raw = raw.replace("```html", "").replace("```", "").strip()
    lines = raw.split("\n")
    title = "Cricket News & AI Match Analysis"
    body = []
    for l in lines:
        if l.startswith("TITLE:"):
            title = l.replace("TITLE:", "").strip()
        else:
            body.append(l)
    return title, "\n".join(body)

def send_post(title, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = title
    msg["From"] = GMAIL_USER
    msg["To"] = BLOGGER_EMAIL
    msg.attach(MIMEText(html, "html"))
    host = "smtp" + ".gmail.com"
    with smtplib.SMTP_SSL(host, 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.sendmail(GMAIL_USER, BLOGGER_EMAIL, msg.as_string())
    print("Published:", title)

if __name__ == "__main__":
    t, b = write_post(get_news())
    send_post(t, b)
