import json, os, datetime
from google import genai

GEMINI_KEY = os.environ["GEMINI_API_KEY"].strip()

def generate_cric_data():
    client = genai.Client(api_key=GEMINI_KEY)
    today = datetime.date.today().strftime("%d %b %Y")
    prompt = f"""
    Today is {today}. Return ONLY valid raw JSON (no markdown, no backticks) with latest real-world cricket data in this exact structure:
    {{
      "updated": "{today}",
      "series": [
        {{"month": "NOVEMBER - DECEMBER 2026", "name": "The Ashes 2026-27", "dates": "Nov 26 - Jan 07"}},
        {{"month": "NOVEMBER - DECEMBER 2026", "name": "India tour of South Africa 2026", "dates": "Nov 28 - Dec 19"}}
      ],
      "wtc": [
        {{"rank": 1, "team": "India", "m": 14, "w": 9, "l": 4, "pct": "66.67%"}},
        {{"rank": 2, "team": "Australia", "m": 14, "w": 9, "l": 4, "pct": "65.48%"}}
      ],
      "players": [
        {{"name": "Virat Kohli", "team": "IND", "role": "Batter", "runs": "27,000+", "avg": "53.5", "sr": "93.6"}},
        {{"name": "Rohit Sharma", "team": "IND", "role": "Batter", "runs": "19,300+", "avg": "49.1", "sr": "92.4"}},
        {{"name": "Jasprit Bumrah", "team": "IND", "role": "Bowler", "runs": "420+ Wkts", "avg": "20.2", "sr": "4.5 Econ"}}
      ],
      "schedule": [
        {{"series": "The Ashes 2026-27", "match": "Australia vs England", "date": "26 Nov 2026, 05:30 AM IST", "venue": "Perth Stadium, Perth"}}
      ],
      "rankings": {{
        "men": {{
          "test": [{{"rank": 1, "name": "Joe Root", "team": "ENG", "pts": 899}}],
          "odi": [{{"rank": 1, "name": "Shubman Gill", "team": "IND", "pts": 784}}],
          "t20": [{{"rank": 1, "name": "Travis Head", "team": "AUS", "pts": 855}}]
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
    Fill at least 6 real top entries in series, wtc, players, schedule, and each rankings list.
    """
    res = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    clean = res.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    with open("cricdata.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Updated full cricdata.json!")

if __name__ == "__main__":
    generate_cric_data()
