from fastapi import status, APIRouter, Body
from fastapi.responses import JSONResponse
import asyncio
import uuid
from controllers.graph_state import run_agent

router = APIRouter()

original_iris_id = str(uuid.uuid4())

@router.get("/api/iris-id")
def get_iris_id():
    return {"iris_id": original_iris_id}

@router.get("/iris/{iris_id}")
async def chat_endpoint(iris_id: str = None, user_input: str = ""):
    if iris_id is None or iris_id != original_iris_id or iris_id == "":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "Invalid iris_id"})
    user_input = user_input.strip()
    agent_response = ""
    async for response in run_agent(user_input, iris_id):
        agent_response = response
    return JSONResponse(status_code=status.HTTP_200_OK, content={"agent_response": agent_response})