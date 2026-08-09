// Edge Function: openai-proxy
// Relaie une requête vers l'API OpenAI Responses API. BYOK : la clé personnelle
// de l'utilisateur est transmise uniquement pour cette requête en cours,
// jamais stockée en base, jamais loggée, jamais renvoyée dans une erreur.
// Exige une session Supabase UTILISATEUR authentifiée valide (pas seulement
// une clé anon) — aucun accès anonyme à ce proxy.
// Aucun prompt métier ni logique PlaniTrip ici : payload minimal, whitelisté,
// relayé vers OpenAI. N'accepte que POST (+ OPTIONS pour le préflight CORS).
// B4 : support optionnel des Structured Outputs (text.format/json_schema) —
// construction du format OpenAI générique, pas de logique métier PlaniTrip.

import { createClient } from "jsr:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// Whitelist des modèles OpenAI réellement supportés par PlaniTrip. Reflète
// volontairement AI_MODELS.openai côté client (index.html) — dupliqué ici
// par choix, pour que cette fonction reste un proxy strict et non un relais
// générique vers n'importe quel modèle OpenAI. À maintenir en synchronisation
// manuelle si AI_MODELS.openai évolue côté client.
const ALLOWED_MODELS = new Set(["gpt-5.6"]);

// Whitelist des tools autorisés — un seul aujourd'hui, cohérent avec
// aiRequest()/webSearch côté client.
function isAllowedTool(t: unknown): boolean {
  return !!t && typeof t === "object" && (t as { type?: string }).type === "web_search";
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
    // autorisés atteignent OpenAI, tout le reste est ignoré/rejeté.
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

    const openaiBody: Record<string, unknown> = { model, input };

    if (raw.tools !== undefined) {
      if (!Array.isArray(raw.tools) || !raw.tools.every(isAllowedTool)) {
        return jsonResponse({ error: "tool_not_allowed" }, 400);
      }
      if (raw.tools.length > 0) openaiBody.tools = raw.tools;
    }
    if (raw.instructions !== undefined) {
      if (typeof raw.instructions !== "string") {
        return jsonResponse({ error: "invalid_instructions" }, 400);
      }
      if (raw.instructions) openaiBody.instructions = raw.instructions;
    }
    if (raw.max_output_tokens !== undefined) {
      const n = Number(raw.max_output_tokens);
      if (!Number.isFinite(n) || n <= 0) {
        return jsonResponse({ error: "invalid_max_output_tokens" }, 400);
      }
      openaiBody.max_output_tokens = Math.floor(n);
    }
    // B4 : Structured Outputs — construit le format OpenAI générique
    // text.format/json_schema à partir d'un schema JSON fourni par le client.
    // Reste un protocole générique OpenAI (pas de logique métier PlaniTrip) :
    // le proxy sait "comment parler à OpenAI", jamais "ce que PlaniTrip veut dire".
    if (raw.schema !== undefined) {
      if (typeof raw.schema !== "object" || raw.schema === null || Array.isArray(raw.schema)) {
        return jsonResponse({ error: "invalid_schema" }, 400);
      }
      const schemaName = typeof raw.schemaName === "string" && raw.schemaName
        ? raw.schemaName.replace(/[^a-zA-Z0-9_]/g, "_").slice(0, 64)
        : "planitrip_response";
      openaiBody.text = {
        format: { type: "json_schema", name: schemaName, schema: raw.schema, strict: true },
      };
    }

    // 3. Relais vers OpenAI. La clé n'est utilisée que pour cet appel réseau —
    // jamais écrite en base, jamais incluse dans un log ou une réponse d'erreur.
    const openaiRes = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(openaiBody),
    });

    const data = await openaiRes.json();

    // Réponse OpenAI relayée telle quelle (même statut HTTP) pour que le
    // mapping d'erreurs côté client (_aiCallOpenAI) reste fonctionnel :
    // 401 -> invalid_key, 429 -> rate_limited/quota, 404 -> model_unavailable,
    // 5xx -> provider_unavailable. Aucune transformation en 500 générique
    // quand OpenAI renvoie un statut exploitable.
    return jsonResponse(data, openaiRes.status);
  } catch (_e) {
    // Ne jamais inclure la clé ni le détail interne dans une erreur exposée.
    return jsonResponse({ error: "proxy_error" }, 500);
  }
});
