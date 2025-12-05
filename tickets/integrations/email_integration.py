"""
Интеграция с email для приёма обращений
"""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any
import logging
from django.conf import settings
from ..channel_handler import ChannelHandler
from ..models import Channel

logger = logging.getLogger(__name__)


class EmailIntegration:
    """Обработчик входящих email-обращений"""
    
    def __init__(self):
        self.imap_server = getattr(settings, 'EMAIL_IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = getattr(settings, 'EMAIL_IMAP_PORT', 993)
        self.email_address = getattr(settings, 'SUPPORT_EMAIL', '')
        self.email_password = getattr(settings, 'SUPPORT_EMAIL_PASSWORD', '')
    
    def fetch_new_emails(self) -> List[Dict[str, Any]]:
        """
        Подключается к почтовому ящику и получает новые письма
        
        Returns:
            Список обработанных сообщений
        """
        if not self.email_address or not self.email_password:
            logger.warning("Email credentials not configured")
            return []
        
        processed = []
        
        try:
            # Подключаемся к IMAP серверу
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select('INBOX')
            
            # Ищем непрочитанные письма
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.error("Failed to search emails")
                return []
            
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                try:
                    # Получаем письмо
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Парсим письмо
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Извлекаем данные
                    subject = self._decode_header(msg['Subject'])
                    from_email = email.utils.parseaddr(msg['From'])[1]
                    message_id = msg['Message-ID']
                    
                    # Получаем текст письма
                    body = self._get_email_body(msg)
                    
                    # Получаем вложения (изображения)
                    image_data = self._get_first_image(msg)
                    
                    # Обрабатываем через единый обработчик
                    result = ChannelHandler.process_incoming_message(
                        channel=Channel.CHANNEL_EMAIL,
                        user_identifier=from_email,
                        text=body or subject,
                        image_data=image_data,
                        external_id=message_id,
                        metadata={
                            "subject": subject,
                            "from": from_email,
                        }
                    )
                    
                    # Отправляем ответ
                    self._send_reply(from_email, subject, result['reply'])
                    
                    # Помечаем как прочитанное
                    mail.store(email_id, '+FLAGS', '\\Seen')
                    
                    processed.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Email integration error: {e}")
        
        return processed
    
    def _decode_header(self, header: str) -> str:
        """Декодирует заголовок письма"""
        if not header:
            return ""
        
        decoded = decode_header(header)
        result = []
        
        for part, encoding in decoded:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                result.append(part)
        
        return ''.join(result)
    
    def _get_email_body(self, msg: email.message.Message) -> str:
        """Извлекает текст письма"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        
        return body.strip()
    
    def _get_first_image(self, msg: email.message.Message) -> bytes:
        """Извлекает первое изображение из вложений"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type.startswith('image/'):
                    try:
                        return part.get_payload(decode=True)
                    except:
                        continue
        return None
    
    def _send_reply(self, to_email: str, original_subject: str, reply_text: str):
        """Отправляет ответ на email"""
        from django.core.mail import send_mail
        
        subject = f"Re: {original_subject}" if not original_subject.startswith("Re:") else original_subject
        
        try:
            send_mail(
                subject=subject,
                message=reply_text,
                from_email=self.email_address,
                recipient_list=[to_email],
                fail_silently=False,
            )
            logger.info(f"Reply sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send reply to {to_email}: {e}")
