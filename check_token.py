import json
import datetime
import sys

token_path = '/Users/tylerbot/credentials/videoask-token.json'
with open(token_path) as f:
    data = json.load(f)
    
obtained = datetime.datetime.fromisoformat(data['obtained_at'].replace('Z', '+00:00'))
expires = obtained + datetime.timedelta(seconds=data['expires_in'])
now = datetime.datetime.now(datetime.timezone.utc)

print('obtained:', obtained)
print('expires:', expires)
print('now:', now)
print('valid for:', expires - now)
print('expired:', now > expires)
print('access_token present:', 'access_token' in data)
sys.exit(0 if not (now > expires) else 1)