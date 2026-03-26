import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

LIST_URL = "https://www.wevity.com/?c=find&s=1&gub=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.wevity.com/",
}

session = requests.Session()
session.headers.update(HEADERS)


def get_contest_links():
    res = session.get(LIST_URL, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        title = a.get_text(" ", strip=True)

        if not title:
            continue

        full_url = urljoin("https://www.wevity.com/", href)

        # 공모전 상세 링크만 통과
        if "ix=" not in full_url:
            continue
        if "gub=1" not in full_url:
            continue
        if "view" not in full_url:
            continue

        # 메뉴/잡링크 제외
        bad_titles = {
            "공모전", "전체", "스페셜", "신규", "마감임박",
            "접수중", "접수예정", "마감", "목록"
        }
        if title in bad_titles:
            continue
        if len(title) < 4:
            continue

        if full_url not in seen:
            seen.add(full_url)
            links.append({"title": title, "link": full_url})

    return links


def parse_detail(url: str):
    res = session.get(url, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    organizer = "정보 없음"
    deadline = "정보 없음"

    for i, line in enumerate(lines):
        if "주최/주관" in line:
            value = line.replace("주최/주관", "").strip()
            if not value and i + 1 < len(lines):
                value = lines[i + 1].strip()
            if value:
                organizer = value

        if "접수기간" in line:
            value = line.replace("접수기간", "").strip()
            if not value and i + 1 < len(lines):
                value = lines[i + 1].strip()
            if value:
                deadline = value

    # 보기 좋게 정리
    deadline = re.sub(r"\s+", " ", deadline).strip()
    organizer = re.sub(r"\s+", " ", organizer).strip()

    return organizer, deadline


def build_html(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 최신순 정렬: 마감일에서 D-숫자 추출, 작은 값이 위
    def sort_key(item):
        m = re.search(r"D-(\d+)", item["deadline"])
        if m:
            return int(m.group(1))
        return 999999

    data = sorted(data, key=sort_key)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>공모전 자동 업데이트</title>
<style>
body {{
    font-family: Arial, sans-serif;
    background: #f2f2f2;
    margin: 0;
    padding: 30px;
}}
.container {{
    max-width: 1200px;
    margin: 0 auto;
}}
h1 {{
    text-align: center;
    margin-bottom: 10px;
}}
.updated {{
    text-align: center;
    color: #666;
    margin-bottom: 30px;
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}}
.card {{
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}}
.title {{
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 12px;
    line-height: 1.5;
}}
.title a {{
    text-decoration: none;
    color: #111;
}}
.title a:hover {{
    color: #0066cc;
}}
.meta {{
    color: #555;
    margin: 8px 0;
    font-size: 14px;
}}
.empty {{
    text-align: center;
    color: #666;
    margin-top: 50px;
}}
</style>
</head>
<body>
<div class="container">
    <h1>🔥 오늘의 공모전</h1>
    <div class="updated">업데이트: {now}</div>
    <div class="grid">
"""

    for item in data:
        html += f"""
        <div class="card">
            <div class="title">
                <a href="{item['link']}" target="_blank">{item['title']}</a>
            </div>
            <div class="meta">📅 마감일: {item['deadline']}</div>
            <div class="meta">🏢 주최기관: {item['organizer']}</div>
        </div>
"""

    html += """
    </div>
"""

    if not data:
        html += '<div class="empty">불러온 공모전이 없습니다.</div>'

    html += """
</div>
</body>
</html>
"""
    return html, data


def main():
    links = get_contest_links()

    data = []
    for item in links[:30]:
        try:
            organizer, deadline = parse_detail(item["link"])
            data.append({
                "title": item["title"],
                "link": item["link"],
                "organizer": organizer,
                "deadline": deadline,
            })
            print("추가:", item["title"])
        except Exception as e:
            print("상세 파싱 실패:", item["title"], e)

    html, sorted_data = build_html(data)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    with open("contests.md", "w", encoding="utf-8") as f:
        f.write("# 오늘의 공모전\n\n")
        for item in sorted_data:
            f.write(f"- [{item['title']}]({item['link']}) | {item['deadline']} | {item['organizer']}\n")

    print("최종 수집 개수:", len(sorted_data))


if __name__ == "__main__":
    main()