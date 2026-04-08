#!/bin/bash
set -euo pipefail

export GOOGLE_WORKSPACE_CLI_CONFIG_DIR="${HOME}/.config/gws-write"

# ---- Candidate 1: Shuntae Hunter ----
s1_contact_id="af372992-a086-4593-81ec-8e2819fcc3dc"
s1_va_date="2026-04-08"
s1_name="Shuntae Hunter"
s1_market="georgia"
s1_rec="APPROVE"
s1_confidence="MEDIUM"
s1_va_link="https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/af372992-a086-4593-81ec-8e2819fcc3dc"
s1_first_name="Shuntae"
s1_doc_id="3aHtxEr9CtTOsUoC8R5GIaxjCP82"
s1_email="msshuntaehunter@gmail.com"
s1_phone_formatted="(470) 694-3372"
s1_zd_link="https://upkid.zendesk.com/agent/search/1?q=msshuntaehunter@gmail.com"
s1_approved_note="2026-04-08 Intro Call Passed. Atlanta, GA, 25-30mi. 13yr; daycare; nanny. PT."
s1_denied_note=""
s1_exp_str="13yr; daycare; nanny"
s1_loc_drive="Atlanta, GA, 25-30mi"
s1_sched_str="PT"
s1_ai_summary="Shuntae shows strong patience and conflict resolution skills with 13 years of mixed childcare (daycare and nanny). She is enthusiastic about returning to childcare after a corporate break and explicitly states flexibility with part-time scheduling. Given Georgia's typical requirement for formal childcare experience, her combination of daycare and nanny is borderline but likely acceptable as formal experience. Recommend APPROVE with medium confidence."
s1_red_flags="None"
s1_q3="Hi, my name is shuntae hunter and I currently live in Atlanta. Georgia, I decided to go with up kids because of the flexibility and I read a little bit about it and I like, what it was about. I was previously a nanny to five children, 6 months to 12, to 13 years old, and I loved it so much and I missed it. But I did go into the corporate world. And, you know, I took a break and now I'm in between jobs and a friend of mine said, well, you love children. You're great with children, why don't you go back into that? And I started looking around for some daycares that I possibly can work in. And I came across up kids, and I started reading. And I'm like, yeah, I like this is flexible. I get to choose. My schedule and where I want to work. So, that's a great opportunity. But yeah, I'm a big fan of kids. Kids love me. I'm very patient. I have a lot of patience and yeah, I look forward to working with you guys."
s1_q4="Sorry, I live in Atlanta, Georgia. Now I am in the college park Riverdale Fayetteville area, currently and I'm willing to travel about 25 to 30 miles."
s1_q5="I am I want to work part-time. And I have a lot of flexibilities. So we more than others where I have like the complete week, you know, free. But then some weeks I don't, I do have a small business on the side as well, but I am looking for part-time."
s1_q6="So how I feel with chilled conflict between two children, like if another one hits another one I would first ask the hitter, you know the kid that hit the child, what prompted me to do that, you know why did you do that? And then from his answer, I can kind of gauge on how to respond. Of course, I consoled. The child that was hit and I asked him to take a seat and the child that did the heading. I would ask them, you know, exactly what made him do that. If he said, oh he took my toy and then I will explain to both of them, the importance of sharing and I'll explain the importance of not being violent. And we do not hit. We do not express. So that way and I would ask them to draw me a picture of a better way, they could have handled it, or I would ask them. Could you draw me a picture of you giving the toy to, you know the person that you had or, you know, I would try to make some type of activity out of it and explain the importance of keeping our hands to ourselves. Yes."
s1_q7="I will be a great kid teacher. I am very compassionate, I'm very patient. People in general, love me, not just the children. I've been known to be very sweet and giving and caring and I know how to handle situations appropriately between children. Actively, and I just think I'll be a good fit."

