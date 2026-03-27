import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


LIST_URL = "https://www.wevity.com/?c=find&s=1&gub=1"
BASE_URL = "https://www.wevity.com/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_html(url: str) -> str:
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()
    return res.text


def collect_links() -> list[dict]:
    html = fetch_html(LIST_URL)
    soup = BeautifulSoup(html, "html.parser")

    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        title = a.get_text(" ", strip=True)

        if not title:
            continue

        full_url = urljoin(BASE_URL, href)

        if "ix=" not in full_url:
            continue
        if "gub=1" not in full_url:
            continue
        if "view" not in full_url:
            continue
        if len(title) < 4:
            continue

        if full_url in seen:
            continue

        seen.add(full_url)
        links.append({
            "title": title,
            "link": full_url
        })

    return links


def parse_detail(url: str) -> tuple[str, str]:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

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

    organizer = re.sub(r"\s+", " ", organizer).strip()
    deadline = re.sub(r"\s+", " ", deadline).strip()

    return organizer, deadline


def build_html(data: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def sort_key(item: dict) -> int:
        # D-숫자가 있으면 마감 임박순 정렬
        m = re.search(r"D-(\d+)", item["deadline"])
        if m:
            return int(m.group(1))
        return 999999

    sorted_data = sorted(data, key=sort_key)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>오늘의 공모전</title>
  <style>
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      background: #f2f2f2;
      color: #111;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 40px 20px 60px;
    }}
    h1 {{
      text-align: center;
      font-size: 52px;
      margin: 0 0 20px;
    }}
    .updated {{
      text-align: center;
      color: #777;
      font-size: 18px;
      margin-bottom: 40px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 24px;
    }}
    .card {{
      background: #fff;
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    }}
    .title {{
      font-size: 20px;
      font-weight: 700;
      line-height: 1.5;
      margin-bottom: 14px;
    }}
    .title a {{
      color: #111;
      text-decoration: none;
    }}
    .title a:hover {{
      color: #0b67d0;
    }}
    .meta {{
      font-size: 15px;
      color: #555;
      margin: 8px 0;
      line-height: 1.5;
      word-break: keep-all;
    }}
    .empty {{
      text-align: center;
      color: #666;
      font-size: 18px;
      margin-top: 60px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>🔥 오늘의 공모전</h1>
    <div class="updated">업데이트: {now}</div>
    <div class="grid">
"""

    for item in sorted_data:
        html += f"""
      <div class="card">
        <div class="title">
          <a href="{item['link']}" target="_blank" rel="noopener noreferrer">{item['title']}</a>
        </div>
        <div class="meta">📅 마감일: {item['deadline']}</div>
        <div class="meta">🏢 주최기관: {item['organizer']}</div>
      </div>
"""

    html += """
    </div>
"""

    if not sorted_data:
        html += """
    <div class="empty">불러온 공모전이 없습니다.</div>
"""

    html += """
  </div>
</body>
</html>
"""
    return html


def main():
    links = collect_links()
    print("링크 수집:", len(links))

    data = []

    for item in links[:15]:
        try:
            organizer, deadline = parse_detail(item["link"])
            data.append({
                "title": item["title"],
                "link": item["link"],
                "organizer": organizer,
                "deadline": deadline
            })
            print("추가:", item["title"])
        except Exception as e:
            print("상세 파싱 실패:", item["title"], e)

    html = build_html(data)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("최종 수집 개수:", len(data))
    print("index.html 생성 완료")


if __name__ == "__main__":
    main()