#!/bin/bash
set -euo pipefail

# Count existing rows in A2:A (non-empty)
existing=$(GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-write gws sheets spreadsheets values get --params '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0","range":"Backlog Reviews!A2:A"}' | jq '[.values[] | select(length>0)] | length')
echo "Existing rows: $existing"
BASE_ROW=$((existing + 2))

# Helper to append a candidate
process_candidate() {
  local idx=$1
  shift
  # Expect all candidate variables as arguments in a fixed order
  c_contact_id=$1; c_va_date=$2; c_name=$3; c_market=$4; c_rec=$5; c_confidence=$6; c_va_link=$7; c_first_name=$8; c_doc_id=$9; c_email=${10}; c_phone_formatted=${11}; c_zd_link=${12}; c_approved_note=${13}; c_denied_note=${14}; c_exp_str=${15}; c_loc_drive=${16}; c_sched_str=${17}; c_ai_summary=${18}; c_red_flags=${19}; c_q3=${20}; c_q4=${21}; c_q5=${22}; c_q6=${23}; c_q7=${24}

  # Generate row JSON using jq
  jq -n \
    --arg va_date "$c_va_date" \
    --arg name "$c_name" \
    --arg market "$c_market" \
    --arg confidence "$c_confidence" \
    --arg va_link "$c_va_link" \
    --arg first_name "$c_first_name" \
    --arg doc_id "$c_doc_id" \
    --arg email "$c_email" \
    --arg phone "$c_phone_formatted" \
    --arg zd_link "$c_zd_link" \
    --arg approved_note "$c_approved_note" \
    --arg denied_note "$c_denied_note" \
    --arg exp_str "$c_exp_str" \
    --arg loc_drive "$c_loc_drive" \
    --arg sched_str "$c_sched_str" \
    --arg ai_summary "$c_ai_summary" \
    --arg red_flags "$c_red_flags" \
    --arg q3 "$c_q3" \
    --arg q4 "$c_q4" \
    --arg q5 "$c_q5" \
    --arg q6 "$c_q6" \
    --arg q7 "$c_q7" \
    '[[false, false, $va_date, "🟢 " + $name, $market, "✅ " + $confidence, "=HYPERLINK(\""+$va_link+"\",\"▶️ Watch\")", $first_name, $doc_id, $email, $phone, "=HYPERLINK(\""+$zd_link+"\",\"🔍\")", $approved_note, $denied_note, $exp_str, $loc_drive, $sched_str, $ai_summary, $red_flags, $q3, $q4, $q5, $q6, $q7]]' > "/tmp/row${idx}.json"

  # Append row using official API (since +append was problematic)
  row_json=$(cat /tmp/row${idx}.json)
  gws_output=$(GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-write gws sheets spreadsheets values append --params '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0","range":"Backlog Reviews!A2","valueInputOption":"USER_ENTERED"}' --json "{\"values\":$row_json}")
  echo "$gws_output" > "/tmp/append${idx}_response.json"
  # Since we know the next free row before appending, the appended row is exactly BASE_ROW + idx - 1
  row_actual=$((BASE_ROW + idx - 1))
  echo "$row_actual" > "/tmp/row${idx}_actual.txt"
  echo "Appended candidate $idx to row $row_actual"

  # Batch update: set background color for the appended row
  start_idx=$((row_actual-1))
  batch_json=$(jq -n --argjson start "$start_idx" --argjson end "$row_actual" '{
    "requests": [
      {
        "repeatCell": {
          "range": {
            "sheetId": 412743935,
            "startRowIndex": $start,
            "endRowIndex": $end,
            "startColumnIndex": 0,
            "endColumnIndex": 24
          },
          "cell": {
            "userEnteredFormat": {
              "backgroundColor": { "red": 1, "green": 1, "blue": 0.8 }
            }
          },
          "fields": "userEnteredFormat.backgroundColor"
        }
      }
    ]}')
  GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-write gws sheets spreadsheets batchUpdate --params '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0"}' --json "$batch_json"

  # Query BigQuery for app account
  bq_query="SELECT firstName, lastName, email, phone, market, FORMAT_TIMESTAMP('%Y-%m-%d', createdAt, 'America/Denver') as created, onboardingInterviewedGeorgia, onboardingInterviewedUtah, onboardingCompletedGeorgia, onboardingCompletedUtah, onboardingBackgroundCheckedGeorgia, onboardingBackgroundCheckedUtah, jobsWorked, hoursWorked, firstShiftCompleted FROM \`upkid-7b192.firestore_sync.teachers\` WHERE document_id = \"${c_doc_id}\""
  GOOGLE_APPLICATION_CREDENTIALS=~/credentials/bigquery-tyler-bot.json /opt/homebrew/bin/bq query --project_id=upkid-7b192 --nouse_legacy_sql --maximum_bytes_billed=53687091200 --format=json "$bq_query" > "/tmp/app${idx}.json" || true

  # Build App section
  app_section=""
  if [ -s "/tmp/app${idx}.json" ] && [ "$(jq length /tmp/app${idx}.json)" -gt 0 ]; then
    app=$(jq -r '.[0]' /tmp/app${idx}.json)
    fname=$(echo "$app" | jq -r '.firstName')
    lname=$(echo "$app" | jq -r '.lastName')
    app_market=$(echo "$app" | jq -r '.market // "N/A"')
    app_created=$(echo "$app" | jq -r '.created // "N/A"')
    app_jobs=$(echo "$app" | jq -r '.jobsWorked // 0')
    app_hours=$(echo "$app" | jq -r '.hoursWorked // 0')
    app_first_shift=$(echo "$app" | jq -r '.firstShiftCompleted // false')
    ga_int=$(echo "$app" | jq -r '.onboardingInterviewedGeorgia // false')
    ut_int=$(echo "$app" | jq -r '.onboardingInterviewedUtah // false')
    ga_comp=$(echo "$app" | jq -r '.onboardingCompletedGeorgia // false')
    ut_comp=$(echo "$app" | jq -r '.onboardingCompletedUtah // false')
    ga_bg=$(echo "$app" | jq -r '.onboardingBackgroundCheckedGeorgia // false')
    ut_bg=$(echo "$app" | jq -r '.onboardingBackgroundCheckedUtah // false')
    app_section="🟢 Exact match: $fname $lname | ID: ${c_doc_id}
Market: $app_market | Created: $app_created | Interview status: GA:int=$ga_int,comp=$ga_comp,bg=$ga_bg; UT:int=$ut_int,comp=$ut_comp,bg=$ut_bg | Shifts: $app_jobs ($app_hours hrs) | First shift: $app_first_shift"
  else
    app_section="🔴 Not found in teachers database"
  fi

  # Build Slack message (card format)
  # For APPROVE, show approved summary; for FLAG, show denied summary and why flagged
  if [ "$c_rec" = "APPROVE" ]; then
    slack_msg="""## ${c_rec} (${c_confidence}) — ${c_name}
📧 ${c_email} | 📱 ${c_phone_formatted} | 📍 Flowery Branch, GA
Questions: 5/5 — Q3 ✅ Q4 ✅ Q5 ✅ Q6 ✅ Q7 ✅

**Experience:** ${c_exp_str}
**Location:** Flowery Branch, GA | Market: ${c_market} | Drive: 20mi
**Schedule:** ${c_sched_str}

**Summary:** ${c_ai_summary}

**Red Flags:** ${c_red_flags}

**Zendesk Summary (if approved):**
> ${c_approved_note}

🔗 **App Account:**
${app_section}
"""
  else
    # FLAG case
    slack_msg="""## ${c_rec} (${c_confidence}) — ${c_name}
📧 ${c_email} | 📱 ${c_phone_formatted} | 📍 Augusta, GA
Questions: 5/5 — Q3 ✅ Q4 ✅ Q5 ✅ Q6 ✅ Q7 ✅

**Experience:** ${c_exp_str}
**Location:** Augusta, GA | Market: ${c_market}
**Schedule:** ${c_sched_str}

**Summary:** ${c_ai_summary}

**Red Flags:** ${c_red_flags}

🔍 **Why flagged:** ${c_ai_summary}
(Note: This candidate requires Erica's manual review. See red flags above.)

**Zendesk Summary (if denied):**
> ${c_denied_note}

🔗 **App Account:**
${app_section}
"""
  fi

  echo "$slack_msg" > "/tmp/slack_message_${idx}.txt"
  echo "${c_contact_id}" > "/tmp/contact_id_${idx}.txt"
}

