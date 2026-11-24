import os, time, random, datetime, smtplib, feedparser, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

GEMINI_KEY = os.environ["GEMINI_API_KEY"].strip()
BLOGGER_EMAIL = os.environ["BLOGGER_EMAIL"].strip()
GMAIL_USER = os.environ["GMAIL_USER"].strip()
GMAIL_PASS = os.environ["GMAIL_PASS"].replace(" ", "").strip()

IMG_HOST = "https://" + ".".join(["images", "unsplash", "com"])
CRICKET_IMAGES = [
    IMG_HOST + "/photo-1531415074968-036ba1b575da?w=900&q=80",
    IMG_HOST + "/photo-1540747913346-19e32dc3e97e?w=900&q=80",
    IMG_HOST + "/photo-1624526267942-ab0ff8a3e972?w=900&q=80",
    IMG_HOST + "/photo-1593341646782-e0b495cff86d?w=900&q=80"
]

FEEDS = [
    "https://" + ".".join(["www", "espncricinfo", "com"]) + "/rss/content/story/feeds/0.xml",
    "https://" + ".".join(["feeds", "bbci", "co", "uk"]) + "/sport/cricket/rss.xml",
    "https://" + ".".join(["news", "google", "com"]) + "/rss/search?q=cricket+match+prediction+OR+IPL+OR+Team+India&hl=en-IN&gl=IN&ceid=IN:en"
]

def get_recent_blog_titles():
    try:
        blog_url = "https://" + ".".join(["criclivepulse", "blogspot", "com"]) + "/feeds/posts/default?alt=json&max-results=6"
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
    today_str = datetime.date.today().strftime("%d %b %Y")
    prompt = f"""
    Today's exact date is {today_str}. You are an expert Indian cricket analyst. Based on these real-time cricket headlines:
    {news}

    STRICT RULES:
    1. Do NOT repeat topics from these recent posts:
       {avoid_text}
    2. NEVER use past dates (like October) or fake names like 'In-Form Opponents'. Use ONLY real international, women's, domestic, or league teams and dates on or after {today_str}.

    Pick a FRESH upcoming or live match (on or after {today_str}) and write a 500-word SEO article in natural HINGLISH.
    Use clean HTML tags (<p>, <h2>, <ul>, <li>, <strong> only; NO <html>, <body>, or backticks).
    First line MUST start with 'TITLE: ' followed by a catchy Hinglish headline.
    Second line MUST be 'TEAMS: ' followed by ONLY the exact full names of the two playing teams separated by ' vs ' (e.g., TEAMS: South Africa vs Bangladesh OR TEAMS: India Women vs Australia Women).
    Third line MUST be 'MATCH_INFO: ' followed by the exact Match Date (on or after {today_str}), IST Start Time, and Stadium Venue (e.g., MATCH_INFO: 25 Nov, 10:00 AM IST | Shere Bangla National Stadium, Dhaka).
    Include:
    1. Match Preview & Exact IST Timing
    2. Stadium Pitch Report & Key Player Stats
    3. Best Fantasy 11 (WK, BAT, ALL, BOWL) & Captain/Vice-Captain Picks
    """
    
    models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
    raw = ""
    for m in models:
        for attempt in range(2):
            try:
                res = client.models.generate_content(model=m, contents=prompt)
                if res.text:
                    raw = res.text
                    break
            except Exception as e:
                time.sleep(3)
        if raw:
            break

    if not raw:
        raise Exception("Gemini API temporarily busy.")

    raw = raw.replace("```html", "").replace("```", "").strip()
    lines = raw.split("\n")
    title = "Cricket News & Fantasy 11 Analysis"
    teams_info = ""
    schedule_info = ""
    body = []
    for l in lines:
        if l.startswith("TITLE:"):
            title = l.replace("TITLE:", "").strip()
        elif l.startswith("TEAMS:"):
            teams_info = l.replace("TEAMS:", "").strip()
        elif l.startswith("MATCH_INFO:"):
            schedule_info = l.replace("MATCH_INFO:", "").strip()
        else:
            body.append(l)

    img_url = random.choice(CRICKET_IMAGES)
    header_html = f'<div style="margin-bottom:14px"><img src="{img_url}" alt="{title}" style="width:100%;border-radius:10px;max-height:360px;object-fit:cover"/></div>'
    if teams_info or schedule_info:
        header_html += f'<p style="background:#ecfdf5;padding:10px;border-left:4px solid #009270;border-radius:6px"><strong>🏏 Teams:</strong> {teams_info} | <strong>⏰ Match Schedule:</strong> {schedule_info}</p>'

    return title, header_html + "\n" + "\n".join(body)

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
