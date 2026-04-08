#!/usr/bin/env python3
import json, sys

# We found 3 new completed contacts
candidates = [
    {
        'contact_id': '5b54cd74-6eb3-4b49-8abe-8f7c5de2ac04',
        'name': 'Kamisha walker',
        'email': 'walkerkanisha95@gmail.com',
        'phone': '+16028003169',
        'market': 'georgia',  # 602 area code -> Georgia
        'rec': 'APPROVE',
        'confidence': 'HIGH',
        'transcripts': {
            'q3': 'Hi. My name is Kenisha in a little bit about me. I\'ve been doing childcare daycare for teachers, for almost about five years now. I love it. I wouldn\'t change it for nothing. Anywhere. L, I love kids. I love teaching kids and things. I love to be there for that kid. Kind of like a second parent for the kid.\n I am a very independent teacher. I love to listen to my kids and I love to see how they\'re feeling and I love to just get on my knees and interact with them and make them feel as one. I love that.',
            'q4': 'I currently live in Atlanta Georgia.\n and\n I\'m willing to travel. Not sure about how many miles because I don\'t have a car at the moment but I do use public transportation.',
            'q5': 'I\'m looking for part-time shifts.\n and\n if full time comes along, I\'m well willing to do full-time, but at the moment I\'m looking for part-time.',
            'q6': 'If I have a conflict between two children, I would separate them immediately.\n and\n I would talk to each individual child.\n and\n figure out what\'s going on and see how we can resolve the issue.',
            'q7': 'I think I will make a great up kid teacher because, as I said, I\'ve been doing child care for about five years now.\n and\n I\'ve worked with all age groups from infants all the way up to after school kids.\n and\n I love it.\n and\n I\'m just willing to work and to get back into the child care workforce.\n and\n I would love to be hired.'
        },
        'questions_answered': 5,
        'first_name': 'Kamisha'
    },
    {
        'contact_id': '56576cae-e46b-49c2-b82d-bf1d9e81cfa4',
        'name': 'Unknown',
        'email': 'Unknown',
        'phone': 'Unknown',
        'market': 'unknown',
        'rec': 'FLAG',
        'confidence': 'LOW',
        'transcripts': {
            'q3': '',
            'q4': '',
            'q5': '',
            'q6': '',
            'q7': ''
        },
        'questions_answered': 0,
        'first_name': ''
    },
    {
        'contact_id': '317cecdf-cb8d-426f-947c-c04c15d43a84',
        'name': 'Unknown',
        'email': 'Unknown',
        'phone': 'Unknown',
        'market': 'unknown',
        'rec': 'FLAG',
        'confidence': 'LOW',
        'transcripts': {
            'q3': '',
            'q4': '',
            'q5': '',
            'q6': '',
            'q7': ''
        },
        'questions_answered': 0,
        'first_name': ''
    }
]

# Only include first 2 candidates as per MAX_PER_RUN = 2
output_candidates = candidates[:2]

print(json.dumps({
    'new_count': len(output_candidates),
    'candidates': output_candidates
}, indent=2))