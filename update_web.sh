#!/bin/bash
# Actualiza el dashboard de peso: regenera los datos desde el Excel y los publica.
# Pensado para ejecutarse solo (launchd) o a mano.

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/davidrochgarcia/health-dashboard || exit 1

# 1) Regenerar data/peso.json desde el Excel
/usr/bin/python3 scripts/build_data.py || { echo "$(date '+%F %T') ERROR generando datos"; exit 1; }

# 2) ¿Hay cambios? Si no, no hacemos nada.
git add -A
if git diff --cached --quiet; then
  echo "$(date '+%F %T') sin cambios, nada que publicar"
  exit 0
fi

# 3) Guardar y subir
git commit -m "Actualización automática ($(date '+%F'))"
git push && echo "$(date '+%F %T') actualizado y publicado" || echo "$(date '+%F %T') ERROR al subir"
