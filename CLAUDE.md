# Health Dashboard — contexto del proyecto

> Documento de contexto y hoja de ruta. Si abres este proyecto en una sesión
> nueva (Claude Code, Cowork u otra herramienta), léelo primero: resume qué es,
> cómo funciona, qué decisiones se tomaron y qué falta por hacer.

**Autor:** David Roch (perfil de negocio, no ingeniero). Montado con Claude Code
desde la terminal como ejercicio de "building in public" y aprendizaje de IA aplicada.

- **Web en vivo:** https://davidrochg.github.io/health-dashboard/
- **Repositorio:** https://github.com/davidrochg/health-dashboard
- **Estado:** MVP funcionando, con **Home + 3 pestañas** (Home resumen · Peso · Deporte) y actualizándose solo cada día (peso y deporte).

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
gráfica del mes y mín/media/máx — y **Deporte**, con el KPI de **días activos** de la
semana (ver más abajo). El KPI de deporte también aparece resumido en Home. Se irán
sumando más pestañas (sueño, alimentación, etc.).

---

## Cómo funciona (3 piezas)

1. **Lectores de datos** — `scripts/build_data.py` (peso) y `scripts/build_deporte.py` (deporte)
   Leen los Excel, aplican las reglas de lectura y escriben `data/peso.json` y
   `data/deporte.json` con los cálculos ya hechos.

2. **Dashboard** — `index.html`
   Página autocontenida (HTML/CSS/JS, sin librerías externas). Lee `data/peso.json` y
   `data/deporte.json` y los pinta. Responsive, tema oscuro. Organizado en **vistas/pestañas**
   (Home · Peso · Deporte) que se muestran/ocultan con JS dentro de una sola página.

3. **Publicación** — GitHub Pages
   El repo se sirve como web estática. Cada `git push` republica la página.

### Actualización automática (en la nube)
- **GitHub Actions** `.github/workflows/update.yml`: dos pasadas al día, **09:00 y 21:00
  hora de Madrid** (cron a prueba de cambio de hora verano/invierno mediante un "portero"
  que solo deja pasar esas horas). En cada pasada el robot **descarga los dos Excel
  directamente de Google Drive** (`scripts/fetch_drive.py`, con una cuenta de servicio),
  regenera los tres JSON y **publica solo si cambia un dato real** (ignora el cambio de
  `generated_at`, para no ensuciar el historial).
- **No depende del Mac**: corre en los servidores de GitHub. Ve al instante lo que se apunte
  desde el móvil, porque lee la nube y no una copia local del portátil.
- **Acceso a Drive**: cuenta de servicio
  `drive-reader@health-dashboard-507211.iam.gserviceaccount.com`, con los dos Excel
  compartidos en solo-lectura. La llave JSON vive como **Secret de GitHub** (`GDRIVE_SA_KEY`);
  los IDs de fichero van fijados en el propio workflow. Nada de esto queda en el repo público.
- **Lanzar a mano**: pestaña **Actions** → "Actualizar dashboard (nube)" → **Run workflow**.

**Histórico (desactivado):** antes se hacía en el Mac con `update_web.sh` + LaunchAgents
(`com.davidroch.healthdashboard[.push]`, 09:00 hora local). Se jubiló al pasar a la nube; los
`.plist` quedaron guardados en `_launchagents_desactivados/`. El cambio resolvió el problema de
fondo: el Mac leía una **copia local** de Drive y las ediciones desde el móvil llegaban tarde
(o el push fallaba al no haber red al despertar).

---

## Fuente de datos

Excel personal en Google Drive (cuenta personal), sincronizado en local:

```
/Users/davidrochgarcia/Library/CloudStorage/GoogleDrive-davidrochgarcia@gmail.com/My Drive/1. dOS/Salud/Peso.xlsx
```

**Estructura de la hoja de peso (¡importante!):**
- Los meses van en **BLOQUES de 3 columnas, uno al lado del otro** en la misma hoja
  (`Sheet1`): agosto en A-C, septiembre en D-F, octubre en G-I, y así.
- **Fila 1** = nombre del mes en la primera columna del bloque (celda combinada de 3):
  A1="Agosto", D1="Septiembre", …
- **Fila 2** = cabeceras del bloque (`Día`, `Peso`, `Eat`). Datos desde la **fila 3**.
- Dentro de cada bloque: 1ª col = día del mes · 2ª = peso (kg, puede estar vacío) ·
  3ª = "Eat" (`X` = cumplí dieta, `-`/vacío = no).
