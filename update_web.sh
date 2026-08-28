#!/bin/bash
# Actualiza el dashboard de peso: regenera los datos desde el Excel y los publica.
# Pensado para ejecutarse solo (launchd) o a mano.

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/davidrochgarcia/health-dashboard || exit 1

# 1) Regenerar los datos desde los Excel
/usr/bin/python3 scripts/build_data.py || { echo "$(date '+%F %T') ERROR generando peso"; exit 1; }
# Deporte es no crítico: si falla (p. ej. hoja del mes aún no creada), seguimos igual.
/usr/bin/python3 scripts/build_deporte.py || echo "$(date '+%F %T') AVISO: deporte no generado"
/usr/bin/python3 scripts/build_dieta.py || echo "$(date '+%F %T') AVISO: dieta no generada"

# 2) ¿Hay cambios? Si no, no hacemos nada.
git add -A
if git diff --cached --quiet; then
  echo "$(date '+%F %T') sin cambios, nada que publicar"
  exit 0
fi

# 3) Guardar el commit
git commit -m "Actualización automática ($(date '+%F'))"

# 4) Subir con reintentos (por si al arrancar el WiFi aún no ha conectado).
#    El commit ya está guardado en local; si hoy no sube, se subirá en la próxima ejecución.
for intento in 1 2 3 4 5; do
  if git push; then
    echo "$(date '+%F %T') actualizado y publicado (intento $intento)"
    exit 0
  fi
  echo "$(date '+%F %T') no se pudo subir (intento $intento), reintento en 60s…"
  sleep 60
done
echo "$(date '+%F %T') ERROR al subir tras 5 intentos (quedará guardado en local y se subirá luego)"
exit 1
