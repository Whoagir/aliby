"""
Room code encryption/decryption for secure links
Format: ROOM_CODE|TIMESTAMP -> base64
Example: BADW|202602011430 -> QkFEV3wyMDI2MDIwMTE0MzA=
"""
import base64
from datetime import datetime
from typing import Optional

def encrypt_room_link(room_code: str) -> str:
    """
    Encrypt room code with timestamp for URL
    BADW -> BADW|202602011430 -> base64
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    payload = f"{room_code}|{timestamp}"
    encrypted = base64.b64encode(payload.encode()).decode()
    return encrypted

def decrypt_room_link(encrypted_link: str) -> Optional[str]:
    """
    Decrypt room link to get room code
    base64 -> BADW|202602011430 -> BADW
    Returns None if invalid
    """
    try:
        decrypted = base64.b64decode(encrypted_link.encode()).decode()
        # Format: ROOM_CODE|TIMESTAMP
        parts = decrypted.split("|")
        if len(parts) != 2:
            return None
        room_code = parts[0]
        # Validate room code (4 uppercase letters)
        if len(room_code) == 4 and room_code.isalpha() and room_code.isupper():
            return room_code
        return None
    except Exception:
        return None
