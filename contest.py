import requests
from bs4 import BeautifulSoup

url = "https://www.wevity.com/?c=find&s=1&gub=1"

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

titles = soup.select("a.tit")

data = []
for t in titles[:10]:
    data.append(t.text.strip())

# 파일 저장
with open("contests.md", "w", encoding="utf-8") as f:
    f.write("# 오늘의 공모전\n\n")
    for d in data:
        f.write(f"- {d}\n")