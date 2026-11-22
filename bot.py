import os, smtplib, feedparser, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
BLOGGER_EMAIL = os.environ["BLOGGER_EMAIL"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_PASS"]

# Multi-Website Cricket RSS Feeds
FEEDS = [
    "https://espncricinfo.com",
    "https://bbci.co.uk"
]

def get_latest_cricket_news():
    headlines = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            headlines.append(f"- {entry.title}: {entry.get('summary', '')[:220]}")
    return "\n".join(headlines)

def generate_ai_article(news_context):
    prompt = f"""
    You are an expert cricket analyst and SEO sports writer. Analyze these real-time cricket news updates:
    {news_context}

    Select the biggest trending story and write a 100% original, engaging, copyright-free cricket article (500-700 words) in clean HTML format (use <h2>, <p>, <ul>, <li>, <strong> tags only; do NOT include <html>, <body>, or markdown backticks).
    Structure:
    1. First line MUST be 'TITLE: ' followed by a catchy, high-CTR SEO headline.
    2. Detailed Match / News Analysis.
    3. Key Player Stats & Pitch/Condition Impact.
    4. Fantasy XI & Expert Match Prediction Insights.
    """
    url = f"https://googleapis.com{GEMINI_KEY}"
    res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
    text = res["candidates"][0]["content"]["parts"][0]["text"]
    text = text.replace("```html", "").replace("```", "").strip()
    
    lines = text.split("\n")
    title = "Latest Cricket Update & AI Match Analysis"
    body_lines = []
    for line in lines:
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        else:
            body_lines.append(line)
    return title, "\n".join(body_lines)

def publish_to_blogger(title, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = title
    msg["From"] = GMAIL_USER
    msg["To"] = BLOGGER_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("://gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, BLOGGER_EMAIL, msg.as_string())
    print("Successfully Auto-Published:", title)

if __name__ == "__main__":
    news = get_latest_cricket_news()
    title, article = generate_ai_article(news)
    publish_to_blogger(title, article)
