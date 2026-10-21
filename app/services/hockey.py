from app.models import Association, League, TeamLeague, Team, AgeTier, RatingHistory
from app import db

import ssl, certifi, requests, re, time, json, redis, os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from bs4 import NavigableString
from typing import Tuple, Optional
from urllib.parse import urlparse, parse_qs
import googlemaps
from sqlalchemy import func
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin
from geoalchemy2.shape import to_shape
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

load_dotenv()

gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

AGE_TIER_RE = re.compile(
    r'(?:^|\s)'
    r'(?:(?P<age>\d{1,2}U|U\d{1,2})\s*)?'
    r'(?P<tier>'
        r'AAA|AA|BB|A|B|C|D|'
        r'[A-Z]\d|'
        r'\d[A-Z]\d?|'
        r'Prep|Varsity|JV|HS'
    r')?'
    r'\s*$',
    re.IGNORECASE
)

GENDER_RE = re.compile(r'\b(Girls|Boys)\b', re.IGNORECASE)

LEAGUE_RE = re.compile(
    r'\((NCDC|EHL|Premier|National|Elite)\)',
    re.IGNORECASE
)

def to_geojson(results):
    association_data = {}
    mhr_data = {}

    # loop through ratung - 30 spits
    for row in results:
        team = row.Team
        association = row.Association
        mhr_data = json.dumps([])

        if row.mhr_rating is not None:
            mhr_ratings = row.mhr_rating.split(",")
            mhr_rating_weeks = row.mhr_rating_week.split(",")

            # create a tuple with (week, rating) then turn it into an array
            # some weeks may be empty until the team gets a rating
            data = list(zip(mhr_rating_weeks, mhr_ratings))
            items = {int(k) - 1: float(v) for k, v in data}
            max_idx = max(items.keys())

            mhr_data = json.dumps([items.get(i, None) for i in range(max_idx + 1)])

        if association.association_name not in association_data:
            association_data[association.association_name] = []

        association_data[association.association_name].append({
            "team_name": team.team_name,
            "rating": team.current_rating,
            "team_url": f"https://myhockeyrankings.com/team-info?t={team.mhr_team_id}&y=2026",
            "mhr_data": mhr_data
        })

    features = []
    processed_associations = {}
    for row in results:
        team = row.Team
        association = row.Association

        # we only need each association once
        # the teams were preset above
        if association in processed_associations:
            continue
        
        processed_associations[association] = 1
    
        geom = to_shape(association.geom)

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [geom.x, geom.y]
            },
            "properties": {
                "id": association.id,
                "mhr_association_url": f"https://myhockeyrankings.com/association-info?a={association.mhr_association_id}",
                "name": association.association_name,
                "association_url": association.url,
                "city": association.city,
                "state": association.state,
                "teams": association_data[association.association_name]
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

def get_association_data(request):
    min_rating = request.args.get("min_rating", None)
    max_rating = request.args.get("max_rating", None)
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    max_miles = request.args.get("max_miles", None)
    age = request.args.get("age", None)
    regions = request.args.get("region", None)
    tier = request.args.get("tier", None)

    query = (
        Team.query.join(Association)
        .outerjoin(RatingHistory)
        .with_entities(
            Team,
            Association,
            func.string_agg(
                func.cast(RatingHistory.mhr_rating_week, db.String), ","
            ).label("mhr_rating_week"),
            func.string_agg(
                func.cast(RatingHistory.rating, db.String), ","
            ).label("mhr_rating")
        )
        .group_by(Team.id, Association.id)
    )

    if age != "":
        age_filters = [s.strip() for s in age.split(",")]
        query = query.filter(
            Team.age_tier.has(AgeTier.age.in_(age_filters))
        )

    if tier != "":
        tier_filters = [s.strip() for s in tier.split(",")]
        query = query.filter(
            Team.age_tier.has(AgeTier.tier.in_(tier_filters))
        )

    if min_rating != "":
        query = query.filter(Team.current_rating >= min_rating)

    if max_rating != "":
        query = query.filter(Team.current_rating <= max_rating)

    if regions != "":
        state_filters = [s.strip() for s in regions.split(",")]
        query = query.filter(Association.state.in_(state_filters))

    if max_miles != "" and regions == '':
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        meters = int(max_miles) * 1609.34

        query = query.filter(
            ST_DWithin(
                func.cast(Association.geom, Geography),
                func.cast(point, Geography),
                meters
            )
        )

    print(
        str(
            query.statement.compile(
                compile_kwargs={"literal_binds": True}
            )
        )
    )

    results = query.all()
    return to_geojson(results)

def load_association_data():
    options = Options()
    options.add_experimental_option(
        "prefs",
        {"profile.default_content_setting_values.javascript": 2} # 1 = Allow, 2 = Block
    )

    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    # get current MHR week
    mhr_rating_week = get_mhr_week()

    # get cached MHR week
    cached_mhr_week = r.get('mhr_week')

    association_key = 'association'
    state_key = 'state'

    if cached_mhr_week is None:
        print(f"Setting MHR week: {mhr_rating_week}")
        r.set('mhr_week', mhr_rating_week)
    else:
        # its a new week so clear our caches
        if cached_mhr_week != mhr_rating_week:
            print('Clearing caches ...')
            r.delete(association_key)
            r.delete(state_key)

    # get our last processed association data
    raw_data = r.get(association_key)

    if raw_data is None:
        processed_associations = {}
    else:
        processed_associations = json.loads(raw_data)

    # get our last processed states
    raw_data = r.get(state_key)

    if raw_data is None:
        processed_states = {}
    else:
        processed_states = json.loads(raw_data)

    # loop through each state and get each association
    for state in [
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
        "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
        "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
        "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
        "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
        "DC","AB","BC","MB","NB","NL", "NS","NT","NU","ON",
        "PE","QC","SK","YT"
    ]:
        if state in processed_states:
            print('*' * 20)
            print(f"Already processed {state}")
            print('*' * 20)
            continue
        else:
            print('*' * 20)
            print(f"Working with {state}")
            print('*' * 20)

        with webdriver.Chrome(options=options) as driver:
            for page in range(1,5):
                # get associations in the state/province
                url = f"https://myhockeyrankings.com/associations/{state}/{page}"
                driver.get(url)

                if 'Forbidden' in driver.page_source:
                    print(f"Stopping with {state} because of 403. We will need to restart.")
                    print(driver.page_source)
                    exit()

                # stop of we have paginated too far (hacky)
                if 'No associations found' in driver.page_source:
                    break

                soup = BeautifulSoup(driver.page_source, 'html.parser')

                for a in soup.find_all("a", href=re.compile(r"association-info")):
                    href = a.get("href")
                    name = a.find("p").get_text(strip=True)

                    # skip this association that we already processed
                    if name in processed_associations:
                        print(f"Skipping {name}")
                        continue

                    # get city/state|province from location
                    location = a.find_all("p")[1].get_text(strip=True)
                    clean = re.sub(r"\s*\|\s*Girls Only\s*$", "", location)

                    location_parts = clean.split(',')
                    city = location_parts[0].strip()
                    state = location_parts[1].strip()

                    # get association id from url
                    parsed = urlparse(href)
                    params = parse_qs(parsed.query)
                    association_id = int(params["a"][0])

                    print(f"{name} ({association_id}) in {city}, {state}")

                    association = Association.query.filter_by(association_name=name).first()

                    if not association:
                        print(f"Adding new association: {name}")

                        association = Association(
                            association_name=name,
                            city=city,
                            state=state,
                            mhr_association_id=association_id
                        )

                        # get lat/long of the association (only one time)
                        geocode_result = gmaps.geocode(f"{city}, {state}")

                        if geocode_result:
                            location = geocode_result[0]["geometry"]["location"]
                            association.set_location(location["lat"], location["lng"])

                        db.session.add(association)
                        db.session.commit()
                        time.sleep(2)

                    # get details about association (teams, etc)
                    url = f"https://myhockeyrankings.com/association-info?a={association_id}"

                    driver.get(url)

                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    parse_association_data(soup, association, mhr_rating_week)

                    # keep track of the last association we completed
                    processed_associations[name] = 1
                    r.set(association_key, json.dumps(processed_associations))

                    time.sleep(.5)

        # keep track of the last state we completed
        processed_states[state] = 1
        r.set(state_key, json.dumps(processed_states))

        # sleep a bit so we dont bring too much attention to ourselves :) [whatever]
        time.sleep(20)

def parse_team(name):
    age = tier = league = gender = ""

    # --- extract gender ---
    gm = GENDER_RE.search(name)
    if gm:
        gender = gm.group(1)

    # REMOVE gender before age/tier parsing
    clean_name = GENDER_RE.sub("", name).strip()

    # --- age + tier (anchored) ---
    m = AGE_TIER_RE.search(clean_name)
    if m:
        age = m.group('age') or ""
        tier = m.group('tier') or ""

        if age:
            age = age.upper()

    # --- league ---
    lm = LEAGUE_RE.search(name)
    if lm:
        league = lm.group(1)

    level = tier or league or gender

    return age, level

def parse_association_data(soup, association, mhr_rating_week):
    teams = []

    # get association url
    if soup.select_one("#social_links a"):
        url = soup.select_one("#social_links a")["href"]
    else:
        url = ''

    # get association status
    status_strong = soup.find("strong", string="Status:")

    if status_strong:
        status = status_strong.next_sibling.strip()
    else:
        status = 'unknown'

    # add association data
    association.status = status
    association.url = url
    db.session.commit()

    # loop through table rows
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

        age, tier = parse_team(team_name)

        #print(f"'{team_name}' : '{age}' : '{tier}'")

        age_tier = AgeTier.query.filter_by(
            age=age,
            tier=tier
        ).first()

        if not age_tier:
            age_tier = AgeTier(
                age=age,
                tier=tier
            )

            db.session.add(age_tier)
            db.session.commit()

        teams.append(team_name)

        parsed = urlparse(team_link.get("href"))
        params = parse_qs(parsed.query)
        team_id = int(params["t"][0])

        team = Team.query.filter_by(team_name=team_name).first()
        current_rating = float(rating)

        if not team:
            team = Team(
                association_id=association.id,
                team_name=team_name,
                mhr_team_id=team_id,
                current_rating=current_rating
            )

            if age_tier:
                team.age_tier_id = age_tier.id

            db.session.add(team)
            db.session.commit()
        else:
            # update rating
            team.age_tier_id = age_tier.id
            team.current_rating = current_rating
            db.session.add(team)
            db.session.commit()

            # add ranking to history
            if mhr_rating_week > 0:
                rating_history = RatingHistory.query.filter_by(
                    team_id=team.id,
                    mhr_rating_week=mhr_rating_week
                ).first()

                if not rating_history:
                    # add to rating history
                    rating_history = RatingHistory(
                        team_id=team.id,
                        rating=float(rating),
                        mhr_rating_week=mhr_rating_week
                    )

                db.session.add(rating_history)
                db.session.commit()
        # 
        for league in leagues:
            a = league.find("a", href=True)
            if not a:
                continue

            league_name = " ".join(a.get_text().split())
            href = a["href"]

            parsed = urlparse(href)
            params = parse_qs(parsed.query)

            league_id = int(params["d"][0])

            # 
            league = League.query.filter_by(league_name=league_name).first()

            if not league:
                league = League(
                    league_name=league_name,
                    mhr_league_id=league_id
                )

                db.session.add(league)
                db.session.commit()

            # sometimes the word 'girls' isnt in the team descrition
            # so go back and change their tier to the girls tier
            # ex: Adirondack Northstars 12U
            if 'Girl' in league_name:
                team = Team.query.filter_by(team_name=team.team_name).first()

                age_tier = AgeTier.query.get(team.age_tier_id)
                age = age_tier.age

                age_tier = AgeTier.query.filter_by(
                    age=age,
                    tier='Girls'
                ).first()

                team.age_tier_id = age_tier.id
                
                db.session.add(team)
                db.session.commit()

            #
            team_league = TeamLeague.query.filter_by(
                team_id=team.id,
                league_id=league.id
            ).first()

            if not team_league:
                team_league = TeamLeague(
                    team_id=team.id,
                    league_id=league.id
                )
                
                db.session.add(team_league)
                db.session.commit()

    #print(teams)

def get_mhr_week(target_date=None):
    if target_date is None:
        target_date = datetime.now()

    # 1. Determine the start year of the current season
    # If month is Sept or later, season started this year; otherwise, it started last year
    if target_date.month >= 9:
        start_year = target_date.year
    else:
        start_year = target_date.year - 1

    # 2. Set Week 1 Start Date (September 30th)
    week_1_start = datetime(start_year, 9, 30)

    # 3. Handle pre-season dates (before Sept 30)
    if target_date < week_1_start:
        return 0  # Pre-season / Week 0

    # 4. Calculate days passed and determine week number
    days_elapsed = (target_date - week_1_start).days
    week_number = (days_elapsed // 7) + 1

    return week_number

def find_associations(request):
    q = request.args.get("q", "").strip()

    if not q:
        return []

    matches = (
        Association.query
        .filter(Association.association_name.ilike(f"%{q}%"))
        .order_by(Association.association_name)
        .limit(10)
        .all()
    )

    return [
        {
            "name": a.association_name,
            "lat": a.latitude,
            "lon": a.longitude
        }
        for a in matches
    ]

def find_teams(request):
    q = request.args.get("q", "").strip()

    if not q:
        return []

    teams = (
        Team.query
        .join(Team.association)
        .filter(Team.team_name.ilike(f"%{q}%"))
        .limit(20)
        .all()
    )

    return [
        {
            "name": team.team_name,
            "lat": team.association.latitude,
            "lon": team.association.longitude
        }
        for team in teams
    ]