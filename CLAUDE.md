# Health Dashboard — contexto del proyecto

> Documento de contexto y hoja de ruta. Si abres este proyecto en una sesión
> nueva (Claude Code, Cowork u otra herramienta), léelo primero: resume qué es,
> cómo funciona, qué decisiones se tomaron y qué falta por hacer.

**Autor:** David Roch (perfil de negocio, no ingeniero). Montado con Claude Code
desde la terminal como ejercicio de "building in public" y aprendizaje de IA aplicada.

- **Web en vivo:** https://davidrochg.github.io/health-dashboard/
- **Repositorio:** https://github.com/davidrochg/health-dashboard
- **Estado:** MVP funcionando, con **Home + pestañas** (Home resumen · Peso detalle) y actualizándose solo cada día.

---

## Qué es

Un dashboard personal de salud, oscuro y estilo tipo WHOOP, pensado para verse
igual en el móvil y en el ordenador. Arranca con **una sola métrica: el peso**, y
está diseñado para ir sumando más (sueño, alimentación, entreno, etc.).

Muestra: peso de hoy, variación vs. ayer y vs. el mismo día de la semana pasada,
media de la semana natural (lunes-domingo) frente a la anterior, gráfica de
tendencia del mes y mín/media/máx.

**Navegación por pestañas** (barra inferior, estilo WHOOP): **Home** — lo primero
que se ve, resumen con la **media semanal** como KPI protagonista — y **Peso** — el
detalle: media semanal arriba, peso de hoy en segundo plano con sus variaciones,
gráfica del mes y mín/media/máx. Se irán sumando pestañas (Deporte, etc.).

---

## Cómo funciona (3 piezas)

1. **Lector de datos** — `scripts/build_data.py`
   Lee el Excel de peso, aplica las reglas de lectura y escribe `data/peso.json`
   con los cálculos ya hechos.

2. **Dashboard** — `index.html`
   Página autocontenida (HTML/CSS/JS, sin librerías externas). Lee `data/peso.json`
   y lo pinta. Responsive, tema oscuro. Organizado en **vistas/pestañas** (Home + Peso)
   que se muestran/ocultan con JS dentro de una sola página.

3. **Publicación** — GitHub Pages
   El repo se sirve como web estática. Cada `git push` republica la página.

### Actualización automática
- **`update_web.sh`**: regenera `peso.json` desde el Excel y hace commit + push si hay cambios.
- **LaunchAgent** `~/Library/LaunchAgents/com.davidroch.healthdashboard.plist`:
  dispara `update_web.sh` **cada día a las 09:00** (hora local del Mac).
- Logs en `~/Library/Logs/healthdashboard.log` y `...-error.log`.

**Para actualizar a mano:** `bash ~/health-dashboard/update_web.sh`
**Para actualizar sin hacer nada:** apuntar el peso en el Excel; a las 09:00 se publica solo.

---

## Fuente de datos

Excel personal en Google Drive (cuenta personal), sincronizado en local:

```
/Users/davidrochgarcia/Library/CloudStorage/GoogleDrive-davidrochgarcia@gmail.com/My Drive/1. dOS/Salud/Peso.xlsx
```

**Estructura de la hoja de peso:**
- Fila 1, col A: nombre del mes (ej. "Agosto").
- Fila 2: cabeceras (`Día`, `Peso`, `Eat`). Datos desde la fila 3.
- Col A = día del mes · Col B = peso (kg, puede estar vacío) · Col C = "Eat" (marca, hoy ignorada).
- Hay días sin peso (huecos) en medio: se saltan, no se corta el recorrido.
- La última fila con un número suelto es la media del mes: se ignora.

---

## Contrato de datos (`data/peso.json`)

```
{
  "generated_at": ISO datetime,
  "unit": "kg",
  "month": "Agosto 2026",
  "current":  {date, day, weight},         // último día registrado
  "previous": {date, day, weight},
  "delta_vs_previous": num|null,            // vs día registrado anterior
  "delta_vs_week": num|null,                // vs exactamente 7 días antes
  "reference_week": {date, day, weight}|null,
  "week": {                                 // medias por SEMANA NATURAL (lun-dom)
    "this": {avg, count},                   //   lunes de esta semana → hoy
    "last": {avg, count},                   //   semana anterior completa
    "delta": num|null,
    "this_start", "last_start", "last_end"
  },
  "stats": {count, min, max, avg},          // sobre los pesos del mes
  "series": [ {date, day, weight}, ... ]    // todos los registros del mes
}
```

