#!/usr/bin/env bash
# Generic MCP caller for the Cup Clash server.
#   ./mcp_call.sh tools_list
#   ./mcp_call.sh call <tool_name> '<json-args>'
#   ./mcp_call.sh raw '<full-jsonrpc-params-for-method>' <method>
# Reads creds from .env. Handles initialize handshake + session id each run.
set -euo pipefail
set -a; source .env; set +a

URL="${APP_MCP_SERVER_URL:?}"
TOKEN="${APP_MCP_SERVER_TOKEN:?}"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
hdr=$(mktemp); trap 'rm -f "$hdr"' EXIT
SESSION=""

post() {
  curl -sS -D "$hdr" -X POST "$URL" \
    -A "$UA" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    ${SESSION:+-H "Mcp-Session-Id: $SESSION"} \
    -d "$1"
}
unwrap() { sed -n 's/^data: //p' | tail -n1; }

# handshake
post '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"cli","version":"0.0.1"}}}' >/dev/null
SESSION=$(grep -i '^mcp-session-id:' "$hdr" | tr -d '\r' | awk '{print $2}' || true)
post '{"jsonrpc":"2.0","method":"notifications/initialized"}' >/dev/null || true

case "${1:-}" in
  tools_list)
    post '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | unwrap | jq .
    ;;
  call)
    NAME="$2"; ARGS="${3:-}"; [ -z "$ARGS" ] && ARGS='{}'
    REQ=$(jq -nc --arg n "$NAME" --argjson a "$ARGS" '{jsonrpc:"2.0",id:3,method:"tools/call",params:{name:$n,arguments:$a}}')
    post "$REQ" | unwrap | jq .
    ;;
  *)
    echo "usage: $0 tools_list | call <tool> '<json-args>'" >&2; exit 2;;
esac
