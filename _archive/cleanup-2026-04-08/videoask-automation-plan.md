# VideoAsk Review Automation — Project Plan

**Created:** March 30, 2026
**Owner:** Tyler
**Key Stakeholders:** Erica (primary reviewer), Kinsey (secondary reviewer)
**Status:** Planning

---

## Problem Statement

Erica and Kinsey manually review every VideoAsk teacher interview submission. Each review takes 2-3 minutes: watch/read transcript, make a hire/flag decision, update Zendesk notes, update Retool status, go back to VideoAsk and mark done. At 20-30 submissions/day, that's 60-90 minutes of manual work daily. The team was 5 days behind at peak volume.

The bottleneck isn't the decision — it's the repetitive process around it. Most teachers who complete the VideoAsk clearly qualify (experience + in-market + available). The automation should handle the obvious cases and surface the edge cases for human judgment.

## Project Philosophy (from Tyler, Mar 30)

**Even if we never reach full automation, making Erica's review process faster is worth it.** The goal is not to remove Erica from the process — it's to remove the tedious parts (watching videos, looking up records in Zendesk, manually typing notes in Retool, switching between 4 tabs) so she can focus on judgment calls.

A tool that shows Erica a pre-built candidate summary, pre-matched identity, and pre-written notes — where she just confirms or edits — would cut her review time from 2-3 minutes to 15-20 seconds per teacher. That alone saves 50-70 minutes/day.

**The AI review is a bonus on top, not the core value.** The core value is the workflow tool. The AI just makes the workflow tool smarter over time.

---

## Current Manual Workflow (from Erica's Loom walkthrough)

1. Open VideoAsk submission
2. Watch video or read auto-generated transcript
3. Evaluate:
   - Does this person have childcare/classroom experience?
   - What market are they in? (identified by phone area code or stated location)
   - What's their drive radius?
   - Are they available part-time or full-time?
   - Any red flags?
4. Go to **Zendesk** → look up the teacher → click "Interviewed/Reviewed"
5. Go to **Retool** (connected to Zoho) → add notes:
   - Date
   - Decision: "Hired" or flagged
   - Location + drive radius
   - Experience summary
   - Change teacher status to "intro call past"
6. Go back to VideoAsk → mark submission as done (purple dot clears)
7. Move to next submission

**Systems touched per review:** VideoAsk → Zendesk → Retool/Zoho → back to VideoAsk

---

## What We Know About the API

### VideoAsk API (confirmed via live testing)
- **Form ID:** `c44b53b4-ec5e-4da7-8266-3c0b327dba88`
- **Organization ID:** `3f29b255-68a4-45c3-9cf7-883383e01bcc`
- **823 total contacts** as of Mar 30
- **7 questions** in the form (see appendix)
- **All audio/video responses auto-transcribed** — transcripts available via API
- **Webhooks available:** `form_response_transcribed` fires when submission + transcription complete
- **Auth:** Temp tokens (2hr) for testing; production OAuth requires registering a developer app
- tyler.b@upkid.com added as VideoAsk user (Mar 30)
- **API docs:** https://developers.videoask.com/

### Systems We Need to Integrate
| System | What We Do There | API Status | Risk Level |
|---|---|---|---|
| **VideoAsk** | Read transcripts, mark as reviewed | API confirmed, tested | Low |
| **Zendesk** | Mark teacher as "Interviewed/Reviewed" | Need API access | Medium — wrong status update affects teacher pipeline |
| **Retool / Zoho** | Add notes, change teacher status to "intro call past" | Need to understand connection | High — this is the source of truth for teacher status |
| **Slack** | Notify Erica/Kinsey of results | Already integrated | Low |

