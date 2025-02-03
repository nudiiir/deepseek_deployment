from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import httpx
from fastapi.responses import StreamingResponse
import asyncio
import json
import re

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama API settings (update if needed)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:1.5b"

class QueryRequest(BaseModel):
    prompt: str

def clean_response(text: str) -> str:
    # Example: remove <think> and </think> tags if needed
    return re.sub(r"</?think>", "", text)

@app.post("/query")
async def send_query_to_ollama(request: QueryRequest):
    payload = {
        "model": MODEL_NAME,
        "prompt": request.prompt,
        "stream": True,  # Set to True for streaming mode
    }
    print('the payload : {payload}')
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5)) as client:
            logging.debug(f"Sending request to Ollama with payload: {payload['prompt']}")
            response = await client.post(OLLAMA_URL, json=payload)

            logging.debug(f"Received response from Ollama: {response.status_code}")
            logging.debug(f"Response headers: {response.headers}")

            if response.status_code != 200:
                # Read full response body for error details
                response_body = await response.aread()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error in Ollama response: {response_body.decode()}"
                )

            async def stream_generator():
                try:
                    # Read the stream as it comes in
                    async for chunk in response.aiter_text():
                        try:
                            data = json.loads(chunk)
                            text = data.get("response", "")
                            text = clean_response(text)

                            # Yield the text piece by piece (word by word)
                            words = text.split()
                            for word in words:
                                yield word + " "
                                await asyncio.sleep(0.05)  # Simulate a slight delay
                        except json.JSONDecodeError:
                            yield chunk  # Yield raw chunk in case of JSON error
                except (httpx.StreamClosed, asyncio.CancelledError) as e:
                    logging.info(f"Stream closed or cancelled: {e}")
                finally:
                    await response.aclose()

            return StreamingResponse(stream_generator(), media_type="text/plain")

    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")
    except (httpx.StreamClosed, asyncio.CancelledError) as e:
        logging.info(f"Stream closed or cancelled: {e}")
        raise HTTPException(status_code=500, detail="Stream closed unexpectedly")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
