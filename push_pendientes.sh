#!/bin/bash
# Sube a GitHub cualquier commit que quedara pendiente (p. ej. si el push de las
# 9:00 falló porque el WiFi aún no estaba listo al despertar el Mac).
# NO genera datos ni crea commits: solo empuja lo que ya esté hecho en local.
# Pensado para correr cada hora y al iniciar sesión (LaunchAgent).

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/davidrochgarcia/health-dashboard || exit 1

# ¿Hay commits locales sin subir?
LOCAL=$(git rev-parse @ 2>/dev/null)
REMOTE=$(git rev-parse @{u} 2>/dev/null)

# Sin rama de seguimiento configurada: no hacemos nada.
[ -z "$REMOTE" ] && exit 0

# Ya está todo sincronizado: nada que hacer, salimos en silencio.
[ "$LOCAL" = "$REMOTE" ] && exit 0

# Hay algo pendiente: intentamos subirlo.
if git push; then
  echo "$(date '+%F %T') [push-pendientes] commit(s) pendientes subidos a GitHub"
else
  echo "$(date '+%F %T') [push-pendientes] aún sin red/permiso; se reintenta en la próxima pasada"
fi