# Build row1 JSON using Python with env vars
export s1_va_date s1_name s1_market s1_confidence s1_va_link s1_first_name s1_doc_id s1_email s1_phone_formatted s1_zd_link s1_approved_note s1_denied_note s1_exp_str s1_loc_drive s1_sched_str s1_ai_summary s1_red_flags s1_q3 s1_q4 s1_q5 s1_q6 s1_q7
python3 - <<'PYEOF'
import os, json
row = [
    False, False,
    os.getenv('s1_va_date'),
    '🟢 ' + os.getenv('s1_name'),
    os.getenv('s1_market'),
    '✅ ' + os.getenv('s1_confidence'),
    '=HYPERLINK("' + os.getenv('s1_va_link') + '","▶️ Watch")',
    os.getenv('s1_first_name'),
    os.getenv('s1_doc_id'),
    os.getenv('s1_email'),
    os.getenv('s1_phone_formatted'),
    '=HYPERLINK("' + os.getenv('s1_zd_link') + '","🔍")',
    os.getenv('s1_approved_note'),
    os.getenv('s1_denied_note'),
    os.getenv('s1_exp_str'),
    os.getenv('s1_loc_drive'),
    os.getenv('s1_sched_str'),
    os.getenv('s1_ai_summary'),
    os.getenv('s1_red_flags'),
    os.getenv('s1_q3'),
    os.getenv('s1_q4'),
    os.getenv('s1_q5'),
    os.getenv('s1_q6'),
    os.getenv('s1_q7')
]
with open('/tmp/row1.json','w') as f:
    json.dump([row], f)
PYEOF

# Append to sheet
gws sheets +append --spreadsheet 1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0 --json-values "$(cat /tmp/row1.json)" > /tmp/append1_response.json

# Extract row number
row=$(jq -r '.updates.updatedRange | capture("!A(?<num>[0-9]+):") .num' /tmp/append1_response.json)
echo "$row" > /tmp/row1.txt

# Batch update: color row (light yellow)
start1=$((row-1))
batch1=$(jq -n --argjson start "$start1" --argjson end "$row" '{
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
  ]
}')
gws sheets spreadsheets batchUpdate --json "$batch1"

# BigQuery lookup for Shuntae
bq_query1="SELECT firstName, lastName, email, phone, market, FORMAT_TIMESTAMP('%Y-%m-%d', createdAt, 'America/Denver') as created, onboardingInterviewedGeorgia, onboardingInterviewedUtah, onboardingCompletedGeorgia, onboardingCompletedUtah, onboardingBackgroundCheckedGeorgia, onboardingBackgroundCheckedUtah, jobsWorked, hoursWorked, firstShiftCompleted FROM `upkid-7b192.firestore_sync.teachers` WHERE document_id = '$s1_doc_id'"
GOOGLE_APPLICATION_CREDENTIALS="${HOME}/credentials/bigquery-tyler-bot.json" bq query --nouse_legacy_sql --maximum_bytes_billed=53687091200 --format=json "$bq_query1" > /tmp/app1.json || true

# Build App Account section
if [ -s /tmp/app1.json ] && [ "$(jq length /tmp/app1.json)" -gt 0 ]; then
  app=$(jq -r '.[0]' /tmp/app1.json)
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
  app_section1="🟢 Exact match: $fname $lname | ID: $s1_doc_id\nMarket: $app_market | Created: $app_created | Interview status: GA:int=$ga_int,comp=$ga_comp,bg=$ga_bg; UT:int=$ut_int,comp=$ut_comp,bg=$ut_bg | Shifts: $app_jobs ($app_hours hrs) | First shift: $app_first_shift"
else
  app_section1="🔴 Not found in teachers database"
fi

# Slack message for Shuntae
slack1="## $s1_rec ($s1_confidence) — $s1_name
📧 $s1_email | 📱 $s1_phone_formatted | 📍 Atlanta, GA
Questions: 5/5 — Q3 ✅ Q4 ✅ Q5 ✅ Q6 ✅ Q7 ✅

**Experience:** mixed ($s1_exp_str)
**Location:** Atlanta, GA | Market: $s1_market | Drive: 25-30mi
**Schedule:** $s1_sched_str

**Summary:** $s1_ai_summary

**Red Flags:** $s1_red_flags

**Zendesk Summary (if approved):**
> $s1_approved_note

