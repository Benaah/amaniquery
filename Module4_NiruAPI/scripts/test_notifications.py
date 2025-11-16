#!/usr/bin/env python3
"""
Test script for Talksasa SMS/WhatsApp notification channels
Tests both SMS and WhatsApp sending capabilities
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Module4_NiruAPI.services.talksasa_service import TalksasaNotificationService
from Module4_NiruAPI.services.notification_service import NotificationService
from Module4_NiruAPI.config_manager import ConfigManager
from loguru import logger
import argparse
from datetime import datetime


def test_talksasa_service(phone_number: str, message: str = None):
    """Test Talksasa service directly"""
    print("\n" + "="*60)
    print("Testing Talksasa Notification Service")
    print("="*60)
    
    # Initialize config manager
    config_manager = ConfigManager()
    api_token = config_manager.get_config("TALKSASA_API_TOKEN") or os.getenv("TALKSASA_API_TOKEN")
    sender_id = config_manager.get_config("TALKSASA_SENDER_ID") or os.getenv("TALKSASA_SENDER_ID", "TALKSASA")
    
    if not api_token:
        print("❌ ERROR: TALKSASA_API_TOKEN not found in config or environment")
        print("   Please set it using:")
        print("   - Config Manager in admin panel, or")
        print("   - Environment variable: export TALKSASA_API_TOKEN='your_token'")
        return False
    
    print(f"✓ API Token: {'*' * (len(api_token) - 4) + api_token[-4:]}")
    print(f"✓ Sender ID: {sender_id}")
    print(f"✓ Phone Number: {phone_number}")
    
    # Initialize service
    service = TalksasaNotificationService(api_token=api_token, sender_id=sender_id)
    
    if not service.available:
        print("❌ Service not available - API token invalid or missing")
        return False
    
    # Default test message
    if not message:
        message = f"Test notification from AmaniQuery at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print(f"\n📝 Test Message: {message}")
    print(f"   Length: {len(message)} characters")
    
    results = {}
    
    # Test SMS
    print("\n" + "-"*60)
    print("Testing SMS Channel...")
    print("-"*60)
    sms_result = service.send_sms(phone_number, message)
    results['sms'] = sms_result
    
    if sms_result.get("status") == "success":
        print("✅ SMS sent successfully!")
        if sms_result.get("data"):
            print(f"   Response: {sms_result.get('data')}")
    else:
        print(f"❌ SMS failed: {sms_result.get('message', 'Unknown error')}")
    
    # Test WhatsApp
    print("\n" + "-"*60)
    print("Testing WhatsApp Channel...")
    print("-"*60)
    whatsapp_result = service.send_whatsapp(phone_number, message)
    results['whatsapp'] = whatsapp_result
    
    if whatsapp_result.get("status") == "success":
        print("✅ WhatsApp sent successfully!")
        if whatsapp_result.get("data"):
            print(f"   Response: {whatsapp_result.get('data')}")
    else:
        error_code = whatsapp_result.get("error_code")
        error_message = whatsapp_result.get("message", "Unknown error")
        details = whatsapp_result.get("details", "")
        
        print(f"❌ WhatsApp failed: {error_message}")
        if error_code == 403:
            print("\n⚠️  403 Forbidden Error Details:")
            print("   This typically means:")
            print("   1. Your Talksasa account doesn't have WhatsApp enabled")
            print("   2. Your API token lacks WhatsApp permissions")
            print("   3. WhatsApp service is not available for your account plan")
            print("\n   Solution:")
            print("   - Contact Talksasa support to enable WhatsApp for your account")
            print("   - Or use SMS notifications instead (which should work)")
            if details:
                print(f"\n   Additional info: {details}")
        elif error_code:
            print(f"   Error code: {error_code}")
    
    # Test notification with fallback
    print("\n" + "-"*60)
    print("Testing Notification with WhatsApp Fallback...")
    print("-"*60)
    notification_result = service.send_notification(phone_number, message, "whatsapp")
    results['notification'] = notification_result
    
    if notification_result.get("status") == "success":
        print("✅ Notification sent successfully!")
    else:
        print(f"❌ Notification failed: {notification_result.get('message', 'Unknown error')}")
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"SMS:        {'✅ Success' if results['sms'].get('status') == 'success' else '❌ Failed'}")
    print(f"WhatsApp:    {'✅ Success' if results['whatsapp'].get('status') == 'success' else '❌ Failed'}")
    print(f"Notification: {'✅ Success' if results['notification'].get('status') == 'success' else '❌ Failed'}")
    
    return all(r.get("status") == "success" for r in results.values())


def test_notification_service(phone_number: str):
    """Test notification service with subscription"""
    print("\n" + "="*60)
    print("Testing Notification Service (with subscription)")
    print("="*60)
    
    try:
        config_manager = ConfigManager()
        notification_service = NotificationService(config_manager=config_manager)
        
        # Create test subscription
        from Module3_NiruDB.notification_models import SubscriptionCreate
        
        subscription = SubscriptionCreate(
            phone_number=phone_number,
            notification_type="whatsapp",
            schedule_type="immediate",
            categories=None,
            sources=None
        )
        
        print(f"📱 Creating subscription for: {phone_number}")
        result = notification_service.subscribe(subscription)
        
        if result:
            print("✅ Subscription created successfully!")
            print(f"   ID: {result.id}")
            print(f"   Type: {result.notification_type}")
            print(f"   Schedule: {result.schedule_type}")
            print(f"   Active: {result.is_active}")
            
            # Test sending notification
            print("\n📤 Testing article notification...")
            test_article = {
                "title": "Test Article: Notification System Working",
                "source_name": "AmaniQuery Test",
                "category": "Technology",
                "url": "https://amaniquery.test/article/1",
                "summary": "This is a test article to verify notification delivery"
            }
            
            sent_count = notification_service.send_article_notification(test_article)
            print(f"✅ Sent {sent_count} notification(s)")
            
            # Cleanup - unsubscribe
            print("\n🧹 Cleaning up test subscription...")
            notification_service.unsubscribe(phone_number)
            print("✅ Test subscription removed")
            
            return True
        else:
            print("❌ Failed to create subscription")
            return False
            
    except Exception as e:
        print(f"❌ Error testing notification service: {e}")
        logger.exception("Notification service test error")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test Talksasa SMS/WhatsApp notification channels"
    )
    parser.add_argument(
        "phone_number",
        help="Phone number to test (e.g., 0712345678 or +254712345678)"
    )
    parser.add_argument(
        "-m", "--message",
        help="Custom test message (optional)"
    )
    parser.add_argument(
        "-s", "--service-only",
        action="store_true",
        help="Test only Talksasa service (skip subscription test)"
    )
    parser.add_argument(
        "-n", "--notification-only",
        action="store_true",
        help="Test only notification service (skip direct Talksasa test)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("AmaniQuery Notification Channel Test")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = True
    
    # Test Talksasa service
    if not args.notification_only:
        success = test_talksasa_service(args.phone_number, args.message) and success
    
    # Test notification service
    if not args.service_only:
        success = test_notification_service(args.phone_number) and success
    
    print("\n" + "="*60)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    print("="*60 + "\n")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

