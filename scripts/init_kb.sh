set -euo pipefail

SQL_FILE="${1:-scripts/kb_create_nim.sql}"
HOST="${MINDSDB_HOST:-127.0.0.1}"
PORT="${MINDSDB_PORT:-47335}"
USER="${MINDSDB_USER:-mindsdb}"
PASS="${MINDSDB_PASSWORD:-}"

if ! command -v mysql >/dev/null 2>&1; then
  echo "Error: mysql client not found. Install it, or run:"
  echo "  docker run --rm -i --network=host mysql:8 mysql -h${HOST} -P${PORT} -u${USER} ${PASS:+-p$PASS} < ${SQL_FILE}"
  exit 1
fi

if [ -n "$PASS" ]; then
  MYSQL_PWD="$PASS" mysql -h "$HOST" -P "$PORT" -u "$USER" < "$SQL_FILE"
else
  mysql -h "$HOST" -P "$PORT" -u "$USER" < "$SQL_FILE"
fi

echo "KB init complete ✓"