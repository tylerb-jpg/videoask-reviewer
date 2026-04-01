# Memory — VideoAsk Reviewer Agent

## Session: 2026-04-01 (Tyler, webchat)

### Token Expiry Incident & Fix
- **Problem:** VideoAsk token expired at ~8am MDT on 4/1. The original 24h token (obtained 3/31) expired and could not be auto-refreshed because VideoAsk doesn't support `client_credentials` or `password` OAuth grants.
- **Root cause of 15-min tokens:** Initially tried the implicit flow (`response_type=token`) which only gives 15-min tokens. The original 24h token came from the **authorization code flow** (`response_type=code`).
- **Fix:** Re-authed using authorization code flow + `offline_access` scope → got 24h token + **refresh_token**.
- **Refresh script rewritten:** `scripts/refresh-videoask-token.py` now uses the `refresh_token` grant — simple API call, no browser/CDP needed. Works indefinitely as long as the refresh token isn't revoked.
- **process-new-submissions.py updated:** Calls refresh script with `--force` when token is expired. Tested: simulated expired token → auto-refreshed → continued processing.
- **Removed 10-min cron job** (`16608f3b-a015-4652-b89b-39d8c982f949`) — unnecessary with 24h tokens + auto-refresh.
- **Refresh token saved** to both `videoask-token.json` and `videoask-oauth.json` for backup.

### 3 Candidates Missing Slack Notifications
- **Jewel Martin**, **Kameon Williams**, **Daniela Trujillo Pastor** — all completed after 8am MDT on 4/1.
- They WERE fully written to the sheet (AI summaries, Zendesk notes, everything) — the cron caught them before the token fully expired.
- BUT their Slack notifications were never sent (cron likely timed out or hit token error after sheet write, before Slack post).
- The sheet email safety net then marked them as "processed" on the next run, preventing re-processing but also preventing Slack notification.
- **Manually posted all 3 to Slack** channel `C0AQQ2LBTKJ` on 4/1.
- **Lesson:** The pipeline can still lose Slack notifications even when the sheet write succeeds. The mark-done flow protects against missing sheet rows but not missing Slack posts. A future improvement could track "slack_posted" separately from "sheet_written".

### OAuth Flow Details (for future reference)
- **Authorization Code flow** (24h tokens): `response_type=code`, exchange code via `/oauth/token` with `client_secret`
- **Implicit flow** (15-min tokens): `response_type=token`, token in URL fragment — DO NOT USE
- **Client credentials** (`client_credentials` grant): NOT SUPPORTED by VideoAsk
- **Password grant**: NOT SUPPORTED by VideoAsk
- **Refresh token grant**: WORKS — use `grant_type=refresh_token` with `client_id` + `client_secret` + `refresh_token`
- **Consent:** Required once for `offline_access` scope (accepted on 4/1). After that, `prompt=none` should work for silent re-auth if ever needed.

### VideoAsk Tab in Chrome
- A VideoAsk tab was opened during debugging but is no longer needed for token refresh (refresh_token handles it).
- The tab can be closed. If browser-based auth is ever needed again, open `https://app.videoask.com` and login with credentials from `~/credentials/videoask-login.json`.

## Session: 2026-03-30 → 2026-03-31 (Tyler, webchat)

### What We Built
- **Google Sheet** for Erica: `1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0`
  - 217 candidates (231 backlog minus 14 already-interviewed in app)
  - All 217 have AI-written summaries (read each transcript individually)
  - Column order: Reviewed ☑️ | Date | Name (with 🟢/🟡 match dot) | Market | Rec | ▶️ VideoAsk link | First Name | App ID | Email | Phone | 🔍 Zendesk | Zendesk Note Approved | Zendesk Note Denied | Experience | Location/Drive | Schedule | Summary | Red Flags | [hidden Q3-Q7]
  - Color-coded rows by recommendation
  - Zendesk notes use `=TEXT(TODAY(),"MM/DD")` so date auto-updates
  - Uses `tyler.b@upkid.com` write access: `GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-write`

- **Cron job** for new submissions: `3ca16bf8-1674-4a09-bfa7-644eb99e6e60`
  - Every 15 min, 7am-8pm Mountain, daily
  - Runs `scripts/process-new-submissions.py` → AI summary → append to sheet → Slack message
  - Slack channel: `C0AQQ2LBTKJ`
  - Max 2 per run (reduced from 5 on 2026-03-31 due to Opus timeout issues)
  - Timeout: 600 seconds (10 min)