🔗 **App Account:**
$app_section1"

echo "$slack1" > /tmp/slack_message_1.txt
echo "$s1_contact_id" > /tmp/contact_id_1.txt

# ---- Candidate 2: Brittney Wilder ----
s2_contact_id="122fe3f6-2879-4ab7-bb8b-92b387e60621"
s2_va_date="2026-04-08"
s2_name="Brittney Wilder"
s2_market="georgia"
s2_rec="APPROVE"
s2_confidence="LOW"
s2_va_link="https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/122fe3f6-2879-4ab7-bb8b-92b387e60621"
s2_first_name="Brittney"
s2_doc_id="El7M9FoibxTDEUXfkuVHX1ogfxL2"
s2_email="wilderbeittney1@gmail.com"
s2_phone_formatted="(678) 900-3167"
s2_zd_link="https://upkid.zendesk.com/agent/search/1?q=wilderbeittney1@gmail.com"
s2_approved_note="2026-04-08 Intro Call Passed. Atlanta, GA, 25-50mi. 8yr (daycare, preschool, ages 2-19). FT."
s2_denied_note=""
s2_exp_str="8yr (daycare, preschool, ages 2-19)"
s2_loc_drive="Atlanta, GA, 25-50mi"
s2_sched_str="FT"
s2_ai_summary="Brittney has 8 years of childcare experience across a group home setting for children ages 2 to 19, describing herself as passionate, patient, and focused on emotional and behavioral development. She is seeking full-time work immediately and expresses a genuine love for children. However, there is an email discrepancy between VideoAsk and Upkid app (wilderbeittney1 vs wilderbrittney1) which should be verified. Despite some vague experience claims, her depth suggests she can succeed. Approve with low confidence."
s2_red_flags="⚠️ Email mismatch: VideoAsk uses wilderbeittney1@gmail.com vs app wilderbrittney1@gmail.com"
s2_q3="My name is Brittany Wilder and I've been working a child care for about 8 years, give or take my very first experience ever working with kids was back in 2016. I actually volunteered as a support staff member at a group home and really just fell in love with the work done in love with the people there, some of my responsibilities required me to assist. different residents in grooming feeding and Washing themselves and dressing themselves and just making sure that their basic needs were met preparing meals leading activities for them to grow mentally socially emotionally because I have worked with kids ranging from ages 2 to 19. I would say I'm just working with them honing in on their behavior, their emotions, and how to express Some cells and deal with that. And yes, it's just truly been a blessing and I love working with children. It's one of the most rewarding experiences and I just feel that if we Embrace working with children more, that we will find that we can learn a lot from working with them as well. Not just about ourselves and about them, but about life about the way of the world and it's just amazing to see these beautiful creative colorful minds and personalities as they flourish and evolve and develop. And I really feel like working with kids offers a sense of healing and love and I feel we all need that, especially in the times that we are in."
s2_q4="I'm currently located in Atlanta, Georgia and I don't mind driving long distances mainly because my line of work requires me to do so. But if I had to put a number on it, I would say anywhere within a 25 to 50 mile radius of Atlanta, Georgia would be perfectly fine."
s2_q5="I'm looking for a full-time position and my availability is Monday through Friday anytime before 4:30 p.m."
s2_q6="As a first offense, I typically like to give both parties the opportunity to tell their side of the story and express, what they feel is the root of the issue so that we can come to a common ground. So no further conflict arises. So I would separate the two individuals and give them the chance to have that conversation with me without being interrupted. Corrupted, because it's important that we listen to each other so that we can find a solution that best works for everyone."
s2_q7="I would make a great up K teacher because I understand that kids go through many things that they don't understand much. Like we asked adults and just humans in general and I try to hone in on that and be as patient and respectful with them as I can. Also I'm very big on individuality and I feel that paying close attention to that is important and crucial as it relates to children learning and growing and developing."

export s2_va_date s2_name s2_market s2_confidence s2_va_link s2_first_name s2_doc_id s2_email s2_phone_formatted s2_zd_link s2_approved_note s2_denied_note s2_exp_str s2_loc_drive s2_sched_str s2_ai_summary s2_red_flags s2_q3 s2_q4 s2_q5 s2_q6 s2_q7

