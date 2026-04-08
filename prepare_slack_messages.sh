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

  # These are passed as arguments in order; assign to named variables
  c_contact_id=$1; c_va_date=$2; c_name=$3; c_market=$4; c_rec=$5; c_confidence=$6; c_va_link=$7; c_first_name=$8; c_doc_id=$9; c_email=$10; c_phone_formatted=$11; c_zd_link=$12; c_approved_note=$13; c_denied_note=$14; c_exp_str=$15; c_loc_drive=$16; c_sched_str=$17; c_ai_summary=$18; c_red_flags=$19; c_q3=$20; c_q4=$21; c_q5=$22; c_q6=$23; c_q7=$24

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

  # Append row
  gws_output=$(GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-write gws sheets +append --spreadsheet 1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0 --json-values "$(cat /tmp/row${idx}.json)")
  echo "$gws_output" > "/tmp/append${idx}_response.json"
  row_actual=$(echo "$gws_output" | jq -r '.updates.updatedRange | capture("!A(?<num>[0-9]+):") .num')
  echo "$row_actual" > "/tmp/row${idx}_actual.txt"

  # Query BigQuery
  bq_query="SELECT firstName, lastName, email, phone, market, FORMAT_TIMESTAMP('%Y-%m-%d', createdAt, 'America/Denver') as created, onboardingInterviewedGeorgia, onboardingInterviewedUtah, onboardingCompletedGeorgia, onboardingCompletedUtah, onboardingBackgroundCheckedGeorgia, onboardingBackgroundCheckedUtah, jobsWorked, hoursWorked, firstShiftCompleted FROM \\\`upkid-7b192.firestore_sync.teachers\\\` WHERE document_id = \"${c_doc_id}\""
  GOOGLE_APPLICATION_CREDENTIALS=~/credentials/bigquery-tyler-bot.json bq query --nouse_legacy_sql --maximum_bytes_billed=53687091200 --format=json "$bq_query" > "/tmp/app${idx}.json" || true

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

  # Slack message
  slack_msg="""## ${c_rec} (${c_confidence}) — ${c_name}
📧 ${c_email} | 📱 ${c_phone_formatted} | 📍 Pleasant View, UT
Questions: 5/5 — Q3 ✅ Q4 ✅ Q5 ✅ Q6 ✅ Q7 ✅

**Experience:** ${c_exp_str}
**Location:** Pleasant View, UT | Market: ${c_market}
**Schedule:** ${c_sched_str}

**Summary:** ${c_ai_summary}

**Red Flags:** ${c_red_flags}

**Zendesk Summary (if approved):>
> ${c_approved_note}

🔗 **App Account:**
${app_section}
"""
  echo "$slack_msg" > "/tmp/slack_message_${idx}.txt"
  echo "${c_contact_id}" > "/tmp/contact_id_${idx}.txt"
}

# Candidate 1 details
c1_contact_id="63154493-8ada-43ee-a1da-c17cb1a65f21"
c1_va_date="2026-04-07"
c1_name="Alissa Chatelain"
c1_market="GE"
c1_rec="APPROVE"
c1_confidence="MEDIUM"
c1_va_link="https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/63154493-8ada-43ee-a1da-c17cb1a65f21"
c1_first_name="Alissa"
c1_doc_id="83s4GFNHkLbJ2Dt7EiGScvXwFoq1"
c1_email="dreammer023@gmail.com"
c1_phone_formatted="(208) 908-2669"
c1_zd_link="https://upkid.zendesk.com/agent/search/1?q=dreammer023@gmail.com"
c1_approved_note="04/07 Intro Call Passed. Pleasant View, UT. substitute; babysitter. FT, PT."
c1_denied_note="04/07 Not Hiring — Intro Call. Pleasant View, UT. Experience: substitute; babysitter."
c1_exp_str="substitute; babysitter"
c1_loc_drive="I am located in Pleasant View Utah. / Harrisville."
c1_sched_str="FT, PT"
c1_ai_summary="Alissa has babysitting experience but no formal childcare setting. Her location is uncertain: she states Pleasant View, UT but her phone area code 208 belongs to Idaho. Given Georgia's preference for formal experience and her informal background, she should be flagged for location verification and experience assessment. Medium confidence recommendation."
c1_red_flags="⚠️ Location mismatch: phone area code 208 (ID) vs claimed UT; Only informal experience (babysitting, substitute); No drive radius; Potential market misassignment (Georgia)."
c1_q3="Hello. So my name is Alyssa Chapman, I was born and raised in Idaho, a small town called mirta Idaho. And so during High School, I was pretty much the babysitter for my small town. So I have experience in that and then when I moved here in Utah, Ogden Utah and 2020. I went on siddur City and I I was babysitting their ages newborn to 9910 roughly. And I pretty much just took care of them as like a babysitter, not necessarily as a substitute. So this is The Substitute part is new to for me, but the babysitting portion and taking care of children is not out of my expertise per se."
c1_q4="I am located in Pleasant View Utah. / Harrisville."
c1_q5="As of right now I am looking for part-time as I just had my child and she is 11 months. So I kind of want something that I could take her with me but part-time for now until maybe I test the waters and then I can decide full-time in the future."
c1_q6="If two children are fighting and one child hits the other child, I will address the situation in front of both of them asking you know, why did we hit and have them both explain their parties and then we can use that as a teaching moment as say if somebody child to took the toy from Child one and that's why child one hit, we can go over. Over that together and learn that. I take that as a learning curve and not discipline."
c1_q7="I feel like I would be a good teacher because I enjoy working with children and helping them grow through my experience with babysitting, especially in high school. I learned how to be patient and attentive and understanding the different personality and needs that each kid."