---

## Decisiones tomadas

- **Alojamiento:** GitHub Pages. En plan gratuito el repo es **público** (los datos
  de peso quedan en un repo público; se asumió para el MVP). URL privada de facto
  (solo la tiene David) y `<meta name="robots" content="noindex">` para no salir en Google.
- **Diseño:** oscuro, estilo tipo WHOOP. Paleta y acento teal.
- **Medias semanales:** semana natural lunes-domingo (no ventana móvil de 7 días).
- **Color de las variaciones:** provisional (bajar = verde). Pendiente de conectar
  el objetivo real de peso para que "verde" signifique "voy bien" de verdad.
- **Identidad de git:** los commits automáticos usan el email del equipo
  (`...@Administradors-MacBook-Pro.local`); es cosmético, no afecta.

---

## Limitaciones / cosas a saber

- **El Mac tiene que estar encendido y con sesión iniciada a las 09:00** para que
  el temporizador dispare. Si no, ese día no se actualiza (se pone al día al siguiente arranque).
- **Permisos de macOS:** para que el temporizador (launchd) pueda leer el Excel de
  Google Drive hubo que dar **"Acceso a disco completo"** a `/bin/bash` y `/usr/bin/python3`
  (Ajustes → Privacidad y seguridad → Acceso a disco completo). Sin esto, la tarea
  automática falla con `PermissionError`.
- **Año en fechas:** el año se toma del año actual del sistema. Caso límite: abrir
  en enero un Excel cuyo mes en A1 sea "Diciembre" daría fechas con año nuevo.

---

## Hoja de ruta (próximos pasos)

**Corto plazo**
- [ ] Conectar el **objetivo de peso** (está en la carpeta `Salud`) para: colorear las
      variaciones según la meta y dibujar una **línea de objetivo** en la gráfica.
- [ ] Opción de que la tarea **solo haga commit cuando haya peso nuevo** (hoy commitea a
      diario porque cambia la hora de "Actualizado").
- [ ] Silenciar el aviso de identidad de git y dejar los commits a nombre de David
      (email noreply de GitHub).

**Medio plazo — más métricas** (cada una: su lector + su pestaña/KPI)
- [ ] **Deporte** (pestaña propia + KPI en Home). Métrica: "días activos" de la semana.
      Definición cerrada: se lee el Excel de entreno (`Salud/Entrenamiento/Entreno 2026.xlsx`,
      hoja del mes, columnas = semanas). Un día de la rutina cuenta como **activo** si en la
      columna de esa semana hay **algún valor escrito** en su bloque; un guion `-` o vacío = no.
      Cuenta cualquier deporte (gimnasio o libre: surf, golf…). Formato **"X/7"**, con el
      denominador = días ya cerrados (hasta ayer, más hoy solo si ya tiene algo apuntado), para
      que "hoy" no cuente como fallo por la mañana. Acompañar con una **tira de 7 puntos** (lun→dom).
- [ ] Sueño · Alimentación · Piel · Dental (mapeadas a las subcarpetas de `Salud`).
- [ ] Vista histórica multi-mes (hoy el Excel es de un mes; guardar histórico).

**Largo plazo — quitar la dependencia del Mac**
- [ ] Automatización **100% en la nube** (p. ej. GitHub Actions programado) leyendo los
      datos desde una fuente accesible en la nube (Google Sheets / Drive API), de modo que
      la web se actualice sola aunque el Mac esté apagado.
- [ ] Privacidad: si algún día los datos son más sensibles, proteger con contraseña
      (p. ej. Cloudflare Access).

---

## Cómo retomar en una sesión nueva

Si entras con Claude Code en `~/health-dashboard`, este archivo se carga solo.
Para orientarte rápido: mira `scripts/build_data.py` (lógica de datos), `index.html`
(dashboard) y `update_web.sh` (automatización). Prueba `bash update_web.sh` para
regenerar y publicar. La hoja de ruta de arriba marca lo siguiente a construir.
