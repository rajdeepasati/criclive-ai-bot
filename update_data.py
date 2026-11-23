import json, os, datetime
from google import genai

GEMINI_KEY = os.environ["GEMINI_API_KEY"].strip()

def generate_cric_data():
    client = genai.Client(api_key=GEMINI_KEY)
    today = datetime.date.today().strftime("%d %b %Y")
    prompt = f"""
    Today is {today}. Return ONLY valid raw JSON (no markdown, no backticks) with latest real-world ICC cricket rankings, upcoming international/IPL schedule, and all-time cricket records in this exact structure:
    {{
      "updated": "{today}",
      "schedule": [
        {{"series": "Series Name", "match": "Team A vs Team B", "date": "25 Nov, 07:30 PM IST", "venue": "Stadium Name"}}
      ],
      "rankings": {{
        "men": {{
          "test": [{{"rank": 1, "name": "Harry Brook", "team": "ENG", "pts": 861}}],
          "odi": [{{"rank": 1, "name": "Rohit Sharma", "team": "IND", "pts": 780}}],
          "t20": [{{"rank": 1, "name": "Suryakumar Yadav", "team": "IND", "pts": 850}}]
        }},
        "women": {{
          "odi": [{{"rank": 1, "name": "Laura Wolvaardt", "team": "SA", "pts": 782}}],
          "t20": [{{"rank": 1, "name": "Beth Mooney", "team": "AUS", "pts": 765}}]
        }}
      }},
      "records": {{
        "batting": [
          {{"title": "Most International Runs", "player": "Sachin Tendulkar (IND)", "stat": "34,357 Runs"}},
          {{"title": "Most International Centuries", "player": "Sachin Tendulkar (IND)", "stat": "100 Centuries"}},
          {{"title": "Most International Sixes", "player": "Rohit Sharma (IND)", "stat": "620+ Sixes"}},
          {{"title": "Highest ODI Individual Score", "player": "Rohit Sharma (IND)", "stat": "264 Runs"}}
        ],
        "bowling": [
          {{"title": "Most International Wickets", "player": "Muttiah Muralitharan (SL)", "stat": "1,347 Wickets"}},
          {{"title": "Best ODI Bowling Figures", "player": "Chaminda Vaas (SL)", "stat": "8/19"}},
          {{"title": "Most 5-Wicket Hauls", "player": "Muttiah Muralitharan (SL)", "stat": "67 Five-Fors"}}
        ]
      }}
    }}
    Fill at least 5 real top entries in schedule and each rankings list.
    """
    res = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    clean = res.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    with open("cricdata.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Updated cricdata.json successfully!")

if __name__ == "__main__":
    generate_cric_data()
