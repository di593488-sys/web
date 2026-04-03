import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


LIST_URL = "https://www.contestkorea.com/sub/list.php?int_gbn=1"
BASE_URL = "https://www.contestkorea.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.contestkorea.com/",
}


def fetch_html(url: str) -> str:
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()
    return res.text


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def collect_links() -> list[dict]:
    html = fetch_html(LIST_URL)
    soup = BeautifulSoup(html, "html.parser")

    links = []
    seen = set()

    # contestkorea는 목록/상세 모두 sub/ 로 많이 잡히므로
    # a 태그 전체에서 상세페이지처럼 보이는 것만 필터링
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        title = clean_text(a.get_text(" ", strip=True))

        if not title:
            continue

        full_url = urljoin(BASE_URL, href)

        # 목록에 섞여 있는 메뉴/광고/카테고리 제거
        if "contestkorea.com/sub/" not in full_url:
            continue
        if "list.php" in full_url:
            continue
        if len(title) < 6:
            continue

        # 공모전/대회 느낌 없는 링크 제거
        keywords = ["공모전", "대회", "모집", "어워즈", "해커톤", "백일장", "서포터즈", "공방전", "공모"]
        if not any(k in title for k in keywords):
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
    lines = [clean_text(line) for line in text.splitlines() if clean_text(line)]

    organizer = "정보 없음"
    deadline = "정보 없음"

    for i, line in enumerate(lines):
        # 주최
        if "주최" in line or "주관" in line:
            value = line
            value = value.replace("주최", "").replace("주관", "").replace(".", " ").replace(":", " ")
            value = clean_text(value)

            if len(value) <= 2 and i + 1 < len(lines):
                value = clean_text(lines[i + 1])

            if value and value != "정보 없음":
                organizer = value

        # 접수기간
        if "접수기간" in line or "접수 " in line:
            m = re.search(r"(\d{2,4}[.\-/]\d{1,2}[.\-/]\d{1,2}\s*[~～\-]\s*\d{2,4}[.\-/]\d{1,2}[.\-/]\d{1,2})", line)
            if m:
                deadline = clean_text(m.group(1))
            else:
                # D-day라도 잡아두기
                d = re.search(r"D-\d+", line)
                if d:
                    deadline = d.group(0)
                elif i + 1 < len(lines):
                    next_line = lines[i + 1]
                    m2 = re.search(r"(\d{2,4}[.\-/]\d{1,2}[.\-/]\d{1,2}\s*[~～\-]\s*\d{2,4}[.\-/]\d{1,2}[.\-/]\d{1,2})", next_line)
                    if m2:
                        deadline = clean_text(m2.group(1))

    return organizer, deadline


