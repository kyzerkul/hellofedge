#!/usr/bin/env bash
# Recherche cTrader depuis un Codespace (spec 0002). Mode d'emploi : deploy/CODESPACES.md
#
#   bash .devcontainer/mesure.sh                 comptes puis mesure de l'écart avec OANDA
#   bash .devcontainer/mesure.sh comptes         comptes cTrader liés au jeton
#   bash .devcontainer/mesure.sh compare         écart avec les points OANDA, profondeur d'historique
#   bash .devcontainer/mesure.sh direct [MIN]    test du direct (30 minutes par défaut, marché ouvert)
#   bash .devcontainer/mesure.sh historique [DE] [A]
#                                                charge les bougies M1 en base (défaut : 7 derniers jours)
#
# Lecture seule : aucune de ces commandes ne passe d'ordre.

set -euo pipefail

SELF="$(realpath "$0")"
cd "$(dirname "$SELF")/../backend"
export PATH="$HOME/.local/bin:$PATH"

case "${1:-tout}" in
  comptes | compare | direct | historique | tout) ;;
  *)
    sed -n '3,10p' "$SELF"
    exit 2
    ;;
esac

missing=()
for name in CTRADER_CLIENT_ID CTRADER_CLIENT_SECRET CTRADER_ACCOUNT_ID \
  CTRADER_ACCESS_TOKEN CTRADER_REFRESH_TOKEN; do
  [[ -n "${!name:-}" ]] || missing+=("$name")
done
if ((${#missing[@]})); then
  echo "Arrêt : secrets Codespaces absents : ${missing[*]}" >&2
  echo "Ajoute-les (deploy/CODESPACES.md, étape 1), puis reconstruis le Codespace." >&2
  exit 1
fi

feed() { uv run hellofedge feed "$@"; }

case "${1:-tout}" in
  comptes) feed ctrader-accounts ;;
  compare) feed compare ;;
  direct) feed live-test --minutes "${2:-30}" ;;
  historique)
    from="${2:-$(date -u -d '7 days ago' +%Y-%m-%dT00:00)}"
    to="${3:-$(date -u +%Y-%m-%dT%H:%M)}"
    feed backfill --from "$from" --to "$to"
    ;;
  tout)
    feed ctrader-accounts
    echo
    feed compare
    ;;
esac

if [[ "${1:-tout}" =~ ^(compare|direct|tout)$ ]]; then
  echo
  echo "Rapport : exemples/mesure_sources.md"
fi
