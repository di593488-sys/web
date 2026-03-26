import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://www.wevity.com/?c=find&s=1&gub=1"

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

items = soup.select(".list li")

data = []

for item in items[:15]:
    title_tag = item.select_one(".tit")
    date_tag = item.select_one(".date")
    org_tag = item.select_one(".organ")

    if title_tag:
        title = title_tag.text.strip()
        link = "https://www.wevity.com" + title_tag.get("href")
    else:
        continue

    deadline = date_tag.text.strip() if date_tag else "정보 없음"
    org = org_tag.text.strip() if org_tag else "정보 없음"

    data.append({
        "title": title,
        "link": link,
        "deadline": deadline,
        "org": org
    })

# 최신순 정렬 (날짜 기반이 아니라 그냥 순서 기준)
data = list(reversed(data))

# HTML 파일 생성
now = datetime.now().strftime("%Y-%m-%d %H:%M")

html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>공모전 자동 업데이트</title>
<style>
body {{
    font-family: Arial;
    background: #f5f5f5;
    padding: 20px;
}}

h1 {{
    text-align: center;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}}

.card {{
    background: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}}

.card a {{
    text-decoration: none;
    color: black;
    font-weight: bold;
}}

.card p {{
    margin: 5px 0;
    color: #555;
}}

.time {{
    text-align: center;
    margin-bottom: 20px;
    color: gray;
}}
</style>
</head>

<body>

<h1>🔥 오늘의 공모전</h1>
<div class="time">업데이트: {now}</div>

<div class="grid">
"""

for d in data:
    html += f"""
    <div class="card">
        <a href="{d['link']}" target="_blank">{d['title']}</a>
        <p>📅 마감일: {d['deadline']}</p>
        <p>🏢 주최: {d['org']}</p>
    </div>
    """

html += """
</div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("완료")