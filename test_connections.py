"""Quick connectivity test for Jira and Microsoft Graph."""
import os
import json
from pathlib import Path

# Load .env
for line in Path(".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

import httpx

# ── Jira ──────────────────────────────────────────────────────────────
print("=" * 50)
print("TESTING JIRA CONNECTION")
print("=" * 50)
try:
    jira_url = os.environ["JIRA_BASE_URL"]
    jira_pat = os.environ["JIRA_PAT"]
    jira_user = os.environ.get("JIRA_USER", "LFI1COB")

    # Try multiple auth methods
    auth_methods = [
        ("Bearer token", {"Authorization": f"Bearer {jira_pat}", "Content-Type": "application/json"}),
        ("Basic auth (user:PAT)", {"Authorization": "Basic " + __import__('base64').b64encode(f"{jira_user}:{jira_pat}".encode()).decode(), "Content-Type": "application/json"}),
        ("PAT is already base64 (raw header)", {"Authorization": f"Basic {jira_pat}", "Content-Type": "application/json"}),
    ]
    
    # First, try to get current user info
    print(f"Jira URL: {jira_url}")
    print(f"User: {jira_user}")
    print()

    for auth_name, headers in auth_methods:
        print(f"  Trying: {auth_name}")
        try:
            with httpx.Client(timeout=20.0, verify=False, trust_env=False) as client:
                # Test /myself first
                myself_resp = client.get(f"{jira_url}/rest/api/2/myself", headers=headers)
                print(f"    /myself: {myself_resp.status_code}", end="")
                if myself_resp.status_code == 200:
                    me = myself_resp.json()
                    print(f" -> {me.get('displayName', '?')} ({me.get('name', '?')})")
                else:
                    print(f" -> {myself_resp.text[:200]}")
                    continue

                # List projects
                proj_resp = client.get(f"{jira_url}/rest/api/2/project", headers=headers)
                print(f"    /project: {proj_resp.status_code}", end="")
                if proj_resp.status_code == 200:
                    projects = proj_resp.json()
                    print(f" -> {len(projects)} projects")
                    for p in projects[:10]:
                        print(f"      {p.get('key')}: {p.get('name')}")
                else:
                    print()

                # Try with assignee=currentUser()
                jql_simple = "assignee=currentUser() AND status != Done ORDER BY updated DESC"
                search_url = f"{jira_url}/rest/api/2/search"
                resp = client.get(search_url, headers=headers, params={"jql": jql_simple, "maxResults": 5, "fields": "summary,status,priority,issuetype,created"})
                print(f"    JQL assignee=currentUser(): {resp.status_code}", end="")
                if resp.status_code == 200:
                    data = resp.json()
                    total = data.get("total", 0)
                    print(f" -> {total} tickets")
                    for issue in data.get("issues", [])[:5]:
                        f = issue["fields"]
                        key = issue["key"]
                        summary = f.get("summary", "?")
                        status = f.get("status", {}).get("name", "?") 
                        print(f"      [{key}] {summary} | {status}")
                else:
                    print(f" -> {resp.text[:200]}")
                break
        except Exception as e:
            print(f"    ERROR: {e}")
            continue
except Exception as e:
    print(f"JIRA ERROR: {e}")

# ── Microsoft Graph ───────────────────────────────────────────────────
print()
print("=" * 50)
print("TESTING MICROSOFT GRAPH (Outlook)")
print("=" * 50)
try:
    client_id = os.environ.get("MS_CLIENT_ID", "")
    tenant_id = os.environ.get("MS_TENANT_ID", "")
    client_secret = os.environ.get("MS_CLIENT_SECRET", "")

    if not all([client_id, tenant_id, client_secret]):
        print("SKIPPED - MS credentials not set in .env")
    else:
        # Step 1: Get access token
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }

        with httpx.Client(timeout=15.0, verify=False, trust_env=False) as client:
            token_resp = client.post(token_url, data=token_data)

        print(f"Token request HTTP Status: {token_resp.status_code}")
        if token_resp.status_code == 200:
            access_token = token_resp.json()["access_token"]
            print("SUCCESS - Got access token")

            # Step 2: Try to fetch emails
            me_url = "https://graph.microsoft.com/v1.0/me"
            with httpx.Client(timeout=15.0, verify=False, trust_env=False) as client:
                me_resp = client.get(me_url, headers={"Authorization": f"Bearer {access_token}"})

            print(f"Graph /me HTTP Status: {me_resp.status_code}")
            if me_resp.status_code == 200:
                user_data = me_resp.json()
                print(f"  User: {user_data.get('displayName', '?')} ({user_data.get('mail', '?')})")
            else:
                # Client credentials flow may not support /me - try /users
                print(f"  /me not available (client credentials flow)")
                print(f"  Response: {me_resp.text[:300]}")
                print()
                print("  NOTE: Client credentials flow accesses org-level data.")
                print("  Trying /users endpoint instead...")
                users_url = "https://graph.microsoft.com/v1.0/users?$top=1&$select=displayName,mail"
                with httpx.Client(timeout=15.0, verify=False, trust_env=False) as client:
                    users_resp = client.get(users_url, headers={"Authorization": f"Bearer {access_token}"})
                print(f"  /users HTTP Status: {users_resp.status_code}")
                if users_resp.status_code == 200:
                    print(f"  SUCCESS - Graph API is accessible!")
                else:
                    print(f"  Response: {users_resp.text[:300]}")
        else:
            error = token_resp.json()
            print(f"FAILED - {error.get('error', '?')}: {error.get('error_description', '?')[:300]}")
except Exception as e:
    print(f"MS GRAPH ERROR: {e}")

print()
print("=" * 50)
print("TESTS COMPLETE")
print("=" * 50)
