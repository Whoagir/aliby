"""
Room access control: decrypt links, verify passwords
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ..room_crypto import decrypt_room_link
from ..api.rooms import active_rooms

router = APIRouter(prefix="/room-access", tags=["room-access"])

class DecryptLinkRequest(BaseModel):
    encrypted_link: str

class VerifyPasswordRequest(BaseModel):
    room_code: str
    password: str

@router.post("/decrypt")
def decrypt_link(request: DecryptLinkRequest):
    """Decrypt room link to get room code"""
    room_code = decrypt_room_link(request.encrypted_link)
    if room_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room link"
        )
    
    # Check if room exists
    if room_code not in active_rooms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found or expired"
        )
    
    room = active_rooms[room_code]
    has_password = bool(room.settings.room_password)
    
    return {
        "room_code": room_code,
        "has_password": has_password
    }

@router.post("/verify-password")
def verify_password(request: VerifyPasswordRequest):
    """Verify room password"""
    if request.room_code not in active_rooms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    room = active_rooms[request.room_code]
    
    # Check if room has password
    if not room.settings.room_password:
        return {"valid": True}  # No password set
    
    # Verify password
    if request.password == room.settings.room_password:
        return {"valid": True}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
