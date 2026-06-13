# oss-health-metrics — Backlog & Research

## Lecturas obligatorias

Estas son las fuentes que definen el contexto del proyecto. Leerlas en orden.

### El problema: las métricas están rotas

1. **[The Mismeasure of Open Source — Andrew Nesbitt (May 2026)](https://nesbitt.io/2026/05/09/the-mismeasure-of-open-source.html)**
   Las métricas que usamos existen porque la API las devuelve, no porque midan algo útil.
   "Availability gets mistaken for relevance." Stars, forks, downloads — no dicen nada
   sobre la salud de la comunidad.

2. **[CHAOSS Metrics in 2026 — Andrew Nesbitt (May 2026)](https://nesbitt.io/2026/05/27/chaoss-metrics-in-2026.html)**
   Las métricas CHAOSS diseñadas entre 2018-2023 ya no funcionan. Los AI agents
   distorsionan New Contributors, Conversion Rate, y todo lo que dependa de contar
   personas. Un bot que abre PRs desde cuentas nuevas registra como "burst de
   new contributors."

3. **[Eternal September of Open Source — GitHub Blog (Feb 2026)](https://github.blog/open-source/maintainers/welcome-to-the-eternal-september-of-open-source-heres-what-we-plan-to-do-for-maintainers/)**
   17M PRs/mes generados por AI agents en marzo 2026. 325% de aumento en 6 meses.
   Los maintainers se están ahogando.

4. **[AI is burning out the people who keep open source alive — CodeRabbit (2026)](https://www.coderabbit.ai/blog/ai-is-burning-out-the-people-who-keep-open-source-alive)**
   Solo 1 de cada 10 PRs generados con AI es legítimo. Cortex 2026: incidentes por PR
   aumentaron 23.5% año a año, mientras PRs por autor subieron 20%.

### El cuello de botella: PRs esperando

5. **[My PR has been waiting a year — Armanc Keser (Apr 2026)](https://armanckeser.com/writing/jellyfin-flow)**
   Aplica Little's Law a Jellyfin: 200 PRs en cola, 30 merges/mes = 6.7 meses de
   espera promedio. "Batch Size Death Spiral": PRs grandes → reviews lentos → se
   acumulan → contributors meten más cambios → PRs más grandes. **Lectura obligatoria.**

6. **[PR Reviews Are the Biggest Engineering Bottleneck — DEV (2025)](https://dev.to/yeahiasarker/pr-reviews-are-the-biggest-engineering-bottleneck-lets-fix-that-22ec)**
   El review no escala. Más código → más PRs → mismo número de reviewers.

### Los contributors: retención y abandono

7. **[Does the First Response Matter for Future Contributions? — Iyer et al. (2021, MSR / Springer 2023)](https://arxiv.org/abs/2104.02933)**
   Analizaron 2,765,917 primeras contribuciones. Hallazgo clave: las interacciones
   positivas están positivamente correlacionadas con contribuciones futuras. Sin
   embargo, predecir si alguien volverá es difícil (F1=0.61) — depende del proyecto,
   el contributor, y la contribución, no solo de la respuesta.

8. **[Understanding the Time to First Response in GitHub Pull Requests (2023, arXiv)](https://arxiv.org/abs/2304.08426)**
   Delays en la primera respuesta impactan significativamente la retención de
   contributors nuevos como contributors a largo plazo.

9. **[On Wasted Contributions (2022, ACM TOSEM)](https://arxiv.org/abs/2110.15447)**
   PRs abandonados se predicen por: complejidad, experiencia del contributor, y
   duración del review. Nadie muestra esto en un dashboard.

10. **[Are You Still Working on This? (2021, IEEE TSE)](https://whystar.github.io/res/paper/abPR_TSE2021.pdf)**
    La falta de responsiveness del maintainer es la causa #1 de abandono de PRs.

11. **[Beyond Stars and Forks — BekahHW, DEV (2025)](https://dev.to/bekahhw/beyond-stars-and-forks-why-open-source-needs-better-collaboration-metrics-hla)**
    "When collaboration is measured effectively, it can reduce contributor burnout,
    increase successful first contributions, and build more sustainable projects."

### Herramientas existentes y sus gaps

12. **[GitHub issue-metrics](https://github.com/github/issue-metrics)**
    Time-to-first-response, time-to-close. Output: tabla markdown en un issue.
    Sin gráficos, sin tendencias, sin contributor journey.

13. **[OpenSauced — Contributor Insights](https://opensauced.pizza/docs/features/contributor-insights/)**
    OSCR score. Enfocado en contributor individual, no en community health de un repo. SaaS.

14. **[Scarf — A Different Approach to Community Health](https://about.scarf.sh/post/community-health-metrics)**
    Critica vanity metrics. Enfocado en OSS companies, no community-driven repos.

15. **[GitHub OSPO — Health Metrics](https://github.com/github/github-ospo/blob/main/docs/open-source-health-metrics.md)**
    Framework de GitHub para repos internos. Bus factor, closure ratio, contributor diversity.

### Frameworks y definiciones

16. **[The Open Source Contributor Funnel — Mike McQuaid (Homebrew)](https://mikemcquaid.com/the-open-source-contributor-funnel-why-people-dont-contribute-to-your-open-source-project/)**
    Define las etapas: User → Contributor → Maintainer. En Homebrew: millones de
    users, miles de contributors, decenas de maintainers. El drop-off entre etapas
    es enorme. **[Video CodeConf 2016](https://www.youtube.com/watch?v=OsOZpF6LFcw)**

17. **[CHAOSS — Types of Contributions](https://chaoss.community/kb/metric-types-of-contributions/)**
    Un contributor es cualquiera que contribuye al proyecto de cualquier manera.
    Incluye: code, docs, triage, community management, mentoring, eventos. No se
    limita a código.

18. **[CHAOSS — Contributor Absence Factor](https://chaoss.community/kb/metric-contributor-absence-factor/)**
    Antes llamado "Bus Factor." El menor número de contributors responsables del
    50% de las contribuciones. Un número bajo = alto riesgo.

19. **[CHAOSS — Conversion Rate](https://chaoss.community/kb/metric-conversion-rate/)**
    Porcentaje de first-time contributors que hacen una segunda contribución.
    Nesbitt (2026): esta métrica está rota por AI agents.

20. **[CHAOSS — Time to First Response](https://chaoss.community/kb/metric-time-to-first-response/)**
    Definición oficial: tiempo desde que se abre un PR/issue hasta la primera
    respuesta de alguien que no sea el autor. Filtrar bots. Filtrar por rol del
    que responde.

21. **[Predicting OSS Sustainability with Deep Learning (Feb 2026, arXiv)](https://arxiv.org/html/2602.09064v1)**
    Contribution activity y community features son las señales más fuertes de
    sostenibilidad. Release frequency predice menos de lo esperado.

22. **[Scaling Maintainer Intuition with PR Triage Boards — Yuvi Panda, 2i2c (Nov 2025)](https://2i2c.org/blog/pr-triage-boards/)**
    Sistema de triage para JupyterHub: priorizar PRs de first-timers, tamaño
    razonable, CI passing. Similar en espíritu a nuestro `fct_open_items`.

23. **[Open Source Contribution Statistics 2026 — Rockstar Developer University](https://rockstardeveloperuniversity.com/open-source-contribution-statistics/)**
    70% de contributors ocasionales nunca vuelven. 40% retention mes a mes para
    contributors regulares. Onboarding success rate: 15%.

---

## Métricas implementadas: definición, bibliografía y decisiones

### 1. Contributor Journey Timeline (`fct_contributor_events`)

**Qué mide**: Cada acción de cada persona en el repo, en orden temporal. Fork,
comment, issue abierto, PR abierto, PR mergeado, review dado.

**Definición formal**: No existe una definición académica estándar. CHAOSS define
[Types of Contributions](https://chaoss.community/kb/metric-types-of-contributions/)
como cualquier actividad (code, docs, triage, mentoring, etc.) pero no define
un timeline unificado de todas las actividades. GitHub Insights muestra una timeline
por contributor pero solo con commits — ignora comments, reviews, forks, issues.

**Lo que nosotros hacemos diferente**: Unificamos 6 tipos de eventos (fork, comment,
issue, PR, merge, review) en una única tabla temporal. Esto permite:
- Ver el journey completo de un contributor
- Detectar patrones de bot (4 comments en <60 segundos, fork→PR en 5 minutos)
- Comparar contributors entre sí
- Ver si alguien "desapareció" y cuándo fue su última actividad

**Quién más lo tiene**: Nadie en esta forma. OpenSauced tiene perfiles de
contributor pero sin la granularidad temporal del timeline.

**Status**: ✅ Implementado.

---

### 2. Time to First Response (`fct_response_times`)

**Qué mide**: Horas desde que se abre un PR/issue hasta la primera respuesta de
alguien que no sea el autor.

**Definición formal**: [CHAOSS — Time to First Response](https://chaoss.community/kb/metric-time-to-first-response/).
"How much time passes between when an activity requiring attention is created and
the first response." Excluir respuestas del autor. Excluir bots.

**Lo que nosotros hacemos diferente**: 
- Combinamos PRs e issues en una sola tabla con `item_type`
- Incluimos `created_at` para poder graficar tendencias / rolling averages
  (issue-metrics da un snapshot, no una serie de tiempo)
- Para PRs: la primera respuesta es el mínimo entre primer comment externo y
  primer review externo — CHAOSS no especifica esto claramente
- Para issues: en repos donde el maintainer crea los issues, el "time to first
  response" mide cuánto tarda la COMUNIDAD en engancharse, no cuánto tarda el
  maintainer en responder. Esto es una inversión del caso estándar. No encontré
  bibliografía que trate esta distinción.

**Bibliografía clave**:
- [Iyer et al. 2021/2023](https://arxiv.org/abs/2104.02933): la primera respuesta
  está correlacionada con contribuciones futuras, pero el efecto es del contexto
  (proyecto + contributor) más que de la respuesta en sí
- [Understanding Time to First Response (2023)](https://arxiv.org/abs/2304.08426):
  delays impactan retención de nuevos contributors
- [Rockstar Developer University 2026](https://rockstardeveloperuniversity.com/open-source-contribution-statistics/):
  contributors que reciben respuesta en <24h tienen 3x más probabilidad de volver

**Status**: ✅ Implementado.

---

### 3. Who Has The Ball (`fct_open_items`)

**Qué mide**: Para cada PR/issue abierto: quién actuó último, hace cuánto, y si
la pelota está con el maintainer o con el contributor.

**Definición formal**: No existe métrica estándar. Lo más cercano es:
- [2i2c PR Triage Boards (2025)](https://2i2c.org/blog/pr-triage-boards/):
  sistema para JupyterHub que prioriza PRs por estado, pero no usa la lógica
  explícita de "waiting on maintainer vs contributor"
- [Apache Airflow PR Triage](https://github.com/apache/airflow/blob/main/contributing-docs/25_maintainer_pr_triage.md):
  checks deterministas (CI status, merge conflicts, unresolved threads) pero
  enfocado en pipelines internos, no en community repos
- [Count.co — PR Bottleneck Analysis](https://count.co/integration/github/pull-request-bottleneck-analysis):
  análisis de bottleneck para equipos de ingeniería (SaaS, SQL custom), no para
  open source community repos

**Lo que nosotros hacemos diferente**: Lógica simple basada en `author_association`:
- Último actor es OWNER/COLLABORATOR/MEMBER → ball con contributor
- Último actor es otro (o nadie respondió) → ball con maintainer
- PR mergeado o issue cerrado → excluido (resuelto)

Esto es lo más accionable del dashboard. Un maintainer abre la vista y sabe
qué espera SU respuesta ahora mismo.

**Limitación**: La lógica de `author_association` depende de cómo GitHub clasifica
a las personas. Un contributor que no es collaborator pero tiene contexto (ej:
otro contributor ayudando) se clasifica como "ball con maintainer" — puede no
ser correcto. Es un edge case aceptable para un MVP.

**Status**: ✅ Implementado.

---

### 4. Little's Law — WIP vs Throughput (`fct_weekly_pulse`)

**Qué mide**: Por semana: PRs abiertos, mergeados, WIP acumulado, throughput
promedio de 4 semanas, y cycle time.

**Definición formal**: [Little's Law](https://en.wikipedia.org/wiki/Little%27s_law)
(1961): L = λW, o equivalentemente **Cycle Time = WIP / Throughput**.
- WIP = items en progreso (PRs abiertos en un momento dado)
- Throughput = items completados por unidad de tiempo (merges/semana)
- Cycle time = tiempo promedio que un item pasa en el sistema

**Aplicación a open source**: El artículo de [Armanc Keser sobre Jellyfin (2026)](https://armanckeser.com/writing/jellyfin-flow)
es la mejor referencia. Aplicó Little's Law a un repo real: 200 PRs abiertos,
30 merges/mes = 6.7 meses de cycle time. No es un backlog temporal, es un estado
permanente del sistema.

También describe el **Batch Size Death Spiral**: PRs grandes → reviews lentos →
contributors acumulan más cambios mientras esperan → PRs más grandes → reviews
aún más lentos.

**Lo que nosotros hacemos diferente**: Nadie publica esta métrica como serie de
tiempo para open source repos. Hay herramientas de Kanban/Agile que calculan
Little's Law (Nave, Jira, etc.) pero son para equipos internos, no para community
repos con contributors externos.

**Nuestra implementación**: Rolling average de 4 semanas de throughput. Cycle time
calculado como WIP / throughput_4w_avg. Cuando throughput = 0, cycle time = NULL
(sistema detenido, no infinito).

**Status**: ✅ Implementado.

---

### 5. Contributor Funnel (`dim_contributors.funnel_stage`)

**Qué mide**: En qué etapa del funnel está cada contributor: engaged → forked →
pr_opened → merged → repeat_contributor.

**Definición formal**: [Mike McQuaid — The Open Source Contributor Funnel](https://mikemcquaid.com/the-open-source-contributor-funnel-why-people-dont-contribute-to-your-open-source-project/)
define tres etapas: User → Contributor → Maintainer. En Homebrew: millones de
users, miles de contributors, decenas de maintainers.

[CHAOSS — Conversion Rate](https://chaoss.community/kb/metric-conversion-rate/)
mide el porcentaje de first-time contributors que hacen una segunda contribución.

**Datos de referencia**:
- [Rockstar Developer University 2026](https://rockstardeveloperuniversity.com/open-source-contribution-statistics/):
  70% de contributors ocasionales nunca vuelven. Retention mes a mes: 40%.
  Onboarding success rate: 15%.
- Nuestro repo (drkrillo/good-first-issues): 5% repeat contributors (3 de 51).

**Lo que nosotros hacemos diferente**: Expandimos el funnel de McQuaid (3 etapas)
a 5 etapas medibles con datos de la API:

| Etapa | Definición | McQuaid equivalente |
|-------|-----------|---------------------|
| `engaged` | Solo comentó/review, sin fork | User (que interactúa) |
| `forked` | Forkeó pero no abrió PR | User (con intención) |
| `pr_opened` | Abrió PR, ninguno mergeado | Contributor (fallido) |
| `merged` | Al menos 1 PR mergeado | Contributor |
| `repeat_contributor` | >1 PR, al menos 1 mergeado | Contributor recurrente |

**Decisión de diseño — ¿quién cuenta como contributor?**

CHAOSS dice: ["A contributor is anyone who contributes to the project in any way"](https://chaoss.community/kb/metric-types-of-contributions/).
Esto incluye comments, issues, reviews — no solo código.

Nosotros contamos a los 51 (todos los que hicieron cualquier actividad), no solo
a los 36 que forkearon. La razón:
- 15 personas comentaron/abrieron issues sin forkear. Son parte de la comunidad.
- Excluirlos del funnel oculta un dato importante: el repo tiene gente que
  PARTICIPA en la conversación pero no da el paso de contribuir código.
- El funnel completo muestra la conversión desde "engagement" hasta "repeat
  contributor", no solo desde "fork" hasta "merge".

Pero el funnel se puede leer de las dos formas:
- **Funnel amplio** (51): engaged(14) → forked(16) → pr_opened(7) → merged(11) → repeat(3)
- **Funnel de código** (desde fork): forked(36) → pr_opened(28) → merged(14) → repeat(3)

Ambas lecturas son válidas. El dashboard debería permitir filtrar.

**Status**: ✅ Implementado (funnel amplio). Filtro por fork pendiente de visualización.

---

### 6. Bot/AI Agent Detection Signals (`dim_contributors` + `fct_contributor_events`)

**Qué mide**: Señales de comportamiento que pueden indicar actividad automatizada:
- `minutes_fork_to_first_action`: tiempo entre fork y primera acción
- `burst_events`: eventos con <60 segundos entre ellos
- `min_seconds_between_events`: mínimo intervalo entre acciones
- `seconds_since_prev_event` en cada evento del timeline

**Definición formal**: No existe métrica estándar. CHAOSS tiene [Bot Activity](https://chaoss.community/kb/metric-bot-activity/)
pero asume que los bots están etiquetados — el problema actual es que los AI
agents usan cuentas normales de usuario y generan texto que parece humano
([Nesbitt 2026](https://nesbitt.io/2026/05/27/chaoss-metrics-in-2026.html)).

**Lo que nosotros hacemos diferente**: En vez de intentar clasificar (bot vs humano),
mostramos las señales de comportamiento crudas. Un fork→PR en 5 minutos o 4
comments en 60 segundos es información. El maintainer decide.

Datos de nuestro repo como ejemplo:
- ARYAN-MISHRA-2006: fork→PR en 5 minutos
- Francisc0Lopes: fork→comment en -1 minuto (casi simultáneo)
- keshavsharma0614-blip: fork→comment en 0 minutos, fork→PR en 16 minutos

**Status**: ✅ Implementado (señales crudas, sin clasificación).

---

## Métricas futuras: backlog priorizado

### 7. Ghost PRs (no implementado)

**Qué mide**: PRs que NUNCA recibieron respuesta. Histórico completo.

**Bibliografía**:
- [Are You Still Working on This? (2021)](https://whystar.github.io/res/paper/abPR_TSE2021.pdf):
  la falta de respuesta es la causa #1 de abandono
- [On Wasted Contributions (2022)](https://arxiv.org/abs/2110.15447):
  PRs abandonados se predicen por duración del review

**Implementación**: Query sobre `fct_response_times WHERE first_response_at IS NULL`.
No necesita nuevo modelo.

**Prioridad**: Alta. Es un dato revelador con implementación trivial.

---

### 8. First-Timer Success Rate (no implementado)

**Qué mide**: % de first-time PR authors que fueron mergeados vs cerrados sin merge.

**Bibliografía**:
- [Does the First Response Matter? (2021/2023)](https://arxiv.org/abs/2104.02933):
  la experiencia del contributor es un factor predictivo
- [Open Source Contribution Stats 2026](https://rockstardeveloperuniversity.com/open-source-contribution-statistics/):
  onboarding success rate global: 15%

**Implementación**: Query sobre `dim_contributors` filtrando `prs_opened = 1`.
No necesita nuevo modelo.

**Prioridad**: Alta. Dato clave para medir qué tan welcoming es el repo.

---

### 9. PR Size vs Review Time (no implementado)

**Qué mide**: Correlación entre tamaño del PR (additions + deletions) y tiempo de respuesta/merge.

**Bibliografía**:
- [Keser 2026 (Jellyfin)](https://armanckeser.com/writing/jellyfin-flow):
  "Batch Size Death Spiral" — PRs grandes causan reviews lentos que causan PRs
  más grandes
- [Little's Law](https://en.wikipedia.org/wiki/Little%27s_law): reducir batch
  size es una de las dos palancas para reducir cycle time

**Implementación**: Join entre `fct_response_times` y `stg_pull_requests`.
No necesita nuevo modelo.

**Prioridad**: Media. Requiere scatter plot en la visualización.

---

### 10. Cross-Pollination Index (no implementado)

**Qué mide**: ¿Los contributors interactúan ENTRE ELLOS o todo pasa por el
maintainer?

**Bibliografía**:
- [CHAOSS — Contributor Absence Factor](https://chaoss.community/kb/metric-contributor-absence-factor/):
  mide concentración de contribuciones. Si un solo contributor hace todo, el
  proyecto es frágil. Nosotros extendemos esto a REVIEWS e INTERACCIONES, no solo
  code contributions.
- [Predicting OSS Sustainability (2026)](https://arxiv.org/html/2602.09064v1):
  "community structure plays a critical role: projects with low bus factor, high
  contributor turnover, or limited repeat participation face elevated risks."

**Nuestra definición**: Si contributor A comenta en el PR de contributor B, eso
es cross-pollination. Si solo el OWNER comenta en todo, el bus factor de reviews
es 1. Porcentaje de comments/reviews que NO son del owner.

**Implementación**: Nuevo cálculo cruzando `stg_issue_comments` con
`stg_pull_requests` (quién comenta en PR de quién).

**Prioridad**: Media-Alta. Métrica verdaderamente novedosa. Nadie la publica.

---

### 11. Review Iterations per PR (no implementado)

**Qué mide**: Ciclos de CHANGES_REQUESTED → revisión por PR.

**Bibliografía**:
- 3-5 review rounds es normal según prácticas de la industria
- "Ping-pong reviews" (5+ rounds) son la causa más común de review cycles lentos
- [Cortex 2026](https://www.coderabbit.ai/blog/ai-is-burning-out-the-people-who-keep-open-source-alive):
  incidentes por PR +23.5%, código se mergea más rápido pero review quality baja

**Implementación**: Contar transiciones de estado en `stg_pr_reviews` por PR.

**Prioridad**: Media.

---

### 12. Time-of-Day Heatmap (no implementado)

**Qué mide**: ¿A qué hora contribuyen? ¿A qué hora responde el maintainer?

**Relevancia**: Señal de burnout (responder a las 2am), desfase de timezones
entre maintainer y contributors.

**Implementación**: Extract hour/weekday de timestamps en `fct_contributor_events`.
Trivial.

**Prioridad**: Baja. Útil para storytelling pero no accionable.

---

### 13. Conversation Depth (no implementado)

**Qué mide**: Cantidad de intercambios (back-and-forth) por PR/issue.

**Implementación**: Count de comments agrupado por item. Parcial — no tenemos
thread-level data (quién responde a quién).

**Prioridad**: Baja.

---

## Visualizaciones: qué gráficos, qué tabla, qué muestran

### V1. Contributor Journey — Timeline individual

**Tabla**: `fct_contributor_events`

**Qué muestra**: Una línea de tiempo por contributor. Cada punto es un evento
(fork, comment, issue abierto, PR abierto, PR mergeado, review). El eje X es
tiempo, el eje Y es el contributor. Se ve el journey completo: cuándo llegó,
qué hizo, si volvió, cuánto tiempo entre acciones.

**Para qué sirve**: Entender el comportamiento individual. ¿Forkeó y nunca
volvió? ¿Hizo 4 comments en un minuto? ¿Abrió PR y esperó 3 meses sin
respuesta? Es la vista principal para investigar un contributor específico.

**Visual sugerido**: Swimlane / timeline horizontal. Cada fila = contributor,
cada punto = evento coloreado por tipo.

---

### V2. Community Activity — Serie de tiempo agregada

**Tabla**: `fct_contributor_events` (agrupado por semana/mes y event_type)

**Qué muestra**: Todos los contributors sumados. Eventos por semana, stacked
por tipo (forks, comments, PRs abiertos, merges, reviews). El volumen total
de actividad de la comunidad a lo largo del tiempo.

**Para qué sirve**: Ver tendencias. ¿La comunidad está creciendo o muriendo?
¿Hay picos de actividad? ¿Los forks suben pero los PRs no? Eso indica que
la gente llega pero no contribuye.

**Visual sugerido**: Stacked area chart. Eje X = semana, eje Y = cantidad de
eventos, colores = tipo de evento.

---

### V3. Contributor Funnel — Conversión por etapa

**Tabla**: `dim_contributors` (campo `funnel_stage`)

**Qué muestra**: Cuántos contributors hay en cada etapa del funnel:
engaged → forked → pr_opened → merged → repeat_contributor.

Ejemplo con nuestros datos:
- engaged: 14 (solo comentaron/review, sin fork)
- forked: 16 (forkearon pero no abrieron PR)
- pr_opened: 7 (abrieron PR, ninguno mergeado)
- merged: 11 (al menos 1 PR mergeado)
- repeat_contributor: 3 (>1 PR, al menos 1 mergeado)

**Para qué sirve**: Identificar dónde se pierde la gente. Si muchos forkean
pero pocos abren PR, el problema es el paso "fork → PR" (¿issues poco claros?
¿contributing guide?). Si muchos abren PR pero pocos mergean, el cuello de
botella está en el review.

**Visual sugerido**: Funnel chart o horizontal bar chart ordenado por etapa.

---

### V4. Little's Law — WIP vs Throughput

**Tabla**: `fct_weekly_pulse`

**Qué muestra**: Por semana:
- `wip`: PRs abiertos acumulados (cuántos están "en cola")
- `throughput_4w_avg`: promedio de merges por semana (rolling 4 semanas)
- `cycle_time_weeks`: WIP / throughput — cuántas semanas tarda un PR promedio
  en el sistema

**Para qué sirve**: Es el indicador más importante de salud operativa. Si el
WIP crece y el throughput no, el cycle time se dispara. Un maintainer solo con
50 PRs abiertos y 2 merges/semana = 25 semanas de espera promedio. Little's Law
te dice si estás ganando o perdiendo la batalla.

**Visual sugerido**: Dual-axis line chart. Eje izquierdo = WIP (área), eje
derecho = cycle_time_weeks (línea). Throughput como línea secundaria.

---

### V5. Time to First Response — Serie de tiempo

**Tabla**: `fct_response_times`

**Qué muestra**: Para cada PR e issue, el `hours_to_first_response` ploteado
en el tiempo (por `created_at`). Separado por `item_type` (PR vs issue).
Con rolling average superpuesto.

**Contexto importante**: En repos donde el maintainer crea los issues (como
drkrillo/good-first-issues), el time to first response en issues mide cuánto
tarda la COMUNIDAD en engancharse — no cuánto tarda el maintainer en responder.

**Para qué sirve**: Ver la tendencia. ¿Estoy respondiendo más rápido o más
lento? ¿Hubo un período donde todo se acumuló? El rolling average suaviza
los picos y muestra la dirección real.

**Visual sugerido**: Scatter plot (cada punto = un item) con línea de rolling
average superpuesta. Color por item_type.

---

### V6. Who Has The Ball — Estado actual

**Tabla**: `fct_open_items`

**Qué muestra**: Todos los items abiertos (PRs e issues), divididos por
`waiting_on`: "maintainer" o "contributor". Incluye `hours_waiting` (hace
cuántas horas espera) y `last_action_type` (qué fue lo último que pasó).

**Para qué sirve**: Es la vista más accionable. El maintainer abre esto y
sabe exactamente: "tengo 3 PRs esperando mi review, el más viejo lleva 48
horas". No es una métrica histórica — es un estado actual, un to-do list
inteligente.

**Visual sugerido**: Dos columnas o stacked bar: "Waiting on me" vs "Waiting
on contributor". Cada item con título, horas esperando, y link. Los más
viejos arriba.

---

### V7. Contributor Scatter — Vista multidimensional

**Tabla**: `dim_contributors`

**Qué muestra**: Cada contributor como un punto en un scatter plot con ejes
configurables. Posibles dimensiones:
- `comments_made` vs `prs_opened`
- `prs_merged` vs `days_active_span`
- `total_events` vs `burst_events`

**Para qué sirve**: Identificar clusters y outliers sin clasificar. Alguien
con 50 comments y 0 PRs es diferente a alguien con 1 comment y 5 PRs merged.
Ambos son contributors válidos, pero el maintainer los entiende diferente.
Los outliers en `burst_events` o `min_seconds_between_events` son candidatos
a investigar como posibles bots/agents.

**Visual sugerido**: Scatter plot interactivo. Tamaño del punto = total_events.
Color = funnel_stage. Hover = nombre del contributor.

---

### V8. Bot/Agent Detection — Señales de velocidad

**Tabla**: `dim_contributors` + `fct_contributor_events`

**Qué muestra**: Las señales crudas de comportamiento automatizado:
- `minutes_fork_to_first_action` (dim_contributors): ¿cuánto tardó del fork
  a la primera acción?
- `burst_events` (dim_contributors): ¿cuántos eventos con <60s entre ellos?
- `min_seconds_between_events` (dim_contributors): ¿cuál fue el intervalo
  mínimo?
- `seconds_since_prev_event` (fct_contributor_events): permite ver el patrón
  temporal exacto de cada contributor

**Para qué sirve**: No clasifica — muestra datos. El maintainer ve que
ARYAN-MISHRA-2006 forkeó→PR en 5 minutos y decide si es un bot o un
contributor rápido. Es la herramienta, no el juicio.

**Visual sugerido**: Tabla ordenable por `minutes_fork_to_first_action` y
`burst_events`. Click en un contributor abre su timeline (V1).

---

## Nuestro diferencial vs herramientas existentes

| Feature | oss-health-metrics | GitHub Insights | issue-metrics | OpenSauced |
|---------|-------------------|-----------------|---------------|------------|
| Contributor Journey Timeline | ✅ 6 event types, temporal | Solo commits | ❌ | Profile sin timeline |
| Who Has The Ball | ✅ Por item abierto | ❌ | ❌ | ❌ |
| Time to Response (tendencia) | ✅ Serie de tiempo | ❌ | Snapshot | ❌ |
| Little's Law / Cycle Time | ✅ Semanal | ❌ | ❌ | ❌ |
| Contributor Funnel | ✅ 5 etapas | ❌ | ❌ | Parcial (active/new/alumni) |
| Bot Detection Signals | ✅ Velocity cruda | ❌ | ❌ | ❌ |
| Zero Infra | ✅ Python+DuckDB | N/A (built-in) | ✅ GitHub Action | ❌ SaaS |
| Cross-Pollination | 🔜 Backlog | ❌ | ❌ | ❌ |
| Ghost PRs | 🔜 Query | ❌ | Parcial | ❌ |
