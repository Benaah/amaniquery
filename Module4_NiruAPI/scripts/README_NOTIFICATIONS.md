# Notification Testing Script

## Overview
The `test_notifications.py` script allows you to test SMS and WhatsApp notification channels through the Talksasa API.

## Prerequisites
1. **Talksasa API Token**: Set `TALKSASA_API_TOKEN` in:
   - Config Manager (admin panel), or
   - Environment variable: `export TALKSASA_API_TOKEN='your_token'`

2. **Sender ID** (optional): Set `TALKSASA_SENDER_ID` (defaults to "TALKSASA")

3. **Database**: PostgreSQL database must be accessible (for subscription tests)

## Usage

### Basic Test (Both Channels)
```bash
python Module4_NiruAPI/scripts/test_notifications.py 0712345678
```

### With Custom Message
```bash
python Module4_NiruAPI/scripts/test_notifications.py 0712345678 -m "Your custom test message"
```

### Test Only Talksasa Service (No Database)
```bash
python Module4_NiruAPI/scripts/test_notifications.py 0712345678 -s
```

### Test Only Notification Service (Skip Direct API Test)
```bash
python Module4_NiruAPI/scripts/test_notifications.py 0712345678 -n
```

## Phone Number Formats
The script accepts phone numbers in various formats:
- `0712345678` (local format)
- `+254712345678` (international format)
- `254712345678` (without +)

All formats will be normalized to the format required by Talksasa API.

## What It Tests

1. **Talksasa Service Direct Tests**:
   - SMS sending capability
   - WhatsApp sending capability
   - Notification with WhatsApp fallback to SMS

2. **Notification Service Tests**:
   - Subscription creation
   - Article notification sending
   - Subscription cleanup

## Example Output

```
============================================================
AmaniQuery Notification Channel Test
============================================================
Time: 2025-01-15 10:30:00

============================================================
Testing Talksasa Notification Service
============================================================
✓ API Token: ****************abc123
✓ Sender ID: TALKSASA
✓ Phone Number: 254712345678

📝 Test Message: Test notification from AmaniQuery at 2025-01-15 10:30:00
   Length: 65 characters

------------------------------------------------------------
Testing SMS Channel...
------------------------------------------------------------
✅ SMS sent successfully!

------------------------------------------------------------
Testing WhatsApp Channel...
------------------------------------------------------------
✅ WhatsApp sent successfully!

============================================================
Test Summary
============================================================
SMS:        ✅ Success
WhatsApp:    ✅ Success
Notification: ✅ Success
```

## Troubleshooting

### "TALKSASA_API_TOKEN not found"
- Set the token in the admin panel Config Manager, or
- Export it as an environment variable before running the script

### "Service not available"
- Verify your API token is correct
- Check that the Talksasa API is accessible from your network

### "Failed to send SMS/WhatsApp"
- Verify the phone number format
- Check your Talksasa account balance/credits
- Ensure the phone number is valid and can receive messages

### Database Connection Errors
- Ensure PostgreSQL is running
- Check `DATABASE_URL` environment variable
- Use `-s` flag to skip database-dependent tests

