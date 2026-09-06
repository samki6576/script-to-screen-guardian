# Hackathon Submission Kit

## Submission checklist

- [ ] Hosted URL (Cloud Run backend + frontend deploy)
- [ ] 3-minute demo video (script below)
- [ ] Public GitHub repository, MIT-licensed
- [ ] Devpost submission form filled out (copy below)

## 3-minute demo video script

**0:00–0:20 — The problem**
"Film productions lose millions to preventable disruptions — a rain delay,
an unavailable rain machine, a scheduling conflict nobody caught until the
call sheet went out. Script-to-Screen Guardian catches these before they
happen."

**0:20–0:50 — Upload & scene breakdown**
Show pasting the sample warehouse scene, hitting "Run production analysis."
Narrate: "A Script Supervisor agent, powered by Gemini, reads the scene and
extracts location, props, characters, and special requirements — here,
a rain effect and a crash sound cue."

**0:50–1:40 — Parallel agent investigation**
"Two agents run in parallel: the Location Scout checks live weather for the
shoot date, and the Logistics Agent checks our ClickHouse-backed inventory
for equipment and crew availability. Here it finds the rain machine is
under scheduled maintenance — a real conflict, not a guess."

**1:40–2:20 — Studio Head verdict & dashboard**
"The Studio Head agent combines both signals into a single risk verdict:
HIGH risk, with concrete recommendations — reschedule, secure a backup rain
machine — and an estimated cost impact. The dashboard updates in real time
over WebSocket, styled like a script supervisor's continuity binder."

**2:20–2:50 — Grafana & scale**
Show the Grafana panel over the `risk_reports` ClickHouse table: "Across an
entire production slate, this becomes a live risk board any studio
executive can check each morning."

**2:50–3:00 — Close**
"Script-to-Screen Guardian: catching the disruption before it's a delay."

## Devpost submission form content

**Inspiration**
Production delays on set are extraordinarily expensive, and most of the
warning signs — weather, equipment status, crew conflicts — already exist
as data. They're just scattered across different tools and nobody
correlates them until it's too late.

**What it does**
Ingests a film script, breaks it into scenes, and runs each scene through a
multi-agent pipeline that checks live weather risk and real equipment/crew
availability, then produces a single risk verdict with concrete
recommendations and a cost-impact estimate.

**How we built it**
Four cooperating agents (Script Supervisor, Location Scout, Logistics
Agent, Studio Head) orchestrated with Gemini for reasoning and ClickHouse
for fast structured queries over equipment inventory and crew schedules,
exposed through a FastAPI backend and a React dashboard, with Grafana for
production-wide visualization.

**Challenges we ran into**
Keeping agent outputs strictly structured (JSON-mode prompting), combining
two independent risk signals into one coherent verdict without
double-counting, and making the demo resilient enough to run even without
live API credentials.

**Accomplishments we're proud of**
A genuinely multi-step agentic workflow (not a single prompt wrapper), a
real ClickHouse partner integration doing real queries, and a dashboard
designed around the actual vocabulary of a film set rather than a generic
SaaS template.

**What we learned**
How much of "AI agent" reliability comes down to disciplined structured
outputs and graceful degradation, not just prompt quality.

**What's next**
Ingesting real call sheets and shooting schedules directly, multi-production
portfolio views, and Slack/email alerts when a scene's risk crosses a
threshold.
