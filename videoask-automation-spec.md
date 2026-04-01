# VideoAsk Review Tool — Full Specification

**Version:** 1.0
**Created:** March 30, 2026
**Owner:** Tyler
**Builder:** Tyler Bot
**Primary User:** Erica (daily reviewer)
**Secondary User:** Kinsey (backup reviewer)
**Status:** Spec complete, awaiting credentials for build

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [The Problem in Detail](#the-problem-in-detail)
3. [The Solution](#the-solution)
4. [User Experience — Erica's New Workflow](#user-experience)
5. [System Architecture](#system-architecture)
6. [AI Evaluation Engine](#ai-evaluation-engine)
7. [Identity Matching](#identity-matching)
8. [Training & Feedback System](#training-and-feedback-system)
9. [Review Queue Dashboard](#review-queue-dashboard)
10. [Data Model](#data-model)
11. [Integration Details](#integration-details)
12. [Decision Criteria Reference](#decision-criteria-reference)
13. [Edge Cases & How We Handle Them](#edge-cases)
14. [Rollout Plan](#rollout-plan)
15. [Success Metrics](#success-metrics)
16. [Open Items](#open-items)

---

## 1. Executive Summary <a name="executive-summary"></a>

**What we're building:** A review tool that reads VideoAsk teacher interview transcripts, generates candidate summaries with pre-written notes, finds the matching teacher in Zendesk and Retool, and presents Erica with a complete review card. She reads the summary, copies the notes, clicks links to the pre-found profiles, and updates status herself.

**What it replaces:** Erica's current process of watching each video, manually searching Zendesk, manually searching Retool, typing notes from scratch, and switching between 4 browser tabs per candidate.

**What it does NOT do:** It does not write to Zendesk, Retool, or any teacher-facing system. It reads and recommends. Erica executes. It never auto-denies a teacher.

**Time savings:** 2-3 minutes per review → ~30 seconds per review. At 20-30 reviews/day, that's 50-70 minutes saved daily.

**Risk level:** Low. The tool only reads from external systems and outputs to Slack + a local dashboard. All teacher-affecting actions remain in Erica's hands.

---

## 2. The Problem in Detail <a name="the-problem-in-detail"></a>

### Current State
Teachers apply via the Upkid app, then complete a VideoAsk "intro call" — a series of 7 video/audio questions about their experience, location, schedule, and fit. VideoAsk auto-transcribes all responses.

Erica (and sometimes Kinsey) reviews each submission manually:

**Step 1 — Watch/Read (60-90 sec):**
Open VideoAsk. Watch the video or read the transcript. Mentally extract: name, experience type, years, location, market, drive radius, schedule, red flags.

**Step 2 — Decide (10-15 sec):**
Approve (mark as "Intro Call Passed") or deny (mark as "Not Hiring"). Decision based on:
- Does the teacher have relevant childcare experience?
- Are they in one of the three markets (Utah, Georgia, Arizona)?
- Are they available to work?
- Any disqualifiers?

**Step 3 — Update Zendesk (30-45 sec):**
Open Zendesk. Search for the teacher by name or email. Click "Interviewed/Reviewed."

**Step 4 — Update Retool (30-45 sec):**
Open Retool. Search for the teacher. Add notes in this format:
```
[DATE] Hired. [CITY], [DRIVE RADIUS]. [EXPERIENCE SUMMARY].
```
Change teacher status to "Intro Call Passed" (or "Not Hiring" for denials).

**Step 5 — Mark VideoAsk done (10 sec):**
Go back to VideoAsk. Mark the submission as reviewed (purple dot clears).

**Total: 2-3 minutes per candidate × 20-30 candidates/day = 60-90 minutes of repetitive manual work.**

### Pain Points
1. **Watching videos is slow.** Most of the information is in the first 30 seconds of Q3 (experience). The rest is confirmatory. But Erica watches each one fully to be thorough.
2. **Searching across systems is tedious.** Open VideoAsk → tab to Zendesk → search → tab to Retool → search → tab back. Four different systems, none connected.
3. **Typing notes is busywork.** The notes follow a rigid format. The information is already in the transcript. Manually re-typing it is pure waste.
4. **Backlog builds fast.** At 20-30/day, missing one day means 40-60 in the queue. The team was 5 days behind at peak.
5. **Context switching kills focus.** Erica jumps between teacher evaluations, customer support, VideoAsk reviews, and AI interview testing. The review process demands deep context that's hard to maintain with interruptions.

### What Happens Downstream

When Erica sets "Intro Call Passed":
- Teacher's app status updates
- Zoho sends the teacher a text message
- If all other requirements are met (profile complete, etc.), teacher becomes eligible for background check submission
- After background check passes → "Ready to Work" → teacher can pick up shifts

When Erica sets "Not Hiring":
- Teacher receives a rejection email
- Teacher receives a rejection text
- Teacher is effectively removed from the pipeline
- **This is non-reversible in practice** — the teacher has already been told "no"

### Teacher Status Pipeline
```
New Profile
  → Complete (profile filled out)
    → Intro Call Scheduled
      → Intro Call Passed ← WE ARE HERE
        → Background Check Submitted
          → Ready to Work
            → First Shift Scheduled
              → First Shift Complete

      → Not Hiring (intro call) ← DENIAL — sends rejection email + text
      → No Show
```

---

## 3. The Solution <a name="the-solution"></a>

### Product Name: **VideoAsk Reviewer** (working title)

### Core Concept
A web-based review queue that presents Erica with pre-built candidate cards. Each card contains:
- AI-generated summary of the teacher's qualifications
- Pre-written notes ready to copy-paste
- Pre-found links to the teacher's Zendesk and Retool profiles
- AI recommendation with confidence level and reasoning
- Feedback buttons for Erica to train the AI

### Design Principles
1. **Read, don't write.** The tool never modifies external systems. It reads from VideoAsk, Zendesk, and Retool. Erica makes all changes in those systems directly.
2. **Faster, not different.** Erica's workflow stays fundamentally the same (evaluate → update Zendesk → update Retool). The tool just eliminates the slow parts (watching video, searching, typing notes).
3. **Bias toward approval.** When in doubt, recommend approval. A false approve is caught at the next gate (background check). A false deny sends a rejection message and may lose a teacher permanently.
4. **Always trainable.** Every review is a training signal. Erica can correct the AI at any point. The system gets smarter over time but never stops accepting feedback.
5. **Transparent reasoning.** The AI shows its work. "Recommending APPROVE because: 5 years daycare experience (formal), located in Atlanta GA (Georgia market), flexible schedule." Erica verifies the reasoning, not just the output.

---

## 4. User Experience — Erica's New Workflow <a name="user-experience"></a>

### The Review Queue

Erica opens the review tool (web dashboard, similar to the CEO kanban board). She sees a queue of unreviewed VideoAsk submissions.

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 VideoAsk Review Queue                    25 pending  │
│                                                             │
│ Filter: [All] [Approve] [Flag] [Unmatched]    Sort: [Newest]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─ Candidate Card ────────────────────────────────────────┐ │
│ │ ✅ APPROVE (HIGH)                    Mar 30, 2026      │ │
│ │                                                         │ │
│ │ Oyanioye Eke                                            │ │
│ │ 📧 eke292@gmail.com  📱 +1 (404) 441-8433             │ │
│ │ 📍 Atlanta, GA — 30 min drive radius                   │ │
│ │                                                         │ │
│ │ Experience: 4+ years daycare, all ages to 14.           │ │
│ │ Grew up in daycare environment. Passionate about         │ │
│ │ flexibility and working with children.                   │ │
│ │                                                         │ │
│ │ Schedule: Flexible, open to part-time or full-time      │ │
│ │                                                         │ │
│ │ 📝 Ready to copy:                                      │ │
│ │ ┌──────────────────────────────────────────────────────┐│ │
│ │ │ 3/30 Hired. Atlanta GA, 30 min. 4+ years daycare,  ││ │
│ │ │ all ages to 14. Flexible schedule.                   ││ │
│ │ └──────────────────────────────────────────────────┤📋│┘│ │
│ │                                                         │ │
│ │ Identity Match:                                         │ │
│ │ 🟢 Found in Zendesk: Oyanioye Eke (eke292@gmail.com)  │ │
│ │    Status: Complete | [Open in Zendesk ↗]               │ │
│ │ 🟢 Found in Retool: Oyanioye Eke (eke292@gmail.com)   │ │
│ │    Status: Complete | [Open in Retool ↗]                │ │
│ │                                                         │ │
│ │ [📋 Copy Notes] [🔗 Zendesk] [🔗 Retool] [🎧 VideoAsk]│ │
│ │                                                         │ │
│ │ Feedback: [✅ Agree] [❌ Override] [✏️ Edit] [⏭️ Skip] │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─ Candidate Card ────────────────────────────────────────┐ │
│ │ 🟡 FLAG (MEDIUM)                     Mar 30, 2026      │ │
│ │                                                         │ │
│ │ Amber Botts                                             │ │
│ │ 📧 amber_botts@icloud.com  📱 +1 (839) 866-1144      │ │
│ │ 📍 Augusta, GA — drive radius not stated                │ │
│ │                                                         │ │
│ │ ⚠️ Flag reason: Only 1 year experience, toddlers       │ │
│ │ only. Limited formal setting details.                    │ │
│ │                                                         │ │
│ │ Experience: 1 year at daycare center, toddlers ages     │ │
│ │ 2+. Has own children. Loves working with children.      │ │
│ │                                                         │ │
│ │ ...                                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Erica's Flow (per candidate)

**For a clear APPROVE (HIGH confidence, identity matched):**
1. Read the summary card (5 seconds)
2. Click "Copy Notes" (1 second)
3. Click "Open in Zendesk" → paste notes, click status change (10 seconds)
4. Click "Open in Retool" → paste notes, click status change (10 seconds)
5. Click "Agree" to log feedback (1 second)
**Total: ~30 seconds**

**For a FLAG (needs judgment):**
1. Read the summary card (5 seconds)
2. Read the flag reason (5 seconds)
3. Optionally click "Listen in VideoAsk" to hear the actual response (30-60 seconds)
4. Make a decision
5. If approving: same as above (copy, Zendesk, Retool, feedback)
6. If denying: click "Override" → select "Deny" → type brief reason → confirm
**Total: 1-2 minutes (vs. 2-3 minutes today, but with better information)**

**For an UNMATCHED identity:**
1. Read the summary card
2. See "🔴 Not found in Zendesk" or "⚠️ Multiple matches"
3. Manually search in Zendesk/Retool
4. If found: proceed with copy/paste flow
5. If truly not found: skip or flag for Tyler
**Total: 1-2 minutes (but this is a data issue, not a review issue)**

### What Erica Does NOT Have to Do Anymore
- ❌ Watch full videos (read the AI summary instead)
- ❌ Search for teachers in Zendesk (pre-found, direct link ready)
- ❌ Search for teachers in Retool (pre-found, direct link ready)
- ❌ Type notes from scratch (copy pre-written notes)
- ❌ Remember the note format (tool generates it)
- ❌ Switch between 4 tabs trying to find the same person (all in one card)

---

## 5. System Architecture <a name="system-architecture"></a>

```
                          ┌──────────────┐
                          │   VideoAsk   │
                          │     API      │
                          └──────┬───────┘
                                 │ Pull new completed contacts
                                 │ + transcripts for Q3-Q7
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                    VideoAsk Reviewer                         │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Transcript   │→│ AI Evaluator │→│ Decision Engine    │   │
│  │ Puller       │  │ (Claude)     │  │ (rules + AI)      │   │
│  └─────────────┘  └──────────────┘  └────────┬──────────┘   │
│                                               │              │
│  ┌─────────────┐  ┌──────────────┐           │              │
│  │ Zendesk     │→│ Identity     │←──────────┘              │
│  │ Searcher    │  │ Matcher      │                           │
│  └─────────────┘  └──────┬───────┘                           │
│  ┌─────────────┐         │                                   │
│  │ Retool      │─────────┘                                   │
│  │ Searcher    │                                             │
│  └─────────────┘         │                                   │
│                          ▼                                   │
│                 ┌──────────────────┐                          │
│                 │ Review Queue     │                          │
│                 │ (Web Dashboard)  │ ← Erica uses this       │
│                 └────────┬─────────┘                          │
│                          │                                   │
│                 ┌────────▼─────────┐                          │
│                 │ Training Logger  │                          │
│                 │ (feedback.json)  │                          │
│                 └──────────────────┘                          │
│                                                              │
│                 ┌──────────────────┐                          │
│                 │ Slack Notifier   │ (daily summaries)        │
│                 └──────────────────┘                          │
└──────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   [Erica clicks        [Erica clicks        [Erica clicks
    in Zendesk]          in Retool]           in VideoAsk]
```

### Components

**1. Transcript Puller**
- Connects to VideoAsk API via OAuth
- Pulls contacts with status = "completed" that haven't been reviewed yet
- For each contact, pulls answers for Q3 (experience), Q4 (location), Q5 (schedule), Q6 (conflict), Q7 (why great teacher)
- Extracts transcription text from each answer
- Deduplicates by email + phone (uses most recent completed submission)
- Runs on a schedule (cron, every 30 min during business hours) or on-demand

**2. AI Evaluator**
- Takes the concatenated transcripts + contact info (name, email, phone)
- Runs a structured LLM prompt (see Section 6) that extracts:
  - Candidate profile (name, location, experience, availability)
  - Recommendation (APPROVE / FLAG)
  - Confidence (HIGH / MEDIUM / LOW)
  - Reasoning (one line explaining why)
  - Pre-written note text (in Erica's exact format)
- Uses the training log to incorporate Erica's past feedback into the prompt

**3. Decision Engine**
- Takes AI Evaluator output and applies hard rules:
  - Never auto-DENY (always FLAG for denials)
  - Market-specific experience thresholds
  - Incomplete transcripts → automatic FLAG
  - Out-of-market → automatic FLAG
- Assigns final recommendation and confidence level

**4. Identity Matcher**
- Searches Zendesk for the teacher by email, phone, and name
- Searches Retool for the teacher by email, phone, and name
- Ranks matches: exact (email + phone), partial (one matches), fuzzy (name similar), none
- Generates direct links to the teacher's profile in each system
- If browser-based: uses OpenClaw browser to search and extract profile URLs
- If API-based (future): queries directly

**5. Review Queue Dashboard**
- Web-based UI served locally (like CEO kanban board)
- Shows candidate review cards in a scrollable queue
- Filters: All, Approve, Flag, Unmatched, Reviewed
- Sort: Newest first, oldest first, by confidence
- Click-to-copy for notes
- Direct links to Zendesk, Retool, VideoAsk profiles
- Feedback buttons on every card
- Password-protected (same pattern as kanban board)

**6. Training Logger**
- Records every review: timestamp, candidate, AI recommendation, Erica's decision, reason, note edits
- Stores in `builds/videoask-reviewer/training-log.json`
- Periodically analyzed to update the AI evaluation prompt
- Tracks accuracy metrics over time

**7. Slack Notifier**
- Daily summary: "Reviewed X teachers: Y approved, Z flagged, W skipped"
- Alerts for: new batch ready for review, unreviewed candidates >24h old, system errors
- Does NOT send individual candidate details to Slack (privacy — teacher info stays in the tool)

### Where It Lives
- **Server:** Node.js process on Tyler's Mac Mini, similar to CEO kanban board
- **Port:** TBD (not 8787 — that's the kanban board)
- **Data:** Local JSON files in `builds/videoask-reviewer/`
- **LaunchAgent:** Auto-starts on login, auto-restarts on crash (same pattern as kanban board)
- **Auth:** Password-protected web UI
- **Access:** Erica accesses via browser (localhost or Tailscale if needed)

---

## 6. AI Evaluation Engine <a name="ai-evaluation-engine"></a>

### Prompt Structure

The AI evaluator receives a structured prompt with:

```
SYSTEM: You are a teacher hiring evaluator for Upkid, a childcare staffing platform
operating in Utah, Georgia, and Arizona. Your job is to review VideoAsk interview
transcripts and recommend whether to approve or flag each candidate.

RULES:
- Bias toward APPROVE. When in doubt, approve. A false approve is caught at the
  next step (background check). A false deny loses a teacher permanently.
- Never recommend DENY. Only APPROVE or FLAG. Denials are always human decisions.
- Be market-aware. Arizona requires 6 months formal childcare experience.
  Utah is more lenient. Georgia is in between.
- "Experience" means: daycare, preschool, classroom teacher, paraprofessional,
  substitute teacher, afterschool program, Head Start, camp counselor, nanny
  with professional references, church childcare program (formal/volunteer).
- "Not experience" means: only raised own children (no professional setting),
  CNA/elderly care (not children), retail/food service (not relevant).
- Babysitting: FLAG if it's the only experience. May be sufficient for Utah,
  probably not for Arizona.

DECISION CRITERIA:
[Insert current criteria from training log, including Erica's custom rules]

CANDIDATE TRANSCRIPT:
Name: {name}
Email: {email}
Phone: {phone}
Market (from area code): {detected_market}

Q3 — Tell us about yourself:
{transcript_q3}

Q4 — Where are you located:
{transcript_q4}

Q5 — Schedule/availability:
{transcript_q5}

Q6 — Conflict resolution:
{transcript_q6}

Q7 — Why would you make a great teacher:
{transcript_q7}

OUTPUT FORMAT (JSON):
{
  "name": "extracted full name",
  "market": "utah|georgia|arizona|unknown",
  "city": "specific city",
  "drive_radius": "stated drive willingness or 'not stated'",
  "experience_type": "formal|informal|mixed|none",
  "experience_summary": "brief description of relevant experience",
  "experience_years": "number or 'not stated'",
  "availability": "full-time|part-time|flexible|limited|not stated",
  "schedule_notes": "any specific schedule constraints mentioned",
  "recommendation": "APPROVE|FLAG",
  "confidence": "HIGH|MEDIUM|LOW",
  "flag_reason": "only if FLAG — brief explanation of what needs human review",
  "note_text": "pre-written note in Erica's format: [DATE] Hired. [CITY], [DRIVE]. [EXPERIENCE].",
  "reasoning": "one sentence explaining the recommendation"
}
```

### Phone Area Code → Market Mapping

Used as a signal (not definitive — people move):

| Area Codes | Market |
|---|---|
| 801, 385, 435 | Utah |
| 404, 470, 678, 770, 762, 706, 912, 229, 478, 346 | Georgia |
| 480, 602, 623, 520, 928 | Arizona |
| Other | Unknown — FLAG for location verification |

### Transcript Quality Check

Before running the AI evaluator, check:
- Is the transcript present? (sometimes transcription fails)
- Is the transcript longer than 10 words? (too short = garbled or blank response)
- Are all expected questions (Q3-Q5 minimum) answered?

If any check fails → automatic FLAG with reason "Incomplete or poor quality transcript — needs human review."

---

## 7. Identity Matching <a name="identity-matching"></a>

### Matching Strategy

For each candidate, search Zendesk and Retool using:

**Search 1 — Email (exact):**
Most reliable. Email should be unique per teacher.

**Search 2 — Phone (exact):**
Second most reliable. Strip formatting, compare digits only.

**Search 3 — Name (fuzzy):**
Least reliable. Teachers change names, transcription garbles names. Use as confirming signal, not primary match.

### Match Confidence Levels

| Level | Criteria | Action |
|---|---|---|
| 🟢 **Exact Match** | Email AND phone both match a single record | Auto-select, show "Open in Zendesk/Retool" links |
| 🟡 **Partial Match** | Email OR phone matches, but not both. Or matches multiple records. | Show all candidates, Erica picks |
| 🔴 **No Match** | Neither email nor phone found in Zendesk/Retool | Flag — teacher may not be in the system yet, or different contact info |
| ⚠️ **Multiple Matches** | Email matches one record, phone matches a different one | Show both, Erica selects the right one |

### Known Matching Challenges
- **Name changes:** Destiny Cervantes → Destiny Hatley (same person, different last name across systems)
- **Phone number formatting:** +14044418433 vs (404) 441-8433 vs 4044418433
- **Email typos:** Teachers sometimes use different emails across systems
- **New teachers:** VideoAsk submission may arrive before the teacher's Zendesk/Retool record exists (timing gap)
- **Duplicate records:** Same teacher may have multiple records in Zendesk or Retool

### Implementation Options

**Option A — Browser-based search (MVP):**
Use OpenClaw browser to search Zendesk and Retool by email/phone. Extract the profile URL and display info. Slower but requires no API access.

**Option B — Retool read access + Zendesk browser (likely):**
If we get Retool read access, query teachers directly. Still use browser for Zendesk. Faster for Retool matches.

**Option C — Both APIs (future):**
If API access is ever granted, search both programmatically. Fastest, most reliable.

---

## 8. Training & Feedback System <a name="training-and-feedback-system"></a>

### Feedback Actions

On every candidate card, Erica has four options:

**✅ Agree**
- AI recommendation was correct
- Erica proceeds to update Zendesk/Retool as recommended
- Logged as: `{action: "agree", ai_rec: "APPROVE", erica_dec: "APPROVE"}`
- Reinforces the current criteria

**❌ Override**
- AI recommendation was wrong
- Erica selects the correct decision: APPROVE or DENY
- Erica types a brief reason: "CNA experience is not childcare" or "Church nursery counts in Utah"
- Logged as: `{action: "override", ai_rec: "APPROVE", erica_dec: "DENY", reason: "..."}`
- Used to refine criteria — if the same override pattern appears 3+ times, it becomes a rule

**✏️ Edit Notes**
- AI-generated notes were close but need correction
- Erica modifies the note text
- The diff is logged: `{action: "edit", original: "...", edited: "...", diff: "..."}`
- Used to improve note generation quality

**⏭️ Skip**
- Erica can't decide right now, or needs more info
- Card stays in the queue
- Not logged as a training signal

**🚩 Flag for Tyler**
- Edge case that needs Tyler's input
- Sends a Slack message to Tyler with the candidate card
- Logged as: `{action: "escalate", reason: "..."}`

### Training Log Format

```json
{
  "reviews": [
    {
      "timestamp": "2026-04-01T10:30:00Z",
      "videoask_contact_id": "f6d6c1bb-...",
      "candidate_name": "Oyanioye Eke",
      "candidate_email": "eke292@gmail.com",
      "candidate_phone": "+14044418433",
      "market_detected": "georgia",
      "ai_recommendation": "APPROVE",
      "ai_confidence": "HIGH",
      "ai_reasoning": "4+ years daycare experience, Atlanta GA, flexible schedule",
      "ai_note_text": "3/30 Hired. Atlanta GA, 30 min. 4+ years daycare, all ages to 14. Flexible schedule.",
      "erica_action": "agree",
      "erica_decision": "APPROVE",
      "erica_reason": null,
      "note_edited": false,
      "identity_match_type": "exact",
      "zendesk_matched": true,
      "retool_matched": true
    },
    {
      "timestamp": "2026-04-01T10:31:00Z",
      "videoask_contact_id": "0b4a8182-...",
      "candidate_name": "Amber Botts",
      "candidate_email": "amber_botts@icloud.com",
      "candidate_phone": "+18398661144",
      "market_detected": "georgia",
      "ai_recommendation": "FLAG",
      "ai_confidence": "MEDIUM",
      "ai_reasoning": "Only 1 year experience, toddlers only. Limited details.",
      "ai_note_text": null,
      "erica_action": "override",
      "erica_decision": "APPROVE",
      "erica_reason": "1 year formal daycare is enough for Georgia. She has own children too.",
      "note_edited": true,
      "note_original": null,
      "note_final": "3/30 Hired. Augusta GA. 1 year daycare, toddlers 2+. Has own children.",
      "identity_match_type": "partial",
      "zendesk_matched": true,
      "retool_matched": false
    }
  ],
  "criteria_updates": [
    {
      "timestamp": "2026-04-01T10:31:00Z",
      "rule": "1 year formal daycare experience is sufficient for Georgia market",
      "source": "Erica override on Amber Botts review",
      "added_by": "erica"
    }
  ],
  "stats": {
    "total_reviews": 2,
    "ai_agree_rate": 0.50,
    "overrides": 1,
    "edits": 1,
    "skips": 0,
    "escalations": 0
  }
}
```

### How Training Improves the AI

1. **After every 10 reviews:** Tyler Bot reads the training log, identifies override patterns, and considers updating the AI prompt's decision criteria section.
2. **Weekly:** Tyler Bot generates a training report: agreement rate, common override reasons, new rules added. Posts to Slack.
3. **On criteria update:** When a new rule is added (e.g., "1 year formal daycare is enough for GA"), the AI prompt is updated and the change is logged.
4. **The training log is the institutional knowledge.** If Erica is unavailable, someone else can review the log to understand decision patterns.

---

## 9. Review Queue Dashboard <a name="review-queue-dashboard"></a>

### Technical Details
- **Framework:** Plain HTML/CSS/JS (same approach as CEO kanban board — no build tools, no frameworks)
- **Server:** Node.js (Express), separate process from kanban board
- **Port:** 8788 (next to kanban 8787)
- **Auth:** Password login, session cookies (same pattern as kanban)
- **Data source:** Local JSON files + VideoAsk API + browser search results
- **Updates:** SSE (Server-Sent Events) for live queue updates

### Pages

**1. Queue (`/queue`)** — Main review page
- List of candidate cards, sorted by newest
- Filters: All, Approve (HIGH), Flag, Unmatched, Reviewed today
- Count badges: "25 pending | 3 flagged | 12 reviewed today"
- Each card is expandable (collapsed shows name + recommendation, expanded shows full card)

**2. Stats (`/stats`)** — Training metrics
- Agreement rate over time (chart)
- Reviews per day (chart)
- Override breakdown by reason
- Common flag reasons
- Market distribution of candidates

**3. Criteria (`/criteria`)** — Current decision rules
- Shows the current decision criteria
- Shows Erica's custom rules (from training log)
- Editable — Erica or Tyler can update rules directly

**4. History (`/history`)** — Past reviews
- Searchable list of all reviewed candidates
- Filter by date, decision, market, match type
- Useful for: "Did we already review this person?" and "What did we decide about the last babysitting-only candidate from Arizona?"

---

## 10. Data Model <a name="data-model"></a>

### File Structure
```
builds/videoask-reviewer/
├── server.js                  # Express server
├── index.html                 # Queue page
├── stats.html                 # Stats page
├── criteria.html              # Criteria page
├── history.html               # History page
├── data/
│   ├── queue.json             # Current unreviewed candidates
│   ├── reviewed.json          # Completed reviews (append-only)
│   ├── training-log.json      # Erica's feedback (append-only)
│   ├── criteria.json          # Current decision criteria + custom rules
│   ├── identity-cache.json    # Cached Zendesk/Retool search results
│   └── videoask-state.json    # Last-polled timestamp, processed contact IDs
├── scripts/
│   ├── pull-videoask.js       # Fetch new contacts from VideoAsk API
│   ├── evaluate.js            # Run AI evaluation on transcripts
│   ├── match-identity.js      # Search Zendesk/Retool for matches
│   └── generate-stats.js      # Compute training metrics
└── README.md
```

### Candidate Object
```json
{
  "id": "uuid",
  "videoask_contact_id": "f6d6c1bb-...",
  "videoask_share_url": "https://www.videoask.com/...",
  "name": "Oyanioye Eke",
  "email": "eke292@gmail.com",
  "phone": "+14044418433",
  "submitted_at": "2026-03-30T22:54:17Z",
  "platform": "mobile",
  "transcripts": {
    "q3_experience": "Hello, my name is Ayana...",
    "q4_location": "I am located in...",
    "q5_schedule": "I am flexible...",
    "q6_conflict": "I would handle...",
    "q7_why_great": "I believe I would..."
  },
  "ai_evaluation": {
    "market": "georgia",
    "city": "Atlanta",
    "drive_radius": "30 min",
    "experience_type": "formal",
    "experience_summary": "4+ years daycare, all ages to 14",
    "experience_years": "4",
    "availability": "flexible",
    "recommendation": "APPROVE",
    "confidence": "HIGH",
    "flag_reason": null,
    "note_text": "3/30 Hired. Atlanta GA, 30 min. 4+ years daycare, all ages to 14. Flexible schedule.",
    "reasoning": "Formal daycare experience, in-market, flexible availability"
  },
  "identity_match": {
    "zendesk": {
      "matched": true,
      "match_type": "exact",
      "profile_url": "https://upkid.zendesk.com/agent/users/...",
      "name_in_system": "Oyanioye Eke",
      "current_status": "Complete"
    },
    "retool": {
      "matched": true,
      "match_type": "exact",
      "profile_url": "https://upkid.retool.com/...",
      "name_in_system": "Oyanioye Eke",
      "current_status": "Complete"
    }
  },
  "review_status": "pending",
  "reviewed_at": null,
  "reviewed_by": null,
  "erica_action": null,
  "erica_decision": null,
  "erica_reason": null,
  "note_final": null
}
```

---

## 11. Integration Details <a name="integration-details"></a>

### VideoAsk API
- **Auth:** Production OAuth (client_id + client_secret) — PENDING
- **Polling schedule:** Every 30 min during business hours (8am-6pm MST, weekdays)
- **Endpoints used:**
  - `GET /forms/{form_id}/contacts?limit=50&offset=N` — list contacts
  - `GET /forms/{form_id}/contacts/{contact_id}` — contact detail + status
  - `GET /questions/{question_id}/answers?limit=50` — answers with transcripts
- **Rate limits:** Unknown, be conservative (1 req/sec)
- **Credentials location:** `~/credentials/videoask-token.json`

### Zendesk (Browser)
- **Access:** tyler.b@upkid.com browser login
- **Usage:** Search by email/phone → extract profile URL → display in candidate card
- **Implementation:** Generate search URLs like `https://upkid.zendesk.com/agent/search?q=email:eke292@gmail.com`
- **Alternative:** If we can get the Zendesk subdomain + search URL pattern, we can generate direct links without browser automation
- **Credentials location:** `~/credentials/zendesk-login.json` (if stored)

### Retool (Read Access)
- **Access:** tyler.b@upkid.com read-only
- **Usage:** Search by email/phone → extract profile URL + current status
- **Implementation:** Depends on what Retool exposes — may need browser search or may have a query interface
- **Credentials location:** `~/credentials/retool-login.json` (if stored)

### Slack
- **Already integrated** via OpenClaw
- **Usage:** Daily review summaries, alerts for overdue reviews, escalation messages
- **Channel:** TBD — could use Erica's DM or a dedicated #videoask-reviews channel

---

## 12. Decision Criteria Reference <a name="decision-criteria-reference"></a>

*This section is the living document that the AI evaluator uses. Updated based on Erica's training feedback.*

### APPROVE (HIGH confidence)
- Has formal childcare experience (daycare, preschool, classroom, para, sub, afterschool, Head Start, camp counselor) in any amount
- Located in Utah, Georgia, or Arizona
- Available part-time or full-time
- Willing to drive any reasonable distance
- Completed all VideoAsk questions with substantive answers

### APPROVE (MEDIUM confidence)
- Has formal childcare experience but limited (less than 1 year)
- Located in-market but in a less-served area
- Mixed experience (some formal, some informal)
- Schedule has some constraints but generally available

### FLAG (needs Erica's review)
- Only informal experience (babysitting, nannying, own children)
- Location unclear or borderline
- Short-term availability (summer only, leaving area)
- Relocating to the area (not there yet)
- Very brief transcript responses
- Conflict resolution answer is concerning
- Under-25 with minimal experience
- Out-of-market area code but claims to be in-market
- Arizona candidate with less than 6 months formal experience

### NEVER AUTO-DENY
- All potential denials are FLAGS
- Erica makes every denial decision personally
- Denial reasons are logged for training

### Market-Specific Rules
| Market | Minimum Experience | Special Considerations |
|---|---|---|
| Utah | Lenient — babysitting may qualify | Broader acceptance of informal experience |
| Georgia | Moderate — prefer formal experience | 1 year formal daycare is sufficient |
| Arizona | Strict — 6 months formal childcare | State DHS licensing requirements. No babysitting-only. |

### Erica's Custom Rules
*(This section grows as Erica trains the system)*

| Rule | Added | Source |
|---|---|---|
| *No rules yet — will populate during Phase 1 training* | | |

---

## 13. Edge Cases & How We Handle Them <a name="edge-cases"></a>

| Edge Case | How We Handle It |
|---|---|
| Teacher gave only audio, no video | Same as video — we use the transcript, not the visual |
| Transcript is garbled/unreadable | FLAG — "Poor transcript quality, needs human review" |
| Teacher answered in Spanish or another language | FLAG — "Non-English transcript, needs human review" |
| Teacher completed Q3 but skipped Q4-Q7 | FLAG — "Incomplete submission" |
| Teacher has 2 VideoAsk submissions (partial + complete) | Use the completed one, ignore the partial. Note "Has prior incomplete submission from [date]" |
| Email matches Zendesk but phone matches a different Retool record | Show both records, Erica picks. ⚠️ Multiple Matches. |
| Teacher not found in Zendesk or Retool | FLAG — "Not found in systems. May be new registration or different contact info." |
| Teacher says they're relocating TO one of the 3 markets | FLAG — "Relocating to [market], not currently there." Erica decides if timing works. |
| Teacher is a current Upkid teacher reapplying | Identity match should catch this (existing status ≠ "New Profile"). Show current status. FLAG — "Already in system as [status]." |
| Teacher mentions criminal history | FLAG — "Mentioned criminal history. Background check may be an issue." Never auto-deny. |
| Teacher is clearly a minor (mentions high school) | FLAG — "Possible minor. Erica to verify age." Never auto-deny. |
| Teacher has great experience but is in an unserved state (NJ, PA, TX) | FLAG — "Out of current markets but qualified. May be relevant for expansion." |
| VideoAsk API returns an error for a specific contact | Skip that contact, log the error, retry next cycle |
| AI evaluator returns unexpected output format | Use the raw transcript as the summary, mark as "AI evaluation failed" |

---

## 14. Rollout Plan <a name="rollout-plan"></a>

### Phase 0: Setup (1-2 days)
- Register VideoAsk developer app, get production OAuth
- Get Retool read access for tyler.b@upkid.com
- Get Zendesk access for tyler.b@upkid.com
- Set up project directory and server skeleton

### Phase 1: AI Reviewer — Read-Only (1 week build + 1-2 weeks training)
**Build:**
- Transcript puller (VideoAsk API → local queue)
- AI evaluator (transcripts → structured evaluation)
- Slack output (post summaries to test channel)

**Train with Erica (the first 20):**
- Pull 20 completed, unreviewed VideoAsk submissions
- Run AI evaluation on all 20
- Sit down with Erica (Slack thread or call): go through each one
- For each: "Here's what the AI thinks. What would you do? Why?"
- Log every agree/override/edit as training data
- Update decision criteria based on patterns

**Measure:**
- What's the agreement rate after 20?
- What are the common overrides?
- Are there criteria we're missing entirely?

### Phase 2: Smart Preparer Dashboard (1-2 weeks build)
**Build:**
- Web dashboard with candidate review cards
- Identity matching (Zendesk search + Retool search)
- Copy-to-clipboard for notes
- Direct links to profiles
- Feedback buttons
- Training log viewer + stats page

**Deploy to Erica:**
- Walk Erica through the tool (15-min Loom or live call)
- First week: Erica uses the tool alongside her normal process (belt and suspenders)
- Second week: Erica switches to tool-primary, falls back to manual only when needed

### Phase 3: Iterate (ongoing)
- Weekly: review training log, update criteria, fix UX issues
- Monthly: generate accuracy report, assess if MVP 3 discussion is warranted

---

## 15. Success Metrics <a name="success-metrics"></a>

| Metric | Phase 1 Target | Phase 2 Target | How We Measure |
|---|---|---|---|
| AI agreement rate | >85% | >92% | Training log: agrees / (agrees + overrides) |
| Review time per candidate | N/A (read-only) | <45 seconds avg | Timestamp between card open and "agree/override" click |
| Daily review capacity | Same as manual | 2-3x manual | Candidates reviewed per hour |
| Erica satisfaction | "This is useful" | "I can't go back to the old way" | Ask her |
| Backlog age | Same | <24 hours | Oldest unreviewed submission |
| False deny rate (by Erica, not AI) | Baseline | Trending down | Override rate where AI said APPROVE but Erica said DENY |
| Identity match rate | N/A | >80% exact match | Training log: exact matches / total reviews |
| Note edit rate | N/A | <20% | Training log: edits / total reviews |

---

## 16. Open Items <a name="open-items"></a>

### Credentials Needed
| System | What | Status | Notes |
|---|---|---|---|
| VideoAsk | Production OAuth | ❌ Pending | Tyler to register developer app |
| Zendesk | Browser access | ❌ Pending | Tyler to add tyler.b@upkid.com |
| Retool | Read/search access | ❌ Pending | Tyler to add tyler.b@upkid.com |

### Questions for Erica
1. When you search for a teacher in Zendesk, what do you search by? (email? name? phone?)
2. What's the Zendesk URL structure for a teacher profile? (need this to generate direct links)
3. What's the Retool URL structure for a teacher profile?
4. Are there teachers you approve who DON'T have any formal experience? What makes you say yes?
5. How often do you deny someone? Rough percentage?
6. Do you ever go back and change a decision after the fact?
7. Are there specific phrases in VideoAsk responses that are instant red flags?
8. How do you handle teachers who are clearly overqualified (master's in education, 20 years experience)?
9. Does the tone/energy of the video matter to your decision, or is it purely content-based?

### Questions for Drew
1. Does Retool have a direct URL to a specific teacher record? (e.g., retool.com/app/teachers/[id])
2. Is there a search endpoint or query we can use with read-only access?
3. Would it ever make sense to add a "reviewed by AI" field to the teacher record in Firestore?

---

*Document version 1.0 — March 30, 2026*
*Will be updated as credentials are obtained and Phase 1 build begins.*
