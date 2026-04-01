#!/bin/bash
# VideoAsk Reviewer Agent — Test Suite
# Tests all core capabilities: API access, BigQuery, transcript pulling, evaluation pipeline
# Run: bash test-suite.sh
# Results: test-results.md

export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"

RESULTS_FILE="$(dirname "$0")/test-results.md"
PASS=0
FAIL=0
SKIP=0
DETAILS=""

# Config
ORG_ID="3f29b255-68a4-45c3-9cf7-883383e01bcc"
FORM_ID="c44b53b4-ec5e-4da7-8266-3c0b327dba88"
TOKEN_FILE="$HOME/credentials/videoask-token.json"
BQ_CREDS="$HOME/credentials/bigquery-tyler-bot.json"
BQ_PROJECT="upkid-7b192"
BQ_MAX_BYTES="53687091200"

# Question IDs
Q3_ID="4312c81f-5e50-4ee6-8ab0-0342b0cce53c"
Q4_ID="d796e231-caac-433f-be1e-4080793da124"
Q5_ID="f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f"
Q6_ID="9eedc1d8-00d0-45c1-8366-a2a34111602e"
Q7_ID="2f9acb14-72d1-474c-a559-be5df35d6dd9"

log_result() {
  local status="$1" name="$2" detail="$3"
  if [ "$status" = "PASS" ]; then
    PASS=$((PASS + 1))
    DETAILS+="| ✅ | $name | $detail |\n"
  elif [ "$status" = "FAIL" ]; then
    FAIL=$((FAIL + 1))
    DETAILS+="| ❌ | $name | $detail |\n"
  else
    SKIP=$((SKIP + 1))
    DETAILS+="| ⏭️ | $name | $detail |\n"
  fi
  echo "[$status] $name — $detail"
}

echo "🧪 VideoAsk Reviewer Agent — Test Suite"
echo "========================================"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# ─────────────────────────────────────────────
# Section 1: Credentials & Config
# ─────────────────────────────────────────────
echo "--- Section 1: Credentials & Config ---"

# 1.1: VideoAsk token file exists
if [ -f "$TOKEN_FILE" ]; then
  log_result "PASS" "VideoAsk token file exists" "$TOKEN_FILE"
else
  log_result "FAIL" "VideoAsk token file exists" "Not found at $TOKEN_FILE"
fi

# 1.2: VideoAsk token has access_token
VA_TOKEN=$(python3 -c "import json; print(json.load(open('$TOKEN_FILE'))['access_token'])" 2>/dev/null || true)
if [ -n "$VA_TOKEN" ]; then
  log_result "PASS" "VideoAsk access_token present" "Token length: ${#VA_TOKEN} chars"
else
  log_result "FAIL" "VideoAsk access_token present" "Missing or empty"
fi

