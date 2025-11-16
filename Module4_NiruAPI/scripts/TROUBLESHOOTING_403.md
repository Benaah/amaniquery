# Troubleshooting WhatsApp 403 Forbidden Error

## Problem
When sending WhatsApp notifications through Talksasa API, you receive a `403 Forbidden` error.

## What 403 Forbidden Means
A 403 error indicates that the server understood your request but is refusing to fulfill it. In the context of Talksasa WhatsApp API, this typically means:

1. **WhatsApp not enabled on your account** - Your Talksasa account may not have WhatsApp service activated
2. **API token lacks permissions** - Your API token may not have WhatsApp permissions
3. **Account plan limitations** - Your subscription plan may not include WhatsApp functionality
4. **Service not available** - WhatsApp may not be available in your region or for your account type

## Solutions

### 1. Contact Talksasa Support
The most reliable solution is to contact Talksasa support to:
- Enable WhatsApp service for your account
- Verify your API token has WhatsApp permissions
- Upgrade your account plan if needed

**Talksasa Support:**
- Website: https://bulksms.talksasa.com
- Check your account dashboard for support contact information

### 2. Use SMS Instead
If WhatsApp is not available, the system will automatically fallback to SMS when using the `send_notification()` method with `notification_type="whatsapp"`. SMS should work if your account has SMS enabled.

To force SMS only:
```python
# In your code
result = talksasa_service.send_sms(phone_number, message)

# Or in subscription
subscription = SubscriptionCreate(
    phone_number=phone_number,
    notification_type="sms",  # Use SMS instead of WhatsApp
    ...
)
```

### 3. Verify Your Configuration
Check that your API token is correct:
```bash
# Test with the test script
python Module4_NiruAPI/scripts/test_notifications.py YOUR_PHONE_NUMBER -s
```

The script will show detailed error information including:
- HTTP status code
- Error message from API
- Response details

### 4. Check Account Dashboard
1. Log into your Talksasa account dashboard
2. Check if WhatsApp service is listed as available
3. Verify your API token permissions
4. Check your account balance/credits

## Current Behavior
The notification service is designed to handle this gracefully:

- **Automatic Fallback**: When WhatsApp fails with 403, the system automatically falls back to SMS
- **Detailed Logging**: All 403 errors are logged with full details for debugging
- **User Experience**: Users will still receive notifications via SMS if WhatsApp is unavailable

## Testing
Run the test script to diagnose the issue:
```bash
python Module4_NiruAPI/scripts/test_notifications.py 0712345678
```

The script will:
- Test SMS (should work)
- Test WhatsApp (will show 403 if not enabled)
- Show detailed error information
- Provide troubleshooting suggestions

## Expected Output for 403 Error
```
------------------------------------------------------------
Testing WhatsApp Channel...
------------------------------------------------------------
❌ WhatsApp failed: WhatsApp access forbidden (403): [error message]

⚠️  403 Forbidden Error Details:
   This typically means:
   1. Your Talksasa account doesn't have WhatsApp enabled
   2. Your API token lacks WhatsApp permissions
   3. WhatsApp service is not available for your account plan

   Solution:
   - Contact Talksasa support to enable WhatsApp for your account
   - Or use SMS notifications instead (which should work)
```

## Next Steps
1. **If SMS works**: Continue using SMS notifications until WhatsApp is enabled
2. **If SMS also fails**: Check your API token and account status
3. **Contact Talksasa**: Request WhatsApp service activation for your account