process_candidate 1 "$c1_contact_id" "$c1_va_date" "$c1_name" "$c1_market" "$c1_rec" "$c1_confidence" "$c1_va_link" "$c1_first_name" "$c1_doc_id" "$c1_email" "$c1_phone_formatted" "$c1_zd_link" "$c1_approved_note" "$c1_denied_note" "$c1_exp_str" "$c1_loc_drive" "$c1_sched_str" "$c1_ai_summary" "$c1_red_flags" "$c1_q3" "$c1_q4" "$c1_q5" "$c1_q6" "$c1_q7"

# Candidate 2 details
c2_contact_id="ec4d90c5-446a-429f-9dee-f19a20bd40ba"
c2_va_date="2026-04-07"
c2_name="Demetrice Walker"
c2_market="GE"
c2_rec="APPROVE"
c2_confidence="HIGH"
c2_va_link="https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/ec4d90c5-446a-429f-9dee-f19a20bd40ba"
c2_first_name="Demetrice"
c2_doc_id="AGyY1RAeAYbEm9iVcjI19cWCviJ2"
c2_email="demetricewalker0124@gmail.com"
c2_phone_formatted="(706) 834-5841"
c2_zd_link="https://upkid.zendesk.com/agent/search/1?q=demetricewalker0124@gmail.com"
c2_approved_note="04/07 Intro Call Passed. Augusta, GA, 25mi. 33yr; daycare; preschool; afterschool. FT, PT."
c2_denied_note="04/07 Not Hiring — Intro Call. Augusta, GA. Experience: 33yr; daycare; preschool; afterschool."
c2_exp_str="33yr; daycare; preschool; afterschool"
c2_loc_drive="Augusta, GA"
c2_sched_str="FT, PT"
c2_ai_summary="Demetrice is an exceptionally strong candidate with over 16 years of childcare experience across daycare, preschool, and afterschool settings. She lives in Augusta, GA with a 25-mile drive radius and is available immediately for full-time or part-time work. Her extensive background and commitment make her a high-confidence approval."
c2_red_flags="None"
c2_q3="33 years old and I have been in and out of childcare for about 16 years. When I started taking care of children, I wasn't home many for a military couple. When I decided to get into the daycare centers, I was 17 and I started in the infant room. And since then I have worked in every age that means infants, toddlers, preschool, school-age after school, every every range of children. Why do I love taking care of kids? It's more being a part of the future, to be one of those voices to raise a child to be a better person. I just love kids. I love to see them grow. I love to see them learn develop, I like to help them with their problem-solving skills. I just love kids."
c2_q4="I live in Augusta, Georgia, and I'm willing to travel up to twenty-five miles for work."
c2_q5="I'm interested in either part-time or full-time at the current moment. I am in the process of leaving my current job and I only have two weeks left. So after the two weeks my availability will be open."
c2_q6="There have been many occasions where I've dealt with conflict between two children. Whether it's a child hitting another child, or a child saying something to another child or a child taking something from another child, it's really about getting on their level and seeing exactly what the issue is and getting the children to learn to get in. It's more about trying to get them to talk out the situation, then use their hands so that if this conflict comes up again, they are better able to manage the situation without having to be physical."
c2_q7="I love children. I love children more than I like people. I would rather have a job invested in my future than to have a job that has no meaning to me at all."

process_candidate 1 "$c2_contact_id" "$c2_va_date" "$c2_name" "$c2_market" "$c2_rec" "$c2_confidence" "$c2_va_link" "$c2_first_name" "$c2_doc_id" "$c2_email" "$c2_phone_formatted" "$c2_zd_link" "$c2_approved_note" "$c2_denied_note" "$c2_exp_str" "$c2_loc_drive" "$c2_sched_str" "$c2_ai_summary" "$c2_red_flags" "$c2_q3" "$c2_q4" "$c2_q5" "$c2_q6" "$c2_q7"
