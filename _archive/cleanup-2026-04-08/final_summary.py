#!/usr/bin/env python3
import json, sys, os

print("📊 Processed 2 new VideoAsk submissions: 1 approved, 1 flagged.")

# Check if we can send to Slack channel C0AQQ2LBTKJ
print("\nSlack summary message ready:")
print("'📊 Processed 2 new VideoAsk submissions: 1 approved, 1 flagged.'")
print("Channel: C0AQQ2LBTKJ (VideoAsk Reviews)")

# Also show what we processed
print("\nCandidates processed:")
print("1. Stephanie Price — ✅ APPROVE (HIGH) | Arizona | 2026-04-06")
print("   'Stephanie has a strong progression from babysitting to paraprofessional work in special education classrooms, with additional training as a behavior technician for ABA therapy. Her commitment to childcare as a 'calling' and clear articulation of conflict resolution strategies make her a standout candidate for Arizona. She's willing to drive 20 miles from Tucson with full-time open availability.'")
print()
print("2. Destiny Scott — 🟡 FLAG (MEDIUM) | Georgia | 2026-04-06")
print("   'Destiny is an enthusiastic 18-year-old with 2 years of childcare experience (likely informal) who is pursuing a science degree. Her genuine passion for working with children and willingness to drive up to 20 miles from East Point, GA are positives, but her young age and lack of formal childcare experience make this a judgment call for Erica given Georgia's preference for formal experience.'")