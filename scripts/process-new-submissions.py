#!/usr/bin/env python3
"""
Process new VideoAsk submissions. Called by the cron job.
Handles: token refresh, API pull, BigQuery lookup, duplicate detection,
evaluation, sheet append, state update.
Returns JSON with new candidates for the cron agent to write AI summaries and Slack messages.
"""
import json, re, subprocess, os, sys, time
from datetime import datetime, timezone, timedelta

# === Config ===
WORKSPACE = '/Users/tylerbot/.openclaw/workspace-videoask-reviewer'
CREDENTIALS_DIR = '/Users/tylerbot/credentials'
ORG_ID = '3f29b255-68a4-45c3-9cf7-883383e01bcc'
FORM_ID = 'c44b53b4-ec5e-4da7-8266-3c0b327dba88'
SPREADSHEET_ID = '1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0'
SHEET_NAME = 'Backlog Reviews'
GWS_ENV = {**os.environ, 'GOOGLE_WORKSPACE_CLI_CONFIG_DIR': '/Users/tylerbot/.config/gws-write'}
BQ_ENV = {**os.environ, 'GOOGLE_APPLICATION_CREDENTIALS': f'{CREDENTIALS_DIR}/bigquery-tyler-bot.json'}
MDT = timezone(timedelta(hours=-6))
MAX_PER_RUN = 2  # Process max 2 per cron run — Opus needs ~3min per candidate

QUESTION_IDS = {
    'q3': '4312c81f-5e50-4ee6-8ab0-0342b0cce53c',
    'q4': 'd796e231-caac-433f-be1e-4080793da124',
    'q5': 'f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f',
    'q6': '9eedc1d8-00d0-45c1-8366-a2a34111602e',
    'q7': '2f9acb14-72d1-474c-a559-be5df35d6dd9',
}

AREA_CODE_MARKET = {
    '801': 'utah', '385': 'utah', '435': 'utah',
    '404': 'georgia', '470': 'georgia', '678': 'georgia', '770': 'georgia',
    '762': 'georgia', '706': 'georgia', '912': 'georgia', '229': 'georgia', '478': 'georgia',
    '480': 'arizona', '602': 'arizona', '623': 'arizona', '520': 'arizona', '928': 'arizona',
}

KNOWN_CITIES = {
    'atlanta': 'Atlanta, GA', 'jonesboro': 'Jonesboro, GA', 'lithonia': 'Lithonia, GA',
    'conyers': 'Conyers, GA', 'riverdale': 'Riverdale, GA', 'decatur': 'Decatur, GA',
    'marietta': 'Marietta, GA', 'lawrenceville': 'Lawrenceville, GA', 'college park': 'College Park, GA',
    'stone mountain': 'Stone Mountain, GA', 'stonecrest': 'Stonecrest, GA',
    'mcdonough': 'McDonough, GA', 'covington': 'Covington, GA', 'augusta': 'Augusta, GA',
    'savannah': 'Savannah, GA', 'macon': 'Macon, GA', 'powder springs': 'Powder Springs, GA',
    'kennesaw': 'Kennesaw, GA', 'douglasville': 'Douglasville, GA',
    'fayetteville': 'Fayetteville, GA', 'stockbridge': 'Stockbridge, GA',
    'south fulton': 'South Fulton, GA', 'forest park': 'Forest Park, GA',
    'provo': 'Provo, UT', 'salt lake': 'Salt Lake City, UT', 'orem': 'Orem, UT',
    'lehi': 'Lehi, UT', 'eagle mountain': 'Eagle Mountain, UT', 'draper': 'Draper, UT',
    'sandy': 'Sandy, UT', 'ogden': 'Ogden, UT', 'layton': 'Layton, UT',
    'american fork': 'American Fork, UT', 'springville': 'Springville, UT',
    'herriman': 'Herriman, UT', 'saratoga springs': 'Saratoga Springs, UT',
    'phoenix': 'Phoenix, AZ', 'tucson': 'Tucson, AZ', 'mesa': 'Mesa, AZ',
    'tempe': 'Tempe, AZ', 'chandler': 'Chandler, AZ', 'gilbert': 'Gilbert, AZ',
    'scottsdale': 'Scottsdale, AZ', 'glendale': 'Glendale, AZ', 'peoria': 'Peoria, AZ',
    'surprise': 'Surprise, AZ', 'avondale': 'Avondale, AZ', 'goodyear': 'Goodyear, AZ',
    'buckeye': 'Buckeye, AZ', 'queen creek': 'Queen Creek, AZ',
    'aiken': 'Aiken, SC ⚠️',
}

