"""
Telegram Notifier Module
Sends messages to Telegram using Bot API
"""
import requests
from typing import Optional
from utils.logger import logger
from config import Config

class TelegramNotifier:
    """Handles sending messages to Telegram"""
    
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message to Telegram
        
        Args:
            message: Message text
            parse_mode: "Markdown" or "HTML"
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_long_message(self, message: str, chunk_size: int = 4000) -> bool:
        """
        Send a long message by splitting it into chunks if necessary
        
        Args:
            message: Long message text
            chunk_size: Maximum size per chunk
            
        Returns:
            True if all chunks sent successfully
        """
        if len(message) <= chunk_size:
            return self.send_message(message)
        
        # Split into chunks
        chunks = self._split_message(message, chunk_size)
        
        success = True
        for i, chunk in enumerate(chunks):
            logger.info(f"Sending chunk {i+1}/{len(chunks)}")
            if not self.send_message(chunk):
                success = False
        
        return success
    
    def _split_message(self, message: str, chunk_size: int) -> list:
        """Split message into chunks at line breaks"""
        lines = message.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > chunk_size:
                # Save current chunk and start new one
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Add last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def test_connection(self) -> bool:
        """
        Test if bot can connect to Telegram
        
        Returns:
            True if connection successful
        """
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"Bot connected: {bot_info.get('result', {}).get('username', 'Unknown')}")
                return True
            else:
                logger.error(f"Bot connection failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error testing bot connection: {e}")
            return False
