"""
Vercel serverless entry point — Sales & Marketing Nanobot Swarm.

Primary:  Ollama Cloud (ministral-3:8b  ~3-5 s)
Fallback: NVIDIA NIM  (meta/llama-3.3-70b-instruct)
Uses httpx directly — no openai SDK dependency.

VibeCaaS.com / NeuralQuantum.ai LLC
"""

import os
import time
import json as _json
import re
import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY", "").strip()

OLLAMA_BASE = "https://ollama.com/v1"
OLLAMA_MODEL = "ministral-3:8b"
NIM_BASE = "https://integrate.api.nvidia.com/v1"
NIM_MODEL = "meta/llama-3.3-70b-instruct"

HTTP_TIMEOUT = 120.0

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Sales & Marketing Nanobot Swarm",
    description=(
        "Hierarchical AI Agent Swarm for Sales & Marketing — "
        "powered by VibeCaaS.com / NeuralQuantum.ai LLC"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

SM_SYSTEM = """You are the Sales & Marketing Nanobot Swarm — a hierarchical AI agent
system built on VibeCaaS.com / NeuralQuantum.ai LLC technology. You orchestrate
a network of specialist agents to execute comprehensive sales and marketing strategies.

## Core Competencies

### Lead Generation & Qualification
- Ideal Customer Profile (ICP) definition: firmographic, technographic, and behavioural signals
- Multi-channel prospecting: LinkedIn Sales Navigator, cold email, intent data, content syndication
- Lead scoring frameworks: ILT (Ideal Lead Template), BANT (Budget / Authority / Need / Timeline),
  MEDDIC (Metrics / Economic Buyer / Decision Criteria / Decision Process / Identify Pain / Champion)
- Lead velocity rate tracking and MQL → SQL → Opportunity funnel conversion optimisation
- Outbound cadence design: touch frequency, channel mix, personalisation at scale
- ICP tier definition (Tier A/B/C) and routing logic to appropriate sales motions

### Content Marketing
- Keyword research and SEO content strategy: TOFU / MOFU / BOFU funnel coverage
- Content brief creation: H1/H2 structure, word count, LSI keywords, internal links
- SEO-optimised writing: Flesch Reading Ease, keyword density, E-E-A-T signals
- Content gap analysis vs. competitor content coverage
- Distribution strategy: organic, paid amplification, email syndication, community seeding
- Content ROI measurement: organic traffic, MQL attribution, topic cluster authority

### Email Marketing Campaigns
- Audience segmentation: lifecycle stage, engagement recency, firmographic, behavioural
- Email sequence design: welcome, nurture, trial follow-up, win-back, post-purchase
- Subject line A/B testing methodology: statistical significance, test one variable at a time
- Deliverability optimisation: SPF / DKIM / DMARC, bounce rate management, spam complaint reduction
- List hygiene: re-engagement campaigns, sunset policies, verification services
- Email metrics: open rate, CTR, RPE (Revenue Per Email), sequence ROI, LTV by acquisition source

### Social Media Strategy
- Platform-specific content strategies: LinkedIn (B2B authority), Twitter/X (real-time),
  Instagram (brand/culture), YouTube (long-form education)
- Organic content calendar: content mix ratios, post frequency, optimal timing
- Employee advocacy programme design and content supply
- Paid social: audience targeting, lookalike audiences, retargeting sequences
- Community management: engagement protocols, DM response playbooks, UGC strategy
- Social listening: brand mentions, competitor tracking, category conversations

### Campaign Analytics
- Multi-touch attribution modelling: first touch, last touch, linear, time decay, data-driven
- Core metrics: CAC (Customer Acquisition Cost), LTV (Customer Lifetime Value), LTV:CAC ratio
- ROAS (Return on Ad Spend) by channel; breakeven ROAS calculation
- CAC payback period analysis; target <12 months for sustainable growth
- Funnel performance: conversion rates at each stage with bottleneck identification
- Budget optimisation: marginal efficiency analysis, reallocation modelling
- MRR growth, churn rate, NPS tracking, and cohort analysis

### Competitive Intelligence
- Competitor landscape mapping: direct, indirect, emerging, and status quo competitors
- Feature and pricing matrix: updated monthly with source documentation
- Positioning gap analysis: identify unowned messaging territory
- Win/loss analysis: pattern identification from CRM data and call recordings
- Battlecard creation: why-we-win, landmines, objection responses for top 5 competitors
- Competitive threat level scoring: High / Medium / Low with evidence-based rationale

### Sales Enablement
- ICP pain point mapping with business impact and cost of inaction quantification
- Sales collateral audit: identify gaps in discovery, demo, proposal, and closing materials
- Objection handling guide: top 20 objections with acknowledge/clarify/respond/confirm framework
- Mutual action plan and success plan templates for enterprise deals
- Pipeline coaching: MEDDIC health scoring, deal risk flags, next-action recommendations
- Sales training content: onboarding programme, ongoing skill development

### Account-Based Marketing (ABM)
- Target account selection: Tier 1 (1:1), Tier 2 (1:few), Tier 3 (programmatic)
- Account scoring model: ICP fit, intent signals, strategic value, relationship depth
- Account research: org chart mapping, decision maker identification, pain signal analysis
- Personalised campaign creation: custom landing pages, direct mail, bespoke content
- Multi-touch outreach: coordinated LinkedIn + email + phone + paid social sequences
- Account progression tracking: engagement scores, pipeline created, deals closed

### Brand Strategy & Messaging
- Brand voice and tone of voice guidelines: personality traits, writing principles, anti-patterns
- Messaging matrix: category claim, persona-specific value propositions, proof pillars
- Brand audit: consistency review across all external touchpoints
- Message A/B testing: data-driven iteration on core positioning claims
- Share of voice tracking: organic search, social media, analyst coverage

### Marketing Automation & CRM
- Lead routing rules: territory, round-robin, ICP tier-based assignment
- Lifecycle stage automation: trigger-based transitions from MQL through Customer
- CRM data hygiene: deduplication, enrichment, required field validation
- Workflow design: nurture sequences, sales task triggers, alert notifications
- Integration design: ESP, CRM, advertising platforms, intent data, analytics

## Operating Principles
- Always ground recommendations in data and specific metrics — avoid vague advice
- Provide concrete, actionable next steps with owners and timelines
- Prioritise revenue impact: focus on the activities that move pipeline and closed-won revenue
- Think in systems: build sustainable, scalable processes not one-off tactics
- Measure everything: no initiative is recommended without a clear success metric
- Be honest about trade-offs: acknowledge resource constraints and opportunity costs
"""


AGENT_BUILDER_SYSTEM = """You are an expert Sales & Marketing Agent Builder for the
Nanobot Swarm platform (VibeCaaS.com / NeuralQuantum.ai LLC).

Your role is to generate complete, production-ready AgentTeam configurations for
sales and marketing use cases.

## Available Tools
- lead_scoring_calc       : ICP fit, BANT, MEDDIC, lead velocity, conversion probability
- campaign_analytics_calc : CAC, LTV, ROAS, payback period, MRR growth, churn, NPS
- content_optimizer       : Readability, keyword density, content gaps, meta score, headline power
- seo_analyzer            : Domain authority, keyword difficulty, traffic potential, rank probability
- email_campaign_manager  : Deliverability, open rate benchmarks, revenue per email, sequence ROI
- social_media_analyzer   : Platform-specific engagement and reach analysis
- competitor_research     : Competitor monitoring, feature comparison, positioning analysis
- market_segmentation     : TAM/SAM/SOM, market penetration, segment attractiveness scoring
- roi_calculator          : Marketing ROI, content ROI, SEO ROI, paid media ROI, event ROI
- crm_integration         : CRM data access, lead routing, lifecycle management
- web_search              : Real-time web search for market research and competitive intelligence
- code_runner             : Execute Python/JS for custom calculations and data processing
- http_fetch              : Fetch external URLs for data enrichment and monitoring
- knowledge_tools         : Read/write to shared knowledge graph for persistent context
- vault_memory            : Secure storage for campaign credentials and API keys

## Agent Configuration Format
When building an agent or team, output a complete JSON configuration:

```json
{
  "name": "agent-slug",
  "description": "One-line description",
  "mode": "hierarchical|flat",
  "agents": ["role-1", "role-2"],
  "tools": ["tool_1", "tool_2"],
  "system_prompt": "Full detailed system prompt...",
  "inject_knowledge": true,
  "inject_history": false,
  "temperature": 0.1,
  "max_tokens": 6144,
  "metadata": {"category": "...", "owner": "..."}
}
```

## Design Principles
1. Hierarchical teams (orchestrator + specialists) work best for multi-step workflows.
2. Flat teams work best for parallel review tasks (e.g., brand review panel).
3. Always include the minimum set of tools needed — avoid tool bloat.
4. System prompts should include a numbered workflow (Step 1 to Step N).
5. Output Format section should define exact deliverable structure.
6. Temperature: 0.0-0.1 for analysis/data tasks; 0.2-0.45 for creative content.
7. max_tokens: 6144-8192 for hierarchical; 3000-4096 for flat/single agents.
"""


TEAM_BUILDER_SYSTEM = """You are an expert Sales & Marketing Team Builder for the
Nanobot Swarm platform (VibeCaaS.com / NeuralQuantum.ai LLC).

You design complete multi-agent team configurations optimised for specific sales
and marketing outcomes. You understand team composition, agent role design, tool
selection, and workflow sequencing.

## Team Design Framework

### Revenue-Stage Alignment
- **Awareness Stage**: content-marketing-team, social-media-strategist, brand-voice-guardian
- **Consideration Stage**: lead-generation-engine, abm-orchestrator, competitive-intelligence
- **Decision Stage**: sales-enablement-team, email-campaign-manager
- **Retention/Expansion**: campaign-analytics-hub, growth-hacker-lab

### Team Topology Patterns
1. **Hierarchical (recommended for execution)**: Orchestrator agent coordinates specialist agents.
   Sequential workflow with handoffs. Best for complex, multi-step campaigns.
2. **Flat (recommended for review)**: All agents work in parallel on same task.
   Best for QA, brand review, or research synthesis.
3. **Hybrid**: Hierarchical with flat sub-teams for specific stages.

### Agent Role Naming Conventions
- Orchestrators: `[domain]-orchestrator`
- Researchers: `[domain]-researcher` or `[domain]-analyst`
- Creators: `[domain]-writer` or `[domain]-creator`
- Reviewers: `[domain]-reviewer` or `[domain]-auditor`
- Executors: `[domain]-agent` or `[domain]-specialist`

When asked to build a team, produce:
1. Team configuration JSON
2. Agent role descriptions (one paragraph each)
3. Workflow diagram (ASCII or text-based)
4. Success metrics and KPIs
5. Tool justification (why each tool is needed)
"""

# ---------------------------------------------------------------------------
# Pre-configured team definitions (static data)
# ---------------------------------------------------------------------------

PRECONFIGURED_TEAMS: dict[str, dict] = {
    "lead-generation-engine": {
        "name": "lead-generation-engine",
        "description": "Multi-channel lead generation with ICP scoring, BANT/MEDDIC qualification, and SQL handoff.",
        "mode": "hierarchical",
        "agents": ["lead-gen-orchestrator", "icp-analyst", "linkedin-prospector", "cold-email-agent",
                   "intent-data-agent", "lead-scorer", "sdr-qualifier"],
        "tools": ["lead_scoring_calc", "campaign_analytics_calc", "market_segmentation",
                  "crm_integration", "web_search", "http_fetch"],
        "use_cases": ["ICP definition and refinement", "LinkedIn prospecting", "Cold email campaigns",
                      "Intent data activation", "BANT/MEDDIC qualification", "SQL pipeline building"],
        "kpis": ["MQLs per week", "MQL → SQL rate", "SQL pipeline value", "CAC by source"],
        "category": "demand-generation",
    },
    "content-marketing-team": {
        "name": "content-marketing-team",
        "description": "SEO content strategy: keyword research → content brief → SEO-optimised writing → distribution.",
        "mode": "hierarchical",
        "agents": ["content-orchestrator", "keyword-researcher", "brief-writer",
                   "seo-content-writer", "content-editor", "distribution-agent"],
        "tools": ["seo_analyzer", "content_optimizer", "roi_calculator", "web_search",
                  "http_fetch", "knowledge_tools"],
        "use_cases": ["Keyword research and content strategy", "Content brief creation",
                      "SEO-optimised blog posts", "Content gap analysis", "Content distribution"],
        "kpis": ["Organic sessions", "Keyword rankings", "Content-attributed MQLs", "Content ROI"],
        "category": "content-marketing",
    },
    "email-campaign-manager": {
        "name": "email-campaign-manager",
        "description": "Email sequence design, audience segmentation, A/B testing, deliverability management.",
        "mode": "hierarchical",
        "agents": ["email-orchestrator", "segmentation-agent", "sequence-designer",
                   "subject-line-tester", "deliverability-agent", "performance-analyst"],
        "tools": ["email_campaign_manager", "campaign_analytics_calc", "content_optimizer",
                  "crm_integration", "knowledge_tools"],
        "use_cases": ["List segmentation", "Email sequence creation", "Subject line testing",
                      "Deliverability optimisation", "Email performance analysis"],
        "kpis": ["Open rate", "CTR", "Revenue per email", "Deliverability score", "Sequence ROI"],
        "category": "email-marketing",
    },
    "social-media-strategist": {
        "name": "social-media-strategist",
        "description": "Platform-specific content calendar, engagement strategy, and paid social amplification.",
        "mode": "flat",
        "agents": ["linkedin-specialist", "twitter-specialist", "instagram-specialist",
                   "youtube-specialist", "paid-social-specialist"],
        "tools": ["social_media_analyzer", "content_optimizer", "campaign_analytics_calc",
                  "roi_calculator", "web_search"],
        "use_cases": ["30-day content calendar", "Platform audit", "Paid social campaigns",
                      "Community engagement strategy", "Influencer identification"],
        "kpis": ["Follower growth rate", "Engagement rate", "Reach", "Social-attributed MQLs", "CPL"],
        "category": "social-media",
    },
    "campaign-analytics-hub": {
        "name": "campaign-analytics-hub",
        "description": "Multi-touch attribution, CAC/LTV/ROAS analysis, funnel optimisation, budget reallocation.",
        "mode": "hierarchical",
        "agents": ["analytics-orchestrator", "attribution-modeler", "metrics-calculator",
                   "funnel-analyst", "budget-optimizer", "reporting-agent"],
        "tools": ["campaign_analytics_calc", "roi_calculator", "lead_scoring_calc",
                  "market_segmentation", "knowledge_tools"],
        "use_cases": ["Attribution modelling", "CAC/LTV/ROAS analysis", "Funnel bottleneck identification",
                      "Budget optimisation", "Marketing performance dashboards"],
        "kpis": ["ROAS by channel", "CAC by source", "LTV:CAC ratio", "Funnel conversion rates"],
        "category": "marketing-analytics",
    },
    "competitive-intelligence": {
        "name": "competitive-intelligence",
        "description": "Competitor tracking, feature matrix, positioning gaps, win/loss analysis, battlecard creation.",
        "mode": "hierarchical",
        "agents": ["intel-orchestrator", "competitor-tracker", "feature-analyst",
                   "positioning-analyst", "winloss-analyst", "battlecard-writer"],
        "tools": ["competitor_research", "market_segmentation", "web_search", "http_fetch", "knowledge_tools"],
        "use_cases": ["Competitor landscape mapping", "Feature comparison matrix", "Positioning gap analysis",
                      "Win/loss pattern analysis", "Battlecard creation and maintenance"],
        "kpis": ["Battlecard coverage", "Win rate vs. each competitor", "Competitive displacement rate"],
        "category": "competitive-intelligence",
    },
    "sales-enablement-team": {
        "name": "sales-enablement-team",
        "description": "Pain mapping, collateral audit, battlecards, objection handling, pipeline coaching.",
        "mode": "hierarchical",
        "agents": ["enablement-orchestrator", "pain-researcher", "collateral-auditor",
                   "battlecard-creator", "objection-handler", "pipeline-coach"],
        "tools": ["lead_scoring_calc", "campaign_analytics_calc", "competitor_research",
                  "crm_integration", "knowledge_tools"],
        "use_cases": ["ICP pain point mapping", "Sales collateral audit", "Objection handling guide",
                      "Pipeline health review", "Rep coaching recommendations"],
        "kpis": ["Ramp time for new reps", "Win rate", "Deal cycle length", "Pipeline quality score"],
        "category": "sales-enablement",
    },
    "abm-orchestrator": {
        "name": "abm-orchestrator",
        "description": "Enterprise ABM: target account selection, account research, personalised multi-touch campaigns.",
        "mode": "hierarchical",
        "agents": ["abm-orchestrator-agent", "account-selector", "account-researcher",
                   "campaign-personalizer", "outreach-coordinator", "account-reporter"],
        "tools": ["lead_scoring_calc", "market_segmentation", "competitor_research",
                  "crm_integration", "web_search", "knowledge_tools"],
        "use_cases": ["Tier 1 account selection", "Account intelligence gathering", "Personalised landing pages",
                      "Multi-channel outreach coordination", "Account engagement scoring"],
        "kpis": ["ABM account MQL rate", "Meeting acceptance rate", "ABM pipeline ACV",
                 "ABM win rate", "ABM CAC vs. non-ABM CAC"],
        "category": "account-based-marketing",
    },
    "brand-voice-guardian": {
        "name": "brand-voice-guardian",
        "description": "Brand audit, tone of voice guidelines, messaging matrix, and pre-launch content review.",
        "mode": "flat",
        "agents": ["brand-strategist", "tone-of-voice-specialist", "messaging-architect", "content-reviewer"],
        "tools": ["content_optimizer", "seo_analyzer", "knowledge_tools", "web_search"],
        "use_cases": ["Brand consistency audit", "Tone of voice documentation", "Messaging matrix development",
                      "Pre-launch content review", "Brand perception monitoring"],
        "kpis": ["Brand audit score", "Content review approval rate", "Share of voice", "Branded search volume"],
        "category": "brand",
    },
    "growth-hacker-lab": {
        "name": "growth-hacker-lab",
        "description": "Viral loop design, referral programme mechanics, ICE-scored experiment backlog.",
        "mode": "hierarchical",
        "agents": ["growth-orchestrator", "growth-model-analyst", "viral-loop-designer",
                   "referral-architect", "experiment-runner", "channel-scout"],
        "tools": ["campaign_analytics_calc", "roi_calculator", "market_segmentation",
                  "lead_scoring_calc", "web_search", "knowledge_tools"],
        "use_cases": ["Growth model mapping (AARRR)", "Viral loop design", "Referral programme architecture",
                      "ICE-scored experiment backlog", "New channel discovery"],
        "kpis": ["Viral coefficient (K-factor)", "Referral CAC", "Experiment velocity (per week)",
                 "Growth rate (MoM)", "CAC reduction trend"],
        "category": "growth",
    },
}

# ---------------------------------------------------------------------------
# Keyword → team routing map
# ---------------------------------------------------------------------------

TEAM_KEYWORDS: list[tuple[list[str], str]] = [
    (["lead", "prospect", "icp", "mql", "sql", "qualification", "bant", "meddic",
      "outbound", "prospecting", "pipeline", "sdr", "cadence", "cold outreach"], "lead-generation-engine"),
    (["content", "blog", "seo", "copy", "copywriting", "article", "keyword",
      "organic", "backlink", "editorial", "landing page", "whitepaper"], "content-marketing-team"),
    (["email", "sequence", "drip", "newsletter", "open rate", "deliverability",
      "subject line", "unsubscribe", "bounce", "esp", "nurture email"], "email-campaign-manager"),
    (["social", "instagram", "linkedin post", "twitter", "tiktok", "youtube",
      "social media", "content calendar", "engagement", "influencer", "reel"], "social-media-strategist"),
    (["analytics", "metrics", "roas", "cac", "ltv", "attribution", "funnel",
      "conversion rate", "churn", "mrr", "arr", "reporting", "dashboard"], "campaign-analytics-hub"),
    (["competitor", "competitive", "battle", "battlecard", "positioning", "market",
      "win loss", "feature matrix", "differentiation", "pricing compare"], "competitive-intelligence"),
    (["sales", "pipeline", "enablement", "objection", "close", "deal", "rep",
      "quota", "forecast", "coaching", "collateral", "pitch deck"], "sales-enablement-team"),
    (["abm", "account based", "enterprise", "target account", "named account",
      "tier 1", "personali", "1:1 marketing"], "abm-orchestrator"),
    (["brand", "messaging", "tone of voice", "voice and tone", "value proposition",
      "positioning statement", "category claim", "brand audit"], "brand-voice-guardian"),
    (["growth", "viral", "referral", "experiment", "a/b test", "hack", "growth loop",
      "k-factor", "activation", "retention", "product led"], "growth-hacker-lab"),
]


def _detect_team(goal: str) -> str:
    """Return the best-matching pre-configured team name for a given goal."""
    goal_lower = goal.lower()
    for keywords, team_name in TEAM_KEYWORDS:
        if any(kw in goal_lower for kw in keywords):
            return team_name
    return "lead-generation-engine"  # sensible default


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SwarmRunRequest(BaseModel):
    goal: str = Field(..., description="High-level goal or task for the swarm to execute.")
    team: Optional[str] = Field(None, description="Override team name. Auto-detected from goal if omitted.")
    context: Optional[dict] = Field(None, description="Optional additional context for the run.")
    stream: bool = Field(False, description="Stream the response token-by-token.")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "ministral-3:8b"
    messages: list[ChatMessage]
    temperature: float = 0.1
    max_tokens: int = 4096
    stream: bool = False


class AgentBuildRequest(BaseModel):
    name: str = Field(..., description="Agent name slug (e.g. 'linkedin-prospector').")
    description: str = Field(..., description="One-line description of agent purpose.")
    role: str = Field(..., description="Detailed description of agent's role and responsibilities.")
    tools: list[str] = Field(default_factory=list, description="Tools this agent should use.")
    context: Optional[str] = Field(None, description="Additional context for agent generation.")


class TeamBuildRequest(BaseModel):
    name: str = Field(..., description="Team name slug (e.g. 'demand-gen-squad').")
    description: str = Field(..., description="One-line team purpose.")
    goal: str = Field(..., description="Primary goal this team achieves.")
    mode: str = Field("hierarchical", description="Team topology: hierarchical or flat.")
    agent_count: int = Field(4, ge=2, le=10, description="Number of agents in the team.")
    tools: list[str] = Field(default_factory=list, description="Tools available to the team.")


# ---------------------------------------------------------------------------
# LLM call helpers
# ---------------------------------------------------------------------------

async def _call_ollama(messages: list[dict], temperature: float = 0.1, max_tokens: int = 4096) -> str:
    """Call Ollama Cloud API. Returns the assistant message content."""
    if not OLLAMA_API_KEY:
        raise RuntimeError("OLLAMA_API_KEY not configured.")

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(
            f"{OLLAMA_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {OLLAMA_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _call_nim(messages: list[dict], temperature: float = 0.1, max_tokens: int = 4096) -> str:
    """Call NVIDIA NIM API (fallback). Returns the assistant message content."""
    if not NVIDIA_API_KEY:
        raise RuntimeError("NVIDIA_API_KEY not configured.")

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(
            f"{NIM_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": NIM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _llm_call(
    messages: list[dict],
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> tuple[str, str]:
    """
    Primary → fallback LLM call.

    Returns (content, backend_used) where backend_used is 'ollama' or 'nvidia_nim'.
    """
    if OLLAMA_API_KEY:
        try:
            content = await _call_ollama(messages, temperature, max_tokens)
            return content, "ollama"
        except Exception:
            pass  # Fall through to NVIDIA NIM

    if NVIDIA_API_KEY:
        content = await _call_nim(messages, temperature, max_tokens)
        return content, "nvidia_nim"

    raise HTTPException(
        status_code=503,
        detail="No LLM backend available. Configure OLLAMA_API_KEY or NVIDIA_API_KEY.",
    )


async def _stream_llm(messages: list[dict], temperature: float = 0.1, max_tokens: int = 4096):
    """
    Streaming LLM call — yields Server-Sent Events tokens.
    Tries Ollama first, falls back to NVIDIA NIM.
    """

    async def _stream_ollama():
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OLLAMA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        yield line + "\n\n"

    async def _stream_nim():
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{NIM_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": NIM_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        yield line + "\n\n"

    if OLLAMA_API_KEY:
        try:
            async for chunk in _stream_ollama():
                yield chunk
            return
        except Exception:
            pass

    if NVIDIA_API_KEY:
        async for chunk in _stream_nim():
            yield chunk
        return

    yield "data: {\"error\": \"No LLM backend available.\"}\n\n"


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _check_auth(x_api_key: Optional[str]) -> None:
    if GATEWAY_API_KEY and x_api_key != GATEWAY_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid or missing X-Api-Key header.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Sales & Marketing Nanobot Swarm",
        "version": "1.0.0",
        "powered_by": "VibeCaaS.com / NeuralQuantum.ai LLC",
        "backends": {
            "ollama": "configured" if OLLAMA_API_KEY else "not configured",
            "nvidia_nim": "configured" if NVIDIA_API_KEY else "not configured",
        },
        "timestamp": time.time(),
    }


@app.post("/swarm/run", tags=["Swarm"])
async def swarm_run(
    req: SwarmRunRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    Execute a sales & marketing task using the swarm.

    Auto-detects the best pre-configured team based on goal keywords,
    or use the 'team' field to override.
    """
    _check_auth(x_api_key)
    t0 = time.time()

    # Resolve team
    team_name = req.team or _detect_team(req.goal)
    team_config = PRECONFIGURED_TEAMS.get(team_name, PRECONFIGURED_TEAMS["lead-generation-engine"])

    # Build prompt
    context_str = ""
    if req.context:
        context_str = f"\n\n## Additional Context\n{_json.dumps(req.context, indent=2)}"

    messages = [
        {"role": "system", "content": SM_SYSTEM},
        {
            "role": "user",
            "content": (
                f"## Team: {team_name}\n"
                f"## Goal\n{req.goal}"
                f"{context_str}\n\n"
                f"Execute this goal using the {team_name} team. "
                f"Follow the team's workflow systematically and provide complete, actionable output."
            ),
        },
    ]

    if req.stream:
        return StreamingResponse(
            _stream_llm(messages, temperature=0.1, max_tokens=8192),
            media_type="text/event-stream",
        )

    content, backend = await _llm_call(messages, temperature=0.1, max_tokens=8192)

    return {
        "goal": req.goal,
        "team": team_name,
        "team_config": {
            "description": team_config["description"],
            "mode": team_config["mode"],
            "agents": team_config["agents"],
            "category": team_config.get("category", ""),
        },
        "result": content,
        "backend": backend,
        "latency_seconds": round(time.time() - t0, 2),
        "powered_by": "VibeCaaS.com / NeuralQuantum.ai LLC",
    }


@app.post("/v1/chat/completions", tags=["OpenAI Compatible"])
async def chat_completions(
    req: ChatCompletionRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    OpenAI-compatible chat completions endpoint.

    Injects SM_SYSTEM as the system message if no system message is present.
    """
    _check_auth(x_api_key)

    messages = [m.model_dump() for m in req.messages]

    # Inject SM_SYSTEM if no system message exists
    if not any(m["role"] == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": SM_SYSTEM})

    if req.stream:
        return StreamingResponse(
            _stream_llm(messages, req.temperature, req.max_tokens),
            media_type="text/event-stream",
        )

    content, backend = await _llm_call(messages, req.temperature, req.max_tokens)

    return {
        "id": f"chatcmpl-sm-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": OLLAMA_MODEL if backend == "ollama" else NIM_MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": -1,
            "completion_tokens": -1,
            "total_tokens": -1,
        },
        "backend": backend,
    }


@app.get("/v1/models", tags=["OpenAI Compatible"])
async def list_models():
    """List available models (OpenAI-compatible format)."""
    models = []
    if OLLAMA_API_KEY:
        models.append({
            "id": OLLAMA_MODEL,
            "object": "model",
            "created": 0,
            "owned_by": "ollama",
            "role": "primary",
        })
    if NVIDIA_API_KEY:
        models.append({
            "id": NIM_MODEL,
            "object": "model",
            "created": 0,
            "owned_by": "nvidia-nim",
            "role": "fallback",
        })
    return {"object": "list", "data": models}


@app.get("/swarm/health", tags=["Swarm"])
async def swarm_health():
    """Detailed swarm health including backend status and available teams."""
    return {
        "status": "operational",
        "service": "Sales & Marketing Nanobot Swarm",
        "version": "1.0.0",
        "backends": {
            "primary": {
                "provider": "Ollama Cloud",
                "model": OLLAMA_MODEL,
                "configured": bool(OLLAMA_API_KEY),
            },
            "fallback": {
                "provider": "NVIDIA NIM",
                "model": NIM_MODEL,
                "configured": bool(NVIDIA_API_KEY),
            },
        },
        "teams_available": len(PRECONFIGURED_TEAMS),
        "team_names": sorted(PRECONFIGURED_TEAMS.keys()),
        "capabilities": [
            "lead_generation_and_qualification",
            "content_marketing_and_seo",
            "email_campaign_management",
            "social_media_strategy",
            "campaign_analytics",
            "competitive_intelligence",
            "sales_enablement",
            "account_based_marketing",
            "brand_strategy",
            "growth_hacking",
        ],
        "powered_by": "VibeCaaS.com / NeuralQuantum.ai LLC",
    }


@app.get("/swarm/topology", tags=["Swarm"])
async def swarm_topology():
    """Return the swarm agent topology and team relationships."""
    topology = {}
    for team_name, config in PRECONFIGURED_TEAMS.items():
        topology[team_name] = {
            "description": config["description"],
            "mode": config["mode"],
            "agent_count": len(config["agents"]),
            "agents": config["agents"],
            "tools": config["tools"],
            "category": config.get("category", ""),
            "kpis": config.get("kpis", []),
        }

    return {
        "swarm_name": "Sales & Marketing Nanobot Swarm",
        "total_teams": len(PRECONFIGURED_TEAMS),
        "total_unique_agents": len(
            {agent for config in PRECONFIGURED_TEAMS.values() for agent in config["agents"]}
        ),
        "coordination_model": "hierarchical + flat hybrid",
        "teams": topology,
        "routing_logic": "keyword-based auto-detection with manual override via 'team' parameter",
        "powered_by": "VibeCaaS.com / NeuralQuantum.ai LLC",
    }


@app.post("/agent/build", tags=["Builder"])
async def agent_build(
    req: AgentBuildRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    AI-powered agent builder.

    Generates a complete agent configuration for a sales & marketing agent role.
    """
    _check_auth(x_api_key)
    t0 = time.time()

    tools_str = ", ".join(req.tools) if req.tools else "auto-select from available tools"

    messages = [
        {"role": "system", "content": AGENT_BUILDER_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Build a complete agent configuration for:\n\n"
                f"**Name**: {req.name}\n"
                f"**Description**: {req.description}\n"
                f"**Role**: {req.role}\n"
                f"**Tools**: {tools_str}\n"
                + (f"**Context**: {req.context}\n" if req.context else "")
                + "\n\nProvide a complete, production-ready agent configuration JSON "
                "with a detailed system prompt following the sales & marketing workflow format. "
                "Include a step-by-step workflow (Step 1 to Step N) and an Output Format section."
            ),
        },
    ]

    content, backend = await _llm_call(messages, temperature=0.15, max_tokens=6144)

    # Attempt to extract JSON configuration from the response
    config = None
    json_match = re.search(r"```(?:json)?\s*(\{[\s\S]+?\})\s*```", content)
    if json_match:
        try:
            config = _json.loads(json_match.group(1))
        except _json.JSONDecodeError:
            pass

    return {
        "agent_name": req.name,
        "generated_configuration": config,
        "full_response": content,
        "backend": backend,
        "latency_seconds": round(time.time() - t0, 2),
    }


@app.post("/team/build", tags=["Builder"])
async def team_build(
    req: TeamBuildRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    AI-powered team builder.

    Generates a complete multi-agent team configuration for a sales & marketing goal.
    """
    _check_auth(x_api_key)
    t0 = time.time()

    tools_str = ", ".join(req.tools) if req.tools else "auto-select from available tools"

    messages = [
        {"role": "system", "content": TEAM_BUILDER_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Build a complete multi-agent team configuration for:\n\n"
                f"**Team Name**: {req.name}\n"
                f"**Description**: {req.description}\n"
                f"**Primary Goal**: {req.goal}\n"
                f"**Mode**: {req.mode}\n"
                f"**Agent Count**: {req.agent_count}\n"
                f"**Available Tools**: {tools_str}\n\n"
                "Produce:\n"
                "1. Complete team configuration JSON\n"
                "2. Agent role descriptions (one paragraph each)\n"
                "3. Step-by-step workflow\n"
                "4. Success metrics and KPIs\n"
                "5. Tool justification"
            ),
        },
    ]

    content, backend = await _llm_call(messages, temperature=0.15, max_tokens=8192)

    # Attempt to extract JSON configuration
    config = None
    json_match = re.search(r"```(?:json)?\s*(\{[\s\S]+?\})\s*```", content)
    if json_match:
        try:
            config = _json.loads(json_match.group(1))
        except _json.JSONDecodeError:
            pass

    return {
        "team_name": req.name,
        "generated_configuration": config,
        "full_response": content,
        "backend": backend,
        "latency_seconds": round(time.time() - t0, 2),
    }


@app.get("/swarm/teams", tags=["Teams"])
async def list_swarm_teams():
    """
    List all pre-configured sales & marketing teams with descriptions and metadata.
    """
    teams_list = []
    for name, config in sorted(PRECONFIGURED_TEAMS.items()):
        teams_list.append({
            "name": name,
            "description": config["description"],
            "mode": config["mode"],
            "agent_count": len(config["agents"]),
            "category": config.get("category", ""),
            "tools": config["tools"],
            "use_cases": config.get("use_cases", []),
            "kpis": config.get("kpis", []),
        })

    return {
        "total": len(teams_list),
        "teams": teams_list,
        "routing_hint": (
            "Use POST /swarm/run with a 'goal' to auto-detect the best team, "
            "or pass a 'team' name from this list to override."
        ),
    }


@app.get("/swarm/teams/{team_name}", tags=["Teams"])
async def get_swarm_team(team_name: str):
    """
    Get detailed configuration for a specific pre-configured team.
    """
    config = PRECONFIGURED_TEAMS.get(team_name)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Team '{team_name}' not found. "
                f"Available teams: {sorted(PRECONFIGURED_TEAMS.keys())}"
            ),
        )

    return {
        "name": config["name"],
        "description": config["description"],
        "mode": config["mode"],
        "agents": config["agents"],
        "agent_count": len(config["agents"]),
        "tools": config["tools"],
        "category": config.get("category", ""),
        "use_cases": config.get("use_cases", []),
        "kpis": config.get("kpis", []),
        "how_to_invoke": {
            "auto": f"POST /swarm/run with a goal describing {config['description'].lower()}",
            "explicit": f"POST /swarm/run with team='{team_name}' and your goal",
        },
    }


# ---------------------------------------------------------------------------
# Vercel handler
# ---------------------------------------------------------------------------

# Vercel expects the FastAPI app exported as 'app' at module level.
# For local development: uvicorn api.index:app --reload
