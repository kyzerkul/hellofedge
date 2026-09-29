#!/usr/bin/env bash
# Sauvegarde de la base Hellofedge (spec 0001) : une copie `pg_dump` compressée par
# nuit dans /opt/hellofedge/backups, 7 jours gardés. Lancée par cron (provision.sh).
# Restauration :
#   gunzip -c backups/hellofedge-AAAA-MM-JJ.sql.gz | docker compose exec -T postgres psql -U hellofedge hellofedge

set -euo pipefail

APP_DIR=/opt/hellofedge
KEEP_DAYS=7

cd "$APP_DIR"
file="backups/hellofedge-$(date -u +%F).sql.gz"
tmp="$file.partial"

docker compose exec -T postgres pg_dump -U hellofedge --no-owner hellofedge | gzip > "$tmp"
mv "$tmp" "$file"
find backups -name 'hellofedge-*.sql.gz' -mtime +"$KEEP_DAYS" -delete

echo "$(date -u +%FT%TZ) sauvegarde écrite : $file ($(du -h "$file" | cut -f1))"
