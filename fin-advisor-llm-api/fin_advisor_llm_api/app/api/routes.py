from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import logging

from fin_advisor_llm_api.app.chains.fin_advisor_chain import generate_chain_with_history, reflective_stream_chain, tool_agent_chain
from fin_advisor_llm_api.app.chains.planning_agent import PlanningAgent

router = APIRouter(prefix='/api/v1', tags=["v1"])

# Create a Pydantic model for the request body
class QuestionRequest(BaseModel):
    question: str
    sessionId: str

logger = logging.getLogger(__name__)

@router.post("/rag/default/stream")
async def rag_stream(request: QuestionRequest):
    try:
        async def generate():
            print("Starting stream generation")
            # Configure the session for this request
            config = {"configurable": {"session_id": request.sessionId}}
            
            # Use the chain with history instead of the base chain
            for chunk in generate_chain_with_history.stream(
                {"question": request.question, "critique_output": "" }, 
                config=config
            ):
                print(f"Generated chunk: {chunk}")
                if chunk:
                    chunk_str = str(chunk)
                    message = f"data: {chunk_str}\n\n".encode('utf-8')
                    print(f"Yielding message: {message}")
                    yield message
                    await asyncio.sleep(0.01)
            
            print("Stream completed")
            yield b"data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "X-Accel-Buffering": "no",
                "Transfer-Encoding": "chunked"
            }
        )
    except Exception as e:
        print(f"Error in stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reflective/stream")
async def reflective_stream(request: QuestionRequest):
    config = {"configurable": {"session_id": request.sessionId}}
    critique_output, logs = reflective_stream_chain(question=request.question, config=config)

    try:
        final_response = generate_chain_with_history.invoke(
            {
                "question": request.question,
                "critique_output": critique_output
            },
            config=config
        )
        
        return {"final_response": final_response, "logs":logs}
    except Exception as e:
        print(f"Error in stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/tool/agent")
async def reflective_stream(request: QuestionRequest):
    config = {"configurable": {"session_id": request.sessionId}}

    try:
        
        response = tool_agent_chain(question=request.question, config=config)
        
        return response
    except Exception as e:
        print(f"Error in stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    


# @router.post("/reflective/stream")
# async def reflective_stream(request: QuestionRequest):
#     config = {"configurable": {"session_id": request.sessionId}}
#     critique_output, logs = reflective_stream_chain(question=request.question, config=config)

#     try:
#         async def generate():
#             print("Starting stream generation")
#             # Configure the session for this request
#             config = {"configurable": {"session_id": request.sessionId}}
#             # Use the chain with history instead of the base chain
#             print(logs)
#             yield logs
#             for chunk in generate_chain_with_history.stream(
#                 {"question": request.question, "critique_output": critique_output }, 
#                 config=config
#             ):
#                 if chunk:
#                     chunk_str = str(chunk)
#                     message = f"data: {chunk_str}\n\n".encode('utf-8')
#                     # print(f"Yielding message: {message}")
#                     yield message
#                     # await asyncio.sleep(0.01)
#             yield b"data: [DONE]\n\n"
        
#         return StreamingResponse(
#             generate(),
#             media_type="text/event-stream",
#             headers={
#                 "Cache-Control": "no-cache",
#                 "Connection": "keep-alive",
#                 "Access-Control-Allow-Origin": "*",
#                 "X-Accel-Buffering": "no",
#                 "Transfer-Encoding": "chunked"
#             }
#         )
#     except Exception as e:
#         print(f"Error in stream: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

    
@router.post("/planning/execute")
async def execute_planning_agent(request: QuestionRequest):
    try:
        config = {"configurable": {"session_id": request.sessionId}}
        planning_agent = PlanningAgent()
        response = planning_agent.run(request.question, config)
        
        # Validate response structure
        if "error" in response:
            raise HTTPException(
                status_code=500,
                detail=response["error"]
            )
            
        return {
            "status": "success",
            "data": response,
            "message": "Financial plan executed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in execute_planning_agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    