def build_html(data: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def sort_key(item: dict) -> tuple[int, str]:
        d = re.search(r"D-(\d+)", item["deadline"])
        if d:
            return (0, f"{int(d.group(1)):06d}")
        return (1, item["deadline"])

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

    :root {{
      --bg: #f8fafc;
      --card: rgba(255, 255, 255, 0.92);
      --text: #0f172a;
      --sub: #64748b;
      --line: #e2e8f0;
      --accent: #2563eb;
      --accent-soft: #dbeafe;
      --danger: #dc2626;
      --warning: #ea580c;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      --radius: 22px;
    }}

    body {{
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      background:
        radial-gradient(circle at top left, #dbeafe 0%, transparent 30%),
        radial-gradient(circle at top right, #e0e7ff 0%, transparent 28%),
        linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
      color: var(--text);
    }}

    .container {{
      max-width: 1240px;
      margin: 0 auto;
      padding: 48px 20px 72px;
    }}

    .hero {{
      text-align: center;
      margin-bottom: 32px;
    }}

    .hero-badge {{
      display: inline-block;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(37, 99, 235, 0.08);
      color: var(--accent);
      font-size: 14px;
      font-weight: 700;
      margin-bottom: 16px;
    }}

    h1 {{
      margin: 0;
      font-size: clamp(32px, 6vw, 56px);
      line-height: 1.15;
      letter-spacing: -0.02em;
    }}

    .hero-desc {{
      margin: 14px auto 0;
      max-width: 720px;
      font-size: 17px;
      color: var(--sub);
      line-height: 1.7;
    }}

    .updated {{
      margin-top: 18px;
      color: var(--sub);
      font-size: 15px;
    }}

    .toolbar {{
      margin: 36px 0 28px;
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
      justify-content: space-between;
      padding: 18px;
      background: rgba(255, 255, 255, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.8);
      backdrop-filter: blur(12px);
      border-radius: 20px;
      box-shadow: var(--shadow);
    }}

    .toolbar-left,
    .toolbar-right {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
    }}

    .search-box {{
      position: relative;
      min-width: 260px;
      flex: 1 1 320px;
    }}

    .search-box input {{
      width: 100%;
      height: 46px;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 0 16px 0 42px;
      font-size: 15px;
      background: #fff;
      outline: none;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}

    .search-box input:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
    }}

    .search-icon {{
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: #94a3b8;
      font-size: 15px;
      pointer-events: none;
    }}

    select {{
      height: 46px;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 0 14px;
      background: #fff;
      font-size: 15px;
      color: var(--text);
      outline: none;
      cursor: pointer;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}

    select:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
    }}

    .result-count {{
      font-size: 14px;
      color: var(--sub);
      font-weight: 600;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 24px;
    }}

    .card {{
      display: block;
      text-decoration: none;
      color: inherit;
      background: var(--card);
      border: 1px solid rgba(255, 255, 255, 0.9);
      border-radius: var(--radius);
      padding: 22px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
      transition:
        transform 0.22s ease,
        box-shadow 0.22s ease,
        border-color 0.22s ease;
      position: relative;
      overflow: hidden;
    }}

    .card::before {{
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.06), transparent 40%);
      pointer-events: none;
    }}

    .card:hover {{
      transform: translateY(-6px);
      box-shadow: 0 18px 40px rgba(37, 99, 235, 0.12);
      border-color: rgba(37, 99, 235, 0.18);
    }}

    .card-top {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
    }}

    .tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 13px;
      font-weight: 700;
      white-space: nowrap;
    }}

    .deadline-badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 74px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 800;
      white-space: nowrap;
      background: #f1f5f9;
      color: #334155;
    }}

    .deadline-badge.urgent {{
      background: #fee2e2;
      color: var(--danger);
    }}

    .deadline-badge.soon {{
      background: #ffedd5;
      color: var(--warning);
    }}

    .title {{
      font-size: 20px;
      font-weight: 800;
      line-height: 1.5;
      margin: 0 0 14px;
      word-break: keep-all;
    }}

    .meta-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-bottom: 18px;
    }}

    .meta {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      font-size: 15px;
      color: #475569;
      line-height: 1.6;
      word-break: keep-all;
    }}

    .meta-label {{
      min-width: 68px;
      font-weight: 700;
      color: #334155;
    }}

    .card-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 18px;
      padding-top: 16px;
      border-top: 1px solid rgba(226, 232, 240, 0.9);
    }}

    .link-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 11px 14px;
      border-radius: 12px;
      background: var(--text);
      color: #fff;
      font-size: 14px;
      font-weight: 700;
      transition: background 0.2s ease, transform 0.2s ease;
    }}

    .card:hover .link-btn {{
      background: var(--accent);
    }}

    .empty {{
      text-align: center;
      color: var(--sub);
      font-size: 18px;
      margin-top: 70px;
      padding: 48px 20px;
      background: rgba(255, 255, 255, 0.8);
      border-radius: 24px;
      box-shadow: var(--shadow);
    }}

    .hidden {{
      display: none !important;
    }}

    @media (max-width: 768px) {{
      .container {{
        padding: 28px 16px 48px;
      }}

      .toolbar {{
        padding: 14px;
      }}

      .toolbar-left,
      .toolbar-right {{
        width: 100%;
      }}

      .search-box {{
        min-width: 100%;
      }}

      select {{
        flex: 1;
        min-width: 0;
      }}

      .card {{
        padding: 18px;
      }}

      .title {{
        font-size: 18px;
      }}

      .meta {{
        font-size: 14px;
      }}

      .card-top {{
        flex-direction: column;
        align-items: flex-start;
      }}

      .deadline-badge {{
        min-width: auto;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <section class="hero">
      <div class="hero-badge">CONTEST ARCHIVE</div>
      <h1>🔥 오늘의 공모전</h1>
      <div class="hero-desc">
        최신 공모전 정보를 한눈에 보고, 검색과 정렬로 원하는 공모전을 빠르게 찾아보세요.
      </div>
      <div class="updated">업데이트: {now}</div>
    </section>

    <section class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <span class="search-icon">🔎</span>
          <input type="text" id="searchInput" placeholder="제목 또는 주최기관으로 검색" />
        </div>
      </div>

      <div class="toolbar-right">
        <select id="sortSelect">
          <option value="default">기본순</option>
          <option value="deadline">마감순</option>
          <option value="title">제목순</option>
        </select>

        <select id="categorySelect">
          <option value="all">전체</option>
          <option value="urgent">마감임박</option>
          <option value="normal">일반</option>
        </select>

        <div class="result-count">총 <span id="resultCount">{len(sorted_data)}</span>개</div>
      </div>
    </section>

    <div class="grid" id="contestGrid">
"""

    for item in sorted_data:
        html += f"""
      <a class="card"
         href="{item['link']}"
         target="_blank"
         rel="noopener noreferrer"
         data-title="{item['title']}"
         data-organizer="{item['organizer']}"
         data-deadline="{item['deadline']}">
        <div class="card-top">
          <div class="tag">공모전</div>
          <div class="deadline-badge">D-day 계산중</div>
        </div>

        <div class="title">{item['title']}</div>

        <div class="meta-list">
          <div class="meta">
            <span class="meta-label">마감일</span>
            <span>{item['deadline']}</span>
          </div>
          <div class="meta">
            <span class="meta-label">주최기관</span>
            <span>{item['organizer']}</span>
          </div>
        </div>

        <div class="card-footer">
          <span style="color:#64748b; font-size:14px;">자세히 보기</span>
          <span class="link-btn">바로가기 ↗</span>
        </div>
      </a>
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

  <script>
    const searchInput = document.getElementById("searchInput");
    const sortSelect = document.getElementById("sortSelect");
    const categorySelect = document.getElementById("categorySelect");
    const cards = Array.from(document.querySelectorAll(".card"));
    const grid = document.getElementById("contestGrid");
    const resultCount = document.getElementById("resultCount");

    function parseDeadline(text) {
      if (!text) return null;

      const match = text.match(/(\\d{4})[.\\-/ ](\\d{1,2})[.\\-/ ](\\d{1,2})/);
      if (!match) return null;

      const year = Number(match[1]);
      const month = Number(match[2]) - 1;
      const day = Number(match[3]);

      const date = new Date(year, month, day);
      if (isNaN(date.getTime())) return null;
      return date;
    }

    function getDDay(deadlineText) {
      const deadline = parseDeadline(deadlineText);
      if (!deadline) return null;

      const today = new Date();
      today.setHours(0, 0, 0, 0);
      deadline.setHours(0, 0, 0, 0);

      const diff = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
      return diff;
    }

    function updateDeadlineBadges() {
      cards.forEach(card => {
        const deadlineText = card.dataset.deadline || "";
        const badge = card.querySelector(".deadline-badge");
        const dday = getDDay(deadlineText);

        if (dday === null) {
          badge.textContent = "일정확인";
          return;
        }

        if (dday < 0) {
          badge.textContent = "마감";
          badge.classList.add("urgent");
          card.dataset.category = "closed";
        } else if (dday === 0) {
          badge.textContent = "D-Day";
          badge.classList.add("urgent");
          card.dataset.category = "urgent";
        } else if (dday <= 3) {
          badge.textContent = `D-${dday}`;
          badge.classList.add("urgent");
          card.dataset.category = "urgent";
        } else if (dday <= 7) {
          badge.textContent = `D-${dday}`;
          badge.classList.add("soon");
          card.dataset.category = "soon";
        } else {
          badge.textContent = `D-${dday}`;
          card.dataset.category = "normal";
        }
      });
    }

    function filterAndSortCards() {
      const keyword = searchInput.value.trim().toLowerCase();
      const category = categorySelect.value;
      const sort = sortSelect.value;

      let visibleCards = cards.filter(card => {
        const title = (card.dataset.title || "").toLowerCase();
        const organizer = (card.dataset.organizer || "").toLowerCase();
        const cardCategory = card.dataset.category || "normal";

        const matchesKeyword =
          title.includes(keyword) || organizer.includes(keyword);

        let matchesCategory = true;
        if (category === "urgent") {
          matchesCategory = cardCategory === "urgent" || cardCategory === "soon";
        } else if (category === "normal") {
          matchesCategory = cardCategory === "normal";
        }

        return matchesKeyword && matchesCategory;
      });

      cards.forEach(card => card.classList.add("hidden"));

      if (sort === "deadline") {
        visibleCards.sort((a, b) => {
          const aDate = parseDeadline(a.dataset.deadline || "");
          const bDate = parseDeadline(b.dataset.deadline || "");

          if (!aDate && !bDate) return 0;
          if (!aDate) return 1;
          if (!bDate) return -1;

          return aDate - bDate;
        });
      } else if (sort === "title") {
        visibleCards.sort((a, b) => {
          return (a.dataset.title || "").localeCompare(b.dataset.title || "", "ko");
        });
      }

      visibleCards.forEach(card => {
        card.classList.remove("hidden");
        grid.appendChild(card);
      });

      resultCount.textContent = visibleCards.length;
    }

    updateDeadlineBadges();
    filterAndSortCards();

    searchInput.addEventListener("input", filterAndSortCards);
    sortSelect.addEventListener("change", filterAndSortCards);
    categorySelect.addEventListener("change", filterAndSortCards);
  </script>
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