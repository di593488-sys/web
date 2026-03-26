import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import re

LIST_URL = "https://www.wevity.com/?c=find&s=1&gub=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)


# 🔹 공모전 링크 수집
def get_links():
    res = session.get(LIST_URL)
    soup = BeautifulSoup(res.text, "html.parser")

    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)

        if "ix=" not in href:
            continue
        if not title or len(title) < 5:
            continue

        full_url = urljoin("https://www.wevity.com/", href)

        if full_url not in seen:
            seen.add(full_url)
            links.append({"title": title, "link": full_url})

    return links


# 🔹 상세 페이지 파싱
def get_detail(url):
    res = session.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    text = soup.get_text("\n", strip=True)

    organizer = "정보 없음"
    deadline = "정보 없음"

    lines = text.split("\n")

    for i, line in enumerate(lines):
        if "주최/주관" in line:
            if i + 1 < len(lines):
                organizer = lines[i + 1]

        if "접수기간" in line:
            if i + 1 < len(lines):
                deadline = lines[i + 1]

    return organizer, deadline


# 🔹 HTML 생성
def build_html(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def sort_key(item):
        m = re.search(r"D-(\d+)", item["deadline"])
        return int(m.group(1)) if m else 999

    data = sorted(data, key=sort_key)

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>공모전 자동 업데이트</title>
<style>
body {{
    font-family: Arial;
    background: #f2f2f2;
    padding: 20px;
}}
.container {{
    max-width: 1100px;
    margin: auto;
}}
h1 {{
    text-align: center;
}}
.updated {{
    text-align: center;
    color: gray;
    margin-bottom: 20px;
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
    box-shadow: 0 3px 8px rgba(0,0,0,0.1);
}}
.card a {{
    text-decoration: none;
    color: black;
    font-weight: bold;
}}
.meta {{
    color: #555;
    font-size: 14px;
    margin-top: 5px;
}}
</style>
</head>

<body>
<div class="container">
<h1>🔥 오늘의 공모전</h1>
<div class="updated">업데이트: {now}</div>
<div class="grid">
"""

    for d in data:
        html += f"""
        <div class="card">
            <a href="{d['link']}" target="_blank">{d['title']}</a>
            <div class="meta">📅 {d['deadline']}</div>
            <div class="meta">🏢 {d['organizer']}</div>
        </div>
"""

    html += """
</div>
</div>
</body>
</html>
"""

    return html


# 🔹 실행
def main():
    links = get_links()
    print("링크 수:", len(links))

    data = []

    for item in links[:15]:  # 👉 개수 조절 가능
        try:
            org, dead = get_detail(item["link"])
            data.append({
                "title": item["title"],
                "link": item["link"],
                "organizer": org,
                "deadline": dead
            })
            print("추가:", item["title"])
        except:
            pass

    html = build_html(data)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("완료")


if __name__ == "__main__":
    main()