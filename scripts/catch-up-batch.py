#!/usr/bin/env python3
"""
VideoAsk catch-up script. Processes ALL unprocessed candidates in one batch.
Finds candidates → pulls transcripts → evaluates → appends to sheet → marks done.

Usage:
  python3 catch-up-batch.py [--max N] [--dry-run]

--max N: Process at most N candidates (default: unlimited for catch-up)
--dry-run: Print what would be done without writing to sheet
"""
import json, subprocess, os, sys, time
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
}


# === Helpers (from process-new-submissions.py) ===
def load_token():
    token_path = f'{CREDENTIALS_DIR}/videoask-token.json'
    oauth_path = f'{CREDENTIALS_DIR}/videoask-oauth.json'
    with open(token_path) as f:
        token_data = json.load(f)
    obtained = token_data.get('obtained_at', '')
    expires_in = token_data.get('expires_in', 86400)
    if obtained:
        obtained_dt = datetime.fromisoformat(obtained.replace('Z', '+00:00'))
        expires_dt = obtained_dt + timedelta(seconds=expires_in - 300)
        if datetime.now(timezone.utc) > expires_dt:
            print("Token expired, refreshing...", file=sys.stderr)
            refresh_script = os.path.join(WORKSPACE, 'scripts', 'refresh-videoask-token.py')
            result = subprocess.run(['python3', refresh_script, '--force'],
                                   capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                with open(token_path) as f:
                    token_data = json.load(f)
            else:
                print(f"Token refresh failed: {result.stderr}", file=sys.stderr)
                sys.exit(1)
    return token_data['access_token']


def va_api(url, token):
    import re
    result = subprocess.run(
        ['curl', '-s', '-w', '\n%{http_code}', url,
         '-H', f'Authorization: Bearer {token}',
         '-H', f'organization-id: {ORG_ID}'],
        capture_output=True, timeout=15
    )
    output = result.stdout
    lines = output.rsplit(b'\n', 1)
    if len(lines) == 2:
        body, status = lines
        status_code = int(status.strip())
        if status_code >= 400:
            return None, f'HTTP_{status_code}'
        cleaned = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b' ', body)
        return json.loads(cleaned), None
    return json.loads(output), None


def load_state():
    state_path = f'{WORKSPACE}/videoask-state.json'
    with open(state_path) as f:
        return json.load(f)

def save_state(state):
    state_path = f'{WORKSPACE}/videoask-state.json'
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)


def get_existing_sheet_emails():
    result = subprocess.run(
        ['gws', 'sheets', 'spreadsheets', 'values', 'get',
         '--params', json.dumps({
             'spreadsheetId': SPREADSHEET_ID,
             'range': f'{SHEET_NAME}!J2:J2000'
         })],
        capture_output=True, text=True, env=GWS_ENV, timeout=15
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return {v[0].lower().strip() for v in data.get('values', []) if v}
    return set()


def fmt_phone(phone):
    import re
    digits = re.sub(r'[^\d]', '', phone)
    if digits.startswith('1') and len(digits) == 11: digits = digits[1:]
    if len(digits) == 10: return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone

def get_area_code(phone):
    import re
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
    return q4_clean[:50].rstrip('.,;')

def extract_drive(q4):
    import re
    if not q4: return ""
    q4_lower = q4.lower()
    m = re.search(r'(\d+)\s*(?:to\s*(\d+))?\s*(?:mile|mi)', q4_lower)
    if m: return f"{m.group(1)}-{m.group(2)}mi" if m.group(2) else f"{m.group(1)}mi"
    m = re.search(r'(\d+)\s*(?:to\s*(\d+))?\s*minut', q4_lower)
    if m: return f"{m.group(1)}-{m.group(2)}min" if m.group(2) else f"{m.group(1)}min"
    return ""

def extract_exp(q3, exp_type):
    import re
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
                  ('elementary','elementary'),('kindergarten','kinder')]:
        if kw in q3_lower and d not in parts: parts.append(d)
    for kw, d in [('lead teacher','lead teacher'),('assistant teacher','asst teacher'),
                  ('substitute','substitute'),('floater','floater'),('nanny','nanny'),('babysit','babysitter')]:
        if kw in q3_lower and d not in parts: parts.append(d)
    if any(w in q3_lower for w in ['education degree','studying education','early childhood']): parts.append('education student')
    elif any(w in q3_lower for w in ['nursing','nurse']): parts.append('nursing bg')
    if not parts: return "See transcript"
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

