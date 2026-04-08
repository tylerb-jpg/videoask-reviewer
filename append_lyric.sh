#!/bin/bash
cd /Users/tylerbot/.openclaw/workspace-videoask-reviewer
export GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-write

# Read the AI summary from file
AI_SUMMARY=$(cat summary-lyric.md)

# Build the row JSON
ROW_JSON='[
  [
    "FALSE",
    "FALSE",
    "20261-04-06",
    "🟢 Lyric Ransom",
    "GA",
    "✅ HIGH",
    "=HYPERLINK(\"https://app.videoask.com/app/organizations/3f29b255-68a4-45c3-9cf7-883383e01bcc/form/c44b53b4-ec5e-4da7-8266-3c0b327dba88/conversation/5080b089-e68b-43bb-a9e8-177f4299c5d2\", \"▶️ Watch\")",
    "Lyric",
    "HElTm8lVPsYxYUybwTYzGeZ0IXD3",
    "ranlyric@gmail.com",
    "(614) 900-3589",
    "=HYPERLINK(\"https://upkid.zendesk.com/agent/search/1?q=ranlyric@gmail.com\", \"🔍\")",
    "04/06 Intro Call Passed. Atlanta, GA, 30-40mi. Formal experience: classroom aide in inclusive classroom, current work at Marcus Autism Center with research on culturally appropriate interventions. Part-time Tuesdays/Thursdays, expanding to Wednesdays/Fridays in May. Strong conflict resolution focused on understanding \"why\" behind behaviors.",
    "04/06 Not Hiring — Intro Call. Atlanta, GA. N/A (approved candidate)",
    "See transcript",
    "Atlanta, GA, 30-40mi",
    "Flex",
    "'"${AI_SUMMARY}"'",
    "",
    "Hello, my name is lyric, Ransom and I really enjoyed working with children because I love seeing them develop and grow into their own people, and really just being and helping stepping stone in their life is really important to me as a black woman. I understand the importance of pouring into communities. I look like myself and other marginalized children and that is one of the main reasons why I want to continue work with kids, to be representation to them, and to provide them with assistance, with understanding and navigating life. I\"m as far as my experience with\n Remove children. While in undergrad. I worked with children in an inclusive classroom where I was working as a classroom aide, and I was helping out with transitions. I was helping out with feeding and then just other social, emotional learning, programs, to better support children with different support needs within the classroom. And now, I currently work at the Marcus Autism Center where I am currently looking at different research outlets and really understanding the best ways to make our interventions more, culturally appropriate and affirming.\n And so yes I really hope to be a part of this program to get a more hands-on experience of the classroom understanding how we can spur our kids better especially on your diverse children in our marginalized children. Thank you.",
    "Hello. I\"m currently in Atlanta Georgia and I live between Midtown and Buckhead and I\"m willing to travel anywhere between 30 to 40 minutes as far as a commute as far as the further said I\"m willing to travel. Thank you.",
    "Hello, I\"m wanting to work part, time shifts, currently right now my bell ability is Tuesdays and Thursdays but starting the second week of May, I\"ll be also available on Wednesdays and Fridays. And so I would appreciate starting off Tuesdays and Thursdays. And then again, that second week of May, I\"ll be available on both Wednesdays and Fridays as well. So that\"s my general availability for now. Thank you.",
    "For me, when it comes to conflict, my biggest thing is understanding the why? So in a situation in which a kid puts their hands on another kid, my first thought is kind of understanding again. Why did that occur? And what ways can I as the dot mediate that situation? So is the thing of the kids had an exchange of words, is it a thing of one of the kids were triggered by something really understanding what really caused the commotion and then understanding the best ways to a mediate that and then also\n Speaking, with the kid, who initiated the contact, so really trying to help them navigate understand their emotions. So that next time, they can verbalize it to me, rather than feeling like they had to put matters into their own hands. And then understand the school\"s policy around things like putting hands on each other or things of that nature to understand the best ways as far as discipline that is appropriate. But then also is actually helpful in the future in terms of making sure that the behavior does not occur again and that the kid feels supported in terms,\n Up next time feel like they can verbalize their their frustrations rather than again putting their hands on the other student. So yes, that\"s how I would mediate that conflict.",
    "I think I will make a great up kid teacher because I love working with children. I work with children and for the majority of my career and I\"m also a big sister of three younger sisters that ranges from ages, 15 all the way to 5. So I\"ve been around kids, all of my life and I just love seeing them develop and grow and then also living in metro Atlanta and realizing how Diversified not only our families. Our but then also our kiddos, I think it\"s so important to have representation within the classrooms whether that\"s Hands-On or kind of\n Behind the scenes but just allowing it supporting kids of different backgrounds. Just so important to me and then also just figuring out ways to help support the community. So I love the flexibility of the shifts. The fact that they\"re posted on a daily basis or weekly basis, I think it\"s really helpful and if any ways I can help my community, I will take advantage of the opportunity. I\"m so I think it\"s just a great opportunity to be involved in community and then also just working with kids, it\"s just so important to me.\n You. So that\"s why I think I\"ll be a great fit for this position."
  ]
]'

echo "Appending row to sheet..."
gws sheets +append \
  --spreadsheet 1ySI_0RG9HIZKIdNCtfqW_gZ_U0VGIxAGkog9Nhnt2Y0 \
  --json-values "$ROW_JSON"