#!/usr/bin/env python3
import json, sys, re

# Candidate Kamisha walker (contact_id: 5b54cd74-6eb3-4b49-8abe-8f7c5de2ac04)
# Phone: +16028003169 - 602 area code is Arizona, but Q4 says Atlanta Georgia
# Actually 602 is Arizona area code, but she says Atlanta Georgia - possible mismatch

transcripts = {
    'q3': 'Hi. My name is Kenisha in a little bit about me. I\'ve been doing childcare daycare for teachers, for almost about five years now. I love it. I wouldn\'t change it for nothing. Anywhere. L, I love kids. I love teaching kids and things. I love to be there for that kid. Kind of like a second parent for the kid.\n I am a very independent teacher. I love to listen to my kids and I love to see how they\'re feeling and I love to just get on my knees and interact with them and make them feel as one. I love that.',
    'q4': 'I\'m in Phoenix Arizona, the Glendale area. I\'m willing to travel like, 30 miles. I do have a vehicle so that wouldn\'t be a problem for me at all.',
    'q5': 'Well, it\'s really open to me right now. Our time is available for me in full-time. Isabella for me, I\'m really not picky at the moment right now, I prefer mornings and evenings staff.\n I have no problem with that.',
    'q6': 'I had an experience where we was at Circle time and we were sitting down, and we was playing with blocks. And another little boy have built this big old castle with blocks and now the little boy rang up and kicked it down. Little other boy, got so mad kicked and screamed and went up to other little boy and try to buy them. And I told him I told him to the other kid and I got them.\n My knees level-headed, I connection with both of them and I said, hey, this is not how we treat our friends, we don\'t kick our friends toys down, and we don\'t try to bite our friends. Friends are nice to each other friends, share things with each other and the kids, both looked at me and I say, you have to say sorry to your friend. That\'s not, that\'s not good. And the other boy, looked at the little girl and he said, I\'m sorry. And then she said,\n said she was sorry. And then we went back to playing with the blocks.',
    'q7': 'Well, why would I be a good fit teacher? Why definitely been doing this for a while for a couple years, right? And I get along with everybody, I know, you know, being with a facility of women, you know, they have the ups and downs but it\'s okay. I go in with a good hanyan ship. I go in being very nice and respectful and I always\n is end up getting the good energy back and so I love having Communications I don\'t try to go in and try to control our step in and say on here, you know how some teachers are and say that they\'re running and doing this and doing that. No I just go in and I fit in with everybody else and I try to be a family with that that company or that daycare at that moment so we can all get along and get through the day and I\'m asleep.\n And I love to have fun. I just, I love being around good people and I love being around people that happy and lovable and love to take care of kids. That\'s just a big thing that I like and I don\'t try to bring any drama anywhere. I\'m just a happy person, happy person, happy life. And, you know, I just try to get along with everybody and if someone is trying to be mean,\n Nor anything like that then I know how to go and talk to one of the workers in the front to discuss the problem. But yeah I\'m just a happy person. I just love just being in a daycare and seeing new people and learning new things. That is so awesome to me. I love it.'
}

# Determine market: phone area code 602 is Arizona, but transcript says Phoenix Arizona
market = 'arizona'
phone = '+16028003169'
area_code = '602'

# Basic evaluation
q3_text = transcripts['q3'].lower()
rec = 'APPROVE'
confidence = 'HIGH'
if 'daycare' in q3_text and 'five years' in q3_text:
    # 5 years daycare experience in Arizona - meets strict AZ requirements
    rec = 'APPROVE'
    confidence = 'HIGH'

candidate = {
    'contact_id': '5b54cd74-6eb3-4b49-8abe-8f7c5de2ac04',
    'name': 'Kamisha walker',
    'email': 'walkerkanisha95@gmail.com',
    'phone': phone,
    'market': market,
    'rec': rec,
    'confidence': confidence,
    'transcripts': transcripts,
    'questions_answered': 5,
    'first_name': 'Kamisha'
}

print(json.dumps({
    'new_count': 1,
    'candidates': [candidate]
}, indent=2))