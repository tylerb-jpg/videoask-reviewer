# VideoAsk Reviewer — Test Results

**Run:** 2026-03-30 21:22:14 MDT
**Total:** 27 tests | ✅ 27 passed | ❌ 0 failed | ⏭️ 0 skipped

## Results

| Status | Test | Detail |
|---|---|---|
| ✅ | VideoAsk token file exists | /Users/tylerbot/credentials/videoask-token.json |
| ✅ | VideoAsk access_token present | Token length: 1059 chars |
| ✅ | VideoAsk token not expired | 21.7h remaining |
| ✅ | BigQuery credentials exist | /Users/tylerbot/credentials/bigquery-tyler-bot.json |
| ✅ | bq CLI available | This is BigQuery CLI 2.1.30 |
| ✅ | VideoAsk OAuth config (client_id + secret) | Present |
| ✅ | All workspace files present | AGENTS.md, SOUL.md, criteria.json, state, list, spec |
| ✅ | VideoAsk API — list forms | HTTP 200 |
| ✅ | VideoAsk API — fetch intro call form | 'Intro Call - Upkid Teacher' |
| ✅ | VideoAsk API — list contacts | 3 contact(s) returned |
| ✅ | VideoAsk API — Q3 answers (experience) | HTTP 200 |
| ✅ | Answers have transcription data | 1142 chars |
| ✅ | Answers have contact matching fields | contact_id,contact_email,contact_name |
| ✅ | All 5 question endpoints accessible | Q3-Q7 all HTTP 200 |
| ✅ | BigQuery — query users table | Got rows from firestore_sync.users |
| ✅ | BigQuery — query teachers table | Got rows from firestore_sync.teachers |
| ✅ | BigQuery — identity search by email | 1 match(es): Oyanioye Eke |
| ✅ | BigQuery — identity search by phone | 1 match(es) |
| ✅ | BigQuery — teachers onboarding fields | 4/4 key fields present |
| ✅ | E2E — find candidate in VideoAsk | contact=f6d6c1bb-1913-4085-99db-7cd5551dd2fa, name=Oyanioye Eke, Q3=330 chars |
| ✅ | E2E — pull all 5 transcripts | 5/5 have content (Q3:✅ Q4:✅ Q5:✅ Q6:✅ Q7:✅ ) |
| ✅ | E2E — BigQuery identity match | 🟢 exact — Oyanioye Eke (eTRCMOWqG4geb50LQElERhBs4xi2) |
| ✅ | E2E — teacher record + onboarding | market=georgia interviewed_GA=None jobs=None created=2026-03-30 |
| ✅ | criteria.json valid | 18 rules across 3 tiers |
| ✅ | videoask-state.json valid | form_id ✓, org_id ✓, 0 processed |
| ✅ | Master review list structure | 3/3 sections, 408 lines |
| ✅ | Phone area code → market mapping | 404→georgia, 801→utah, 480→arizona (hardcoded in AGENTS.md) |

## Sections

1. **Credentials & Config** — token files, bq CLI, OAuth, workspace files
2. **VideoAsk API** — forms, contacts, answers, transcriptions, all 5 questions
3. **BigQuery** — users table, teachers table, email/phone search, onboarding fields
4. **End-to-End Pipeline** — full candidate flow: VideoAsk → transcripts → BQ match → teacher record
5. **Data Integrity** — criteria.json, state file, master list, area code mapping