### Key Decisions
- **Never auto-deny** — only APPROVE or FLAG. Denials trigger rejection email+text.
- **Erica's workflow**: glance at row → ▶️ watch video if needed → search Retool by first name → 🔍 Zendesk → copy Zendesk note → check ☑️ → next
- **Male candidates**: flagged with 👨 for placement consideration (many centers won't hire men)
- **Gender screening**: we do NOT analyze voice/appearance to identify biological sex — legal risk. Only flag by name.
- **Profile not complete** flag removed — expected pre-interview
- **Oldest candidates at top**, newest at bottom (cron appends)
- **Slack messages should be short**: rec + name + market + date + 1-line summary + sheet link

### Holes Fixed in Cron Pipeline
1. Token auto-refresh (refresh_token then client_credentials, then Slack alert)
2. AI summary quality (examples in prompt + full transcript passed)
3. Duplicate detection (checks sheet emails)
4. BQ sync race condition (pending_match queue, 3 retries)
5. Sheet append API (ignores sorting/filtering)
6. Rate limits (max 2 per run)
7. Cron agent gets raw transcripts to write real summaries
8. Slack links to sheet + candidate name for Cmd+F

### Critical Fix: No Candidates Fall Through Cracks (2026-03-31)
**Problem discovered:** The Python script (`process-new-submissions.py`) was marking candidates as "processed" in `videoask-state.json` BEFORE the cron agent finished writing to the sheet/Slack. If the cron agent timed out, candidates were permanently skipped — they'd never come back.

**Root cause:** State update happened in the script (before AI work), not after successful sheet write.

**Fix (three parts):**
1. **`process-new-submissions.py` no longer marks candidates as processed.** It outputs candidate JSON but does NOT touch the state file's `processed_contacts` list. Only "already interviewed" skips and sheet-email safety catches update state.
2. **New script: `scripts/mark-done.py`** — Called by the cron agent AFTER successfully writing each candidate to the sheet and posting to Slack. Usage: `python3 scripts/mark-done.py <contact_id>`. This is the ONLY way candidates get marked as done.
3. **Sheet email cross-check as safety net.** Before processing, the script reads all emails from the sheet (column I). If a candidate's email is already in the sheet but not in state, it marks them processed and skips. Belt and suspenders — even if state gets corrupted, we won't re-add someone already in the sheet.

**Cron agent flow (per candidate, sequential):**
1. Run `process-new-submissions.py` → get candidate JSON
2. Write AI summary
3. Append row to sheet
4. Apply checkbox + row color formatting via batchUpdate
5. Post to Slack
6. Call `mark-done.py <contact_id>` ← **only then is it "done"**
7. Move to next candidate

If the job times out after step 5 but before step 6, the candidate is NOT marked done and will be re-processed next run. The sheet email cross-check (safety net) will catch it and mark it done without duplicating the row.

**Batch size reduced to 2** per run (from 5) because Opus needs ~3 min per candidate for AI summary + all API calls. 2 candidates × 3 min = 6 min, well within the 10-min timeout.

### Erica Feedback (2026-03-31)
- **Aiyanna Martin**: Erica denied her. AI rated ✅ LOW. Reason: "lack of explanation of experience" — transcript mentioned loving kids and a classroom of 10+ two-year-olds but never named an employer or setting. Lesson: vague experience claims without specifics (employer, setting, duration) should be flagged, not approved.
- **New criteria rule added**: Flag candidates who claim experience but give no specifics
- **Denial notes**: Added `=TEXT(TODAY(),"MM/DD") & " Not Hiring — Intro Call. [City, State]."` to all 175 approved candidates that were missing denial notes. Every candidate now has both an approval and denial note ready.
- **Anca (popelizabeth2007)**: Erica denied. AI rated 🟡 LOW. Only 2.5yr Sunday school (ages 6-13) over 13 years, only answered Q3. Erica wrote: "only answered 1 question of experience — only teaching Sunday school." Updated denial note to match.
- **Denial notes must be specific**: Erica wants the WHY in denial notes, not just location. Updated all 175 approved denial notes to include experience details (e.g. "Only informal experience (babysitter)" or "Experience: daycare; substitute").
- **Arizona nannying rule**: AZ candidates must have specifically worked in a child care center, daycare, or preschool. Nannying is NOT considered professional experience per AZ regulations. This is AZ-specific only — does not apply to GA or UT. Updated criteria.json with new custom rule + qualifying/disqualifying settings for AZ.

### Slack Channel Live (2026-03-31)
- Bot is live in VideoAsk Reviews channel (`C0AQQ2LBTKJ`)
- Binding routes channel → `videoask-reviewer` agent
- `requireMention: true` — only responds when @mentioned
- All Slack channel replies go to threads (`replyToModeByChatType.channel = "all"`)
- **Training loop**: Erica (or Tyler) @mentions with feedback in threads → log to `training-log.json` + update `criteria.json` if new pattern
- **Thread replies are the primary feedback mechanism** — more context than emoji reactions
- Emoji reactions (✅ ❌ 👀 ⏭️) are secondary — log when they happen but don't rely on them
- Erica may or may not use emojis; Tyler will talk to her about it

### Still TODO
- Tweak sheet formatting if Erica has feedback
- Consider Cloudflare Tunnel for webhook (real-time) vs current cron (15min delay)
- Set up Erica's emoji reactions as training loop (Slack → training-log.json)
- May want to add Retool deep link if we can figure out the URL format

### VideoAsk URL Format
- Dashboard: `https://app.videoask.com/app/organizations/{org}/form/{form}/conversation/{contact_id}`
- Do NOT use `www.videoask.com` share URLs

### Config Changes (2026-03-31)
- **Binding added**: `bindings[0]` routes Slack channel `C0AQQ2LBTKJ` → `videoask-reviewer` agent
- **Channel allowlisted**: `channels.slack.channels.C0AQQ2LBTKJ` = `{allow: true, requireMention: true}`
- **Thread replies**: `channels.slack.replyToModeByChatType.channel = "all"` (all Slack channels reply in threads)
- **Cron job updated**: Sheet ID `412743935` added to cron instructions; checkbox data validation now applied after row append via `batchUpdate` (fixes "FALSE" text instead of checkbox)

### Sheet Technical Details
- Spreadsheet ID: `1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0`
- Sheet tab: "Backlog Reviews"
- Sheet ID (for batchUpdate API): `412743935`
- Column A checkbox: requires `setDataValidation` with `BOOLEAN` type + `repeatCell` with `boolValue: false` after every append
- Row colors by recommendation type (see cron job instructions)
- GWS write env: `GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-write`

### Dates
- All dates must be Mountain time (MDT currently, UTC-6)
- VideoAsk API returns UTC — always convert

### People
- **Tyler**: Owner/admin. Built this system. Communicates via webchat TUI and Slack.
- **Erica**: Primary reviewer. Reviews candidates in the Google Sheet. Will @mention bot in Slack for feedback. Her decisions are final — she approves/denies in Retool and Zendesk.
- **Kinsey**: Secondary reviewer. Also does VideoAsk reviews but less frequently than Erica.

### Training System
- `training-log.json`: Every Erica/Tyler decision logged here — candidate, AI rec, human decision, reason, lesson learned
- `criteria.json`: Decision criteria including market rules, examples, and Erica's custom rules. Updated when feedback reveals new patterns.
- Agreement rate tracked in `training-log.json` stats
- As of 2026-03-31: 2 logged overrides (Aiyanna Martin — vague experience; Anca — Sunday school only)

### Scripts
- `scripts/process-new-submissions.py` — Pulls new VideoAsk contacts, does BQ lookup, outputs candidate JSON. Does NOT mark candidates as processed.
- `scripts/mark-done.py` — Marks contact IDs as processed in state file. Called by cron agent AFTER successful sheet+Slack write. Usage: `python3 scripts/mark-done.py <contact_id> [<contact_id2> ...]`

### Incident Log
- **2026-03-31 12pm-3:30pm**: Anthropic API overloaded for ~3 hours. Cron runs failed with "AI service temporarily overloaded" or timed out. 5 new VideoAsk completions came in during this window. Previously, the script marked them as processed before the AI could write to the sheet — causing them to fall through cracks. Fixed by separating state update from processing (see "Critical Fix" section above). The 5 candidates are now safely queued and will process as the API recovers, 2 per run.
