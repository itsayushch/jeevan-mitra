#!/bin/sh
set -e

# Ensure data directory exists for persistent SQLite database
mkdir -p /app/data

echo "[JeevanMitra 2.0] Container initialized. Starting service..."
exec "$@"