### Open Questions — ANSWERED (Mar 30, Tyler)
- [x] **How does Retool connect?** Retool is a UI layer on BigQuery. Edit access is restricted. We are read-only on BigQuery (tyler.b@upkid.com). ⚠️ This means we likely can't write to Retool's data directly — need to understand the write path (does Retool write to Firestore which syncs to BQ? Or does it write to BQ directly?)
- [x] **What happens when "intro call past" is set?** It marks completion in the app. If the teacher has completed everything else, it allows them to start working shifts. It also triggers a Zoho text to the teacher. **⚠️ FALSE APPROVES HAVE REAL CONSEQUENCES — teacher gets a text and may be cleared to work.**
- [x] **What happens when a teacher is denied?** Sends an email AND text to the teacher saying they were not approved. **⚠️ FALSE DENIES ARE THE HIGHEST-RISK FAILURE MODE — teacher gets a rejection message, may never come back. Extremely hard to recover from.**
- [x] **Are decision criteria market-specific?** Yes. Arizona is stricter (6 months formal childcare). Utah is more lenient. Georgia in between.
- [x] **AI interview transition?** AI interviews are still far out from replacing VideoAsk. This automation is worth building even if we only get to MVP 2 (making Erica's review faster without full automation).

### Still Open
- [x] **Full teacher status list** — ANSWERED (Mar 30, see below)
- [ ] What does "marking done" in VideoAsk actually do? Tag? Status? Just UI?
- [x] **Write path** — NO direct API write access to Retool or Zendesk. Instead: give Tyler Bot read/search access to Retool, and browser access to Zendesk. Erica does the actual clicks. (Mar 30)
- [ ] Does Erica update Zendesk AND Retool independently, or does one sync to the other?

### Teacher Status Pipeline (confirmed Mar 30)
```
New Profile → Complete → Intro Call Scheduled → Intro Call Passed → Background Check Submitted → Ready to Work → First Shift Scheduled → First Shift Complete
                                                    ↘ Not Hiring (intro call)
                                                    ↘ No Show
```

**Status definitions:**
| Status | What It Means | Triggered By |
|---|---|---|
| New Profile | Teacher created account in app | Self-registration |
| Complete | Profile filled out | Teacher completes profile |
| Intro Call Scheduled | VideoAsk or interview booked | Zoho/scheduling |
| **Intro Call Passed** | **← THIS IS WHAT WE'RE AUTOMATING** | Erica marks in Retool after VideoAsk review |
| Not Hiring (intro call) | Denied at interview stage | Erica marks — triggers rejection email + text |
| No Show | Didn't show up for scheduled call | Erica marks |
| Background Check Submitted | Passed interview, BG check initiated | Automatic after "intro call passed" + other requirements |
| Ready to Work | All checks passed, can pick up shifts | System |
| First Shift Scheduled | Booked first shift | Teacher action |
| First Shift Complete | Worked first shift | System after shift completion |

**⚠️ Critical insight:** "Intro Call Passed" is the gate between "candidate" and "entering the workforce pipeline." Everything after it (background check, ready to work) is mostly automatic. This is the most important human judgment point in the entire teacher journey.

### Access Model (confirmed Mar 30)
| System | Access Level | How We Use It |
|---|---|---|
| **VideoAsk** | API (production OAuth when registered) + browser | Read transcripts, mark as reviewed |
| **Zendesk** | Browser only (no API) | Search for teacher, Erica clicks status changes |
| **Retool** | Read/search access (no write) | Search for teacher profile, Erica clicks status changes in the UI |
| **Slack** | Full API | Notifications, summaries, candidate cards |

**This means: NO automated writes to any teacher-facing system. The tool reads and recommends. Erica executes.**

---

## Key Features

### Feature 1: AI Transcript Review
**What:** Read VideoAsk transcripts and extract structured data + make a recommendation
**Inputs:** Q3 (experience), Q4 (location), Q5 (schedule), Q6 (conflict resolution), Q7 (why great teacher)
**Outputs:**
- Name
- Experience type + years (formal classroom, para, daycare, babysitting, afterschool, etc.)
- Market (Utah, Georgia, Arizona, or out-of-market)
- City + drive radius
- Availability (part-time, full-time, specific schedule constraints)
- Recommendation: APPROVE / FLAG / DENY
- Confidence level: HIGH / MEDIUM / LOW
- Reason summary (one line, matches Erica's note format)

### Feature 2: Erica Training Loop (Permanent, Not Just Onboarding)
**What:** A persistent feedback mechanism where Erica trains the AI on every review — not just the first 20, but forever. The system gets smarter over time but Erica always has the ability to correct and teach.

**How it works:**

**On every single candidate review, Erica can:**
1. ✅ **Agree** — AI got it right. One click. Logged as positive training signal.
2. ❌ **Override** — AI got it wrong. Erica selects the correct decision AND writes a brief reason:
   - "Deny — only worked with elderly, not children"
   - "Approve — church nursery counts as formal experience in Utah"
   - "Flag — says she's relocating but hasn't moved yet"
3. ✏️ **Edit Notes** — AI summary was close but not quite right. Erica corrects the note text. The diff is logged.
4. 🏷️ **Add Criteria** — Erica can tag a review with a new rule:
   - "CNA experience = not childcare"
   - "Military base teacher = always approve"
   - "Less than 3 months experience in AZ = deny"
   These get added to the decision criteria reference and the AI incorporates them going forward.

**Training phases:**
- **Phase 1 (first 20 reviews):** Erica and Tyler Bot do them together. Every candidate gets a detailed walkthrough: here's what the AI thought, here's what Erica thinks, here's why. This builds the initial training set.
- **Phase 2 (ongoing):** Every review Erica does through the tool is a training signal. Agrees reinforce the criteria. Overrides refine them. The AI prompt evolves based on accumulated feedback.
- **Phase 3 (mature):** The tool shows Erica its confidence AND why: "Approving because: 5 years daycare experience (formal), located in Atlanta (GA market), flexible schedule. Similar to candidates #47, #89, #112 that you approved." Erica can verify the reasoning, not just the output.

**Feedback storage:**
- All feedback stored in a local training log: `builds/videoask-reviewer/training-log.json`
- Each entry: timestamp, candidate name, AI recommendation, Erica's decision, reason, any new criteria added
- Periodically: Tyler Bot reviews the log, identifies patterns, updates the AI evaluation prompt
- The training log IS the institutional knowledge — if Erica is out sick, the log captures her decision patterns

**Why "always trainable" matters:**
- New markets might open (NJ, PA, TX) with different requirements
- Upkid's standards might change over time
- Erica learns new patterns herself as she reviews more candidates
- The tool should grow with the team, not be a static ruleset

### Feature 3: Zendesk Status Update
**What:** Automatically mark the teacher as "Interviewed/Reviewed" in Zendesk
**Risk:** If we mark the wrong person or mark someone who should have been denied, it moves them forward in the pipeline incorrectly
**Safeguard:** Only auto-update Zendesk for HIGH confidence APPROVE decisions. Everything else waits for Erica's confirmation.

### Feature 4: Retool/Zoho Note Writing
**What:** Automatically add the review notes in Erica's format and update teacher status
**Note format:** `[DATE] Hired. [CITY], [DRIVE RADIUS]. [EXPERIENCE SUMMARY].`
**Example:** `3/30 Hired. Draper, 20 min. Worked as a sub and para in Germany. Babysitting experience.`
**Risk:** Writing to the wrong teacher record, or writing notes that are inaccurate
**Safeguard:** Match on email + phone number (double verification). Don't write until Erica confirms (in MVP).

### Feature 5: VideoAsk Completion Marking
**What:** Mark the submission as "done" in VideoAsk so the purple dot clears
**Risk:** Low — this is UI bookkeeping, not pipeline-affecting
**Implementation:** Likely via tagging the contact or updating their status

### Feature 6: Real-Time Webhook Processing
**What:** Process new submissions automatically as they come in (vs. batch)
**When:** Phase 2, after batch processing is validated
**Trigger:** VideoAsk `form_response_transcribed` webhook

---

## MVP Phases

### MVP 1: "AI Reviewer" — Read-Only + Slack Output
**Goal:** Prove the AI can make the same decisions Erica makes, without touching any systems.
**What it does:**
1. Pull the last N unreviewed VideoAsk submissions via API
2. Read transcripts for Q3-Q7
3. Run AI evaluation against decision criteria
4. Post results to a dedicated Slack channel:
   - ✅ APPROVE (HIGH confidence): Name, location, experience, recommended note text
   - 🟡 FLAG (needs review): Name, what's unclear, link to VideoAsk submission
   - ❌ DENY (clear disqualifier): Name, reason

**What it does NOT do:**
- Does NOT update Zendesk
- Does NOT update Retool/Zoho
- Does NOT mark anything in VideoAsk
- Does NOT make any irreversible changes

**Testing:** Run against 20-30 submissions Erica has already reviewed. Compare AI decisions vs. Erica's actual decisions. Target: 90%+ agreement rate before moving to MVP 2.

**Erica's role:** Reviews AI output daily, marks agreements and overrides. Helps refine criteria.

### MVP 2: "Smart Preparer" — AI Reads, Erica Clicks
**Goal:** AI does the review and prep work. Erica reviews a pre-built summary and clicks status changes in the actual systems (Zendesk + Retool). No automated writes.

**Why this approach:** Tyler confirmed no direct API write access to Zendesk or Retool. But this is actually BETTER — it eliminates the entire category of "wrong-person write" and "accidental denial" risks. The tool reads and recommends. Erica executes.

**What it does:**
1. Everything from MVP 1 (AI transcript review)
2. For each candidate, the tool shows a **Candidate Review Card**:

   **Section A — AI Summary:**
   - Name, phone, email (from VideoAsk)
   - Experience summary (extracted from transcript)
   - Market + city + drive radius
   - Availability (part-time/full-time, schedule notes)
   - AI recommendation: APPROVE / FLAG + confidence + reason
   - **Pre-written note text** (copy-paste ready, in Erica's exact format)
   - Example: `3/30 Hired. Augusta GA, 30 min. 4 years daycare experience, all ages to 14. Flexible schedule.`

   **Section B — Identity Lookup:**
   - Tool searches Zendesk (via browser automation or search link) for the teacher by email/phone
   - Tool searches Retool (via read access) for the teacher by email/phone
   - Shows what it found:
     - 🟢 **Found in both** — shows links to both profiles (clickable, opens in new tab)
     - 🟡 **Found in one but not the other** — shows what it found + flags the mismatch
     - 🔴 **Not found** — Erica manually searches
     - ⚠️ **Multiple possible matches** — shows all, Erica picks the right one
   - Each match shows: name, current status, phone, email, last activity
   - **Direct links:** "Open in Zendesk" / "Open in Retool" buttons

   **Section C — Erica's Actions:**
   - 📋 **Copy Notes** — copies the AI-generated note text to clipboard
   - 🔗 **Open in Zendesk** — opens the teacher's Zendesk profile in a new tab
   - 🔗 **Open in Retool** — opens the teacher's Retool profile in a new tab
   - 🔗 **Listen in VideoAsk** — opens the original submission
   - ✅ **Mark Reviewed** — marks this candidate as done in the tool's queue
   - ⏭️ **Skip** — come back later
   - 🚩 **Flag for Tyler** — escalates edge case

3. Erica's workflow becomes:
   ```
   Read summary (5 sec) → Copy notes (1 click) → Open Zendesk (1 click) → 
   Paste notes + click status (10 sec) → Open Retool (1 click) → 
   Paste notes + click status (10 sec) → Mark reviewed (1 click)
   Total: ~30 seconds vs. 2-3 minutes
   ```

**Why this is still a massive win without API writes:**
- **No more watching videos** — AI summary replaces this entirely
- **No more searching for records** — tool pre-finds the teacher in Zendesk and Retool
- **No more typing notes from scratch** — copy-paste the AI-generated notes
- **No risk of wrong-person writes** — Erica sees the actual profile before clicking anything
- **Erica retains full control** — she's clicking buttons in the real systems, not approving an automation

**What changes from MVP 1:**
- Retool read/search access integrated
- Zendesk browser search integrated (or search link generation)
- Review queue with candidate cards (web dashboard, similar to CEO kanban board)
- Copy-to-clipboard functionality for notes
- **Time per review drops from 2-3 min to ~30 seconds**

**Safeguards:**
- Tool never writes to any system — zero risk of automated errors
- Erica sees the actual Zendesk/Retool profile before making any changes
- Every review is logged (who, when, what recommendation, what Erica did)
- Daily summary: "Reviewed 25 teachers: 20 approved, 3 flagged, 2 skipped"

### MVP 3: "Full Automation" — Future State (requires write access)
**Goal:** Clear approvals process automatically. Only exceptions reach Erica.
**Status:** NOT in scope until Retool/Zendesk write access is granted.

**What it would do (if we ever get there):**
1. HIGH confidence APPROVE → auto-updates Zendesk + Retool + VideoAsk (approvals only, never denials)
2. MEDIUM confidence → posted to review queue for Erica's one-click confirm
3. LOW confidence or potential DENY → flagged for full human review
4. Daily summary: "Processed 25 submissions: 18 auto-approved, 5 confirmed by Erica, 2 flagged for review"

**Prerequisites before even discussing:**
- [ ] MVP 2 running for at least 4 weeks (extended from 2 — higher bar given downstream consequences)
- [ ] AI agreement rate consistently >97% (raised from 95% — status changes trigger texts + clear for shifts)
- [ ] Erica explicitly comfortable with auto-approve
- [ ] Tyler and Drew approve write access
- [ ] Undo/rollback process tested and working
- [ ] False deny rate at 0% (non-negotiable — denials are ALWAYS human-only)

**Realistic assessment:** MVP 2 ("Smart Preparer") may be the permanent end state, and that's fine. If Erica can review 25 teachers in 12 minutes instead of 75 minutes, that's a 5x improvement without any automation risk. MVP 3 only makes sense if volume grows past what the Erica-assisted model can handle.

---

## Decision Criteria (Initial — Erica will refine)

### Auto-Approve (HIGH confidence)
- Has formal childcare experience: daycare, preschool, classroom teacher, para, substitute teacher, afterschool program, Head Start, camp counselor
- Located in Utah, Georgia, or Arizona (confirmed by stated location or phone area code)
- Willing to drive reasonable distance (any stated willingness)
- Available part-time or full-time
- Completed all VideoAsk questions

### Flag for Review (MEDIUM confidence)
- Only informal experience (babysitting, nannying, own children — no formal setting)
- Location unclear or borderline (e.g., near state border, rural area)
- Short-term availability mentioned (summer only, leaving soon)
- Relocating to the area
- Very brief or unclear transcript responses
- Conflict resolution answer raises minor concerns

### Deny (LOW confidence / clear disqualifier)
- No childcare experience at all
- Clearly out of market (different state, no plans to relocate)
- Under 18 / still in high school
- States they can't pass a background check
- Major red flags in conflict resolution answer

### What We Don't Know Yet (Erica needs to teach us)
- What subtle signals does Erica pick up that aren't in the criteria above?
- Are there specific phrases or patterns that are instant approvals or denials?
- How does she weigh babysitting-only candidates? (Seems like Utah is more lenient?)
- Does the quality of the video/audio matter (engagement, professionalism)?
- Are there specific center types or programs that qualify differently?

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| AI approves unqualified teacher | Teacher enters pipeline, bad experience for centers | Medium | MVP 1-2 have human confirmation. Erica trains the criteria. |
| AI denies qualified teacher | Lost teacher supply, missed revenue | Medium | All denials reviewed by Erica in MVP 1-2. "Denied" teachers can be rescued. |
| Wrong person updated in Zendesk/Retool | Incorrect teacher status, pipeline confusion | Low | Double-match on email + phone. Audit log. Undo capability. |
| Zendesk/Retool API breaks or changes | Writes fail silently | Low | Error alerts to Slack. Retry logic. Manual fallback. |
| VideoAsk API token expires | Batch processing stops | Medium | Production OAuth with refresh tokens (not temp tokens). |
| Erica doesn't trust the AI | Reverts to manual process, automation unused | Medium | Start read-only (MVP 1). Show accuracy stats. Let Erica control the pace. |
| AI interviews replace VideoAsk entirely | Automation becomes unnecessary | Low (short-term) | Build modularly — the AI review logic can apply to any transcript source. |

---

## Technical Architecture (Draft)

```
VideoAsk API ──→ Transcript Puller ──→ AI Evaluator ──→ Decision Engine
                                                              │
                                     ┌────────────────────────┤
                                     │                        │
                                     ▼                        ▼
                              Slack Notification         System Updates
                              (Erica reviews)         (Zendesk + Retool)
                                     │
                                     ▼
                              Feedback Logger
                              (trains criteria)
```

### Components
1. **Transcript Puller** — Polls VideoAsk API (MVP 1-2) or receives webhook (MVP 3) for new submissions
2. **AI Evaluator** — LLM prompt with decision criteria, extracts structured data from transcripts
3. **Decision Engine** — Applies rules to AI output, assigns confidence level
4. **Slack Notifier** — Posts results with action buttons for Erica
5. **System Writer** — Updates Zendesk + Retool/Zoho on confirmed decisions
6. **Feedback Logger** — Records Erica's overrides, tracks accuracy over time

### Where It Runs
- OpenClaw cron job or webhook handler
- Could be a dedicated agent (like the EA agent) or part of main agent

---

## Credentials & Access Needed

| System | What We Need | Status |
|---|---|---|
| VideoAsk | Production OAuth (client_id + client_secret) | ❌ Need to register developer app |
| VideoAsk | tyler.b@upkid.com user access | ✅ Added Mar 30 |
| Zendesk | API token or OAuth credentials | ❌ Need from Erica/Tyler |
| Retool | API access or understand Zendesk→Zoho sync | ❌ Need to investigate |
| Zoho | API token (if updating directly) | ❌ Need from Kinsey |
| Slack | Already connected | ✅ |

---

## Success Metrics

| Metric | MVP 1 Target | MVP 2 Target | MVP 3 Target |
|---|---|---|---|
| AI vs. Erica agreement rate | >90% | >95% | >97% |
| Time per review (Erica) | Same (read-only) | <15 sec (click confirm) | 0 sec (auto) for clear cases |
| Daily review capacity | Same | 3-5x current | Unlimited |
| Erica override rate | Baseline | <10% | <3% |
| False approve rate | Measure only | <5% | <2% |
| False deny rate | Measure only | <3% | <1% |

---

## Timeline (Tentative)

| Phase | Duration | Dependencies |
|---|---|---|
| MVP 1: Read-only AI reviewer | 1 week to build, 1 week to test | VideoAsk production OAuth |
| Erica training period | 2 weeks of daily feedback | Erica's time, Slack channel |
| MVP 2: Assisted writes | 1 week to build | Zendesk + Retool API access |
| MVP 2 validation | 2 weeks | Erica confirming daily |
| MVP 3: Full auto (if warranted) | 1 week to build | Tyler approval, proven accuracy |

---

## Appendix: VideoAsk Form Questions

| # | Title | Type | Question ID |
|---|---|---|---|
| 1 | Welcome | Button | `f752c5cb-8e4b-4f32-bd06-c4211c68a34b` |
| 2 | How Upkid Works | Poll (Yes) | `c9eb8339-81dd-4b72-bb09-32878bf076e0` |
| 3 | Tell us about yourself | Audio/Video | `4312c81f-5e50-4ee6-8ab0-0342b0cce53c` |
| 4 | Location | Audio/Video | `d796e231-caac-433f-be1e-4080793da124` |
| 5 | Schedule | Audio/Video | `f5e5b16d-4d2b-4b46-b2e6-caf7f3ab411f` |
| 6 | Conflict resolution | Audio/Video | `9eedc1d8-00d0-45c1-8366-a2a34111602e` |
| 7 | Why great teacher | Audio/Video | `2f9acb14-72d1-474c-a559-be5df35d6dd9` |

## Appendix: Sample Transcripts (from API)

**Q3 — Tell us about yourself (Ayana):**
> "Hello, my name is Ayana, a gay. And I have four plus years of working with children. I actually grew up in the daycare myself. I have experience working with all ages up to 14 years old..."

**Q4 — Location (Amber):**
> "I'm located in the Augusta, Georgia area."

**Q4 — Location (Jonesboro):**
> "I am located in Jonesboro Georgia, Clayton County."

---

## Pressure Testing — Holes & Hard Questions

### 🔴 Hole 1: Status changes have real downstream consequences — CONFIRMED
**Problem:** Setting "intro call past" does three things: (1) marks completion in the app, (2) if all other steps are done, clears the teacher to start working shifts, (3) triggers a Zoho text to the teacher. This means a false approve isn't just a data error — it's a text message to a teacher and potentially clearing them to work.

**Implication for the plan:**
- **MVP 3 (auto-approve) is much higher risk than initially scoped.** Auto-approving means auto-texting teachers and potentially auto-clearing them for shifts. We need near-perfect accuracy before turning this on.
- **MVP 2 (Erica confirms) is the right stopping point for now.** Even if AI is 99% accurate, the 1% that slips through gets a text they shouldn't get.
- **The "undo" capability is critical, not nice-to-have.** If we write to Zendesk/Retool and realize it was wrong, can we reverse the Zoho text? Probably not. The text is already sent.

**Revised safeguard:** In MVP 2, show Erica a preview of exactly what will happen: "This will mark [teacher] as 'intro call past' in Retool, which will trigger a text to [phone number] and may clear them to work shifts. Confirm?" Make the consequences visible, not hidden behind a button.

**Action still needed:** Get the complete status list. We know "intro call past" but what are the others? What does the full journey look like?

### 🔴 Hole 2: Retool is a UI on BigQuery — write path is unclear — PARTIALLY ANSWERED
**Problem:** Tyler confirmed Retool is a UI layer on BigQuery with restricted edit access. We have read-only BQ access (tyler.b@upkid.com). But the write path is still unclear.

**The data flow question:** When Erica changes a teacher's status in Retool, where does that write actually go?
- Option A: Retool → Firestore → BQ sync (Firestore is the source of truth, BQ is a read replica)
- Option B: Retool → BQ directly (BQ is the source of truth)
- Option C: Retool → Zoho → some other sync

**Why it matters for us:** We can't write to BQ (read-only access, and we should never write to production data per TOOLS.md rules). So we need to find the actual write endpoint. Options:
1. Write via Zendesk API and let the Zendesk→Zoho sync propagate
2. Write via Zoho API directly
3. Write via the same API Retool uses (probably Firestore)
4. Ask Drew to give us a dedicated write endpoint or webhook

**Action needed:** Ask Drew: "What API does Retool call when Erica updates a teacher's status? Is it writing to Firestore, Zoho, or BQ directly?"

### 🔴 Hole 3: Transcript quality is inconsistent
**Problem:** We saw in the sample transcripts that auto-transcription has errors. "Ayana, a gay" is probably "Ayana Agay" or similar. "Up kid" instead of "Upkid." These are minor, but what about:
- Heavy accents that produce garbled transcripts
- Background noise making transcriptions unreliable
- Teachers who give very short, one-word answers
- Teachers who respond in a language other than English

**What could go wrong:** AI makes a decision based on a bad transcript. Teacher says "I have 10 years of experience at a daycare" but the transcript says "I have ten years of experience at a day camp" — different qualification.

**Mitigation:** Include transcript quality as a confidence factor. If the transcript is very short, garbled, or has low-confidence words, auto-flag for human review. Never auto-deny based on a transcript alone.

### 🔴 Hole 4: Denials send rejection email + text — CONFIRMED, HIGH RISK
**Problem:** Tyler confirmed: denying a teacher sends an email AND text saying they were not approved. This is the single highest-risk failure mode in the entire system.

**Impact of a false deny:**
- Teacher receives a rejection email + text
- Teacher may never reapply (psychological impact of being told "you're not approved")
- Upkid loses a potential worker permanently
- No easy way to un-send the rejection message
- Reputational risk if the teacher tells others they were wrongly rejected

**Impact of a false approve:**
- Teacher gets a welcome text
- Teacher enters the pipeline but still has other gates (background check, etc.)
- Can be caught and corrected at the next step
- Teacher's experience is positive even if corrected later

**This means the system should STRONGLY BIAS toward approval.** When in doubt, approve and let the next step catch issues. Never auto-deny. Every denial should require Erica's explicit confirmation.

**Revised decision framework:**
- AUTO (MVP 3): Only approvals, never denials
- ERICA CONFIRMS (MVP 2): Approvals are one-click. Denials require Erica to type a brief reason before the rejection fires.
- FLAGS (all MVPs): "Probably deny" is always a flag, never an auto-action

**New rule: NO AI-initiated denials. Ever.** The AI can flag someone as "likely not qualified" but the deny button always requires a human click + reason. This is non-negotiable.

### 🟡 Hole 5: Duplicate/repeat submissions — CONFIRMED, COMMON
**Problem:** Tyler confirmed this is a real issue. Teachers often do a partial VideoAsk (one or two questions), then come back later and complete all questions. This creates multiple contact records for the same person.

**What could go wrong:**
- AI processes the same teacher twice, writes duplicate notes
- Erica already reviewed the partial submission and skipped it, then the AI picks up the complete one — good. But Erica might also have already approved the partial one.
- The identity matching gets confused by multiple VideoAsk records for the same email

**Mitigation:**
1. Before processing, deduplicate contacts by email + phone
2. If multiple submissions exist, use the most recent COMPLETED one (status = "completed")
3. Show Erica if there are prior submissions: "This teacher also has 2 incomplete submissions from [dates]"
4. Skip contacts with status != "completed" entirely (don't waste time on partials)

### 🟡 Hole 6: The "babysitting only" judgment call
**Problem:** Erica mentioned in her Loom that Utah is more lenient on experience requirements. Arizona requires 6 months of formal childcare experience. Georgia falls somewhere in between. Our decision criteria treats all markets the same.

**What could go wrong:** AI approves a babysitting-only candidate for Arizona (where they won't qualify for the state background check requirements) or denies a babysitting-only candidate for Utah (where they'd be fine).

**Action needed:** Decision criteria need to be market-specific. Build a market requirements matrix with Erica:
| Market | Minimum Experience | Special Requirements |
|---|---|---|
| Utah | ? | ? |
| Georgia | ? | ? |
| Arizona | 6 months formal childcare | AZ DHS licensing rules |

### 🟡 Hole 7: Incomplete submissions
**Problem:** What percentage of contacts complete all 7 questions vs. dropping off partway? The API showed contact statuses like "completed" but there might be "abandoned" or "partial" submissions too. If a teacher answers Q3 (experience) but drops off before Q4 (location), do we:
- Process with incomplete data and flag?
- Ignore entirely?
- Send a follow-up nudge?

**Action needed:** Check the data. How many of the 823 contacts have status "completed" vs. other statuses? What's the drop-off rate by question?

### 🟡 Hole 8: What is "experience" exactly?
**Problem:** Our criteria say "formal childcare experience" but teachers describe their experience in wildly different ways:
- "I worked at a daycare" — clear
- "I'm a certified teacher with a master's in education" — clear
- "I raised 5 kids" — own children, not professional
- "I volunteered at my church nursery for 3 years" — volunteer, not paid, but relevant
- "I worked at a summer camp" — seasonal, is this childcare?
- "I'm a CNA and worked with elderly patients" — care experience but not children
- "I have my CDA" — credential, but no stated work experience

**What could go wrong:** AI draws the line in the wrong place. Each of these edge cases might be an approve in one market and a flag in another.

**Action needed:** Get Erica to rank 20 real examples from easy approve to clear deny. Use these as the training set for the AI prompt. This IS MVP 1.

### 🟡 Hole 9: The AI Interview overlap
**Problem:** AI Interviews launched today (Mar 30). If VideoAsk is being phased out, the volume of new VideoAsk submissions should drop. But there's probably a backlog of unreviewed submissions AND a transition period where some teachers go through VideoAsk and others go through AI Interviews.

**Questions:**
- Will new teachers still be routed to VideoAsk, or only AI Interviews?
- Is there a cutover date?
- Do teachers who did VideoAsk also need to do AI Interviews, or is one enough?
- If VideoAsk is gone in 2 months, is MVP 2/3 even worth building? Maybe MVP 1 (batch process the backlog) + a lightweight Slack review tool is enough.

**Impact on scope:** If VideoAsk has 2-3 months of life left, we should build for the backlog cleanup + transition period, not for ongoing automation. This changes the ROI calculation significantly.

### 🟢 Hole 10: Where does this tool live?
**Problem:** The plan mentions "OpenClaw cron job or webhook handler" and "could be a dedicated agent" but doesn't decide. For MVP 2, Erica needs a UI with action buttons. Slack buttons work for simple approve/deny, but the Candidate Review Card (Section A + B + C) is too complex for a Slack message.

**Options:**
1. **Slack-only** — works for MVP 1. For MVP 2, we'd need Slack interactive messages with dropdowns for identity selection. Gets clunky fast.
2. **Web dashboard** (like the CEO kanban board) — better UX for the Candidate Review Card. Erica opens a page, sees the queue, clicks through. Could run on the same server as the kanban board.
3. **Retool app** — if Retool is already in Erica's workflow, building the review tool inside Retool keeps her in one place. But we'd need Retool development access.

**Recommendation:** Start with Slack for MVP 1 (notifications only). For MVP 2, build a simple web dashboard. Don't overcomplicate.

### 🟢 Hole 11: Volume and cost
**Problem:** We're calling an LLM for every submission. At 20-30/day × 5 questions each = 100-150 LLM calls/day. Using Claude for evaluation, each call is maybe 1-2K tokens in, 500 tokens out.

**Cost:** Roughly $0.50-$1/day. Negligible. Not a real concern.

**But:** If we ever batch-process the backlog of 823 contacts, that's ~4,000 LLM calls at once. Still only $20-30. Fine.

### 🟢 Hole 12: Erica adoption risk
**Problem:** The plan mentions "Erica doesn't trust the AI" as a risk, but the bigger risk is simpler: Erica doesn't use the tool. If it's easier to just watch the video and do it the old way than to learn a new tool, she'll default to her current process.

**Mitigation:**
- MVP 1 should require ZERO behavior change from Erica. She keeps doing her job normally. We just run the AI in parallel and show her the comparison.
- MVP 2 should be strictly easier than her current process. If she has to click through more screens or wait longer, it's a net negative.
- Get Erica's input on the tool design before building it. She knows her workflow better than we do.

---

## Revised Action Items (Priority Order)

### Answered ✅
1. ~~Map the full teacher status pipeline~~ — ✅ Done (Mar 30). 10 statuses mapped. "Intro Call Passed" is the key gate.
2. ~~Understand Retool's role~~ — ✅ Retool is UI on BigQuery. No write access for us. Read/search only.
3. ~~Map the denial flow~~ — ✅ Sends rejection email + text. Non-reversible. AI never auto-denies.
4. ~~Clarify VideoAsk → AI Interview transition~~ — ✅ AI interviews are long way out. VideoAsk automation is worth building.

### Before code — still needed:
5. **[ ] Get market-specific experience requirements** — What qualifies in each state? Get from Erica/Kinsey. (Can do alongside MVP 1 testing)
6. **[ ] Get Retool read/search access** — Tyler to add tyler.b@upkid.com or create a read-only role. Need to be able to search teachers by email/phone.
7. **[ ] Get Zendesk browser access** — Tyler to add tyler.b@upkid.com. Need to search + generate direct links to teacher profiles.
8. **[ ] Register VideoAsk developer app** — Production OAuth credentials. Tyler to do in Organization Settings > Developer Apps.
9. **[ ] Check completion rates** — How many of 823 contacts actually completed all questions? (Can do with temp token)

### Build MVP 1:
10. **[ ] Build AI transcript reviewer** — Pull VideoAsk transcripts, run evaluation, output to Slack
11. **[ ] Backtest against 20-30 submissions** — Compare AI decisions vs. what Erica actually did. This IS the training process — do it together with Erica.
12. **[ ] Iterate on decision criteria** — Based on Erica's feedback. Refine the prompt.

### Build MVP 2:
13. **[ ] Build review queue web dashboard** — Candidate Review Cards with AI summary + identity lookup + copy-paste notes + direct links to Zendesk/Retool profiles
14. **[ ] Integrate Zendesk search** — Auto-find teacher profile, generate direct link
15. **[ ] Integrate Retool search** — Auto-find teacher profile, generate direct link
16. **[ ] Deploy for Erica** — Train her on the tool, get daily feedback, iterate

### Maybe later:
17. **[ ] MVP 3: Auto-writes** — Only if/when write access is granted AND accuracy is proven over 4+ weeks

---

*This document will be updated as we progress through each MVP phase.*
