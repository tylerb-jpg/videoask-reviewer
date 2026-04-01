#!/usr/bin/env python3
"""
Refresh VideoAsk access token using the OAuth refresh_token grant.

Usage: python3 scripts/refresh-videoask-token.py [--force]
  --force: refresh even if current token hasn't expired yet
"""

import json
import os
import sys
import time
import calendar
import urllib.request

CREDENTIALS_DIR = os.path.expanduser("~/credentials")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "videoask-token.json")
OAUTH_FILE = os.path.join(CREDENTIALS_DIR, "videoask-oauth.json")
ORG_ID = "3f29b255-68a4-45c3-9cf7-883383e01bcc"


def is_token_valid(buffer_seconds=300):
    """Check if current token is still valid (with buffer)."""
    try:
        with open(TOKEN_FILE) as f:
            token = json.load(f)
        obtained = token.get("obtained_at", "")
        expires_in = token.get("expires_in", 86400)
        if obtained:
            obtained_ts = calendar.timegm(time.strptime(obtained[:19], "%Y-%m-%dT%H:%M:%S"))
            expires_at = obtained_ts + expires_in
            remaining = expires_at - time.time()
            if remaining > buffer_seconds:
                print(f"Token still valid ({int(remaining)}s remaining, {int(remaining/3600)}h)")
                return True
            print(f"Token expired or expiring soon ({int(remaining)}s remaining)")
            return False
    except Exception as e:
        print(f"Cannot check token: {e}")
        return False


def refresh_via_refresh_token():
    """Use the refresh_token grant to get a new access token."""
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        print("ERROR: No refresh_token in token file")
        return False

    with open(OAUTH_FILE) as f:
        oauth = json.load(f)

    req_data = json.dumps({
        "grant_type": "refresh_token",
        "client_id": oauth["client_id"],
        "client_secret": oauth["client_secret"],
        "refresh_token": refresh_token,
    }).encode()

    req = urllib.request.Request(
        "https://auth.videoask.com/oauth/token",
        data=req_data,
        headers={"Content-Type": "application/json"},
    )

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        new_token = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"ERROR: Refresh failed ({e.code}): {body}")
        return False

    if "access_token" not in new_token:
        print(f"ERROR: No access_token in response: {json.dumps(new_token)[:200]}")
        return False

    # Preserve refresh_token if not returned (some providers don't rotate it)
    if "refresh_token" not in new_token and refresh_token:
        new_token["refresh_token"] = refresh_token

    new_token["obtained_at"] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

    # Test the new token
    test_req = urllib.request.Request(
        "https://api.videoask.com/me",
        headers={
            "Authorization": f"Bearer {new_token['access_token']}",
            "organization-id": ORG_ID,
        },
    )
    try:
        test_resp = urllib.request.urlopen(test_req, timeout=10)
        if test_resp.status == 200:
            print("New token verified successfully")
    except Exception as e:
        print(f"WARNING: Token test failed: {e}")

    with open(TOKEN_FILE, "w") as f:
        json.dump(new_token, f, indent=2)

    expires_h = new_token.get("expires_in", 0) / 3600
    print(f"Token refreshed (expires_in={new_token.get('expires_in')}s / {expires_h:.0f}h)")
    return True


def main():
    force = "--force" in sys.argv

    if not force and is_token_valid():
        return True

    print("Refreshing VideoAsk token via refresh_token grant...")
    return refresh_via_refresh_token()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