python3 - <<'PYEOF'
import os, json
row = [
    False, False,
    os.getenv('s2_va_date'),
    '🟢 ' + os.getenv('s2_name'),
    os.getenv('s2_market'),
    '✅ ' + os.getenv('s2_confidence'),
    '=HYPERLINK("' + os.getenv('s2_va_link') + '","▶️ Watch")',
    os.getenv('s2_first_name'),
    os.getenv('s2_doc_id'),
    os.getenv('s2_email'),
    os.getenv('s2_phone_formatted'),
    '=HYPERLINK("' + os.getenv('s2_zd_link') + '","🔍")',
    os.getenv('s2_approved_note'),
    os.getenv('s2_denied_note'),
    os.getenv('s2_exp_str'),
    os.getenv('s2_loc_drive'),
    os.getenv('s2_sched_str'),
    os.getenv('s2_ai_summary'),
    os.getenv('s2_red_flags'),
    os.getenv('s2_q3'),
    os.getenv('s2_q4'),
    os.getenv('s2_q5'),
    os.getenv('s2_q6'),
    os.getenv('s2_q7')
]
with open('/tmp/row2.json','w') as f:
    json.dump([row], f)
PYEOF

gws sheets +append --spreadsheet 1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0 --json-values "$(cat /tmp/row2.json)" > /tmp/append2_response.json

row2=$(jq -r '.updates.updatedRange | capture("!A(?<num>[0-9]+):") .num' /tmp/append2_response.json)
echo "$row2" > /tmp/row2.txt

start2=$((row2-1))
batch2=$(jq -n --argjson start "$start2" --argjson end "$row2" '{
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
  ]
}')
gws sheets spreadsheets batchUpdate --json "$batch2"

# BigQuery for Brittney
bq_query2="SELECT firstName, lastName, email, phone, market, FORMAT_TIMESTAMP('%Y-%m-%d', createdAt, 'America/Denver') as created, onboardingInterviewedGeorgia, onboardingInterviewedUtah, onboardingCompletedGeorgia, onboardingCompletedUtah, onboardingBackgroundCheckedGeorgia, onboardingBackgroundCheckedUtah, jobsWorked, hoursWorked, firstShiftCompleted FROM `upkid-7b192.firestore_sync.teachers` WHERE document_id = '$s2_doc_id'"
GOOGLE_APPLICATION_CREDENTIALS="${HOME}/credentials/bigquery-tyler-bot.json" bq query --nouse_legacy_sql --maximum_bytes_billed=53687091200 --format=json "$bq_query2" > /tmp/app2.json || true

if [ -s /tmp/app2.json ] && [ "$(jq length /tmp/app2.json)" -gt 0 ]; then
  app=$(jq -r '.[0]' /tmp/app2.json)
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
  app_section2="🟢 Exact match: $fname $lname | ID: $s2_doc_id\nMarket: $app_market | Created: $app_created | Interview status: GA:int=$ga_int,comp=$ga_comp,bg=$ga_bg; UT:int=$ut_int,comp=$ut_comp,bg=$ut_bg | Shifts: $app_jobs ($app_hours hrs) | First shift: $app_first_shift"
else
  app_section2="🔴 Not found in teachers database"
fi

slack2="## $s2_rec ($s2_confidence) — $s2_name
📧 $s2_email | 📱 $s2_phone_formatted | 📍 Atlanta, GA
Questions: 5/5 — Q3 ✅ Q4 ✅ Q5 ✅ Q6 ✅ Q7 ✅

**Experience:** $s2_exp_str
**Location:** Atlanta, GA | Market: $s2_market | Drive: 25-50mi
**Schedule:** $s2_sched_str

**Summary:** $s2_ai_summary

**Red Flags:** $s2_red_flags

**Zendesk Summary (if approved):**
> $s2_approved_note

🔗 **App Account:**
$app_section2"

echo "$slack2" > /tmp/slack_message_2.txt
echo "$s2_contact_id" > /tmp/contact_id_2.txt