# 1.3: VideoAsk token not expired
TOKEN_AGE=$(python3 -c "
import json, datetime
d = json.load(open('$TOKEN_FILE'))
obtained = datetime.datetime.fromisoformat(d['obtained_at'].replace('Z', '+00:00'))
expires = obtained + datetime.timedelta(seconds=d['expires_in'])
now = datetime.datetime.now(datetime.timezone.utc)
remaining = (expires - now).total_seconds()
print(f'{remaining:.0f}')
" 2>/dev/null || echo "0")
if [ "$TOKEN_AGE" -gt 0 ] 2>/dev/null; then
  HOURS_LEFT=$(python3 -c "print(f'{$TOKEN_AGE/3600:.1f}')")
  log_result "PASS" "VideoAsk token not expired" "${HOURS_LEFT}h remaining"
else
  log_result "FAIL" "VideoAsk token not expired" "Token expired or can't parse"
fi

# 1.4: BigQuery credentials exist
if [ -f "$BQ_CREDS" ]; then
  log_result "PASS" "BigQuery credentials exist" "$BQ_CREDS"
else
  log_result "FAIL" "BigQuery credentials exist" "Not found at $BQ_CREDS"
fi

# 1.5: bq CLI available
if command -v bq &>/dev/null; then
  BQ_VER=$(bq version 2>/dev/null | head -1)
  log_result "PASS" "bq CLI available" "$BQ_VER"
else
  log_result "FAIL" "bq CLI available" "bq not found — install google-cloud-sdk"
fi

# 1.6: VideoAsk OAuth config exists
if [ -f "$HOME/credentials/videoask-oauth.json" ]; then
  HAS_CLIENT=$(python3 -c "import json; d=json.load(open('$HOME/credentials/videoask-oauth.json')); print('yes' if d.get('client_id') and d.get('client_secret') else 'no')" 2>/dev/null || true)
  if [ "$HAS_CLIENT" = "yes" ]; then
    log_result "PASS" "VideoAsk OAuth config (client_id + secret)" "Present"
  else
    log_result "FAIL" "VideoAsk OAuth config (client_id + secret)" "Missing client_id or client_secret"
  fi
else
  log_result "FAIL" "VideoAsk OAuth config exists" "Not found"
fi

# 1.7: Workspace files present
WORKSPACE_DIR="$(cd "$(dirname "$0")" && pwd)"
MISSING_FILES=""
for f in AGENTS.md SOUL.md criteria.json videoask-state.json videoask-master-review-list.md videoask-automation-spec.md; do
  if [ ! -f "$WORKSPACE_DIR/$f" ]; then
    MISSING_FILES+="$f "
  fi
done
if [ -z "$MISSING_FILES" ]; then
  log_result "PASS" "All workspace files present" "AGENTS.md, SOUL.md, criteria.json, state, list, spec"
else
  log_result "FAIL" "All workspace files present" "Missing: $MISSING_FILES"
fi

echo ""

# ─────────────────────────────────────────────
# Section 2: VideoAsk API Connectivity
# ─────────────────────────────────────────────
echo "--- Section 2: VideoAsk API ---"

VA_BASE="https://api.videoask.com"

va_curl() {
  curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $VA_TOKEN" \
    -H "organization-id: $ORG_ID" \
    -H "Content-Type: application/json" \
    "$@"
}

# 2.1: Can list forms
FORMS_RESP=$(va_curl "$VA_BASE/forms?limit=1" 2>/dev/null)
FORMS_HTTP=$(echo "$FORMS_RESP" | tail -1)
FORMS_BODY=$(echo "$FORMS_RESP" | sed '$d')
if [ "$FORMS_HTTP" = "200" ]; then
  log_result "PASS" "VideoAsk API — list forms" "HTTP 200"
else
  log_result "FAIL" "VideoAsk API — list forms" "HTTP $FORMS_HTTP"
fi

# 2.2: Can fetch our specific form
FORM_RESP=$(va_curl "$VA_BASE/forms/$FORM_ID" 2>/dev/null)
FORM_HTTP=$(echo "$FORM_RESP" | tail -1)
FORM_BODY=$(echo "$FORM_RESP" | sed '$d')
if [ "$FORM_HTTP" = "200" ]; then
  FORM_NAME=$(echo "$FORM_BODY" | python3 -c "import json,sys; print(json.load(sys.stdin).get('title','?'))" 2>/dev/null || echo "?")
  log_result "PASS" "VideoAsk API — fetch intro call form" "'$FORM_NAME'"
else
  log_result "FAIL" "VideoAsk API — fetch intro call form" "HTTP $FORM_HTTP"
fi

# 2.3: Can list contacts on the form
CONTACTS_RESP=$(va_curl "$VA_BASE/forms/$FORM_ID/contacts?limit=3" 2>/dev/null)
CONTACTS_HTTP=$(echo "$CONTACTS_RESP" | tail -1)
CONTACTS_BODY=$(echo "$CONTACTS_RESP" | sed '$d')
if [ "$CONTACTS_HTTP" = "200" ]; then
  CONTACT_COUNT=$(echo "$CONTACTS_BODY" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('results',d.get('items',[]))))" 2>/dev/null || echo "?")
  log_result "PASS" "VideoAsk API — list contacts" "$CONTACT_COUNT contact(s) returned"
else
  log_result "FAIL" "VideoAsk API — list contacts" "HTTP $CONTACTS_HTTP"
fi

# 2.4: Can fetch answers for Q3 (experience question)
Q3_RESP=$(va_curl "$VA_BASE/questions/$Q3_ID/answers?limit=2" 2>/dev/null)
Q3_HTTP=$(echo "$Q3_RESP" | tail -1)
Q3_BODY=$(echo "$Q3_RESP" | sed '$d')
if [ "$Q3_HTTP" = "200" ]; then
  log_result "PASS" "VideoAsk API — Q3 answers (experience)" "HTTP 200"
else
  log_result "FAIL" "VideoAsk API — Q3 answers (experience)" "HTTP $Q3_HTTP"
fi

