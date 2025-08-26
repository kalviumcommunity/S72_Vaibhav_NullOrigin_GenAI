require("dotenv").config();
const express = require("express");
const { GoogleGenerativeAI } = require("@google/generative-ai");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// ---- Gemini Setup ----
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const GEN_MODEL = process.env.GEMINI_MODEL || "gemini-1.5-flash";

// ---- In-memory World Store ----
let worlds = [];

// ---- Embedding Helpers ----
function getClient() {
  try {
    return new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
  } catch {
    return null;
  }
}

async function embedText(text, retries = 3) {
  const client = getClient();
  if (!client) return null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const model = client.getGenerativeModel({ model: "text-embedding-004" });
      const res = await model.embedContent(text);
      const values = res?.embedding?.values;
      if (Array.isArray(values)) return values;
    } catch (err) {
      if (err.response?.status === 429 && attempt < retries) {
        const delay = 1000 * Math.pow(2, attempt); // 1s, 2s, 4s...
        console.warn(`Rate limit hit. Retrying in ${delay / 1000}s... (attempt ${attempt + 1})`);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      console.error("Gemini embedding error:", err.message);
      return null;
    }
  }

  return null;
}

// ---- Dot Product Similarity ----
function dotProduct(vecA, vecB) {
  if (!vecA || !vecB || vecA.length !== vecB.length) return null;
  return vecA.reduce((sum, val, i) => sum + val * vecB[i], 0);
}

// ---- Prompt Builder ----
function buildChainOfThoughtPrompt(biome, culture, tone) {
  let toneInstruction = "";
  if (tone.toLowerCase() === "mystical") {
    toneInstruction = "Use poetic language and evoke ancient mysteries.";
  } else if (tone.toLowerCase() === "grimdark") {
    toneInstruction = "Emphasize brutality, decay, and moral ambiguity.";
  } else if (tone.toLowerCase() === "hopeful") {
    toneInstruction = "Highlight resilience, rebirth, and unity.";
  }

  return `
You are an AI worldbuilder. Your task is to generate a fictional world using step-by-step reasoning.

Step 1: Describe the biome — its climate, terrain, and flora.
Step 2: Based on the biome, infer the types of civilizations that could emerge.
Step 3: Describe the dominant culture — values, rituals, and architecture.
Step 4: Reflect the tone (${tone}) in the world’s atmosphere and conflicts.
Step 5: Create a myth or legend that embodies the world’s essence.

User Input:
Biome: ${biome}
Culture: ${culture}
Tone: ${tone}

Instructions:
${toneInstruction}

First, reason through each step in natural language.
Then, return the final result in compact JSON format.
Do not skip the reasoning. Do not return only JSON.
`;
}

// ---- Response Parser ----
function extractJsonAndReasoning(text) {
  const jsonStart = text.indexOf("{");
  const jsonEnd = text.lastIndexOf("}");
  if (jsonStart === -1 || jsonEnd === -1 || jsonEnd <= jsonStart) return null;

  const reasoning = text.slice(0, jsonStart).trim();
  const jsonText = text.slice(jsonStart, jsonEnd + 1);

  try {
    const parsed = JSON.parse(jsonText);
    return { reasoning, world: parsed };
  } catch {
    return null;
  }
}

// ---- World Generator ----
async function generateWorld(biome, culture, tone) {
  const model = genAI.getGenerativeModel({ model: GEN_MODEL });
  const prompt = buildChainOfThoughtPrompt(biome, culture, tone);

  try {
    const result = await model.generateContent(prompt);
    const fullText = result.response.text();

    console.log("Gemini full response:\n", fullText); // For debugging

    const parsed = extractJsonAndReasoning(fullText);
    if (!parsed) throw new Error("Failed to parse Gemini response");

    return parsed;
  } catch (err) {
    console.error("Gemini generation error:", err.message);
    return {
      reasoning: "",
      world: {
        summary: "A mystical desert world shaped by nomadic wisdom.",
        biome,
        culture,
        tone,
        myth: "The Whispering Wind guides lost souls to hidden sanctuaries."
      }
    };
  }
}

// ---- Routes ----

// POST /generate-world
app.post("/generate-world", async (req, res) => {
  const { biome, culture, tone } = req.body;
  if (!biome || !culture || !tone) {
    return res.status(400).json({ error: "biome, culture, and tone are required" });
  }

  const { reasoning, world } = await generateWorld(biome, culture, tone);

  const embeddingInput = `${world.summary} ${world.biome} ${world.culture} ${world.myth}`;
  await new Promise(resolve => setTimeout(resolve, 1000)); // throttle
  const embedding = await embedText(embeddingInput);

  const newId = worlds.length ? Math.max(...worlds.map(w => w.id)) + 1 : 1;
  const fullWorld = {
    id: newId,
    reasoning,
    ...world,
    embedding
  };

  worlds.push(fullWorld);
  res.status(201).json({ message: "World generated", world: fullWorld });
});

// GET /worlds
app.get("/worlds", (req, res) => {
  res.json({ worlds });
});

// PUT /update-world/:id
app.put("/update-world/:id", (req, res) => {
  const id = Number(req.params.id);
  const { biome, culture, tone, summary, myth } = req.body;

  const idx = worlds.findIndex(w => w.id === id);
  if (idx === -1) return res.status(404).json({ error: "World not found" });

  const before = { ...worlds[idx] };
  if (biome) worlds[idx].biome = biome;
  if (culture) worlds[idx].culture = culture;
  if (tone) worlds[idx].tone = tone;
  if (summary) worlds[idx].summary = summary;
  if (myth) worlds[idx].myth = myth;

  res.json({ message: "World updated", before, after: worlds[idx] });
});

// POST /similar-worlds-dot
app.post("/similar-worlds-dot", async (req, res) => {
  const { query, topN = 3 } = req.body;
  if (!query) return res.status(400).json({ error: "Query is required" });

  const queryEmbedding = await embedText(query);
  if (!queryEmbedding) return res.status(500).json({ error: "Failed to embed query" });

  const scored = worlds
    .filter(w => Array.isArray(w.embedding))
    .map(w => ({
      id: w.id,
      summary: w.summary,
      tone: w.tone,
      score: dotProduct(queryEmbedding, w.embedding)
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topN);

  res.json({ matches: scored });
});

// ---- Start Server ----
app.listen(PORT, () => {
  console.log(`🚀 NullOrigin server running at http://localhost:${PORT}`);
});