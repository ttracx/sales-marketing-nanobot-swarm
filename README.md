# 🚀 Sales & Marketing Nanobot Swarm

> Hierarchical AI Agent Swarm for Sales & Marketing — powered by [VibeCaaS.com](https://vibecaas.com) / [NeuralQuantum.ai LLC](https://neuralquantum.ai)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ttracx/sales-marketing-nanobot-swarm)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)
[![Open in Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ttracx/sales-marketing-nanobot-swarm)

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-orange)](https://ollama.ai)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM%20Ready-76b900?logo=nvidia)](https://developer.nvidia.com/nim)
[![OpenAI Compatible](https://img.shields.io/badge/OpenAI-Compatible%20API-412991?logo=openai)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

The **Sales & Marketing Nanobot Swarm** is a production-ready, hierarchical AI agent platform that coordinates specialized sub-agents to execute complex marketing and sales workflows autonomously. Instead of relying on a single LLM call, it dispatches a coordinated swarm of specialist agents—each with a focused system prompt, dedicated tool set, and domain expertise—that work in parallel and synthesize their outputs into actionable results.

Think of it as spinning up an entire marketing department at AI speed: SEO analysts, copywriters, paid ads strategists, email marketers, CRO experts, sales intelligence analysts, and brand strategists—all working in concert on a single objective.

Built on **FastAPI** with an **OpenAI-compatible API**, it plugs into any existing tool, workflow, or platform that speaks the OpenAI protocol. Run it locally with **Ollama** for zero-cost inference, or connect it to **NVIDIA NIM**, OpenAI, Azure, or any other OpenAI-compatible backend.

---

## Features

- **10 Pre-Configured Agent Teams** — Full Funnel, SEO, Paid Ads, Content Creation, Email Marketing, Social Media, CRO, Sales Intelligence, Analytics & Reporting, Brand Strategy
- **OpenAI-Compatible API** — Drop-in replacement for OpenAI clients via `/v1/chat/completions`
- **Hierarchical Orchestration** — Director agent decomposes tasks and synthesizes results from specialist agents
- **Parallel Agent Execution** — Multiple agents run concurrently (configurable concurrency)
- **7 Marketing Calculation Tools** — ROAS, CAC, LTV, conversion rate, email revenue, SEO opportunity, content quality scorer
- **CRM Integrations** — HubSpot and Salesforce sync for lead management
- **Analytics Integration** — Google Analytics 4 via Measurement Protocol and Data API
- **Social Media Tools** — LinkedIn and X (Twitter) API publishing
- **Custom Agent & Team Builder** — Build and register custom agents at runtime via API
- **Async Job Queue** — Submit long-running swarms and poll for results
- **Session Memory** — Thread-based context persistence via Redis
- **Interactive Dashboard** — Full-featured web UI with real-time agent monitoring
- **1-Click Deploy** — Vercel, Render, Railway, Docker Compose, GitHub Codespaces
- **Self-Hosted Friendly** — Run entirely air-gapped with local Ollama

---

## Quick Start

### Option 1: Vercel (Fastest — 2 minutes)

Click the deploy button above, connect your repo, and set the environment variables in the Vercel dashboard. Uses your OpenAI API key for inference.

### Option 2: Local / Docker

```bash
# 1. Clone the repository
git clone https://github.com/ttracx/sales-marketing-nanobot-swarm.git
cd sales-marketing-nanobot-swarm

# 2. Start Ollama with the default model (local inference — free!)
ollama pull llama3.3
ollama serve

# 3. Run the setup script
./scripts/setup.sh

# 4. Configure your environment
cp .env.example .env
# Edit .env with your API keys (only AI_API_KEY is required for non-Ollama backends)

# 5. Launch the swarm
./scripts/launch.sh
# → API running at http://localhost:8200
# → Dashboard at http://localhost:8200/nanobot/static/index.html
```

### Option 3: Docker Compose (includes Ollama sidecar)

```bash
git clone https://github.com/ttracx/sales-marketing-nanobot-swarm.git
cd sales-marketing-nanobot-swarm
cp .env.example .env
docker compose up -d
```

### Your First Swarm Run

```bash
curl -X POST http://localhost:8200/swarm/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a 30-day LinkedIn content calendar for a B2B SaaS company targeting VP Engineering",
    "team": "content_creation",
    "context": {
      "company": "Acme Corp",
      "product": "DevOps automation platform",
      "audience": "VP Engineering at 50-500 person tech companies",
      "tone": "professional, insightful"
    }
  }'
```

Or use any OpenAI client:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8200/v1",
    api_key="your-secret-key"  # or blank for unauthenticated local dev
)

response = client.chat.completions.create(
    model="swarm/full_funnel",
    messages=[{"role": "user", "content": "Plan a product launch campaign for our new analytics feature"}]
)
print(response.choices[0].message.content)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SM NANOBOT SWARM PLATFORM                             │
│                      (FastAPI · Python 3.11+ · Async)                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ HTTP REST / WebSocket
                    ┌────────────┴────────────┐
                    │                         │
          ┌─────────▼──────────┐   ┌──────────▼────────────┐
          │   Dashboard UI      │   │   API Clients         │
          │  (Static HTML/CSS)  │   │  OpenAI SDK · cURL    │
          │  /static/index.html │   │  Zapier · LangChain   │
          └────────────────────┘   └───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    SWARM ORCHESTRATOR   │  ← POST /swarm/run
                    │    (Director Agent)     │     POST /v1/chat/completions
                    │  Task decomposition     │
                    │  Agent dispatch         │
                    │  Result synthesis       │
                    └────┬──────┬──────┬──────┘
                         │      │      │   parallel async dispatch
              ┌──────────┘  ┌───┘  ┌───┘  └─────────┐
              ▼             ▼      ▼                  ▼
     ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
     │  Specialist  │ │ Copywrite│ │Analytics │ │ Strategy │
     │  Agent 1     │ │ Agent 2  │ │ Agent 3  │ │ Agent N  │
     │  (SEO Expert)│ │ (Writer) │ │ (Data)   │ │  ...     │
     └──────┬───────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
            │              │            │             │
     ┌──────▼──────────────▼────────────▼─────────────▼──────┐
     │                  TOOL EXECUTION LAYER                   │
     │  calculate_roas · calculate_cac · calculate_ltv         │
     │  calculate_conversion_rate · estimate_email_revenue     │
     │  calculate_seo_opportunity · score_content_quality      │
     └───────────────────────┬────────────────────────────────┘
                             │
     ┌───────────────────────┼────────────────────────────────┐
     │                       │                                │
┌────▼────────┐   ┌──────────▼──────┐   ┌────────────────────▼───┐
│  HubSpot    │   │  Salesforce     │   │  Google Analytics 4    │
│  CRM API    │   │  CRM API        │   │  Data API              │
└─────────────┘   └─────────────────┘   └────────────────────────┘
                             │
     ┌───────────────────────▼────────────────────────────────┐
     │                   LLM BACKEND                           │
     │   Ollama (local) · NVIDIA NIM · OpenAI · Azure OAI     │
     │   Any OpenAI-compatible endpoint                        │
     └─────────────────────────────────────────────────────────┘
```

---

## Agent Teams

### 🎯 Full Funnel Swarm (`full_funnel`)

The universal entry point. Use this when unsure which team to choose. The Director decomposes your goal, routes sub-tasks to appropriate specialists, and synthesizes a cohesive strategy. Best for: campaign planning, product launches, market entry strategies.

### 🔍 SEO Research Swarm (`seo_research`)

Four coordinated agents: Keyword Researcher, SERP Analyst, Content Gap Identifier, and Technical SEO Advisor. Delivers prioritized keyword lists, competitive SERP analysis, content opportunity reports, and technical audit checklists. Uses `calculate_seo_opportunity` to quantify traffic and revenue potential.

### 📢 Paid Ads Swarm (`paid_ads`)

Five agents covering Google Ads architecture, Meta Ads creative strategy, bidding optimization, ad copy generation, and landing page alignment. Outputs campaign structure, ad group taxonomy, copy variants, and ROAS/CAC projections using built-in calculators.

### ✍️ Content Creation Swarm (`content_creation`)

Four agents: Content Strategist, Copywriter, SEO Optimizer, and Editor. Produces long-form blog posts, landing page copy, email sequences, social media posts, and video scripts. Automatically runs content quality and SEO density scoring on all outputs.

### 📧 Email Marketing Swarm (`email_marketing`)

Four agents specializing in drip sequence architecture, subject line optimization, list segmentation strategy, and deliverability best practices. Generates complete multi-email sequences with A/B variants, send-time recommendations, and projected revenue using the email revenue estimator. Integrates with HubSpot for list management.

### 📱 Social Media Swarm (`social_media`)

Five agents with platform-specific expertise for LinkedIn, X (Twitter), Instagram, Facebook, TikTok, and YouTube. Generates platform-native content respecting character limits, hashtag strategies, optimal posting schedules, and trend integration. Supports direct publishing via LinkedIn and X APIs.

### 🧪 CRO Swarm (`cro`)

Four agents: UX Analyst, A/B Test Architect, Copy Optimizer, and Funnel Analyst. Generates conversion hypotheses ranked by ICE score, A/B test design documents, copy variants, and funnel drop-off analysis. Uses conversion rate calculator to quantify revenue impact of optimization scenarios.

### 🤝 Sales Intelligence Swarm (`sales_intelligence`)

Five agents covering ICP development, lead scoring model design, outreach sequence writing, objection handling scripts, and competitive positioning. Integrates with HubSpot and Salesforce for contact enrichment and lead creation. Outputs battle cards, persona profiles, and personalized outreach sequences.

### 📊 Analytics & Reporting Swarm (`analytics_reporting`)

Four agents: KPI Architect, Attribution Modeler, Cohort Analyst, and Executive Summarizer. Reads GA4 data (when configured), applies marketing attribution models, performs cohort retention analysis, and produces executive-ready summaries with recommendations. Calculates LTV, CAC, and ROAS ratios automatically.

### 🎨 Brand Strategy Swarm (`brand_strategy`)

Four agents focused on competitive analysis, positioning frameworks (Jobs-to-be-Done, Category Design), messaging hierarchy development, and persona creation. Produces positioning statements, messaging matrices, brand voice guidelines, and competitive differentiation maps.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/swarm/run` | Execute a swarm task (primary endpoint) |
| `POST` | `/v1/chat/completions` | OpenAI-compatible completions |
| `GET` | `/v1/models` | List models and teams (OpenAI format) |
| `GET` | `/swarm/teams` | List all registered agent teams |
| `GET` | `/swarm/teams/{name}` | Get team details, agents, and tools |
| `GET` | `/swarm/run/{run_id}` | Poll async run status |
| `POST` | `/agent/build` | Create a custom agent at runtime |
| `POST` | `/team/build` | Assemble a custom team at runtime |
| `GET` | `/health` | Health check with dependency status |
| `GET` | `/docs` | Swagger UI (interactive API explorer) |
| `GET` | `/redoc` | ReDoc API documentation |

### POST /swarm/run — Request Schema

```json
{
  "task": "string (required) — natural language task description",
  "team": "string (optional, default: full_funnel) — team slug",
  "context": {
    "key": "value — arbitrary context injected into agent prompts"
  },
  "async": false,
  "thread_id": "string (optional) — for session-persistent context",
  "max_agents": 5
}
```

### POST /swarm/run — Response Schema

```json
{
  "run_id": "run_7f3c9a12e4b8",
  "status": "completed | pending | failed",
  "team": "email_marketing",
  "duration_ms": 4823,
  "agents_used": 4,
  "result": {
    "summary": "...",
    "deliverables": ["..."],
    "agent_outputs": {
      "agent_name": { "output": "...", "tokens_used": 312 }
    },
    "recommendations": []
  },
  "cost_estimate_usd": 0.0142
}
```

---

## Deployment Options

### Vercel (Serverless)

Best for: quick demos, lower-traffic APIs, no DevOps overhead.

```bash
vercel --prod
# or use the 1-click button above
```

Note: 60s execution limit on Hobby (300s on Pro). Use async mode for long runs.

### Render

Best for: always-on deployments with auto-sleep on free tier.

```bash
# render.yaml is included — just connect your repo
```

### Railway

Best for: persistent workloads, easy scaling, generous free tier.

```bash
# Procfile is included
railway up
```

### Docker Compose (Self-Hosted)

Best for: local development, privacy-sensitive workloads, air-gapped environments.

```bash
docker compose up -d
# Starts API server + Ollama sidecar
# Pre-pulls llama3.3 model automatically
```

### GitHub Codespaces

Best for: development, testing, demos without local setup.

Click "Open in Codespaces" above. The `.devcontainer` sets up Python, installs dependencies, and starts Ollama automatically.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_API_BASE_URL` | `http://localhost:11434` | LLM backend endpoint |
| `AI_API_KEY` | — | LLM provider API key (blank for local Ollama) |
| `AI_MODEL_NAME` | `llama3.3` | Default model for agents |
| `PORT` | `8200` | API server port |
| `API_SECRET_KEY` | — | Bearer token for API authentication |
| `MAX_CONCURRENT_AGENTS` | `5` | Parallel agent concurrency |
| `SWARM_TIMEOUT_SECONDS` | `120` | Max wall-clock time per swarm run |
| `AGENT_TIMEOUT_SECONDS` | `30` | Max time per individual agent |
| `REDIS_URL` | — | Redis for sessions and async job queue |
| `HUBSPOT_API_KEY` | — | HubSpot CRM integration |
| `SALESFORCE_ACCESS_TOKEN` | — | Salesforce CRM integration |
| `SALESFORCE_INSTANCE_URL` | — | Salesforce org URL |
| `GA4_MEASUREMENT_ID` | — | Google Analytics 4 Measurement ID |
| `GA4_API_SECRET` | — | GA4 Measurement Protocol API secret |
| `SLACK_BOT_TOKEN` | — | Slack notifications on swarm completion |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `SM_PRO_LICENSE_KEY` | — | Unlocks Pro features |

---

## Project Structure

```
sales-marketing-nanobot-swarm/
├── api/                        # Vercel serverless function entry points
│   └── index.py                # Main FastAPI app for Vercel
├── nanobot/
│   ├── api/
│   │   ├── __init__.py
│   │   └── gateway.py          # FastAPI app for Docker/Railway/Render
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agents.py           # Base agent class
│   │   ├── director.py         # Director orchestrator
│   │   └── swarm.py            # Swarm execution engine
│   ├── teams/
│   │   ├── __init__.py
│   │   ├── full_funnel.py
│   │   ├── seo_research.py
│   │   ├── paid_ads.py
│   │   ├── content_creation.py
│   │   ├── email_marketing.py
│   │   ├── social_media.py
│   │   ├── cro.py
│   │   ├── sales_intelligence.py
│   │   ├── analytics_reporting.py
│   │   └── brand_strategy.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── marketing_calculators.py
│   │   ├── hubspot_tools.py
│   │   ├── salesforce_tools.py
│   │   └── ga4_tools.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── hubspot.py
│   │   ├── salesforce.py
│   │   ├── google_analytics.py
│   │   └── slack.py
│   ├── knowledge/
│   │   └── __init__.py
│   ├── state/
│   │   └── __init__.py         # Redis-backed session state
│   ├── scheduler/
│   │   └── __init__.py         # Cron job registry (Pro)
│   └── static/
│       ├── index.html          # Dashboard UI
│       ├── docs-page.html      # Documentation
│       └── faq.html            # FAQ
├── scripts/
│   ├── setup.sh                # Development setup
│   └── launch.sh               # Start the API server
├── tests/
│   ├── unit/
│   └── integration/
├── docs/                       # Extended documentation
├── .env.example                # Environment template
├── vercel.json                 # Vercel routing config
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## Pro Version (Coming Soon)

The open-source core is MIT-licensed and production-ready. **SM Nanobot Swarm Pro** adds:

| Feature | Free / OSS | Pro |
|---------|-----------|-----|
| All 10 Agent Teams | ✅ | ✅ |
| OpenAI-Compatible API | ✅ | ✅ |
| 7 Marketing Tools | ✅ | ✅ |
| HubSpot / Salesforce / GA4 | ✅ | ✅ |
| Concurrent Agents | Up to 5 | Unlimited |
| Long-term Vector Memory | ❌ | ✅ |
| Scheduled Swarm Campaigns | ❌ | ✅ |
| Multi-User Workspaces | ❌ | ✅ |
| Workflow Automation Pipelines | ❌ | ✅ |
| Advanced Analytics Dashboard | ❌ | ✅ |
| White-Label Dashboard | ❌ | ✅ |
| Zapier / Make.com Connectors | ❌ | ✅ |
| SSO / SAML | ❌ | ✅ |
| Dedicated NIM Endpoints | ❌ | ✅ |
| SOC 2 Compliance Mode | ❌ | ✅ |
| Support | GitHub Issues | Priority + SLA |

**Pricing** (planned):
- **Starter**: $49/month — 5,000 swarm runs, 1 workspace, 3 users
- **Growth**: $149/month — 25,000 runs, 5 workspaces, 10 users, white-label
- **Agency**: $399/month — unlimited runs, unlimited workspaces, unlimited users
- **Enterprise**: Custom — on-premise, SLA, dedicated account manager

> 📬 [Join the waitlist](mailto:pro@neuralquantum.ai) for early access and 50% off the first 6 months.

---

## Contributing

Contributions are welcome! Here is how to get started:

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/sales-marketing-nanobot-swarm.git
cd sales-marketing-nanobot-swarm

# Set up development environment
./scripts/setup.sh

# Create a feature branch
git checkout -b feature/my-new-agent-team

# Run tests
pytest tests/ -v

# Make your changes, then submit a PR
```

### Contributing Guidelines

- **New agent teams**: Add a file to `nanobot/teams/` following the existing team structure. Include docstrings with team description, example prompts, and agent roles.
- **New tools**: Add to `nanobot/tools/` and decorate with `@register_tool`. Include unit tests in `tests/unit/`.
- **New integrations**: Add to `nanobot/integrations/`. Ensure credentials are loaded from environment variables only.
- **Bug reports**: Open a GitHub Issue with reproduction steps and the `/health` endpoint output.
- **Feature requests**: Open a GitHub Discussion before investing in implementation.

All PRs must include:
- Unit tests with >80% coverage for new code
- Updated docstrings
- An entry in `CHANGELOG.md`

---

## License

MIT License — Copyright (c) 2025 NeuralQuantum.ai LLC

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

---

## Powered By

<table>
  <tr>
    <td align="center"><a href="https://vibecaas.com"><strong>VibeCaaS.com</strong></a><br/>Vibe coding IDE &amp; platform</td>
    <td align="center"><a href="https://neuralquantum.ai"><strong>NeuralQuantum.ai LLC</strong></a><br/>Quantum-inspired AI algorithms</td>
    <td align="center"><a href="https://ollama.ai"><strong>Ollama</strong></a><br/>Local LLM runtime</td>
    <td align="center"><a href="https://developer.nvidia.com/nim"><strong>NVIDIA NIM</strong></a><br/>GPU-accelerated inference</td>
  </tr>
</table>

---

*Built with ❤️ by [Tommy Xaypanya](https://neuralquantum.ai) — Chief AI & Quantum Systems Officer, NeuralQuantum.ai LLC*

<!-- THOX-DOCS-STANDARD:START -->
## Repository Description

Hierarchical AI Agent Swarm for Sales & Marketing — powered by VibeCaaS.com / NeuralQuantum.ai LLC

## Documentation

- [Repository documentation](docs/README.md)
- [Security policy](SECURITY.md)
- [Contributing guide](CONTRIBUTING.md)
- [Legal notice](NOTICE.md)

## THOX.ai LLC

This repository is maintained by THOX.ai LLC.

- Tommy Xaypanya is CTO.
- Craig Ross is CEO.

## Copyright and Legal

Copyright (c) 2026 THOX.ai LLC. All rights reserved unless this repository includes a separate license file that states otherwise.

THOX-specific documentation, configuration, branding, product definitions, and integration work are owned by THOX.ai LLC unless explicitly noted. Third-party dependencies, forks, vendored components, and upstream source materials remain governed by their original licenses and notices.
<!-- THOX-DOCS-STANDARD:END -->
