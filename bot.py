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
    return "\n".join(items) if items else "Latest Cricket Updates"

def write_post(news):
    client = genai.Client(api_key=GEMINI_KEY)
    prompt = f"Write a 500-word SEO cricket news & fantasy analysis article in clean HTML (<p>, <h2>, <ul>, <li> only) based on:\n{news}\nFirst line must start with TITLE: "
    
    models = ["gemini-3.8-flash", "gemini-3.8-flash-lite", "gemini-3.8-pro"]
    raw = ""
    for m in models:
        for attempt in range(3):
            try:
                res = client.models.generate_content(model=m, contents=prompt)
                raw = res.text
                break
            except Exception as e:
                print(f"Retrying {m}...", e)
                time.sleep(5)
        if raw:
            break

    raw = raw.replace("```html", "").replace("```", "").strip()
    lines = raw.split("\n")
    title = "Cricket News & AI Analysis"
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
