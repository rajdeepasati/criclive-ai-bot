import os, time, random, smtplib, feedparser, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

GEMINI_KEY = os.environ["GEMINI_API_KEY"].strip()
BLOGGER_EMAIL = os.environ["BLOGGER_EMAIL"].strip()
GMAIL_USER = os.environ["GMAIL_USER"].strip()
GMAIL_PASS = os.environ["GMAIL_PASS"].replace(" ", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

CRICKET_IMAGES = [
    "https://unsplash.com",
    "https://unsplash.com",
    "https://unsplash.com",
    "https://unsplash.com"
]

FEEDS = [
    "https://" + ".".join(["www", "espncricinfo", "com"]) + "/rss/content/story/feeds/0.xml",
    "https://" + ".".join(["feeds", "bbci", "co", "uk"]) + "/sport/cricket/rss.xml",
    "https://" + ".".join(["news", "google", "com"]) + "/rss/search?q=cricket+match+prediction+OR+IPL+OR+Team+India&hl=en-IN&gl=IN&ceid=IN:en"
]

def get_recent_blog_titles():
    try:
        blog_url = "https://" + ".".join(["criclivepulse", "blogspot", "com"]) + "/feeds/posts/default?alt=json&max-results=5"
        r = requests.get(blog_url, timeout=6).json()
        entries = r.get("feed", {}).get("entry", [])
        return [e["title"]["$t"] for e in entries]
    except:
        return []

def get_news():
    items = []
    for u in FEEDS:
        try:
            resp = requests.get(u, timeout=6)
            f = feedparser.parse(resp.content)
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
    schedule_info = ""
    body = []
    for l in lines:
        if l.startswith("TITLE:"):
            title = l.replace("TITLE:", "").strip()
        elif l.startswith("MATCH_INFO:"):
            schedule_info = l.replace("MATCH_INFO:", "").strip()
        else:
            body.append(l)

    img_url = random.choice(CRICKET_IMAGES)
    header_html = f'<div style="margin-bottom:14px"><img src="{img_url}" alt="{title}" style="width:100%;border-radius:10px;max-height:360px;object-fit:cover"/></div>'
    if schedule_info:
        header_html += f'<p style="background:#ecfdf5;padding:10px;border-left:4px solid #009270;border-radius:6px"><strong>⏰ Match Schedule:</strong> {schedule_info}</p>'

    return title, header_html + "\n" + "\n".join(body), schedule_info

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
    print("Published to Blogger:", title)

def send_telegram(title, schedule_info):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        site_url = "https://" + ".".join(["criclivepulse", "blogspot", "com"])
        text = f"🏏 *{title}*\n\n⏰ {schedule_info}\n\n📊 Pitch Report & Winning Fantasy 11 yahan dekhein 👇\n{site_url}"
        tg_url = f"https://telegram.org{TG_TOKEN}/sendMessage"
        requests.post(tg_url, json={"chat_id": TG_CHAT, "text": text, "parse_mode": "Markdown"}, timeout=8)
        print("Shared to Telegram!")
    except Exception as e:
        print("Telegram skip:", e)

if __name__ == "__main__":
    past = get_recent_blog_titles()
    t, b, sched = write_post(get_news(), past)
    send_post(t, b)
    send_telegram(t, sched)