- Hay días sin peso (huecos) en medio: se saltan, no se corta el recorrido.
- La fila con un número suelto bajo "Peso" (sin día) es la media del mes: se ignora.
- **El lector une TODOS los bloques en una sola línea temporal continua.** Así, "ayer",
  "vs. hace 7 días" y la **media semanal** funcionan aunque la semana cruce el cambio de mes
  (p. ej. lun 31-ago → dom 6-sep mezcla los bloques de agosto y septiembre). Las stats y la
  gráfica muestran el **mes en curso** (el del último registro). Esto lo arreglamos el 1-sep-2026:
  antes el lector solo miraba el primer bloque (agosto) y no veía el mes nuevo.

**Excel de entreno** (misma carpeta de Drive):

```
.../My Drive/1. dOS/Salud/Entrenamiento/Entreno 2026.xlsx
```

- Una hoja por mes: `Entreno <Mes> 2026`. Fila 2 = cabeceras: `Ejercicio, Series, Reps`
  y luego **una columna por semana** (fecha del lunes). Las filas se agrupan en bloques
  `Día 1 … Día 7`, que son **huecos/tipos de deporte, NO días fijos de la semana** (puedes
  apuntar el correr en el hueco "Correr" el día que salgas a correr).
- En la celda de cada semana se apunta la carga/actividad. Un `-` o vacío = no hecho.
- **Ojo (esto fue un bug):** los deportes de gimnasio llevan el nombre del ejercicio en la
  columna A; los de **deporte libre** (golf, pádel, SUP…) van con la **columna A vacía** y el
  texto en otra columna. El lector debe mirar TODAS las filas de cada bloque `Día`, tengan o
  no etiqueta en la columna A.

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

## Contrato de datos (`data/deporte.json`)

```
{
  "generated_at": ISO datetime,
  "week_start": "AAAA-MM-DD",          // lunes de la semana en curso
  "dias_activos": num,                 // huecos con algo apuntado (capado a los transcurridos)
  "dias_transcurridos": num,           // días naturales lun→hoy (1..7)
  "total_semana": 7,
  "slots_marcados": num,               // conteo bruto de huecos con algo (sin capar)
  "pattern": [ "active"|"rest"|"future" x7 ],  // para la barra de progreso
  "sheet": "Entreno <Mes> <año>",
  "week_col_date": "AAAA-MM-DD"
}
```

---

## Decisiones tomadas

- **Alojamiento:** GitHub Pages. En plan gratuito el repo es **público** (los datos
  de peso quedan en un repo público; se asumió para el MVP). URL privada de facto
  (solo la tiene David) y `<meta name="robots" content="noindex">` para no salir en Google.
- **Diseño:** oscuro, estilo tipo WHOOP. Paleta y acento teal.
- **Medias semanales:** semana natural lunes-domingo (no ventana móvil de 7 días).
- **Días activos (deporte):** se cuentan los **huecos** (`Día 1…7`) con algo apuntado esta
  semana, NO días concretos (el Excel guarda el hueco/tipo, no el día real). Denominador =
  días naturales transcurridos (lun→hoy). Se capa para no mostrar "X de menos que X". La barra
  de 7 segmentos es **por conteo**, no por día de la semana.
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
- [x] **Deporte** — HECHO. Pestaña propia + KPI "días activos X/Y" en Home. Regla y contrato
      arriba (conteo de huecos vs. días transcurridos; barra de 7 segmentos por conteo).
      Pendiente opcional: un desglose por día real de la semana requeriría apuntar la fecha de
      cada deporte en el Excel.
- [ ] Sueño · Alimentación · Piel · Dental (mapeadas a las subcarpetas de `Salud`).
- [ ] Vista histórica multi-mes (hoy los Excel son de un mes; guardar histórico).

**Largo plazo — quitar la dependencia del Mac**
- [x] Automatización **100% en la nube** — HECHO. GitHub Actions (2 pasadas: 09:00 y 21:00
      Madrid) que lee los Excel desde Google Drive con una cuenta de servicio. La web se
      actualiza sola aunque el Mac esté apagado. Ver "Actualización automática (en la nube)".
- [ ] Privacidad: si algún día los datos son más sensibles, proteger con contraseña
      (p. ej. Cloudflare Access).

---

## Cómo retomar en una sesión nueva

Si entras con Claude Code en `~/health-dashboard`, este archivo se carga solo.
Para orientarte rápido: mira `scripts/build_data.py` y `scripts/build_deporte.py` (lógica de
datos), `index.html` (dashboard con pestañas) y `update_web.sh` (automatización). Prueba
`bash update_web.sh` para regenerar y publicar. La hoja de ruta de arriba marca lo siguiente.
