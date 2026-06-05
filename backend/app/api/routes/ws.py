# backend/app/api/routes/ws.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from jose import jwt, JWTError
from app.core.config import settings
from app.core.websocket_manager import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/admin")
async def admin_websocket(
    websocket: WebSocket,
    token: str = Query(...),          # JWT passed as ?token= because browsers
):                                     # cannot set Authorization headers on WS
    """
    WebSocket endpoint for live admin dashboard updates.
    1. Decode JWT from query param
    2. Verify role == admin
    3. Accept connection and add to manager
    4. Keep alive — receive loop runs until client disconnects
    """

    # --- Step 1 & 2: Authenticate before accepting ---
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        role: str = payload.get("role")
        if role != "admin":
            # Close with 403 before accepting — note: we close without accepting
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # --- Step 3: Accept and register ---
    await manager.connect(websocket)

    # --- Step 4: Keep-alive receive loop ---
    try:
        while True:
            # We don't process incoming messages from admin,
            # but we MUST await receive to detect disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Admin WebSocket client disconnected cleanly.")
    except Exception as e:
        manager.disconnect(websocket)
        logger.warning(f"Admin WebSocket error: {e}")