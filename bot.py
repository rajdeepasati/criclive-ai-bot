import os, time, smtplib, feedparser, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

GEMINI_KEY = os.environ["GEMINI_API_KEY"].strip()
BLOGGER_EMAIL = os.environ["BLOGGER_EMAIL"].strip()
GMAIL_USER = os.environ["GMAIL_USER"].strip()
GMAIL_PASS = os.environ["GMAIL_PASS"].replace(" ", "").strip()

FEEDS = [
    "https://www." + "://espncricinfo.com",
    "https://feeds." + "bbci.co.uk/sport/cricket/rss.xml",
    "https://news." + "://google.com"
]

def get_recent_blog_titles():
    try:
        blog_url = "https://criclivepulse" + "://"
        r = requests.get(blog_url, timeout=10).json()
        entries = r.get("feed", {}).get("entry", [])
        return [e["title"]["$t"] for e in entries]
    except:
        return []

def get_news():
    items = []
    for u in FEEDS:
        try:
            f = feedparser.parse(u)
            for e in f.entries[:4]:
                items.append(f"- {e.title}")
        except:
            pass
    return "\n".join(items[:10]) if items else "Latest International & IPL Cricket Updates"

def write_post(news, past_titles):
    client = genai.Client(api_key=GEMINI_KEY)
    avoid_text = "\n".join([f"- {t}" for t in past_titles]) if past_titles else "None"
    prompt = f"""
    You are an expert Indian cricket analyst. Based on these real-time cricket headlines:
    {news}

    IMPORTANT: Do NOT write about topics already covered in these recent posts:
    {avoid_text}

    Pick a FRESH upcoming or live match and write a 500-word SEO article in natural HINGLISH.
    Use clean HTML tags (<p>, <h2>, <ul>, <li>, <strong> only; NO <html>, <body>, or backticks).
    First line MUST start with 'TITLE: ' followed by a unique, catchy Hinglish headline.
    Second line MUST be 'MATCH_INFO: ' followed by the exact Match Date, IST Start Time, and Stadium Venue (e.g., MATCH_INFO: 24 Nov, 07:30 PM IST | Wankhede Stadium, Mumbai).
    Include:
    1. Match Preview & Exact IST Timing
    2. Stadium Pitch Report & Key Player Stats
    3. Best Fantasy 11 (WK, BAT, ALL, BOWL) & Captain/Vice-Captain Picks
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
                time.sleep(5)
        if raw:
            break

    if not raw:
        raise Exception("Models busy, skipping empty post.")

    raw = raw.replace("```html", "").replace("```", "").strip()
    lines = raw.split("\n")
    title = "Cricket News & Fantasy 11 Analysis"
    body = []
    for l in lines:
        if l.startswith("TITLE:"):
            title = l.replace("TITLE:", "").strip()
        elif l.startswith("MATCH_INFO:"):
            info = l.replace("MATCH_INFO:", "").strip()
            body.insert(0, f"<p><strong>⏰ Match Schedule:</strong> {info}</p>")
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
    past = get_recent_blog_titles()
    t, b = write_post(get_news(), past)
    send_post(t, b)
