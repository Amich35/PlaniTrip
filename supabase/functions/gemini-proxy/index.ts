// Edge Function: gemini-proxy
// Relaie une requête vers l'API Gemini (generateContent, endpoint stable
// recommandé pour la production — l'Interactions API plus récente reste en
// Beta au moment de l'implémentation). BYOK : la clé personnelle de
// l'utilisateur est transmise uniquement pour cette requête en cours, jamais
// stockée en base, jamais loggée, jamais renvoyée dans une erreur.
// Exige une session Supabase UTILISATEUR authentifiée valide (pas seulement
// une clé anon) — aucun accès anonyme à ce proxy. Même architecture que
// openai-proxy, pour une cohérence de sécurité entre tous les fournisseurs IA.
// Aucun prompt métier ni logique PlaniTrip ici : payload minimal, whitelisté,
// relayé vers Gemini. N'accepte que POST (+ OPTIONS pour le préflight CORS).
// B4 : support optionnel des Structured Outputs (responseSchema) — protocole
// générique Gemini, pas de logique métier PlaniTrip.

import { createClient } from "jsr:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// Whitelist des modèles Gemini réellement supportés par PlaniTrip. Reflète
// volontairement AI_MODELS.gemini côté client (index.html) — dupliqué ici par
// choix, pour que cette fonction reste un proxy strict et non un relais
// générique vers n'importe quel modèle Gemini. À maintenir en synchronisation
// manuelle si AI_MODELS.gemini évolue côté client.
const ALLOWED_MODELS = new Set(["gemini-3.6-flash"]);

// Whitelist des tools autorisés — seul le grounding Google Search est utilisé
// par PlaniTrip. Un item valide est exactement { google_search: {} }.
function isAllowedTool(t: unknown): boolean {
  if (!t || typeof t !== "object") return false;
  const keys = Object.keys(t as Record<string, unknown>);
  if (keys.length !== 1 || keys[0] !== "google_search") return false;
  const v = (t as Record<string, unknown>).google_search;
  return !!v && typeof v === "object" && Object.keys(v as Record<string, unknown>).length === 0;
}

function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return jsonResponse({ error: "method_not_allowed" }, 405);
  }

  try {
    // 1. Authentification : exige une session utilisateur Supabase valide,
    // pas seulement un JWT anon. Rejette explicitement tout appel anonyme.
    const authHeader = req.headers.get("Authorization") || "";
    if (!authHeader) {
      return jsonResponse({ error: "unauthorized" }, 401);
    }
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
      global: { headers: { Authorization: authHeader } },
    });
    const { data: userData, error: userErr } = await supabaseClient.auth.getUser();
    if (userErr || !userData?.user) {
      return jsonResponse({ error: "unauthorized" }, 401);
    }

    // 2. Payload reçu — validé puis WHITELISTÉ champ par champ ci-dessous.
    // Ne jamais relayer le body brut : seuls les champs explicitement
    // autorisés atteignent Gemini, tout le reste est ignoré/rejeté.
    let raw: Record<string, unknown>;
    try {
      raw = await req.json();
    } catch {
      return jsonResponse({ error: "invalid_json" }, 400);
    }

    const apiKey = typeof raw.apiKey === "string" ? raw.apiKey.trim() : "";
    const model = typeof raw.model === "string" ? raw.model.trim() : "";
    const input = typeof raw.input === "string" ? raw.input : "";

    if (!apiKey || !model || !input) {
      return jsonResponse({ error: "apiKey, model et input sont requis" }, 400);
    }
    if (!ALLOWED_MODELS.has(model)) {
      return jsonResponse({ error: "model_not_allowed" }, 400);
    }

    const geminiBody: Record<string, unknown> = {
      contents: [{ parts: [{ text: input }] }],
    };

    if (raw.tools !== undefined) {
      if (!Array.isArray(raw.tools) || !raw.tools.every(isAllowedTool)) {
        return jsonResponse({ error: "tool_not_allowed" }, 400);
      }
      if (raw.tools.length > 0) geminiBody.tools = raw.tools;
    }
    if (raw.systemInstruction !== undefined) {
      if (typeof raw.systemInstruction !== "string") {
        return jsonResponse({ error: "invalid_system_instruction" }, 400);
      }
      if (raw.systemInstruction) {
        geminiBody.systemInstruction = { parts: [{ text: raw.systemInstruction }] };
      }
    }

    const generationConfig: Record<string, unknown> = {};
    if (raw.max_output_tokens !== undefined) {
      const n = Number(raw.max_output_tokens);
      if (!Number.isFinite(n) || n <= 0) {
        return jsonResponse({ error: "invalid_max_output_tokens" }, 400);
      }
      generationConfig.maxOutputTokens = Math.floor(n);
    }
    // B4 : Structured Outputs — responseSchema/responseMimeType. Protocole
    // générique Gemini, pas de logique métier PlaniTrip.
    if (raw.schema !== undefined) {
      if (typeof raw.schema !== "object" || raw.schema === null || Array.isArray(raw.schema)) {
        return jsonResponse({ error: "invalid_schema" }, 400);
      }
      generationConfig.responseMimeType = "application/json";
      generationConfig.responseSchema = raw.schema;
    }
    if (Object.keys(generationConfig).length > 0) {
      geminiBody.generationConfig = generationConfig;
    }

    // 3. Relais vers Gemini. La clé n'est utilisée que pour cet appel réseau —
    // jamais écrite en base, jamais incluse dans un log ou une réponse d'erreur.
    const geminiRes = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`,
      {
        method: "POST",
        headers: {
          "x-goog-api-key": apiKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(geminiBody),
      },
    );

    const data = await geminiRes.json();

    // Réponse Gemini relayée telle quelle (même statut HTTP) pour que le
    // mapping d'erreurs côté client (_aiCallGemini) reste fonctionnel.
    // Aucune transformation en 500 générique quand Gemini renvoie un statut
    // exploitable.
    return jsonResponse(data, geminiRes.status);
  } catch (_e) {
    // Ne jamais inclure la clé ni le détail interne dans une erreur exposée.
    return jsonResponse({ error: "proxy_error" }, 500);
  }
});
