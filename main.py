import os
import math
import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import json

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()
GEN_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
EMBED_MODEL = "text-embedding-004"

worlds = []

# ---- Data Models ----
class WorldRequest(BaseModel):
    biome: str
    culture: str
    tone: str

class QueryRequest(BaseModel):
    query: str
    topN: int = 3

class FunctionCallRequest(BaseModel):
    message: str

# ---- Similarity Functions ----
def dot_product(a, b):
    return sum(x * y for x, y in zip(a, b))

def cosine_similarity(a, b):
    dot = dot_product(a, b)
    norm_a = math.sqrt(dot_product(a, a))
    norm_b = math.sqrt(dot_product(b, b))
    return dot / (norm_a * norm_b)

def euclidean_distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# ---- Prompt Builder ----
def build_prompt(biome, culture, tone):
    tone_instruction = {
        "mystical": "Use poetic language and evoke ancient mysteries.",
        "grimdark": "Emphasize brutality, decay, and moral ambiguity.",
        "hopeful": "Highlight resilience, rebirth, and unity."
    }.get(tone.lower(), "")

    return f"""
You are an AI worldbuilder. Your task is to generate a fictional world using step-by-step reasoning.

Step 1: Describe the biome - its climate, terrain, and flora.
Step 2: Based on the biome, infer the types of civilizations that could emerge.
Step 3: Describe the dominant culture - values, rituals, and architecture.
Step 4: Reflect the tone ({tone}) in the world's atmosphere and conflicts.
Step 5: Create a myth or legend that embodies the world's essence.

User Input:
Biome: {biome}
Culture: {culture}
Tone: {tone}

Instructions:
{tone_instruction}

First, reason through each step in natural language.
Then, return the final result in compact JSON format.
Do not skip the reasoning. Do not return only JSON.
"""

# ---- Gemini Helpers ----
def extract_json_and_reasoning(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    reasoning = text[:start].strip()
    json_text = text[start:end+1]
    try:
        parsed = json.loads(json_text)
        return reasoning, parsed
    except:
        return None

async def embed_text(text):
    model = genai.GenerativeModel(EMBED_MODEL)
    for attempt in range(3):
        try:
            res = model.embed_content(text)
            return res.embedding.values
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
            else:
                print("Embedding error:", e)
                return None

async def generate_world(biome, culture, tone):
    model = genai.GenerativeModel(GEN_MODEL)
    prompt = build_prompt(biome, culture, tone)

    # Define fallback world
    world = {
        "summary": "A mystical desert world shaped by nomadic wisdom.",
        "biome": biome,
        "culture": culture,
        "tone": tone,
        "myth": "The Whispering Wind guides lost souls to hidden sanctuaries."
    }
    reasoning = ""

    try:
        res = model.generate_content(prompt)
        text = res.text
        parsed = extract_json_and_reasoning(text)

        if parsed:
            reasoning, parsed_world = parsed
            # Only update keys that exist in fallback
            for key in world:
                if key in parsed_world:
                    world[key] = parsed_world[key]
    except Exception as e:
        print("Gemini generation error:", e)

    embedding_input = f"{world['summary']} {world['biome']} {world['culture']} {world['myth']}"
    embedding = await embed_text(embedding_input)

    return {
        "reasoning": reasoning,
        "world": world,
        "embedding": embedding
    }

# ---- Routes ----
@app.post("/generate-world")
async def generate_world_route(req: WorldRequest):
    result = await generate_world(req.biome, req.culture, req.tone)
    new_id = len(worlds) + 1
    full_world = {
        "id": new_id,
        "reasoning": result["reasoning"],
        **result["world"],
        "embedding": result["embedding"]
    }
    worlds.append(full_world)
    return { "message": "World generated", "world": full_world }

@app.get("/worlds")
def get_worlds():
    return { "worlds": worlds }

@app.post("/similar-worlds-dot")
async def similar_dot(req: QueryRequest):
    query_embedding = await embed_text(req.query)
    matches = [
        {
            "id": w["id"],
            "summary": w["summary"],
            "tone": w["tone"],
            "score": dot_product(query_embedding, w["embedding"])
        }
        for w in worlds if w["embedding"]
    ]
    matches.sort(key=lambda x: -x["score"])
    return { "matches": matches[:req.topN] }

@app.post("/similar-worlds-cosine")
async def similar_cosine(req: QueryRequest):
    query_embedding = await embed_text(req.query)
    matches = [
        {
            "id": w["id"],
            "summary": w["summary"],
            "tone": w["tone"],
            "similarity": cosine_similarity(query_embedding, w["embedding"])
        }
        for w in worlds if w["embedding"]
    ]
    matches.sort(key=lambda x: -x["similarity"])
    return { "matches": matches[:req.topN] }

@app.post("/similar-worlds-l2")
async def similar_l2(req: QueryRequest):
    query_embedding = await embed_text(req.query)
    matches = [
        {
            "id": w["id"],
            "summary": w["summary"],
            "tone": w["tone"],
            "distance": euclidean_distance(query_embedding, w["embedding"])
        }
        for w in worlds if w["embedding"]
    ]
    matches.sort(key=lambda x: x["distance"])
    return { "matches": matches[:req.topN] }

@app.post("/ai-function-call")
async def function_call(req: FunctionCallRequest):
    model = genai.GenerativeModel(GEN_MODEL)
    try:
        res = model.generate_content(
            {
                "contents": [{ "role": "user", "parts": [{ "text": req.message }] }]
            },
            {
                "functionDeclarations": [
                    {
                        "function": {
                            "name": "generateWorld",
                            "description": "Generate a fictional world",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "biome": { "type": "string" },
                                    "culture": { "type": "string" },
                                    "tone": { "type": "string" }
                                },
                                "required": ["biome", "culture", "tone"]
                            }
                        }
                    }
                ]
            }
        )
        fn = res.function_call
        if not fn or fn.name != "generateWorld":
            return { "error": "No valid function call returned" }

        result = await generate_world(fn.args["biome"], fn.args["culture"], fn.args["tone"])
        new_id = len(worlds) + 1
        full_world = {
            "id": new_id,
            "reasoning": result["reasoning"],
            **result["world"],
            "embedding": result["embedding"]
        }
        worlds.append(full_world)
        return { "message": "Function call successful", "functionCall": fn, "world": full_world }

    except Exception as e:
        print("Function calling error:", e)
        return { "error": "Function calling failed" }

# ---- Run Server ----
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)