# ============ CANDIDATE 1: BRIANNA ============
c1_contact_id="76fad6b6-62fa-415f-b1dd-3f02bea60776"
c1_va_date="2026-04-07"
c1_name="Brianna Ramos"
c1_market="GA"
c1_rec="APPROVE"
c1_confidence="MEDIUM"
c1_va_link="https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/76fad6b6-62fa-415f-b1dd-3f02bea60776"
c1_first_name="Brianna"
c1_doc_id="LJh5FzHvfgNFP8Db0nkpYgHSeoN2"
c1_email="briannabramos2006@gmail.com"
c1_phone_formatted="(678) 997-6675"
c1_zd_link="https://upkid.zendesk.com/agent/search/1?q=briannabramos2006@gmail.com"
c1_approved_note="04/07 Intro Call Passed. Flowery Branch, GA. Willing to drive 20-30 miles. Babysitting experience; college student pursuing EMT. Full-time schedule, unavailable Mondays and some Tuesdays. Brianna shows genuine enthusiasm for working with children."
c1_denied_note="04/07 Not Hiring — Intro Call. Flowery Branch, GA. Experience: only informal babysitting; no formal childcare setting. Limited availability (no Mondays)."
c1_exp_str="babysitter; college student"
c1_loc_drive="I currently stay in Flowery Branch Georgia right n, 20mi"
c1_sched_str="FT"
c1_ai_summary="Brianna is a motivated 19-year-old college student studying to be an EMT with babysitting experience. She's talkative and enthusiastic but lacks formal childcare experience, which could be a concern for Georgia's standards. She seeks full-time work but has limited availability on Mondays and some Tuesdays. Overall, she's a medium-confidence approval given her informal experience but strong interest."
c1_red_flags=""
c1_q3="Hi, good afternoon. My name is Brianna. I'm currently 19 turning 20. I'm almost done with high school next month and I am going to school and I'm in college right now going to school for to become an EMT, a medic. Um, I like spending time with family, I like babysitting watching kids meeting new people. Interacting with people having great conversation\n Ian's, I like going to the gym painting cooking. That's just a little bit about me."
c1_q4="I currently stay in Flowery Branch Georgia right next to Buford Georgia and I'm willing to go 15 or 20 miles 30, even if possible I'm willing to travel at like on trust me Transportation. So and I have a very flexible schedule."
c1_q5="Hi, Brina. I'm currently looking for a full-time schedule. I can't work on Mondays. I prefer to work morning and afternoon shifts or even evening if possible. My schedule is very flexible. I chase can't work on days and sometimes Tuesdays."
c1_q6="Like if it has something to do with a toy to kids are bickering, about a toy, I'll take the toy away. And one goes on the other Corner. That one goes in the other Corner separated like just, you know, make sure like, give them maybe like a little time out too.\n Yeah."
c1_q7="Yeah, I'm really passionate about my job. I love helping kids working with kids. I love interacting with kids. I feel like I'll be a great fit for this because I love working with kids and I just love watching kids, little kids, interacting helping them, just making sure you know, they're okay."

