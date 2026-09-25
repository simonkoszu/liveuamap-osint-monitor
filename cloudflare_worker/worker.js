/**
 * Aegis OSINT Tactical Radar - Cloudflare Worker Relay
 * 
 * Bezpieczny pośrednik serwerless (Zero-Login Trigger)
 * Uruchamia workflow GitHub Actions na żądanie użytkownika z poziomu panelu HTML
 * bez konieczności logowania się do GitHub przez przeglądarkę.
 * 
 * Zmienne środowiskowe wymagane w Cloudflare Worker:
 * - GH_TOKEN: Twój GitHub Personal Access Token (z uprawnieniem 'workflow' lub 'repo')
 * - GH_REPO: simonkoszu/liveuamap-osint-monitor (opcjonalne, domyślna wartość poniżej)
 * - GH_WORKFLOW: update_report.yml (opcjonalne, domyślna wartość poniżej)
 */

const DEFAULT_REPO = "simonkoszu/liveuamap-osint-monitor";
const DEFAULT_WORKFLOW = "update_report.yml";
const COOLDOWN_SECONDS = 90; // Minimalny odstęp między wywołaniami (ochrona przed spamem)

// Pamięć podręczna ostatniego uruchomienia w obrębie instancji
let lastTriggerTime = 0;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const repo = env?.GH_REPO || globalThis?.GH_REPO || DEFAULT_REPO;
    const workflow = env?.GH_WORKFLOW || globalThis?.GH_WORKFLOW || DEFAULT_WORKFLOW;
    const token = env?.GH_TOKEN || globalThis?.GH_TOKEN || env?.GITHUB_TOKEN || globalThis?.GITHUB_TOKEN;

    // Nagłówki CORS - zezwalają na wywołanie z GitHub Pages i localhost
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
      "Access-Control-Max-Age": "86400",
    };

    // Obsługa preflight OPTIONS
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // Endpoint 1: POST /trigger (uruchomienie skanu)
    if (request.method === "POST" && (url.pathname === "/trigger" || url.pathname === "/")) {
      if (!token) {
        return new Response(JSON.stringify({
          status: "error",
          message: "Brak skonfigurowanej zmiennej GH_TOKEN w Cloudflare Worker Settings."
        }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
        });
      }

      // Ochrona przed zbyt częstym wywoływaniem (cooldown)
      const now = Math.floor(Date.now() / 1000);
      const elapsed = now - lastTriggerTime;
      if (lastTriggerTime > 0 && elapsed < COOLDOWN_SECONDS) {
        const remaining = COOLDOWN_SECONDS - elapsed;
        return new Response(JSON.stringify({
          status: "cooldown",
          message: `Skan został już wywołany i jest przetwarzany w chmurze. Odczekaj jeszcze ${remaining}s.`,
          seconds_remaining: remaining
        }), {
          status: 429,
          headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
        });
      }

      try {
        const ghHeaders = {
          "Accept": "application/vnd.github+json",
          "Authorization": `Bearer ${token}`,
          "User-Agent": "Aegis-OSINT-Cloudflare-Relay",
          "X-GitHub-Api-Version": "2022-11-28",
          "Content-Type": "application/json"
        };

        // Próba 1: repository_dispatch (wymaga tylko repo:write, nie wymaga praw Admina)
        let ghResponse = await fetch(`https://api.github.com/repos/${repo}/dispatches`, {
          method: "POST",
          headers: ghHeaders,
          body: JSON.stringify({ event_type: "refresh-radar", client_payload: { trigger: "cloudflare_relay" } })
        });

        // Próba 2: workflow_dispatch jako fallback
        if (ghResponse.status !== 204) {
          ghResponse = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`, {
            method: "POST",
            headers: ghHeaders,
            body: JSON.stringify({ ref: "main" })
          });
        }

        if (ghResponse.status === 204) {
          lastTriggerTime = now;
          return new Response(JSON.stringify({
            status: "success",
            message: "🚀 Skan chmurowy Aegis Radar został pomyślnie uruchomiony!",
            eta_seconds: 90
          }), {
            status: 200,
            headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
          });
        }

        const errText = await ghResponse.text();
        return new Response(JSON.stringify({
          status: "error",
          message: `GitHub API zwrócił błąd ${ghResponse.status}: ${errText}`
        }), {
          status: ghResponse.status,
          headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
        });

      } catch (err) {
        return new Response(JSON.stringify({
          status: "error",
          message: `Błąd sieciowy pośrednika: ${err.message}`
        }), {
          status: 502,
          headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
        });
      }
    }

    // Endpoint 2: GET /status (sprawdzenie stanu ostatniego zadania)
    if (request.method === "GET" && url.pathname === "/status") {
      if (!token) {
        return new Response(JSON.stringify({ status: "error", message: "Brak GH_TOKEN" }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
        });
      }

      try {
        const ghResponse = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/${workflow}/runs?per_page=1`, {
          headers: {
            "Accept": "application/vnd.github+json",
            "Authorization": `Bearer ${token}`,
            "User-Agent": "Aegis-OSINT-Cloudflare-Relay",
            "X-GitHub-Api-Version": "2022-11-28"
          }
        });

        if (ghResponse.ok) {
          const data = await ghResponse.json();
          const run = data.workflow_runs?.[0] || null;
          return new Response(JSON.stringify({
            status: "ok",
            run: run ? {
              id: run.id,
              status: run.status,          // 'queued', 'in_progress', 'completed'
              conclusion: run.conclusion,  // 'success', 'failure', null
              updated_at: run.updated_at,
              html_url: run.html_url
            } : null
          }), {
            status: 200,
            headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
          });
        }

        return new Response(JSON.stringify({ status: "error", code: ghResponse.status }), {
          status: ghResponse.status,
          headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ status: "error", message: err.message }), {
          status: 502,
          headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
        });
      }
    }

    // Informacja powitalna na GET /
    return new Response(JSON.stringify({
      name: "Aegis OSINT Radar - Cloudflare Relay API",
      status: "ready",
      has_token: !!token,
      detected_vars: Object.keys(env || {}),
      endpoints: {
        "POST /trigger": "Uruchamia workflow GitHub Actions",
        "GET /status": "Sprawdza status trwającego zadania w chmurze"
      }
    }, null, 2), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" }
    });
  }
};