def evaluate(exp_type, market, q_count):
    if exp_type == 'formal' and q_count >= 4:
        return 'APPROVE', 'MEDIUM' if market == 'arizona' else 'HIGH'
    elif exp_type == 'mixed':
        return 'APPROVE', 'MEDIUM'
    elif exp_type == 'informal':
        return ('APPROVE', 'MEDIUM') if market == 'utah' else ('FLAG', 'MEDIUM')
    elif exp_type == 'none':
        return 'FLAG', 'LOW'
    return 'APPROVE', 'LOW'

def lookup_bq(email, phone):
    query = f"SELECT document_id, LOWER(email) as email, phone, firstName, lastName FROM `upkid-7b192.firestore_sync.users` WHERE LOWER(email) = LOWER('{email}')"
    result = subprocess.run(
        ['bq', 'query', '--use_legacy_sql=false', '--format=json', '--max_rows=5',
         '--maximum_bytes_billed=53687091200', '--project_id=upkid-7b192', query],
        capture_output=True, text=True, env=BQ_ENV, timeout=15
    )
    if result.returncode == 0:
        rows = json.loads(result.stdout)
        if rows: return rows[0]
    if phone:
        query2 = f"SELECT document_id, LOWER(email) as email, phone, firstName, lastName FROM `upkid-7b192.firestore_sync.users` WHERE phone = '{phone}'"
        result2 = subprocess.run(
            ['bq', 'query', '--use_legacy_sql=false', '--format=json', '--max_rows=5',
             '--maximum_bytes_billed=53687091200', '--project_id=upkid-7b192', query2],
            capture_output=True, text=True, env=BQ_ENV, timeout=15
        )
        if result2.returncode == 0:
            rows2 = json.loads(result2.stdout)
            if rows2: return rows2[0]
    return None

