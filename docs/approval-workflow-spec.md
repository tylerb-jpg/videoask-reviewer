# Approval Workflow Spec — Erica-Approved Candidates

## Overview
When Erica marks a candidate as approved in the Google Sheet, this workflow updates Zendesk and Retool to move the candidate to "Intro Call Passed" status.

## Prerequisites
- Logged into Zendesk (upkid.zendesk.com/agent)
- Logged into Retool (upkid.retool.com — Users Dashboard, Teachers tab)
- Google Sheet open (VideoAsk Teacher Reviews)

## Per-Candidate Steps

### Step 1: Get candidate info from the sheet
- **Email** (column J) → used for Zendesk search
- **App ID** (column I) → used for Retool search
- **Zendesk Note - Approved** (column M) → copy this text for Zendesk notes

### Step 2: Zendesk — Find the teacher
- Go to Zendesk search (🔍 icon or Cmd+K)
- Search by **email address**
- Click on the teacher's user profile from results

### Step 3: Zendesk — Set Teacher Status
- In the user profile sidebar, find **"Teacher Status"** field
- Change it to **"Intro Call Passed"**

### Step 4: Zendesk — Add Notes
- In the user profile sidebar, find the **"Notes"** section
- Paste the **Zendesk Note (Approved)** text from column M of the sheet
- Save/update the profile

### Step 5: Retool — Find the teacher
- Go to the Retool Users Dashboard → **Teachers** tab
- In the **"Name or ID"** search field, paste the **App ID** from column I
- Click **Search**
- Click **View** on the result row

### Step 6: Retool — Mark as Interviewed
- Wait for the detail view to load
- Find the **Onboarding** section
- The correct **state** should already be selected (GA/UT/AZ)
- Check the **"Interviewed"** checkbox
- It auto-saves — close the detail view

### Step 7: Move to next candidate
- For Zendesk: replace the email in search with the next candidate's email
- For Retool: replace the ID in the search field with the next candidate's ID

### Step 7: Mark as Reviewed in the sheet
- Use the Sheets API (NOT browser click — too error-prone, risk of renaming the document):
  ```
  GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-write gws sheets spreadsheets values update \
    --params '{"spreadsheetId":"1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0","range":"Backlog Reviews!A<ROW>","valueInputOption":"USER_ENTERED"}' \
    --json '{"values":[["TRUE"]]}'
  ```
- ⚠️ NEVER use the Google Sheets Name Box via browser — clicking it can accidentally hit the document title rename field

## Batch Efficiency
- Zendesk and Retool sessions stay open
- Only need email + App ID + Zendesk approved note per candidate
- Can process in sequence: all Zendesk first, then all Retool (or interleaved)

## Safeguards
- Only process candidates where Erica Approved = TRUE (column B checked)
- Never change status to "Not Hiring" — that sends a rejection
- Verify the name matches between sheet and Zendesk/Retool before making changes
- If a teacher is NOT found in Zendesk or Retool, skip and flag for manual review
