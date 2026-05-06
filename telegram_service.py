import requests
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramService:
    """
    Service for sending notifications and alerts via Telegram
    """
    
    def __init__(self, bot_token=None, chat_id=None):
        """
        Initialize Telegram service
        
        Args:
            bot_token: Telegram bot token (from @BotFather)
            chat_id: Telegram chat ID to send messages to
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None
        
        if not self.bot_token:
            print("[WARNING] Telegram Bot Token not found in environment variables")
        if not self.chat_id:
            print("[WARNING] Telegram Chat ID not found in environment variables")

    def send_message(self, message):
        """
        Send a text message to the configured chat
        
        Args:
            message: Text message to send
            
        Returns:
            Boolean indicating success
        """
        if not self.api_url or not self.chat_id:
            return False
            
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram message: {e}")
            return False

    def send_alert(self, alert_type, data):
        """
        Send a formatted alert message
        
        Args:
            alert_type: Type of alert (e.g., 'speeding', 'wrong_way', 'blacklist')
            data: Dictionary containing alert details
            
        Returns:
            Boolean indicating success
        """
        emoji_map = {
            'speeding': '🚀',
            'wrong_way': '⛔',
            'blacklist': '🚨',
            'heavy_traffic': '🚗🚕🚙',
            'system': '🔧'
        }
        
        emoji = emoji_map.get(alert_type, '⚠️')
        title = alert_type.replace('_', ' ').upper()
        
        message = f"<b>{emoji} {title} ALERT {emoji}</b>\n\n"
        
        for key, value in data.items():
            formatted_key = key.replace('_', ' ').capitalize()
            message += f"<b>{formatted_key}:</b> {value}\n"
            
        message += f"\n<i>Timestamp: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}</i>"
        
        return self.send_message(message)

    def send_photo(self, photo_path, caption=None):
        """
        Send a photo to the configured chat
        
        Args:
            photo_path: Path to the photo file
            caption: Optional caption for the photo
            
        Returns:
            Boolean indicating success
        """
        if not self.bot_token or not self.chat_id:
            return False
            
        photo_url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                payload = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(photo_url, data=payload, files=files, timeout=20)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram photo: {e}")
            return False
