import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
import torch
import os
import json
import asyncio
from threading import Thread

# For debugging
import debugpy
debugpy.listen(("0.0.0.0", 5681))
print("Waiting for debugger attach...")

app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
tokenizer = None

@app.on_event("startup")
async def load_model():
    global model, tokenizer
    print("Loading model...")
    # model_name = os.getenv("MODEL_NAME", "distilgpt2") 
    model_name = "distilgpt2"
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            # load_in_8bit=True,
            low_cpu_mem_usage=True
        )
        
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        print(f"Model {model_name} loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

@app.post("/generate")
async def generate_text(request: fastapi.Request):
    global model, tokenizer
    
    if model is None or tokenizer is None:
        raise fastapi.HTTPException(status_code=503, detail="Model not loaded yet")
    
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        max_tokens = data.get("max_tokens", 512)
        temperature = data.get("temperature", 0.7)
        
        if not prompt:
            raise fastapi.HTTPException(status_code=400, detail="Prompt is required")
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        
        # Move to device if using GPU
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=temperature,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=2
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove the original prompt from response
        if response.startswith(prompt):
            response = response[len(prompt):].strip()
        
        return {"response": response}
        
    except Exception as e:
        print(f"Generation error: {e}")
        raise fastapi.HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.websocket("/generate-stream")
async def generate_stream(websocket: WebSocket):
    global model, tokenizer
    
    await websocket.accept()
    
    if model is None or tokenizer is None:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Model not loaded yet"
        }))
        await websocket.close()
        return
    
    try:
        while True:
            # Receive request
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            prompt = request_data.get("prompt", "")
            max_tokens = request_data.get("max_tokens", 512)
            temperature = request_data.get("temperature", 0.7)
            
            if not prompt:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Prompt is required"
                }))
                continue
            
            # Send start signal
            await websocket.send_text(json.dumps({
                "type": "start",
                "message": "Starting generation..."
            }))
            
            # Tokenize input
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            
            # Move to device if using GPU
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Create streamer
            streamer = TextIteratorStreamer(
                tokenizer, 
                timeout=120, 
                skip_prompt=True, 
                skip_special_tokens=True
            )
            
            # Generation parameters
            generation_kwargs = dict(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=temperature,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                streamer=streamer,
                no_repeat_ngram_size=2
            )
            
            # Run generation in separate thread
            thread = Thread(target=model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Stream tokens as they're generated
            full_response = ""
            for new_text in streamer:
                if new_text:
                    full_response += new_text
                    await websocket.send_text(json.dumps({
                        "type": "token",
                        "token": new_text,
                        "full_text": full_response
                    }))
                    # await asyncio.sleep(0.05)
            
            # Send completion signal
            await websocket.send_text(json.dumps({
                "type": "complete",
                "full_response": full_response
            }))
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Generation error: {str(e)}"
            }))
        except:
            pass

@app.get("/health")
def health():
    global model, tokenizer
    status = "healthy" if (model is not None and tokenizer is not None) else "loading"
    return {"status": f"LLM service is {status}"}