from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from ..services.vision import analyze_image_with_vision, make_autonomous_decision

router = APIRouter()

@router.post("/vision/analyze")
async def vision_analyze(image: UploadFile = File(...), prompt: str = Form("Describe what you see in detail")):
    if not image:
        raise HTTPException(status_code=400, detail="No image uploaded")
    try:
        image_bytes = await image.read()
        description = analyze_image_with_vision(image_bytes, prompt)
        return JSONResponse({"success": True, "description": description, "prompt": prompt})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {str(e)}")

@router.post("/autonomous/decide")
async def autonomous_decide(image: UploadFile = File(...), goal: str = Form(...), previous_actions: str = Form("[]")):
    if not image:
        raise HTTPException(status_code=400, detail="No image uploaded")
    try:
        import json
        image_bytes = await image.read()
        actions_list = json.loads(previous_actions)
        result = make_autonomous_decision(image_bytes, goal, actions_list)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error making decision: {str(e)}")
