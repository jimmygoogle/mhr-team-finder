import re

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




teams = [
    "Birmingham Bulls 14U A1",
    "MassConn United 10U AAA",
    "Connecticut Clippers 12U A",
    "Connecticut Jr Rangers (National) 15U AAA",
    "Connecticut Jr Rangers (Premier)",
    "New York Apple Core (EHL)",
    "Nichols School Prep",
    "New York Dynamo (NCDC)",
    "Green Bay Bobcats (Gold) 12U 1A",
    "Hudson Raiders (Blue) 12U 1C2",
    "Radville Nationals U18 B",
    "Mound Westonka White Hawks B1", 
    "Fairbanks Hockey Club Freeze 16U",
    "Northwest Arkansas Ice Hogs HS",
    "Rochester Edge (Black) 10U Girls",
    "PAL Jr Islanders (Elite)",
    "Winona Winhawks 10U B1 Girls",
]

for team in teams:
    age, level = parse_team(team)
    print(f"{team} :: {age} :: {level}")
