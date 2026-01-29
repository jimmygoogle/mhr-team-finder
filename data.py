# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from bs4 import NavigableString
from typing import Tuple, Optional
from urllib.parse import urlparse, parse_qs
import requests, re

# mobile_emulation = {
#     "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0 },
#     "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"
# }

# options = Options()
# options.add_argument("--headless")      # remove if you want to see the browser
# options.add_argument("--disable-gpu")
# options.add_argument("--no-sandbox")

# options.add_experimental_option("mobileEmulation", mobile_emulation)

# # browser = webdriver.Chrome(
# #     service=Service(ChromeDriverManager().install()),
# #     options=options
# # )

# # WebDriverWait(browser, 10).until(
# #     lambda d: d.execute_script("return document.readyState") == "complete"
# # )

# urls = [
#     'https://myhockeyrankings.com/rank.php?d=NE&y=2025&v=124',
#     #'https://myhockeyrankings.com/rank.php?d=NY&y=2025&a=1&v=122',
#     # 'https://myhockeyrankings.com/rank.php?d=NE&y=2025&a=1&v=122',
#     # 'https://myhockeyrankings.com/rank.php?d=MA&y=2025&a=1&v=122',
# ]

# def get_pagination_urls(url):
#     """
#     Docstring for pagination_links
    
#     :param url: Description
#     """

#     print(f"Getting pagination urls: {url}")

#     browser = webdriver.Chrome(
#         service=Service(ChromeDriverManager().install()),
#         options=options
#     )
#     browser.get(url)
#     html = browser.page_source
#     browser.close()

#     soup = BeautifulSoup(html, 'html.parser')

#     links = []
    
#     for a in soup.find_all(
#         "a",
#         class_="pagination-nav-link",
#         href=lambda h: h
#     ):
#         links.append('https://myhockeyrankings.com' + a.get("href"))

#     return list(dict.fromkeys(links))


def get_association_data():

    for url in []:
        pass

    url = 'https://myhockeyrankings.com/associations/NY'
    response = requests.get(url, timeout=10)

    soup = BeautifulSoup(response.text, 'html.parser')

    location_data = []
    for a in soup.find_all("a", href=re.compile(r"association-info")):
        href = a.get("href")
        name = a.find("p").get_text(strip=True)

        if name != 'Westchester Express':
            continue

        location = a.find_all("p")[1].get_text(strip=True)

        clean = re.sub(r"\s*\|\s*Girls Only\s*$", "", location)
        location = re.sub(r"\s+", " ", clean).strip()

        parsed = urlparse(href)
        params = parse_qs(parsed.query)

        association_id = int(params["a"][0])

        location_data.append({
            name: name,
            association_id: association_id,
            location: location
        })

        print(f"'{association_id}' : '{name}' : '{location}'")

        url = f"https://myhockeyrankings.com/association-info?a={association_id}"

        response = requests.get(url, timeout=10)

        soup = BeautifulSoup(response.text, 'html.parser')
        parse_association_data(soup)

    return location_data

def parse_association_data(soup):
    teams = []

    url = soup.select_one("#social_links a")["href"]

    status_strong = soup.find("strong", string="Status:")
    status = status_strong.next_sibling.strip()

    age_group_tier_pattern = re.compile(
        r'(?P<age>\d{1,2}U)\s*(?P<tier>AAA|AA|A|B|C|D)?(?:\s+Girls)?$'
    )

    # Loop through table rows
    for row in soup.select("table.rating-math tr"):
        team_link = row.select_one('a[href^="/team-info"]')
        if not team_link:
            continue  # skip headers & section rows

        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        team_name = team_link.get_text(strip=True)
        rating = cells[-1].get_text(strip=True)
        leagues = cells[1].find_all("li")

        print(f"working with team_name {team_name}")

        match = age_group_tier_pattern.search(team_name)
        age = None
        tier = None

        if match:
            age = match.group("age") if not None else ""
            tier = match.group("tier") if not None else ""
            print(f"'{age}' : '{tier}'")

        parsed = urlparse(team_link.get("href"))
        params = parse_qs(parsed.query)
        team_id = int(params["t"][0])

        teams.append({
            "team_name": team_name,
            "rating": rating,
            "leagues": leagues,
            "age": age,
            "tier": tier,
        })

        #league_data = []
        for league in leagues:
            a = league.find("a", href=True)
            if not a:
                continue

            league_name = " ".join(a.get_text().split())
            href = a["href"]

            parsed = urlparse(href)
            params = parse_qs(parsed.query)

            league_id = int(params["d"][0])
            print(f"league_id is {league_id} :: {league_name}")


    for t in teams:
        print(t)

def get_longitude_latitude():
    pass

locations = get_association_data()
exit()