MALE_NAMES = {'brian','john','matt','matthew','jarvis','james','george','nicholas','nico',
              'josue','elan','denetric','brodie','robert','michael','david','daniel','joseph',
              'william','richard','charles','thomas','chris','jason','ryan','kevin','brandon'}
AMBIGUOUS_NAMES = {'mar','sammy','sam','morgan','jacee','alex','taylor','casey','jamie','terry'}


# === Token Management ===
def load_token():
    """Load VideoAsk token, refresh if expired."""
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    oauth_path = f'{CREDENTIALS_DIR}/videoask-oauth.json'
    
    with open(token_path) as f:
        token_data = json.load(f)
    
    # Check if expired
    obtained = token_data.get('obtained_at', '')
    expires_in = token_data.get('expires_in', 86400)
    if obtained:
        obtained_dt = datetime.fromisoformat(obtained.replace('Z', '+00:00'))
        expires_dt = obtained_dt + timedelta(seconds=expires_in - 300)  # 5min buffer
        if datetime.now(timezone.utc) > expires_dt:
            print("Token expired, attempting refresh...", file=sys.stderr)
            refresh_script = os.path.join(WORKSPACE, 'scripts', 'refresh-videoask-token.py')
            result = subprocess.run(
                ['python3', refresh_script, '--force'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print(f"Token refresh: {result.stdout.strip()}", file=sys.stderr)
                with open(token_path) as f:
                    token_data = json.load(f)
            else:
                print(f"Token refresh failed: {result.stdout.strip()} {result.stderr.strip()}", file=sys.stderr)
                print("TOKEN_EXPIRED", file=sys.stderr)
                return None
    
    return token_data['access_token']

def refresh_token(oauth_path, token_path):
    """Refresh the VideoAsk OAuth token.
    
    Tries two methods:
    1. refresh_token grant (if we have a refresh token saved)
    2. client_credentials grant (if we have client_id + client_secret)
    
    If neither works, returns False and the caller should alert via Slack.
    """
    if not os.path.exists(oauth_path):
        return False
    try:
        with open(oauth_path) as f:
            oauth = json.load(f)
        
        # Method 1: refresh_token grant
        if oauth.get('refresh_token'):
            result = subprocess.run(
                ['curl', '-s', '-X', 'POST', 'https://auth.videoask.com/oauth/token',
                 '-H', 'Content-Type: application/json',
                 '-d', json.dumps({
                     'grant_type': 'refresh_token',
                     'client_id': oauth.get('client_id', ''),
                     'refresh_token': oauth.get('refresh_token', ''),
                 })],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                new_token = json.loads(result.stdout)
                if 'access_token' in new_token:
                    new_token['obtained_at'] = datetime.now(timezone.utc).isoformat()
                    with open(token_path, 'w') as f:
                        json.dump(new_token, f, indent=2)
                    # Save refresh token back to oauth if returned
                    if 'refresh_token' in new_token:
                        oauth['refresh_token'] = new_token['refresh_token']
                        with open(oauth_path, 'w') as f:
                            json.dump(oauth, f, indent=2)
                    print("Token refreshed via refresh_token", file=sys.stderr)
                    return True
        
        # Method 2: client_credentials (for M2M)
        if oauth.get('client_id') and oauth.get('client_secret'):
            result = subprocess.run(
                ['curl', '-s', '-X', 'POST', oauth.get('token_url', 'https://auth.videoask.com/oauth/token'),
                 '-H', 'Content-Type: application/json',
                 '-d', json.dumps({
                     'grant_type': 'client_credentials',
                     'client_id': oauth['client_id'],
                     'client_secret': oauth['client_secret'],
                     'audience': oauth.get('api_base', 'https://api.videoask.com/'),
                 })],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                new_token = json.loads(result.stdout)
                if 'access_token' in new_token:
                    new_token['obtained_at'] = datetime.now(timezone.utc).isoformat()
                    with open(token_path, 'w') as f:
                        json.dump(new_token, f, indent=2)
                    print("Token refreshed via client_credentials", file=sys.stderr)
                    return True
        
        print("All refresh methods failed", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Token refresh failed: {e}", file=sys.stderr)
        return False

def clean_json(raw):
    cleaned = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b' ', raw)
    return json.loads(cleaned)

def va_api(url, token):
    """Make a VideoAsk API call with error handling."""
    result = subprocess.run(
        ['curl', '-s', '-w', '\n%{http_code}', url,
         '-H', f'Authorization: Bearer {token}',
         '-H', f'organization-id: {ORG_ID}'],
        capture_output=True, timeout=15
    )
    output = result.stdout
    # Extract status code from last line
    lines = output.rsplit(b'\n', 1)
    if len(lines) == 2:
        body, status = lines
        status_code = int(status.strip())
        if status_code == 401 or status_code == 403:
            return None, 'TOKEN_EXPIRED'
        if status_code >= 400:
            return None, f'HTTP_{status_code}'
        return clean_json(body), None
    return clean_json(output), None


# === State Management ===
def load_state():
    state_path = f'{WORKSPACE}/videoask-state.json'
    if os.path.exists(state_path):
        with open(state_path) as f:
            return json.load(f)
    return {'processed_contacts': [], 'pending_match': []}

def save_state(state):
    state_path = f'{WORKSPACE}/videoask-state.json'
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)


# === Sheet Duplicate Detection ===
def get_existing_sheet_emails():
    """Read emails from current sheet to detect duplicates."""
    result = subprocess.run(
        ['gws', 'sheets', 'spreadsheets', 'values', 'get',
         '--params', json.dumps({
             'spreadsheetId': SPREADSHEET_ID,
             'range': f'{SHEET_NAME}!I2:I1000'  # Email column
         })],
        capture_output=True, text=True, env=GWS_ENV
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return {v[0].lower().strip() for v in data.get('values', []) if v}
    return set()


# === Helpers ===
def fmt_phone(phone):
    digits = re.sub(r'[^\d]', '', phone)
    if digits.startswith('1') and len(digits) == 11: digits = digits[1:]
    if len(digits) == 10: return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone

def get_area_code(phone):
    digits = re.sub(r'[^\d]', '', phone)
    if digits.startswith('1') and len(digits) == 11: return digits[1:4]
    elif len(digits) == 10: return digits[:3]
    return ''

def extract_city(q4, market):
    if not q4: return market.title()
    q4_lower = q4.lower()
    best_match, best_pos = None, len(q4_lower)
    for city_key, city_display in KNOWN_CITIES.items():
        pos = q4_lower.find(city_key)
        if pos >= 0 and pos < best_pos:
            best_match, best_pos = city_display, pos
    if best_match: return best_match
    q4_clean = q4.strip()
    for prefix in ['I am currently located in ','I currently reside here in ',
                   'I live in the ','I live in ',"I'm in ",'I am in ','I stay in ']:
        if q4_clean.lower().startswith(prefix.lower()):
            q4_clean = q4_clean[len(prefix):].strip(); break
    for delim in ['. ',', and ',' and I',' I ',' my ',' which ']:
        idx = q4_clean.lower().find(delim.lower())
        if 3 < idx < 80: q4_clean = q4_clean[:idx].strip(); break
    return q4_clean[:50].rstrip('.,;')

def extract_drive(q4):
    if not q4: return ""
    q4_lower = q4.lower()
    m = re.search(r'(\d+)\s*(?:to\s*(\d+))?\s*(?:mile|mi)', q4_lower)
    if m: return f"{m.group(1)}-{m.group(2)}mi" if m.group(2) else f"{m.group(1)}mi"
    m = re.search(r'(\d+)\s*(?:to\s*(\d+))?\s*minut', q4_lower)
    if m: return f"{m.group(1)}-{m.group(2)}min" if m.group(2) else f"{m.group(1)}min"
    if 'wherever' in q4_lower or 'anywhere' in q4_lower: return "anywhere"
    return ""

def extract_exp(q3, exp_type):
    if not q3: return "No transcript"
    q3_lower = q3.lower()
    parts = []
    years = re.findall(r'(\d+)\+?\s*(?:year|yr)', q3_lower)
    months = re.findall(r'(\d+)\s*month', q3_lower)
    if years: parts.append(f"{max(int(y) for y in years)}yr")
    elif months: parts.append(f"{max(int(m) for m in months)}mo")
    for kw, d in [('daycare','daycare'),('preschool','preschool'),('head start','Head Start'),
                  ('montessori','Montessori'),('boys and girls club','B&G Club'),('ymca','YMCA'),
                  ('summer camp','camp'),('camp counselor','camp counselor'),('after school','afterschool'),
                  ('sunday school','Sunday school'),('church','church'),('elementary','elementary'),('kindergarten','kinder')]:
        if kw in q3_lower and d not in parts: parts.append(d)
    for kw, d in [('lead teacher','lead teacher'),('assistant teacher','asst teacher'),
                  ('substitute','substitute'),('floater','floater'),('nanny','nanny'),('babysit','babysitter')]:
        if kw in q3_lower and d not in parts: parts.append(d)
    if any(w in q3_lower for w in ['education degree','studying education','elementary education','early childhood']): parts.append('education student')
    elif any(w in q3_lower for w in ['nursing','nurse']): parts.append('nursing bg')
    elif any(w in q3_lower for w in ['college','university','student']): parts.append('college student')
    if any(p in q3_lower for p in ['no experience',"don't have experience",'do not currently have']): parts.append('⚠️ no childcare exp')
    if any(w in q3_lower for w in ['healthcare','health care','medical','hospice','cna']): parts.append('healthcare bg')
    if not parts:
        if exp_type == 'informal': return "Informal (babysitting/family)"
        if exp_type == 'unclear': return "Mentions kids exp, vague"
        if exp_type == 'none': return "No childcare exp"
        return "See transcript"
    return '; '.join(parts)

def extract_sched(q5):
    if not q5: return ""
    q5_lower = q5.lower()
    parts = []
    if 'full-time' in q5_lower or 'full time' in q5_lower: parts.append('FT')
    if 'part-time' in q5_lower or 'part time' in q5_lower: parts.append('PT')
    if not parts: parts.append('Flex')
    if any(w in q5_lower for w in ['school','class','student']): parts.append('around school')
    return ', '.join(parts)

def detect_experience_type(q3):
    if not q3: return 'unknown'
    q3_lower = q3.lower()
    FORMAL = ['daycare','preschool','head start','montessori','after school','camp counselor',
              'summer camp','ymca','boys and girls club','classroom','teacher','substitute',
              'kindergarten','elementary','learning center','child development','tutor','school']
    INFORMAL = ['babysit','nanny','own children','my kids','niece','nephew','sibling']
    has_formal = any(kw in q3_lower for kw in FORMAL)
    has_informal = any(kw in q3_lower for kw in INFORMAL)
    if has_formal and has_informal: return 'mixed'
    if has_formal: return 'formal'
    if has_informal: return 'informal'
    if any(w in q3_lower for w in ['experience','worked with','children','kids']): return 'unclear'
    return 'none'

def evaluate(candidate):
    """Evaluate a candidate. Returns recommendation + confidence."""
    exp_type = candidate['exp_type']
    market = candidate['market']
    q_count = candidate['questions_answered']
    
    if exp_type == 'formal' and q_count >= 4:
        if market == 'arizona':
            return 'APPROVE', 'MEDIUM'  # AZ needs 6mo verification
        return 'APPROVE', 'HIGH'
    elif exp_type == 'mixed':
        return 'APPROVE', 'MEDIUM'
    elif exp_type == 'informal':
        if market == 'utah': return 'APPROVE', 'MEDIUM'
        if market == 'arizona': return 'FLAG', 'HIGH'
        return 'FLAG', 'MEDIUM'
    elif exp_type == 'none':
        return 'FLAG', 'LOW'
    elif exp_type == 'unclear':
        return 'APPROVE', 'LOW'
    else:
        return 'FLAG', 'LOW'


# === BigQuery ===
def lookup_bq(email, phone):
    """Find app account by email then phone. Returns dict or None."""
    # Try email
    query = f"SELECT document_id, LOWER(email) as email, phone, firstName, lastName FROM `upkid-7b192.firestore_sync.users` WHERE LOWER(email) = LOWER('{email}')"
    result = subprocess.run(
        ['bq', 'query', '--use_legacy_sql=false', '--format=json', '--max_rows=5',
         '--maximum_bytes_billed=53687091200', '--project_id=upkid-7b192', query],
        capture_output=True, text=True, env=BQ_ENV, timeout=15
    )
    if result.returncode == 0:
        rows = json.loads(result.stdout)
        if rows:
            return rows[0]
    
    # Try phone
    query2 = f"SELECT document_id, LOWER(email) as email, phone, firstName, lastName FROM `upkid-7b192.firestore_sync.users` WHERE phone = '{phone}'"
    result2 = subprocess.run(
        ['bq', 'query', '--use_legacy_sql=false', '--format=json', '--max_rows=5',
         '--maximum_bytes_billed=53687091200', '--project_id=upkid-7b192', query2],
        capture_output=True, text=True, env=BQ_ENV, timeout=15
    )
    if result2.returncode == 0:
        rows2 = json.loads(result2.stdout)
        if rows2:
            return rows2[0]
    
    return None

def check_interviewed(doc_id):
    """Check if teacher is already interviewed in app."""
    query = f"""SELECT 
        COALESCE(
            JSON_EXTRACT_SCALAR(data, '$.onboarding.market.georgia.interviewed'),
            JSON_EXTRACT_SCALAR(data, '$.onboarding.market.utah.interviewed'),
            JSON_EXTRACT_SCALAR(data, '$.onboarding.market.arizona.interviewed')
        ) as interviewed
    FROM `upkid-7b192.firestore_sync.teachers_raw_latest`
    WHERE document_id = '{doc_id}'"""
    result = subprocess.run(
        ['bq', 'query', '--use_legacy_sql=false', '--format=json', '--max_rows=1',
         '--maximum_bytes_billed=53687091200', '--project_id=upkid-7b192', query],
        capture_output=True, text=True, env=BQ_ENV, timeout=15
    )
    if result.returncode == 0:
        rows = json.loads(result.stdout)
        if rows and rows[0].get('interviewed') == 'true':
            return True
    return False


# === Main ===
def main():
    state = load_state()
    processed = set(state.get('processed_contacts', []))
    pending_match = state.get('pending_match', [])
    
    # Step 1: Load token
    token = load_token()
    if not token:
        print(json.dumps({"error": "TOKEN_EXPIRED", "candidates": []}))
        return
    
    # Step 2: Get completed contacts
    all_contacts = []
    offset = 0
    while True:
        data, err = va_api(
            f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=100&offset={offset}&status=completed',
            token
        )
        if err:
            print(json.dumps({"error": err, "candidates": []}))
            return
        items = data.get('results', data.get('items', []))
        all_contacts.extend(items)
        if not data.get('next') or len(items) == 0:
            break
        offset += 100
    
    # Step 2b: Also check sheet emails as safety net
    # Even if state says "not processed", if they're already in the sheet, skip them
    existing_sheet_emails = get_existing_sheet_emails()
    
    # Filter to new (unprocessed) contacts — check BOTH state file AND sheet
    new_contacts = []
    for c in all_contacts:
        cid = c['contact_id']
        email = (c.get('email') or '').strip().lower()
        if cid in processed:
            continue
        # Safety net: if email is already in the sheet, mark as processed and skip
        if email and email in existing_sheet_emails:
            processed.add(cid)
            state['processed_contacts'] = list(processed)
            save_state(state)
            continue
        new_contacts.append(c)
    
    if not new_contacts:
        print(json.dumps({"new_count": 0, "candidates": []}))
        return
    
    # Rate limit: max N per run
    new_contacts = new_contacts[:MAX_PER_RUN]
    
    # Step 3: Process each new contact (sheet emails already loaded above)
    candidates = []
    
    for contact in new_contacts:
        cid = contact['contact_id']
        email = (contact.get('email') or '').strip()
        phone = (contact.get('phone_number') or '').strip()
        name = (contact.get('name') or '').strip()
        created_utc = contact.get('created_at', '')
        share_url = contact.get('share_url', '')
        
        # Convert date to MDT
        va_date = ''
        if created_utc:
            utc_dt = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
            mdt_dt = utc_dt.astimezone(MDT)
            va_date = mdt_dt.strftime('%Y-%m-%d')
        
        # Duplicate check (candidate passed the sheet filter above but may match on a different email variant)
        is_duplicate = email.lower() in existing_sheet_emails if email else False
        
        # Pull transcripts for Q3-Q7
        transcripts = {}
        for qkey, qid in QUESTION_IDS.items():
            # Search answers for this contact
            data, err = va_api(
                f'https://api.videoask.com/questions/{qid}/answers?limit=50',
                token
            )
            if err:
                continue
            items = data.get('results', data.get('items', []))
            for ans in items:
                if ans.get('contact_id') == cid:
                    t = ans.get('transcription', '')
                    if t and t.strip():
                        transcripts[qkey] = t.strip()
                    break
        
        q_count = sum(1 for q in ['q3','q4','q5','q6','q7'] if transcripts.get(q))
        
        # Determine market
        phone_market = AREA_CODE_MARKET.get(get_area_code(phone), 'unknown')
        market = phone_market if phone_market != 'unknown' else 'georgia'  # default
        
        # Experience type
        exp_type = detect_experience_type(transcripts.get('q3'))
        
        # BigQuery lookup
        bq_match = lookup_bq(email, phone) if email or phone else None
        doc_id = bq_match['document_id'] if bq_match else ''
        app_name = f"{bq_match.get('firstName','')} {bq_match.get('lastName','')}" if bq_match else ''
        
        # Check if email matches
        app_match = '🟢'
        mismatches = ''
        if bq_match:
            bq_email = (bq_match.get('email') or '').lower()
            if email.lower() != bq_email and bq_email:
                app_match = '🟡'
                mismatches = f"email: VA={email} APP={bq_email}"
        elif not bq_match and (email or phone):
            # Pending match - try again next run
            if cid not in [p['contact_id'] for p in pending_match]:
                pending_match.append({'contact_id': cid, 'email': email, 'phone': phone, 'attempts': 1})
            app_match = '🔴'
            app_name = 'Not found'
        
        # Check if already interviewed — mark processed and skip
        if doc_id and check_interviewed(doc_id):
            processed.add(cid)
            state['processed_contacts'] = list(processed)
            save_state(state)
            continue
        
        # Evaluate
        rec, conf = evaluate({
            'exp_type': exp_type, 'market': market,
            'questions_answered': q_count
        })
        
        # Extract structured data
        city = extract_city(transcripts.get('q4'), market)
        drive = extract_drive(transcripts.get('q4'))
        exp_str = extract_exp(transcripts.get('q3'), exp_type)
        sched_str = extract_sched(transcripts.get('q5'))
        
        # Red flags
        flags = []
        first_name_lower = name.split()[0].lower() if name else ''
        if first_name_lower in MALE_NAMES:
            flags.append('👨 MALE — centers may not place')
        elif first_name_lower in AMBIGUOUS_NAMES:
            flags.append('❓ Gender unclear — verify')
        if phone_market != 'unknown' and phone_market != market:
            flags.append(f'📞 Area code = {phone_market.title()}')
        if is_duplicate:
            flags.append('⚠️ DUPLICATE — already in sheet')
        
        # VideoAsk dashboard link
        va_link = f'https://app.videoask.com/app/organizations/{ORG_ID}/form/{FORM_ID}/conversation/{cid}'
        
        # Zendesk search link
        email_enc = email.replace('+', '%2B')
        zd_link = f'https://upkid.zendesk.com/agent/search/1?q={email_enc}'
        
        # Build candidate object
        candidate = {
            'contact_id': cid,
            'name': name,
            'email': email,
            'phone': phone,
            'phone_formatted': fmt_phone(phone),
            'market': market,
            'va_date': va_date,
            'rec': rec,
            'confidence': conf,
            'exp_type': exp_type,
            'exp_str': exp_str,
            'city': city,
            'drive': drive,
            'loc_drive': city + (f", {drive}" if drive else ""),
            'sched_str': sched_str,
            'questions_answered': q_count,
            'app_match': app_match,
            'app_name': app_name,
            'doc_id': doc_id,
            'mismatches': mismatches,
            'red_flags': flags,
            'va_link': va_link,
            'zd_link': zd_link,
            'is_duplicate': is_duplicate,
            'transcripts': transcripts,
            'first_name': app_name.split()[0] if app_name and app_name != 'Not found' else name.split()[0] if name else '',
        }
        
        candidates.append(candidate)
        # NOTE: We do NOT mark as processed here. The cron agent calls
        # mark-done.py after successfully writing each candidate to the sheet.
        # This prevents candidates from falling through cracks on timeout.
    
    # Only save pending_match updates (NOT processed contacts)
    state['pending_match'] = [p for p in pending_match if p.get('attempts', 0) < 3]
    save_state(state)
    
    # Output candidates as JSON for the cron agent
    output = {
        'new_count': len(candidates),
        'total_checked': len(all_contacts),
        'candidates': candidates,
        'pending_match_count': len(state['pending_match']),
    }
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
