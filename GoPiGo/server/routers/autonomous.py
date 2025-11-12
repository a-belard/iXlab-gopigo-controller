from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

# Simple in-memory autonomous state
autonomous_state = {
    "active": False,
    "goal": "",
    "history": [],
    "last_action": "",
    "action_count": 0,
    "max_actions": 0,
}

class AutonomousCommand(BaseModel):
    goal: str
    max_actions: int = 20

@router.post("/autonomous/start")
async def autonomous_start(command: AutonomousCommand):
    global autonomous_state
    autonomous_state.update({
        "active": True,
        "goal": command.goal,
        "history": [],
        "last_action": "",
        "action_count": 0,
        "max_actions": command.max_actions,
    })
    return JSONResponse({
        "success": True,
        "message": f"Autonomous mode started with goal: {command.goal}",
        "max_actions": command.max_actions,
    })

@router.post("/autonomous/stop")
async def autonomous_stop():
    global autonomous_state
    autonomous_state["active"] = False
    return JSONResponse({
        "success": True,
        "message": "Autonomous mode stopped",
        "total_actions": autonomous_state.get("action_count", 0),
        "history": autonomous_state.get("history", []),
    })

@router.get("/autonomous/status")
async def autonomous_status():
    return JSONResponse({
        "active": autonomous_state.get("active", False),
        "goal": autonomous_state.get("goal", ""),
        "action_count": autonomous_state.get("action_count", 0),
        "last_action": autonomous_state.get("last_action", ""),
        "max_actions": autonomous_state.get("max_actions", 0),
        "history_length": len(autonomous_state.get("history", [])),
    })
