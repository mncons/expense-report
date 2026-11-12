#!/usr/bin/env bash
# AGENTS.md dice "Money is Decimal, never float"; este gate lo hace cumplir.
bad="$(git diff "$FACTORY_BASE" -- report/ | grep -E '^\+' | grep -E 'float\(' || true)"
if [ -n "$bad" ]; then echo "Montos con float en el cambio (usa decimal.Decimal):"; echo "$bad"; exit 1; fi
echo "Sin float en montos."
