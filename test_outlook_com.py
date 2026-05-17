"""Test Outlook COM connectivity — reads inbox and calendar."""
import sys
import pythoncom
import win32com.client
from datetime import datetime, timedelta

# Initialize COM for this thread
pythoncom.CoInitialize()

try:
    print("Connecting to Outlook...")
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    print("Connected!")

    # Test 1: Inbox emails today
    print()
    print("=" * 50)
    print("INBOX - Today's Emails")
    print("=" * 50)
    inbox = outlook.GetDefaultFolder(6)  # 6 = Inbox
    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)

    today = datetime.now().replace(hour=0, minute=0, second=0)
    today_str = today.strftime("%m/%d/%Y")
    filtered = messages.Restrict(f"[ReceivedTime] >= '{today_str}'")

    count = filtered.Count
    print(f"Found {count} emails today")
    for i in range(min(5, count)):
        msg = filtered.Item(i + 1)
        print(f"  From: {msg.SenderName}")
        print(f"  Subject: {msg.Subject}")
        received = str(msg.ReceivedTime)[:19]
        print(f"  Time: {received}")
        print()

    # Test 2: Calendar today
    print("=" * 50)
    print("CALENDAR - Today's Meetings")
    print("=" * 50)
    cal = outlook.GetDefaultFolder(9)  # 9 = Calendar
    items = cal.Items
    items.IncludeRecurrences = True
    items.Sort("[Start]")

    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%m/%d/%Y")
    restriction = f"[Start] >= '{today_str}' AND [Start] < '{tomorrow_str}'"
    cal_items = items.Restrict(restriction)

    cal_count = cal_items.Count
    print(f"Found {cal_count} meetings today")
    for i in range(min(5, cal_count)):
        apt = cal_items.Item(i + 1)
        start_str = str(apt.Start)[:16]
        end_str = str(apt.End)[:16]
        print(f"  {start_str} - {end_str}")
        print(f"  Subject: {apt.Subject}")
        print(f"  Organizer: {apt.Organizer}")
        location = getattr(apt, "Location", "")
        if location:
            print(f"  Location: {location}")
        print()

    print("=" * 50)
    print("OUTLOOK COM TEST COMPLETE - SUCCESS")
    print("=" * 50)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    pythoncom.CoUninitialize()

