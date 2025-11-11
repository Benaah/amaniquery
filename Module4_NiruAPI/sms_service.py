"""
Africa's Talking SMS Service Integration
Handles sending and receiving SMS messages
"""
from typing import Optional, Dict
from loguru import logger
import os


class AfricasTalkingSMSService:
    """Service for Africa's Talking SMS integration"""
    
    def __init__(self, username: str = None, api_key: str = None):
        """
        Initialize Africa's Talking SMS service
        
        Args:
            username: Africa's Talking username (default from env)
            api_key: Africa's Talking API key (default from env)
        """
        self.username = username or os.getenv("AT_USERNAME", "sandbox")
        self.api_key = api_key or os.getenv("AT_API_KEY", "")
        
        # Initialize Africa's Talking SDK
        try:
            import africastalking
            self.africastalking = africastalking
            self.africastalking.initialize(self.username, self.api_key)
            self.sms = self.africastalking.SMS
            self.available = True
            logger.info(f"Africa's Talking initialized for user: {self.username}")
        except ImportError:
            logger.warning("africastalking package not installed. SMS features disabled.")
            self.available = False
        except Exception as e:
            logger.error(f"Failed to initialize Africa's Talking: {e}")
            self.available = False
    
    def send_sms(self, phone_number: str, message: str) -> Dict:
        """
        Send SMS to a phone number
        
        Args:
            phone_number: Recipient phone number (format: +254XXXXXXXXX)
            message: SMS message text (max 160 chars for single SMS)
            
        Returns:
            Dictionary with status and details
        """
        if not self.available:
            return {
                "success": False,
                "error": "SMS service not available",
                "message": "africastalking package not installed"
            }
        
        try:
            # Validate phone number format
            if not phone_number.startswith("+"):
                phone_number = f"+{phone_number}"
            
            # Send SMS
            response = self.sms.send(message, [phone_number])
            
            logger.info(f"SMS sent to {phone_number}: {response}")
            
            # Parse response
            if response['SMSMessageData']['Recipients']:
                recipient = response['SMSMessageData']['Recipients'][0]
                
                if recipient['status'] == 'Success':
                    return {
                        "success": True,
                        "message_id": recipient.get('messageId'),
                        "cost": recipient.get('cost'),
                        "phone_number": phone_number,
                        "message": message
                    }
                else:
                    return {
                        "success": False,
                        "error": recipient.get('status'),
                        "phone_number": phone_number
                    }
            else:
                return {
                    "success": False,
                    "error": "No recipients in response",
                    "response": response
                }
                
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number
            }
    
    def send_multi_part_sms(self, phone_number: str, messages: list) -> Dict:
        """
        Send multiple SMS messages in sequence
        
        Args:
            phone_number: Recipient phone number
            messages: List of message strings
            
        Returns:
            Dictionary with status and details
        """
        results = []
        
        for i, message in enumerate(messages):
            result = self.send_sms(phone_number, message)
            results.append({
                "part": i + 1,
                "total": len(messages),
                **result
            })
            
            if not result.get("success"):
                logger.error(f"Failed to send part {i+1}/{len(messages)}")
                break
        
        all_success = all(r.get("success") for r in results)
        
        return {
            "success": all_success,
            "parts_sent": len(results),
            "total_parts": len(messages),
            "results": results,
            "phone_number": phone_number
        }
    
    def parse_incoming_sms(self, webhook_data: Dict) -> Dict:
        """
        Parse incoming SMS webhook data from Africa's Talking
        
        Args:
            webhook_data: Webhook POST data from Africa's Talking
            
        Returns:
            Parsed SMS data
        """
        try:
            return {
                "from": webhook_data.get("from"),
                "to": webhook_data.get("to"),
                "text": webhook_data.get("text", "").strip(),
                "date": webhook_data.get("date"),
                "id": webhook_data.get("id"),
                "linkId": webhook_data.get("linkId"),
                "networkCode": webhook_data.get("networkCode"),
            }
        except Exception as e:
            logger.error(f"Error parsing incoming SMS: {e}")
            return {
                "error": str(e),
                "raw_data": webhook_data
            }
    
    def validate_webhook_signature(self, request_data: str, signature: str) -> bool:
        """
        Validate webhook signature for security
        
        Args:
            request_data: Raw request body
            signature: X-Africastalking-Signature header value
            
        Returns:
            True if signature is valid
        """
        # TODO: Implement HMAC signature validation
        # For now, basic validation
        return True
    
    def format_kenyan_phone(self, phone_number: str) -> str:
        """
        Format phone number to Kenya format (+254...)
        
        Args:
            phone_number: Phone number in various formats
            
        Returns:
            Formatted phone number with +254 prefix
        """
        # Remove spaces and special characters
        phone = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Handle different formats
        if phone.startswith("+254"):
            return phone
        elif phone.startswith("254"):
            return f"+{phone}"
        elif phone.startswith("0"):
            return f"+254{phone[1:]}"
        elif phone.startswith("7") or phone.startswith("1"):
            return f"+254{phone}"
        else:
            return phone  # Return as-is if unrecognized
    
    def get_account_balance(self) -> Dict:
        """Get Africa's Talking account balance"""
        if not self.available:
            return {"error": "Service not available"}
        
        try:
            application = self.africastalking.Application
            response = application.fetch_application_data()
            
            return {
                "balance": response.get("UserData", {}).get("balance"),
                "currency": "KES"  # Kenya Shillings
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {"error": str(e)}
