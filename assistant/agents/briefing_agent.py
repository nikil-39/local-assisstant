"""
Morning Briefing Agent — Generates a newspaper-style HTML briefing.

Data sources:
    1. Microsoft Outlook (today's emails + calendar) via MS Graph API
    2. Jira tickets (assigned to user) via Jira REST API
    3. AI summary of everything via Ollama / Gemini

Triggered by: "morning briefing", "give briefing", "briefing"
Output: Opens an HTML newspaper page in the default browser.
"""

import json
import logging
import os
import webbrowser
import base64
from datetime import datetime, timezone
from pathlib import Path

from assistant.agents.base_agent import BaseAgent

logger = logging.getLogger("jarvis.agents.briefing")

# Token cache location (gitignored)
TOKEN_CACHE = Path(__file__).parent.parent.parent / "config" / ".ms_tokens.json"


class BriefingAgent(BaseAgent):
    """Fetches emails, calendar, Jira tickets and builds a newspaper HTML."""

    name = "Morning Briefing"
    triggers = ["briefing"]

    def __init__(self, settings: dict, ai_manager=None):
        self.settings = settings
        self.ai_manager = ai_manager
        agent_cfg = settings.get("agents", {}).get("briefing", {})

        # Microsoft Graph
        self._ms_client_id = os.getenv("MS_CLIENT_ID", agent_cfg.get("ms_client_id", ""))
        self._ms_client_secret = os.getenv("MS_CLIENT_SECRET", agent_cfg.get("ms_client_secret", ""))
        self._ms_tenant_id = os.getenv("MS_TENANT_ID", agent_cfg.get("ms_tenant_id", ""))

        # Jira
        self._jira_url = os.getenv("JIRA_BASE_URL", agent_cfg.get("jira_base_url", ""))
        self._jira_pat = os.getenv("JIRA_PAT", agent_cfg.get("jira_pat", ""))
        self._jira_user = os.getenv("JIRA_USER", agent_cfg.get("jira_user", ""))
        self._jira_jql = agent_cfg.get(
            "jira_jql",
            'project="Team Accelerate" AND assignee={user} AND status != Done ORDER BY updated DESC',
        )

        # Output
        self._output_dir = Path(__file__).parent.parent.parent / "output"
        self._output_dir.mkdir(exist_ok=True)

    # ── Microsoft Graph ───────────────────────────────────────────────

    def _get_ms_token(self) -> str | None:
        """Get MS Graph access token using client credentials flow."""
        if not all([self._ms_client_id, self._ms_client_secret, self._ms_tenant_id]):
            logger.warning("Microsoft credentials not configured — skipping email/calendar")
            return None

        try:
            import httpx

            # Try cached token first
            if TOKEN_CACHE.exists():
                cached = json.loads(TOKEN_CACHE.read_text())
                if cached.get("expires_at", 0) > datetime.now(timezone.utc).timestamp() + 60:
                    return cached["access_token"]

            # Request new token (client credentials flow)
            token_url = f"https://login.microsoftonline.com/{self._ms_tenant_id}/oauth2/v2.0/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": self._ms_client_id,
                "client_secret": self._ms_client_secret,
                "scope": "https://graph.microsoft.com/.default",
            }
            with httpx.Client(timeout=15.0, verify=False) as client:
                resp = client.post(token_url, data=data)
                resp.raise_for_status()
                token_data = resp.json()

            # Cache token
            token_data["expires_at"] = datetime.now(timezone.utc).timestamp() + token_data.get("expires_in", 3600)
            TOKEN_CACHE.write_text(json.dumps(token_data, indent=2))
            return token_data["access_token"]

        except Exception as e:
            logger.error(f"MS Graph token error: {e}")
            return None

    def _fetch_emails(self, token: str) -> list[dict]:
        """Fetch today's emails from Outlook via MS Graph."""
        try:
            import httpx
            today = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
            url = (
                "https://graph.microsoft.com/v1.0/me/messages"
                f"?$filter=receivedDateTime ge {today}"
                "&$select=subject,from,receivedDateTime,isRead,importance,bodyPreview"
                "&$orderby=receivedDateTime desc"
                "&$top=25"
            )
            with httpx.Client(timeout=15.0, verify=False) as client:
                resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
                resp.raise_for_status()
                return resp.json().get("value", [])
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            return []

    def _fetch_calendar(self, token: str) -> list[dict]:
        """Fetch today's calendar events from Outlook via MS Graph."""
        try:
            import httpx
            now = datetime.now(timezone.utc)
            start = now.strftime("%Y-%m-%dT00:00:00Z")
            end = now.strftime("%Y-%m-%dT23:59:59Z")
            url = (
                f"https://graph.microsoft.com/v1.0/me/calendarView"
                f"?startDateTime={start}&endDateTime={end}"
                "&$select=subject,start,end,organizer,location,isAllDay"
                "&$orderby=start/dateTime"
            )
            with httpx.Client(timeout=15.0, verify=False) as client:
                resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
                resp.raise_for_status()
                return resp.json().get("value", [])
        except Exception as e:
            logger.error(f"Failed to fetch calendar: {e}")
            return []

    # ── Jira ──────────────────────────────────────────────────────────

    def _fetch_jira_tickets(self) -> list[dict]:
        """Fetch assigned Jira tickets via REST API."""
        if not all([self._jira_url, self._jira_pat]):
            logger.warning("Jira credentials not configured — skipping tickets")
            return []

        try:
            import httpx
            jql = self._jira_jql.replace("{user}", self._jira_user or "currentUser()")
            api_url = f"{self._jira_url}/rest/api/2/search"
            params = {
                "jql": jql,
                "maxResults": 30,
                "fields": "summary,status,priority,issuetype,created,updated,assignee,duedate",
            }
            headers = {
                "Authorization": f"Bearer {self._jira_pat}",
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=20.0, verify=False) as client:
                resp = client.get(api_url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

            tickets = []
            for issue in data.get("issues", []):
                fields = issue.get("fields", {})
                created = fields.get("created", "")
                # Calculate days open
                days_open = 0
                if created:
                    try:
                        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        days_open = (datetime.now(timezone.utc) - created_dt).days
                    except Exception:
                        pass

                tickets.append({
                    "key": issue.get("key", ""),
                    "summary": fields.get("summary", ""),
                    "status": fields.get("status", {}).get("name", ""),
                    "priority": fields.get("priority", {}).get("name", ""),
                    "type": fields.get("issuetype", {}).get("name", ""),
                    "days_open": days_open,
                    "due": fields.get("duedate", ""),
                    "updated": fields.get("updated", "")[:10],
                })
            return tickets
        except Exception as e:
            logger.error(f"Failed to fetch Jira tickets: {e}")
            return []

    # ── AI Summary ────────────────────────────────────────────────────

    def _ai_summarize(self, emails: list, calendar: list, tickets: list) -> str:
        """Ask the AI to produce a brief spoken summary."""
        if not self.ai_manager:
            return ""

        data_blob = []
        if emails:
            data_blob.append(f"EMAILS ({len(emails)} today):")
            for e in emails[:10]:
                fr = e.get("from", {}).get("emailAddress", {}).get("name", "?")
                data_blob.append(f"  - From: {fr} | Subject: {e.get('subject', '?')}")
        if calendar:
            data_blob.append(f"\nMEETINGS ({len(calendar)} today):")
            for c in calendar:
                start = c.get("start", {}).get("dateTime", "?")[:16]
                data_blob.append(f"  - {start}: {c.get('subject', '?')}")
        if tickets:
            open_count = sum(1 for t in tickets if t["status"] not in ("Done", "Closed", "Resolved"))
            data_blob.append(f"\nJIRA TICKETS ({open_count} open):")
            for t in tickets[:10]:
                data_blob.append(f"  - {t['key']}: {t['summary']} [{t['status']}] ({t['days_open']}d open)")

        prompt = (
            "You are Jarvis, summarizing a morning briefing for the user. "
            "Be concise — 3-5 sentences spoken aloud. Highlight important emails, "
            "upcoming meetings, and overdue/critical Jira tickets.\n\n"
            + "\n".join(data_blob)
        )

        try:
            return self.ai_manager.ask_sync(prompt)
        except Exception as e:
            logger.error(f"AI summary failed: {e}")
            return ""

    # ── HTML Newspaper ────────────────────────────────────────────────

    def _generate_html(self, emails: list, calendar: list, tickets: list, ai_summary: str) -> Path:
        """Build a newspaper-style HTML page and return its path."""
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")

        # Email rows
        email_rows = ""
        for e in emails:
            fr = e.get("from", {}).get("emailAddress", {}).get("name", "Unknown")
            subj = e.get("subject", "(no subject)")
            preview = e.get("bodyPreview", "")[:120]
            importance = e.get("importance", "normal")
            read_badge = "" if e.get("isRead") else '<span class="badge new">NEW</span>'
            imp_class = "high" if importance == "high" else ""
            recv = e.get("receivedDateTime", "")[:16].replace("T", " ")
            email_rows += f"""
            <tr class="{imp_class}">
                <td>{read_badge} {subj}</td>
                <td>{fr}</td>
                <td class="preview">{preview}</td>
                <td>{recv}</td>
            </tr>"""

        # Calendar rows
        cal_rows = ""
        for c in calendar:
            start = c.get("start", {}).get("dateTime", "")
            end = c.get("end", {}).get("dateTime", "")
            start_time = start[11:16] if len(start) > 16 else "All Day"
            end_time = end[11:16] if len(end) > 16 else ""
            organizer = c.get("organizer", {}).get("emailAddress", {}).get("name", "")
            location = c.get("location", {}).get("displayName", "")
            cal_rows += f"""
            <tr>
                <td>{start_time} – {end_time}</td>
                <td>{c.get("subject", "")}</td>
                <td>{organizer}</td>
                <td>{location}</td>
            </tr>"""

        # Jira rows
        ticket_rows = ""
        open_count = 0
        critical_count = 0
        for t in tickets:
            status = t["status"]
            if status not in ("Done", "Closed", "Resolved"):
                open_count += 1
            if t["priority"] in ("Blocker", "Critical"):
                critical_count += 1
            status_class = {
                "Open": "status-open", "In Progress": "status-progress",
                "Done": "status-done", "Closed": "status-done",
                "To Do": "status-open",
            }.get(status, "status-open")
            days_badge = f'<span class="badge overdue">{t["days_open"]}d</span>' if t["days_open"] > 14 else f'{t["days_open"]}d'
            ticket_rows += f"""
            <tr>
                <td><strong>{t["key"]}</strong></td>
                <td>{t["summary"]}</td>
                <td><span class="badge {status_class}">{status}</span></td>
                <td>{t["priority"]}</td>
                <td>{t["type"]}</td>
                <td>{days_badge}</td>
                <td>{t["updated"]}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jarvis Morning Briefing — {date_str}</title>
<style>
  :root {{
    --bg: #0f172a; --surface: #1e293b; --border: #334155;
    --text: #e2e8f0; --muted: #94a3b8; --accent: #6366f1;
    --green: #22c55e; --yellow: #eab308; --red: #ef4444; --blue: #3b82f6;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--bg); color: var(--text);
    line-height: 1.6; padding: 20px;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  /* Header */
  .header {{
    text-align: center; border-bottom: 3px double var(--accent);
    padding-bottom: 20px; margin-bottom: 30px;
  }}
  .header h1 {{
    font-size: 2.5em; font-weight: 300; letter-spacing: 6px;
    text-transform: uppercase; color: var(--accent);
  }}
  .header .date {{ color: var(--muted); font-size: 1.1em; margin-top: 4px; }}
  .header .edition {{ font-style: italic; color: var(--muted); font-size: 0.9em; }}
  /* AI Summary */
  .summary-box {{
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1));
    border: 1px solid rgba(99,102,241,0.3); border-radius: 12px;
    padding: 20px 24px; margin-bottom: 30px;
  }}
  .summary-box h2 {{ color: var(--accent); font-size: 1.1em; margin-bottom: 8px; }}
  .summary-box p {{ color: var(--text); }}
  /* Stats bar */
  .stats {{
    display: flex; gap: 16px; margin-bottom: 30px; flex-wrap: wrap;
  }}
  .stat-card {{
    flex: 1; min-width: 150px; background: var(--surface);
    border: 1px solid var(--border); border-radius: 10px;
    padding: 16px; text-align: center;
  }}
  .stat-card .number {{ font-size: 2em; font-weight: 700; }}
  .stat-card .label {{ color: var(--muted); font-size: 0.85em; }}
  .stat-card.emails .number {{ color: var(--blue); }}
  .stat-card.meetings .number {{ color: var(--green); }}
  .stat-card.tickets .number {{ color: var(--yellow); }}
  .stat-card.critical .number {{ color: var(--red); }}
  /* Sections */
  .section {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; margin-bottom: 24px;
  }}
  .section h2 {{
    font-size: 1.2em; color: var(--accent); margin-bottom: 14px;
    border-bottom: 1px solid var(--border); padding-bottom: 8px;
  }}
  /* Tables */
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
  th {{
    text-align: left; padding: 8px 10px; color: var(--muted);
    border-bottom: 1px solid var(--border); font-weight: 600;
  }}
  td {{ padding: 8px 10px; border-bottom: 1px solid rgba(51,65,85,0.5); }}
  tr.high {{ background: rgba(239,68,68,0.08); }}
  .preview {{ color: var(--muted); font-size: 0.85em; max-width: 300px; }}
  /* Badges */
  .badge {{
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 0.8em; font-weight: 600;
  }}
  .badge.new {{ background: var(--blue); color: white; }}
  .badge.overdue {{ background: var(--red); color: white; }}
  .badge.status-open {{ background: rgba(234,179,8,0.2); color: var(--yellow); }}
  .badge.status-progress {{ background: rgba(59,130,246,0.2); color: var(--blue); }}
  .badge.status-done {{ background: rgba(34,197,94,0.2); color: var(--green); }}
  /* Footer */
  .footer {{
    text-align: center; color: var(--muted); font-size: 0.8em;
    margin-top: 30px; padding-top: 16px; border-top: 1px solid var(--border);
  }}
  .empty {{ color: var(--muted); font-style: italic; padding: 16px; }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <div class="edition">The Jarvis Daily</div>
    <h1>Morning Briefing</h1>
    <div class="date">{date_str} &mdash; {time_str}</div>
  </div>

  {"" if not ai_summary else f'''
  <div class="summary-box">
    <h2>&#x1F916; AI Summary</h2>
    <p>{ai_summary}</p>
  </div>
  '''}

  <div class="stats">
    <div class="stat-card emails">
      <div class="number">{len(emails)}</div>
      <div class="label">Emails Today</div>
    </div>
    <div class="stat-card meetings">
      <div class="number">{len(calendar)}</div>
      <div class="label">Meetings</div>
    </div>
    <div class="stat-card tickets">
      <div class="number">{open_count}</div>
      <div class="label">Open Tickets</div>
    </div>
    <div class="stat-card critical">
      <div class="number">{critical_count}</div>
      <div class="label">Critical / Blocker</div>
    </div>
  </div>

  <div class="section">
    <h2>&#128231; Today's Emails</h2>
    {"<p class='empty'>No emails fetched (credentials not configured or no emails today).</p>" if not emails else f'''
    <table>
      <thead><tr><th>Subject</th><th>From</th><th>Preview</th><th>Received</th></tr></thead>
      <tbody>{email_rows}</tbody>
    </table>
    '''}
  </div>

  <div class="section">
    <h2>&#128197; Today's Meetings</h2>
    {"<p class='empty'>No meetings fetched (credentials not configured or free day!).</p>" if not calendar else f'''
    <table>
      <thead><tr><th>Time</th><th>Subject</th><th>Organizer</th><th>Location</th></tr></thead>
      <tbody>{cal_rows}</tbody>
    </table>
    '''}
  </div>

  <div class="section">
    <h2>&#127919; Jira Tickets</h2>
    {"<p class='empty'>No Jira tickets fetched (credentials not configured).</p>" if not tickets else f'''
    <table>
      <thead><tr><th>Key</th><th>Summary</th><th>Status</th><th>Priority</th><th>Type</th><th>Age</th><th>Updated</th></tr></thead>
      <tbody>{ticket_rows}</tbody>
    </table>
    '''}
  </div>

  <div class="footer">
    Generated by Jarvis &mdash; {date_str} at {time_str}
  </div>

</div>
</body>
</html>"""

        out_file = self._output_dir / f"briefing_{now.strftime('%Y%m%d_%H%M')}.html"
        out_file.write_text(html, encoding="utf-8")
        return out_file

    # ── Main Entry Point ──────────────────────────────────────────────

    def run(self, data: dict | None = None) -> str:
        """Fetch all data, generate HTML, open in browser, return summary."""
        logger.info("Morning Briefing Agent starting...")

        # 1. Fetch data
        emails, calendar, tickets = [], [], []

        ms_token = self._get_ms_token()
        if ms_token:
            emails = self._fetch_emails(ms_token)
            calendar = self._fetch_calendar(ms_token)
            logger.info(f"Outlook: {len(emails)} emails, {len(calendar)} meetings")

        tickets = self._fetch_jira_tickets()
        logger.info(f"Jira: {len(tickets)} tickets")

        # 2. AI summary
        ai_summary = self._ai_summarize(emails, calendar, tickets)

        # 3. Generate HTML
        html_path = self._generate_html(emails, calendar, tickets, ai_summary)
        logger.info(f"Briefing HTML saved: {html_path}")

        # 4. Open in browser
        webbrowser.open(str(html_path))

        # 5. Spoken summary
        parts = []
        if emails:
            unread = sum(1 for e in emails if not e.get("isRead"))
            parts.append(f"You have {len(emails)} emails today, {unread} unread.")
        if calendar:
            parts.append(f"You have {len(calendar)} meetings scheduled.")
        if tickets:
            open_t = sum(1 for t in tickets if t["status"] not in ("Done", "Closed", "Resolved"))
            parts.append(f"There are {open_t} open Jira tickets assigned to you.")
        if not parts:
            parts.append("Your briefing is ready.")

        if ai_summary:
            # Use AI summary as the spoken part
            return ai_summary

        return " ".join(parts) + " I've opened the full briefing in your browser."