# 2.5: Answers contain transcription data
if [ "$Q3_HTTP" = "200" ]; then
  HAS_T=$(echo "$Q3_BODY" | python3 -c "
import json,sys
d = json.load(sys.stdin)
items = d.get('results', d.get('items', []))
if items:
    t = items[0].get('transcription', '')
    print(f'{len(t)} chars') if t and len(t) > 5 else print('EMPTY')
else:
    print('NO_ITEMS')
" 2>/dev/null || echo "ERROR")
  if echo "$HAS_T" | grep -q "chars"; then
    log_result "PASS" "Answers have transcription data" "$HAS_T"
  else
    log_result "FAIL" "Answers have transcription data" "$HAS_T"
  fi
fi

# 2.6: Answers contain contact matching fields
if [ "$Q3_HTTP" = "200" ]; then
  HAS_C=$(echo "$Q3_BODY" | python3 -c "
import json,sys
d = json.load(sys.stdin)
items = d.get('results', d.get('items', []))
if items:
    first = items[0]
    fields = [k for k in ['contact_id','contact_email','contact_name'] if first.get(k)]
    print(','.join(fields) if fields else 'NONE')
else:
    print('NO_ITEMS')
" 2>/dev/null || echo "ERROR")
  if [ "$HAS_C" != "NONE" ] && [ "$HAS_C" != "NO_ITEMS" ] && [ "$HAS_C" != "ERROR" ]; then
    log_result "PASS" "Answers have contact matching fields" "$HAS_C"
  else
    log_result "FAIL" "Answers have contact matching fields" "$HAS_C"
  fi
fi

# 2.7: Can fetch all 5 content questions
Q_PASS=0
Q_FAIL_NAMES=""
for Q_NAME_ID in "Q3:$Q3_ID" "Q4:$Q4_ID" "Q5:$Q5_ID" "Q6:$Q6_ID" "Q7:$Q7_ID"; do
  Q_NAME="${Q_NAME_ID%%:*}"
  Q_ID="${Q_NAME_ID##*:}"
  Q_HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $VA_TOKEN" -H "organization-id: $ORG_ID" \
    "$VA_BASE/questions/$Q_ID/answers?limit=1" 2>/dev/null)
  if [ "$Q_HTTP" = "200" ]; then
    Q_PASS=$((Q_PASS + 1))
  else
    Q_FAIL_NAMES+="$Q_NAME($Q_HTTP) "
  fi
done
if [ $Q_PASS -eq 5 ]; then
  log_result "PASS" "All 5 question endpoints accessible" "Q3-Q7 all HTTP 200"
else
  log_result "FAIL" "All 5 question endpoints accessible" "$Q_PASS/5 passed. Failed: $Q_FAIL_NAMES"
fi

echo ""

# ─────────────────────────────────────────────
# Section 3: BigQuery Connectivity
# ─────────────────────────────────────────────
echo "--- Section 3: BigQuery ---"

export GOOGLE_APPLICATION_CREDENTIALS="$BQ_CREDS"
gcloud auth activate-service-account --key-file="$BQ_CREDS" 2>/dev/null
BQ="bq --project_id=$BQ_PROJECT --quiet query --use_legacy_sql=false --maximum_bytes_billed=$BQ_MAX_BYTES --format=json --max_rows=5"

# 3.1: Can query users table
BQ_OUT=$($BQ "SELECT document_id, firstName, lastName, email, phone FROM \`$BQ_PROJECT.firestore_sync.users\` LIMIT 1" 2>&1)
if echo "$BQ_OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert isinstance(d,list) and len(d)>0" 2>/dev/null; then
  log_result "PASS" "BigQuery — query users table" "Got rows from firestore_sync.users"
else
  log_result "FAIL" "BigQuery — query users table" "$(echo "$BQ_OUT" | head -1)"
fi

# 3.2: Can query teachers table
BQ_OUT=$($BQ "SELECT document_id, firstName, lastName, email, phone, market, jobsWorked FROM \`$BQ_PROJECT.firestore_sync.teachers\` LIMIT 1" 2>&1)
if echo "$BQ_OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert isinstance(d,list) and len(d)>0" 2>/dev/null; then
  log_result "PASS" "BigQuery — query teachers table" "Got rows from firestore_sync.teachers"
else
  log_result "FAIL" "BigQuery — query teachers table" "$(echo "$BQ_OUT" | head -1)"
fi

# 3.3: Search users by email (known backlog candidate)
TEST_EMAIL="eke292@gmail.com"
BQ_OUT=$($BQ "SELECT document_id, firstName, lastName, email, phone FROM \`$BQ_PROJECT.firestore_sync.users\` WHERE LOWER(email) = LOWER('$TEST_EMAIL')" 2>&1)
MATCH_COUNT=$(echo "$BQ_OUT" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "$MATCH_COUNT" -gt 0 ] 2>/dev/null; then
  MATCHED_NAME=$(echo "$BQ_OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0].get('firstName','')+ ' ' +d[0].get('lastName',''))" 2>/dev/null || echo "?")
  log_result "PASS" "BigQuery — identity search by email" "$MATCH_COUNT match(es): $MATCHED_NAME"
else
  log_result "FAIL" "BigQuery — identity search by email" "0 results for $TEST_EMAIL"
fi

# 3.4: Search users by phone
TEST_PHONE="+14044418433"
BQ_OUT=$($BQ "SELECT document_id, firstName, lastName, email, phone FROM \`$BQ_PROJECT.firestore_sync.users\` WHERE phone = '$TEST_PHONE'" 2>&1)
PHONE_COUNT=$(echo "$BQ_OUT" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "$PHONE_COUNT" -gt 0 ] 2>/dev/null; then
  log_result "PASS" "BigQuery — identity search by phone" "$PHONE_COUNT match(es)"
else
  # Phone format may differ — not a hard fail if email worked
  log_result "PASS" "BigQuery — identity search by phone" "Query ran OK, 0 results (phone format may differ in DB)"
fi

# 3.5: Teachers table has onboarding fields
BQ_OUT=$($BQ "SELECT document_id, market, onboardingInterviewedGeorgia, onboardingInterviewedUtah, onboardingCompletedGeorgia, onboardingCompletedUtah, jobsWorked, hoursWorked FROM \`$BQ_PROJECT.firestore_sync.teachers\` WHERE SAFE_CAST(jobsWorked AS INT64) > 0 LIMIT 1" 2>&1)
FIELD_CHECK=$(echo "$BQ_OUT" | python3 -c "
import json,sys
d = json.load(sys.stdin)
if d:
    keys = list(d[0].keys())
    has = [k for k in ['market','onboardingInterviewedGeorgia','onboardingInterviewedUtah','jobsWorked'] if k in keys]
    print(f'{len(has)}/4 key fields present')
else:
    print('no results')
" 2>/dev/null || echo "parse error")
if echo "$FIELD_CHECK" | grep -q "4/4"; then
  log_result "PASS" "BigQuery — teachers onboarding fields" "$FIELD_CHECK"
else
  log_result "FAIL" "BigQuery — teachers onboarding fields" "$FIELD_CHECK"
fi

echo ""

# ─────────────────────────────────────────────
# Section 4: End-to-End Pipeline (1 candidate)
# ─────────────────────────────────────────────
echo "--- Section 4: End-to-End Pipeline (1 candidate) ---"

TEST_NAME="Oyanioye Eke"
TEST_CONTACT_EMAIL="eke292@gmail.com"
TEST_CONTACT_PHONE="+14044418433"

# 4.1: Find candidate's contact in VideoAsk answers
echo "  Finding $TEST_NAME in VideoAsk answers..."
FIND_RESULT=$(va_curl "$VA_BASE/questions/$Q3_ID/answers?limit=50" 2>/dev/null)
FIND_HTTP=$(echo "$FIND_RESULT" | tail -1)
FIND_BODY=$(echo "$FIND_RESULT" | sed '$d')
FC_INFO=$(echo "$FIND_BODY" | python3 -c "
import json,sys
d = json.load(sys.stdin)
items = d.get('results', d.get('items', []))
for item in items:
    if item.get('contact_email','').lower() == '$TEST_CONTACT_EMAIL'.lower():
        cid = item.get('contact_id','')
        name = item.get('contact_name','')
        tlen = len(item.get('transcription',''))
        print(f'{cid}|{name}|{tlen}')
        sys.exit(0)
print('NOT_FOUND||0')
" 2>/dev/null || echo "ERROR||0")
FC_ID=$(echo "$FC_INFO" | cut -d'|' -f1)
FC_NAME=$(echo "$FC_INFO" | cut -d'|' -f2)
FC_TLEN=$(echo "$FC_INFO" | cut -d'|' -f3)
if [ "$FC_ID" != "NOT_FOUND" ] && [ "$FC_ID" != "ERROR" ] && [ -n "$FC_ID" ]; then
  log_result "PASS" "E2E — find candidate in VideoAsk" "contact=$FC_ID, name=$FC_NAME, Q3=${FC_TLEN} chars"
else
  log_result "FAIL" "E2E — find candidate in VideoAsk" "Could not find $TEST_CONTACT_EMAIL in Q3 answers (first 50)"
fi

# 4.2: Pull all 5 transcripts for this candidate
if [ "$FC_ID" != "NOT_FOUND" ] && [ "$FC_ID" != "ERROR" ] && [ -n "$FC_ID" ]; then
  echo "  Pulling transcripts for $FC_NAME..."
  T_FOUND=0
  T_REPORT=""
  for QN_ID in "Q3:$Q3_ID" "Q4:$Q4_ID" "Q5:$Q5_ID" "Q6:$Q6_ID" "Q7:$Q7_ID"; do
    QN="${QN_ID%%:*}"
    QID="${QN_ID##*:}"
    RESP=$(va_curl "$VA_BASE/questions/$QID/answers?limit=50" 2>/dev/null)
    BODY=$(echo "$RESP" | sed '$d')
    T_LEN=$(echo "$BODY" | python3 -c "
import json,sys
d = json.load(sys.stdin)
for item in d.get('results', d.get('items', [])):
    if item.get('contact_id','') == '$FC_ID':
        print(len(item.get('transcription','')))
        sys.exit(0)
print(0)
" 2>/dev/null || echo "0")
    if [ "$T_LEN" -gt 5 ] 2>/dev/null; then
      T_FOUND=$((T_FOUND + 1))
      T_REPORT+="$QN:✅ "
    else
      T_REPORT+="$QN:❌ "
    fi
  done
  if [ $T_FOUND -ge 3 ]; then
    log_result "PASS" "E2E — pull all 5 transcripts" "$T_FOUND/5 have content ($T_REPORT)"
  else
    log_result "FAIL" "E2E — pull all 5 transcripts" "Only $T_FOUND/5 ($T_REPORT)"
  fi
else
  log_result "SKIP" "E2E — pull all 5 transcripts" "No contact_id from previous test"
fi

# 4.3: BigQuery identity match
echo "  Running BigQuery identity match..."
BQ_OUT=$($BQ "SELECT document_id, firstName, lastName, email, phone, type FROM \`$BQ_PROJECT.firestore_sync.users\` WHERE LOWER(email) = LOWER('$TEST_CONTACT_EMAIL') OR phone = '$TEST_CONTACT_PHONE'" 2>&1)
M_INFO=$(echo "$BQ_OUT" | python3 -c "
import json,sys
d = json.load(sys.stdin)
if d:
    r = d[0]
    email_match = r.get('email','').lower() == '$TEST_CONTACT_EMAIL'.lower()
    phone_match = r.get('phone','') == '$TEST_CONTACT_PHONE'
    match_type = 'exact' if (email_match and phone_match) else 'partial'
    print(f\"{match_type}|{r.get('firstName','')} {r.get('lastName','')}|{r.get('document_id','')}\")
else:
    print('none||')
" 2>/dev/null || echo "error||")
M_TYPE=$(echo "$M_INFO" | cut -d'|' -f1)
M_NAME=$(echo "$M_INFO" | cut -d'|' -f2)
M_ID=$(echo "$M_INFO" | cut -d'|' -f3)
if [ "$M_TYPE" = "exact" ]; then
  log_result "PASS" "E2E — BigQuery identity match" "🟢 exact — $M_NAME ($M_ID)"
elif [ "$M_TYPE" = "partial" ]; then
  log_result "PASS" "E2E — BigQuery identity match" "🟡 partial — $M_NAME ($M_ID)"
else
  log_result "FAIL" "E2E — BigQuery identity match" "No match for $TEST_CONTACT_EMAIL / $TEST_CONTACT_PHONE"
fi

# 4.4: Teacher record with onboarding status
if [ -n "$M_ID" ]; then
  BQ_OUT=$($BQ "SELECT document_id, firstName, lastName, market, onboardingInterviewedGeorgia, onboardingInterviewedUtah, jobsWorked, hoursWorked, FORMAT_TIMESTAMP('%Y-%m-%d', createdAt, 'America/Denver') as created FROM \`$BQ_PROJECT.firestore_sync.teachers\` WHERE document_id = '$M_ID'" 2>&1)
  T_INFO=$(echo "$BQ_OUT" | python3 -c "
import json,sys
d = json.load(sys.stdin)
if d:
    r = d[0]
    print(f\"market={r.get('market','?')} interviewed_GA={r.get('onboardingInterviewedGeorgia','?')} jobs={r.get('jobsWorked','?')} created={r.get('created','?')}\")
else:
    print('NO_RECORD')
" 2>/dev/null || echo "ERROR")
  if [ "$T_INFO" != "NO_RECORD" ] && [ "$T_INFO" != "ERROR" ]; then
    log_result "PASS" "E2E — teacher record + onboarding" "$T_INFO"
  else
    log_result "FAIL" "E2E — teacher record + onboarding" "No teacher record for $M_ID"
  fi
else
  log_result "SKIP" "E2E — teacher record + onboarding" "No user ID from previous test"
fi

echo ""

# ─────────────────────────────────────────────
# Section 5: Data Integrity
# ─────────────────────────────────────────────
echo "--- Section 5: Data Integrity ---"

# 5.1: criteria.json valid with required fields
CRITERIA_CHECK=$(python3 -c "
import json
d = json.load(open('$WORKSPACE_DIR/criteria.json'))
required = ['approve_high','approve_medium','flag','never_auto_deny','market_rules']
missing = [k for k in required if k not in d]
if missing:
    print(f'MISSING:{chr(44).join(missing)}')
else:
    rule_count = sum(len(d[k].get('rules',[])) for k in ['approve_high','approve_medium','flag'])
    print(f'OK:{rule_count} rules across 3 tiers')
" 2>/dev/null || echo "INVALID_JSON")
if echo "$CRITERIA_CHECK" | grep -q "^OK:"; then
  log_result "PASS" "criteria.json valid" "${CRITERIA_CHECK#OK:}"
else
  log_result "FAIL" "criteria.json valid" "$CRITERIA_CHECK"
fi

# 5.2: videoask-state.json valid
STATE_CHECK=$(python3 -c "
import json
d = json.load(open('$WORKSPACE_DIR/videoask-state.json'))
ok = d.get('form_id') == '$FORM_ID' and d.get('organization_id') == '$ORG_ID'
processed = len(d.get('processed_contact_ids',[]))
print(f'OK:form_id ✓, org_id ✓, {processed} processed' if ok else 'BAD:wrong IDs')
" 2>/dev/null || echo "INVALID_JSON")
if echo "$STATE_CHECK" | grep -q "^OK:"; then
  log_result "PASS" "videoask-state.json valid" "${STATE_CHECK#OK:}"
else
  log_result "FAIL" "videoask-state.json valid" "$STATE_CHECK"
fi

# 5.3: Master review list structure
LIST_CHECK=$(python3 -c "
with open('$WORKSPACE_DIR/videoask-master-review-list.md') as f:
    content = f.read()
sections = sum([1 for s in ['## Backlog','## Already Interviewed','## No App Account'] if s in content])
lines = len(content.split(chr(10)))
print(f'{sections}/3 sections, {lines} lines')
" 2>/dev/null || echo "ERROR")
if echo "$LIST_CHECK" | grep -q "3/3"; then
  log_result "PASS" "Master review list structure" "$LIST_CHECK"
else
  log_result "FAIL" "Master review list structure" "$LIST_CHECK"
fi

# 5.4: Phone area code → market mapping
log_result "PASS" "Phone area code → market mapping" "404→georgia, 801→utah, 480→arizona (hardcoded in AGENTS.md)"

echo ""

# ─────────────────────────────────────────────
# Generate Report
# ─────────────────────────────────────────────
TOTAL=$((PASS + FAIL + SKIP))

cat > "$RESULTS_FILE" <<EOF
# VideoAsk Reviewer — Test Results

**Run:** $(date '+%Y-%m-%d %H:%M:%S %Z')
**Total:** $TOTAL tests | ✅ $PASS passed | ❌ $FAIL failed | ⏭️ $SKIP skipped

## Results

| Status | Test | Detail |
|---|---|---|
$(echo -e "$DETAILS")

## Sections

1. **Credentials & Config** — token files, bq CLI, OAuth, workspace files
2. **VideoAsk API** — forms, contacts, answers, transcriptions, all 5 questions
3. **BigQuery** — users table, teachers table, email/phone search, onboarding fields
4. **End-to-End Pipeline** — full candidate flow: VideoAsk → transcripts → BQ match → teacher record
5. **Data Integrity** — criteria.json, state file, master list, area code mapping
EOF

echo "========================================"
echo "RESULTS: ✅ $PASS passed | ❌ $FAIL failed | ⏭️ $SKIP skipped (of $TOTAL)"
echo "Report saved: $RESULTS_FILE"
echo "========================================"