process_candidate 1 "$c1_contact_id" "$c1_va_date" "$c1_name" "$c1_market" "$c1_rec" "$c1_confidence" "$c1_va_link" "$c1_first_name" "$c1_doc_id" "$c1_email" "$c1_phone_formatted" "$c1_zd_link" "$c1_approved_note" "$c1_denied_note" "$c1_exp_str" "$c1_loc_drive" "$c1_sched_str" "$c1_ai_summary" "$c1_red_flags" "$c1_q3" "$c1_q4" "$c1_q5" "$c1_q6" "$c1_q7"

# ============ CANDIDATE 2: LADEA ============
c2_contact_id="c0c630f9-2618-42a2-ad79-c318f3cc8922"
c2_va_date="2026-04-07"
c2_name="Ladea Blocker"
c2_market="GA"
c2_rec="FLAG"
c2_confidence="LOW"
c2_va_link="https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/c0c630f9-2618-42a2-ad79-c318f3cc8922"
c2_first_name="Ladea"
c2_doc_id="CCOBJAb5sITaQxDjGxS57n7XJhC3"
c2_email="Blockerladea05@gmail.com"
c2_phone_formatted="(706) 755-6084"
c2_zd_link="https://upkid.zendesk.com/agent/search/1?q=Blockerladea05@gmail.com"
c2_approved_note="04/07 Intro Call Passed. Augusta, GA. Claims 17 years experience with children newborn to six. Available FT/PT. Candidate's experience claims require verification; responses were brief and transcript quality is poor."
c2_denied_note="04/07 Not Hiring — Intro Call. Augusta, GA. Experience: claims 17 years starting at age 6 (inconsistent); vague conflict resolution; poor transcript quality."
c2_exp_str="23yr"
c2_loc_drive="Augusta, GA"
c2_sched_str="FT, PT"
c2_ai_summary="Ladea claims 23 years of age and 17 years of experience, which raises an immediate red flag (started at age 6?). She lives in Augusta, GA and is available full- or part-time. Her conflict resolution answer is vague and does not demonstrate a clear strategy. The transcript quality is poor with grammatical errors and unclear phrasing. Given the questionable experience claim and weak responses, she should be flagged for Erica's careful review and possible verification of experience."
c2_red_flags="⚠️ Age/experience inconsistency: 23yo with 17yr exp; ⚠️ Vague conflict resolution response; ⚠️ Poor transcript quality (grammar, clarity)"
c2_q3="Good evening. My name is Lady of blocker. I am 23 years old. I have 17 years of experience working with children from age ranges newborn to six years old.\n I enjoy working with children because I believe that I set an example for them to do better and believe that they can do better."
c2_q4="I am located in Augusta. Georgia."
c2_q5="Part-time or full-time."
c2_q6="I will properly deal with the matter. I will let my supervisor know after that. I will let the parents know.\n What happened?"
c2_q7="I think I want me to grade up kid teacher because I feel as if I relate to the kids and I have a good connection with all kids that I encounter\n and I'm here to push for them and to help them learn and grow and be the best person that they can be."

process_candidate 2 "$c2_contact_id" "$c2_va_date" "$c2_name" "$c2_market" "$c2_rec" "$c2_confidence" "$c2_va_link" "$c2_first_name" "$c2_doc_id" "$c2_email" "$c2_phone_formatted" "$c2_zd_link" "$c2_approved_note" "$c2_denied_note" "$c2_exp_str" "$c2_loc_drive" "$c2_sched_str" "$c2_ai_summary" "$c2_red_flags" "$c2_q3" "$c2_q4" "$c2_q5" "$c2_q6" "$c2_q7"