def check_interviewed(doc_id):
    query = f"""SELECT COALESCE(
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


def find_next_row():
    result = subprocess.run(
        ['gws', 'sheets', 'spreadsheets', 'values', 'get',
         '--params', json.dumps({
             'spreadsheetId': SPREADSHEET_ID,
             'range': f'{SHEET_NAME}!A2:A2000',
             'majorDimension': 'COLUMNS',
         })],
        capture_output=True, text=True, env=GWS_ENV, timeout=15
    )
    if result.returncode != 0:
        print(f"Error finding next row: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(result.stdout)
    values = data.get('values', [[]])
    col_a = values[0] if values else []
    count = sum(1 for v in col_a if v and v.strip())
    return count + 2


def append_row(candidate, next_row):
    """Append a candidate row to the sheet."""
    name = candidate.get('name', '')
    va_date = candidate.get('va_date', '')
    market = candidate.get('market', '')
    rec = candidate.get('rec', 'APPROVE')
    conf = candidate.get('confidence', 'MEDIUM')
    va_link = candidate.get('va_link', '')
    first_name = candidate.get('first_name', name.split()[0] if name else '')
    doc_id = candidate.get('doc_id', '')
    email = candidate.get('email', '')
    phone = candidate.get('phone_formatted', '')
    zd_link = candidate.get('zd_link', '')
    loc_drive = candidate.get('loc_drive', '')
    exp_str = candidate.get('exp_str', '')
    sched_str = candidate.get('sched_str', '')
    ai_summary = candidate.get('ai_summary', '')
    red_flags = ', '.join(candidate.get('red_flags', []))
    transcripts = candidate.get('transcripts', {})

    notes_parts = [va_date]
    if loc_drive: notes_parts.append(loc_drive)
    if exp_str: notes_parts.append(exp_str)
    intro_notes = ' | '.join(notes_parts)

    rec_emoji = '✅' if rec == 'APPROVE' else '🟡' if rec == 'FLAG' else '❌'
    rec_display = f"{rec_emoji} {rec}"
    if conf: rec_display += f" ({conf})"

    row = [
        False, f"🟢 {name}", market, rec_display,
        f'=HYPERLINK("{va_link}","VideoAsk")', first_name, doc_id,
        email, phone, f'=HYPERLINK("{zd_link}","Zendesk")',
        intro_notes, '', exp_str, loc_drive, sched_str, ai_summary,
        red_flags,
        transcripts.get('q3', ''), transcripts.get('q4', ''),
        transcripts.get('q5', ''), transcripts.get('q6', ''),
        transcripts.get('q7', ''),
    ]

    # Note: row has 23 elements (no checkbox cols A+B in the list)
    # A and B are handled by setDataValidation only, not cell values
    # C=col 0 through X=col 22 in the actual sheet

    # Build cell data — map to actual sheet columns
    # Col A (idx 0) and B (idx 1) = checkboxes via data validation
    # Col C (idx 2) = date, Col D (idx 3) = name, etc.
    cell_data = []

    # A: Karen Reviewed checkbox
    cell_data.append({'userEnteredValue': {'boolValue': False}})

    # B: Erica Approved checkbox
    cell_data.append({'userEnteredValue': {'boolValue': False}})

    # C through X (idx 2-23)
    for value in row:
        if isinstance(value, bool):
            cell_data.append({'userEnteredValue': {'boolValue': value}})
        elif isinstance(value, str) and value.startswith('='):
            cell_data.append({'userEnteredValue': {'formulaValue': value}})
        else:
            cell_data.append({'userEnteredValue': {'stringValue': str(value)}})

    request = {
        'requests': [
            # Set checkbox data validation on A:B
            {
                'setDataValidation': {
                    'range': {
                        'sheetId': 412743935,
                        'startRowIndex': next_row - 1,
                        'endRowIndex': next_row,
                        'startColumnIndex': 0,
                        'endColumnIndex': 2,
                    },
                    'rule': {
                        'condition': {'type': 'BOOLEAN'}
                    }
                }
            },
            # Write all cell values
            {
                'updateCells': {
                    'range': {
                        'sheetId': 412743935,
                        'startRowIndex': next_row - 1,
                        'endRowIndex': next_row,
                        'startColumnIndex': 0,
                        'endColumnIndex': 24,
                    },
                    'rows': [{'values': cell_data}],
                    'fields': 'userEnteredValue',
                }
            }
        ]
    }

    result = subprocess.run(
        ['gws', 'sheets', 'spreadsheets', 'batchUpdate',
         '--params', json.dumps({'spreadsheetId': SPREADSHEET_ID}),
         '--json', json.dumps(request)],
        capture_output=True, text=True, env=GWS_ENV, timeout=20
    )

    if result.returncode != 0 or '"error"' in result.stdout:
        print(f"Error appending row {next_row}: {result.stdout[:300]}", file=sys.stderr)
        return False

    print(f"  Appended {name} to row {next_row}", file=sys.stderr)
    return True


def mark_done(contact_id):
    state = load_state()
    if contact_id not in state.get('processed_contacts', []):
        state.setdefault('processed_contacts', []).append(contact_id)
        save_state(state)
    print(f"  Marked {contact_id} as done", file=sys.stderr)


def main():
    max_candidates = None
    dry_run = False
    for arg in sys.argv[1:]:
        if arg == '--dry-run':
            dry_run = True
        elif arg.startswith('--max='):
            max_candidates = int(arg.split('=')[1])

    print("=== VideoAsk Catch-Up Batch ===", file=sys.stderr)

    # Load token
    token = load_token()

    # Load state
    state = load_state()
    processed = set(state.get('processed_contacts', []))

    # Get sheet emails for duplicate check
    existing_emails = get_existing_sheet_emails()
    print(f"Sheet has {len(existing_emails)} emails", file=sys.stderr)

    # Get all API contacts
    all_contacts = []
    offset = 0
    while True:
        data, err = va_api(
            f'https://api.videoask.com/forms/{FORM_ID}/contacts?limit=100&offset={offset}&status=completed',
            token
        )
        if err:
            print(f"API error: {err}", file=sys.stderr)
            sys.exit(1)
        items = data.get('results', data.get('items', []))
        all_contacts.extend(items)
        if not data.get('next') or len(items) == 0:
            break
        offset += 100

    # Filter to unprocessed + not in sheet
    new_contacts = []
    for c in all_contacts:
        cid = c['contact_id']
        email = (c.get('email') or '').strip().lower()
        if cid in processed:
            continue
        if email and email in existing_emails:
            # Already in sheet by email, mark processed
            processed.add(cid)
            continue
        new_contacts.append(c)

    if max_candidates:
        new_contacts = new_contacts[:max_candidates]

    print(f"Found {len(new_contacts)} candidates to process", file=sys.stderr)

    if not new_contacts:
        print("No candidates to process!")
        return

    # Collect contact IDs we need answers for
    needed_cids = {c['contact_id'] for c in new_contacts}
    print(f"Fetching transcripts for {len(needed_cids)} candidates...", file=sys.stderr)
    answers_cache = {}  # contact_id -> {qkey: transcript}
    for qkey, qid in QUESTION_IDS.items():
        a_offset = 0
        while True:
            data, err = va_api(
                f'https://api.videoask.com/questions/{qid}/answers?limit=100&offset={a_offset}',
                token
            )
            if err:
                break
            items = data.get('results', data.get('items', []))
            found_any = False
            for ans in items:
                cid = ans.get('contact_id')
                if cid in needed_cids:
                    t = ans.get('transcription', '')
                    if t and t.strip():
                        answers_cache.setdefault(cid, {})[qkey] = t.strip()
                    found_any = True
            if not data.get('next') or len(items) == 0:
                break
            a_offset += 100
    print(f"Cached transcripts for {len(answers_cache)} candidates", file=sys.stderr)

    # Process each candidate
    success_count = 0
    fail_count = 0
    skip_count = 0

    for contact in new_contacts:
        cid = contact['contact_id']
        email = (contact.get('email') or '').strip()
        phone = (contact.get('phone_number') or '').strip()
        name = (contact.get('name') or '').strip()

        print(f"\nProcessing: {name} ({email})", file=sys.stderr)

        # Date
        created_utc = contact.get('created_at', '')
        va_date = ''
        if created_utc:
            utc_dt = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
            mdt_dt = utc_dt.astimezone(MDT)
            va_date = mdt_dt.strftime('%Y-%m-%d')

        # Transcripts from cache
        transcripts = answers_cache.get(cid, {})
        q_count = sum(1 for q in ['q3','q4','q5','q6','q7'] if transcripts.get(q))

        # Market
        phone_market = AREA_CODE_MARKET.get(get_area_code(phone), 'unknown')
        market = phone_market if phone_market != 'unknown' else 'georgia'

        # Experience
        exp_type = detect_experience_type(transcripts.get('q3'))

        # BQ lookup
        bq_match = lookup_bq(email, phone) if email or phone else None
        doc_id = bq_match['document_id'] if bq_match else ''
        first_name = bq_match.get('firstName', name.split()[0]) if bq_match else name.split()[0] if name else ''

        # Skip if already interviewed
        if doc_id and check_interviewed(doc_id):
            print(f"  Skipped: already interviewed", file=sys.stderr)
            mark_done(cid)
            skip_count += 1
            continue

        # Evaluate
        rec, conf = evaluate(exp_type, market, q_count)

        # Extract structured data
        city = extract_city(transcripts.get('q4'), market)
        drive = extract_drive(transcripts.get('q4'))
        exp_str = extract_exp(transcripts.get('q3'), exp_type)
        sched_str = extract_sched(transcripts.get('q5'))
        loc_drive = city + (f", {drive}" if drive else "")

        va_link = f'https://app.videoask.com/app/organizations/{ORG_ID}/form/{FORM_ID}/conversation/{cid}'
        email_enc = email.replace('+', '%2B')
        zd_link = f'https://upkid.zendesk.com/agent/search/1?q={email_enc}'

        # Build AI summary from transcripts (simple extraction, not model-generated)
        # For catch-up, we generate a basic summary from the data we have
        summary_parts = []
        if exp_str:
            summary_parts.append(f"{exp_str} experience")
        if loc_drive:
            summary_parts.append(f"based in {loc_drive}")
        if sched_str:
            summary_parts.append(f"seeking {sched_str} work")
        ai_summary = name + " has " + ". ".join(summary_parts) + "." if summary_parts else "No details available."

        candidate = {
            'contact_id': cid, 'name': name, 'email': email,
            'phone_formatted': fmt_phone(phone), 'market': market,
            'va_date': va_date, 'rec': rec, 'confidence': conf,
            'exp_type': exp_type, 'exp_str': exp_str,
            'loc_drive': loc_drive, 'sched_str': sched_str,
            'va_link': va_link, 'zd_link': zd_link,
            'doc_id': doc_id, 'first_name': first_name,
            'ai_summary': ai_summary,
            'red_flags': [],
            'transcripts': transcripts,
        }

        if dry_run:
            print(f"  DRY RUN: Would append {name} to sheet", file=sys.stderr)
            success_count += 1
            continue

        # Find next row and append
        next_row = find_next_row()
        if append_row(candidate, next_row):
            mark_done(cid)
            success_count += 1
        else:
            fail_count += 1

        time.sleep(1)  # Rate limit

    print(f"\n=== DONE ===", file=sys.stderr)
    print(f"Processed: {success_count} | Failed: {fail_count} | Skipped (interviewed): {skip_count}")
    print(f"Total: {len(new_contacts)}")


if __name__ == '__main__':
    main()
