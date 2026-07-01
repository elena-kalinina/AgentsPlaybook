#!/usr/bin/env bash
# Smoke test: connect to the Cup Clash MCP server and list its tools.
# Reads APP_MCP_SERVER_URL and APP_MCP_SERVER_TOKEN from .env.
set -euo pipefail
set -a; source .env; set +a

URL="${APP_MCP_SERVER_URL:?missing APP_MCP_SERVER_URL}"
TOKEN="${APP_MCP_SERVER_TOKEN:?missing APP_MCP_SERVER_TOKEN}"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

hdr=$(mktemp); body=$(mktemp)
trap 'rm -f "$hdr" "$body"' EXIT

post() { # $1=json -> stdout body, headers in $hdr
  curl -sS -D "$hdr" -X POST "$URL" \
    -A "$UA" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    ${SESSION:+-H "Mcp-Session-Id: $SESSION"} \
    -d "$1"
}

# strip SSE framing ("event:"/"data:") down to the JSON payload
unwrap() { sed -n 's/^data: //p' | tail -n1; }

echo "==> URL: $URL"
echo

echo "==> 1) initialize"
INIT=$(post '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0.0.1"}}}')
SESSION=$(grep -i '^mcp-session-id:' "$hdr" | tr -d '\r' | awk '{print $2}' || true)
echo "$INIT" | unwrap | jq '{serverInfo:.result.serverInfo, capabilities:.result.capabilities}'
echo "session: ${SESSION:-<none>}"
echo

echo "==> 2) notifications/initialized"
post '{"jsonrpc":"2.0","method":"notifications/initialized"}' >/dev/null || true
echo "ok"
echo

echo "==> 3) tools/list"
TOOLS=$(post '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}')
echo "$TOOLS" | unwrap | jq -r '.result.tools[] | "- \(.name): \(.description // "" | gsub("\n";" ") | .[0:90])"'
echo
echo "tool count: $(echo "$TOOLS" | unwrap | jq '.result.tools | length')"
