#!/bin/bash
# Archive sessions older than 30 days
mkdir -p sessions/archive
find sessions/ -maxdepth 1 -name "*.json" -mtime +30 -exec mv {} sessions/archive/ \;
echo "✅ Archived sessions older than 30 days to sessions/archive/"
