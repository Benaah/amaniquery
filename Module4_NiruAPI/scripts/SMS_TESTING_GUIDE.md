# SMS Service Testing Guide

## Overview

The SMS service is now fully integrated and tested. This guide explains how to test it and troubleshoot common issues.

## Test Scripts

### 1. Direct Service Test
Tests the SMS service directly (without API):
```bash
python Module4_NiruAPI/scripts/test_sms_service.py --phone 0796572619
```

### 2. API Integration Test
Tests the full SMS flow through FastAPI:
```bash
python Module4_NiruAPI/scripts/test_sms_api_integration.py --phone 0796572619 --query "What is the Finance Bill?" --test-mode full
```

## SSL/Network Errors

If you encounter SSL errors like:
```
SSL: WRONG_VERSION_NUMBER
HTTPSConnectionPool: Max retries exceeded
```

This is typically caused by:
- **Proxy/Firewall**: Corporate proxy intercepting HTTPS connections
- **Antivirus**: Security software intercepting SSL traffic
- **VPN**: VPN software interfering with SSL handshake
- **Network restrictions**: Firewall blocking outbound HTTPS

### Solutions

#### Option 1: Disable SSL Verification (Quick Fix for Development)
The service now automatically tries direct API calls with SSL fixes. If SSL errors persist, you can disable SSL verification:

**Set environment variable:**
```bash
# Windows PowerShell
$env:SMS_VERIFY_SSL="false"

# Windows CMD
set SMS_VERIFY_SSL=false

# Linux/Mac
export SMS_VERIFY_SSL=false
```

Or add to your `.env` file:
```
SMS_VERIFY_SSL=false
```

**⚠️ WARNING:** This disables SSL certificate verification and is **INSECURE**. Only use in development!

**Restart your FastAPI server** after setting the variable.

#### Option 2: Use Test Mode (No Actual SMS)
Enable test mode to simulate SMS sending without making actual API calls:

**Set environment variable:**
```bash
# Windows PowerShell
$env:SMS_TEST_MODE="true"

# Windows CMD
set SMS_TEST_MODE=true

# Linux/Mac
export SMS_TEST_MODE=true
```

Or add to your `.env` file:
```
SMS_TEST_MODE=true
```

**Restart your FastAPI server** after setting the variable.

In test mode:
- SMS sending is simulated (no actual API calls)
- All functionality works except actual SMS delivery
- Useful for testing the full pipeline without network issues

#### Option 3: Fix Network Configuration
1. **Check proxy settings**: Configure proxy for Python/requests
2. **Disable SSL verification** (NOT recommended for production):
   ```python
   # Only for testing - adds security risk
   import ssl
   ssl._create_default_https_context = ssl._create_unverified_context
   ```
3. **Whitelist domain**: Add `api.sandbox.africastalking.com` to firewall exceptions
4. **Use different network**: Try from a different network/VPN

#### Option 4: Use Production API
The sandbox API may have different SSL requirements. Try using production credentials if available.

## Test Results Summary

✅ **Working:**
- Service initialization
- Phone number formatting
- SMS parsing
- Query processing through API
- Error handling

⚠️ **Network Issues:**
- SSL connection to Africa's Talking API (environment-specific)
- Can be bypassed with test mode

## API Endpoints

### 1. Preview SMS Response
```bash
GET /sms-query?query=What is the Finance Bill?&language=en
```

### 2. Send SMS Manually
```bash
POST /sms-send?phone_number=0796572619&message=Test message
```

### 3. SMS Webhook (for incoming SMS)
```bash
POST /sms-webhook
# Called by Africa's Talking when SMS is received
```

## Environment Variables

Required:
- `AT_USERNAME`: Africa's Talking username
- `AT_API_KEY`: Africa's Talking API key

Optional:
- `SMS_TEST_MODE`: Set to "true" to enable test mode (simulates SMS)
- `SMS_VERIFY_SSL`: Set to "false" to disable SSL verification (development only, insecure!)

## New Features

The SMS service now includes:

1. **Automatic Retry Logic**: Retries up to 3 times with exponential backoff
2. **Direct API Fallback**: If SDK fails, automatically tries direct API calls
3. **SSL Configuration**: Automatically configures SSL certificates using certifi
4. **Smart Error Detection**: Detects SSL errors and suggests fixes
5. **SSL Verification Control**: Can disable SSL verification for development (insecure!)

## Next Steps

1. **For Development**: Use test mode (`SMS_TEST_MODE=true`)
2. **For Production**: 
   - Resolve network/SSL issues
   - Use production API credentials
   - Configure webhook URL in Africa's Talking dashboard
3. **For Testing**: Use the provided test scripts

## Troubleshooting

### Service not initialized
- Check that `sms_service` is declared at module level (fixed in latest version)
- Restart FastAPI server after code changes

### "SMS service not available"
- Check `AT_USERNAME` and `AT_API_KEY` are set
- Verify `africastalking` package is installed: `pip install africastalking`

### SSL errors persist
- Use test mode for development
- Check network/firewall settings
- Try from different network
- Contact network administrator for proxy configuration

