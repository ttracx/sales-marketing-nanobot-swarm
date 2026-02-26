"""
Sales & Marketing Nanobot Swarm — Specialized calculation and analysis tools.

Provides 7 domain-specific tools for:
- Lead scoring and qualification (ICP, BANT, MEDDIC)
- Campaign analytics (CAC, LTV, ROAS, payback period)
- Content optimization (readability, SEO, headline power)
- SEO analysis (keyword difficulty, traffic potential)
- Email campaign management (deliverability, sequence ROI)
- Market segmentation (TAM/SAM/SOM estimation)
- ROI calculation (multi-channel marketing ROI)

All tools follow the BaseTool / ToolResult contract and support
both Anthropic and OpenAI schema formats.
"""

from __future__ import annotations

import math
from typing import Any

from nanobot.tools.base import BaseTool, ToolResult


# ---------------------------------------------------------------------------
# 1. Lead Scoring Calculator
# ---------------------------------------------------------------------------

class LeadScoringCalcTool(BaseTool):
    """
    Scores and qualifies leads using ICP fit, BANT, MEDDIC, and predictive models.

    Supported calc_types:
      - ilt_score          : Ideal Lead Template score (0-100, ICP fit)
      - bant_qualify       : Budget / Authority / Need / Timeline scoring
      - meddic_score       : MEDDIC qualification framework score
      - lead_velocity_rate : Month-over-month growth in qualified leads
      - conversion_probability : Probability of lead → closed-won
    """

    name = "lead_scoring_calc"
    description = (
        "Scores and qualifies sales leads using ICP fit (ILT), BANT, MEDDIC frameworks, "
        "lead velocity rate, and conversion probability. Returns scores 0-100 with "
        "qualification status and prioritised next-step recommendations."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "calc_type": {
                "type": "string",
                "enum": [
                    "ilt_score",
                    "bant_qualify",
                    "meddic_score",
                    "lead_velocity_rate",
                    "conversion_probability",
                ],
                "description": "Type of lead scoring calculation to perform.",
            },
            "company_size": {
                "type": "integer",
                "description": "Number of employees at prospect company.",
            },
            "industry": {
                "type": "string",
                "description": "Industry vertical of the prospect.",
            },
            "title_seniority": {
                "type": "string",
                "enum": ["C-Suite", "VP", "Director", "Manager", "Individual Contributor", "Unknown"],
                "description": "Seniority level of the primary contact.",
            },
            "engagement_signals": {
                "type": "integer",
                "description": "Number of tracked engagement events (email opens, site visits, demo requests).",
            },
            "budget_range": {
                "type": "string",
                "enum": ["<$10k", "$10k-$50k", "$50k-$200k", "$200k-$1M", ">$1M", "Unknown"],
                "description": "Stated or inferred budget range.",
            },
            "timeline_months": {
                "type": "number",
                "description": "Stated purchase timeline in months (0 = immediate, 12+ = long-term).",
            },
            "pain_score": {
                "type": "integer",
                "description": "Self-reported or inferred pain intensity score (0-10).",
            },
            "decision_maker_confirmed": {
                "type": "boolean",
                "description": "Whether a confirmed economic buyer / decision maker has been identified.",
            },
            "champion_identified": {
                "type": "boolean",
                "description": "Whether an internal champion has been identified.",
            },
            "current_month_qualified": {
                "type": "integer",
                "description": "Qualified leads generated this month (for lead_velocity_rate).",
            },
            "previous_month_qualified": {
                "type": "integer",
                "description": "Qualified leads generated last month (for lead_velocity_rate).",
            },
            "stage_win_rates": {
                "type": "array",
                "items": {"type": "number"},
                "description": "Array of stage-by-stage win rates [0-1] from prospect to close.",
            },
            "days_in_stage": {
                "type": "number",
                "description": "Number of days lead has been in current pipeline stage.",
            },
        },
        "required": ["calc_type"],
    }

    # ICP target ranges for scoring
    _IDEAL_COMPANY_SIZE_MIN = 50
    _IDEAL_COMPANY_SIZE_MAX = 5000
    _SENIORITY_WEIGHTS = {
        "C-Suite": 1.0,
        "VP": 0.9,
        "Director": 0.75,
        "Manager": 0.55,
        "Individual Contributor": 0.3,
        "Unknown": 0.2,
    }
    _BUDGET_WEIGHTS = {
        "<$10k": 0.1,
        "$10k-$50k": 0.4,
        "$50k-$200k": 0.75,
        "$200k-$1M": 0.95,
        ">$1M": 1.0,
        "Unknown": 0.15,
    }

    def run(self, **kwargs: Any) -> ToolResult:  # noqa: C901
        calc_type = kwargs.get("calc_type", "")

        try:
            if calc_type == "ilt_score":
                return self._ilt_score(**kwargs)
            elif calc_type == "bant_qualify":
                return self._bant_qualify(**kwargs)
            elif calc_type == "meddic_score":
                return self._meddic_score(**kwargs)
            elif calc_type == "lead_velocity_rate":
                return self._lead_velocity_rate(**kwargs)
            elif calc_type == "conversion_probability":
                return self._conversion_probability(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown calc_type '{calc_type}'. Valid: ilt_score, bant_qualify, "
                          "meddic_score, lead_velocity_rate, conversion_probability.",
                    tool_name=self.name,
                )
        except Exception as exc:
            return ToolResult(success=False, error=str(exc), tool_name=self.name)

    # ------------------------------------------------------------------
    def _ilt_score(self, **kw) -> ToolResult:
        company_size = int(kw.get("company_size", 0))
        title_seniority = kw.get("title_seniority", "Unknown")
        engagement_signals = int(kw.get("engagement_signals", 0))
        industry = kw.get("industry", "")

        # Firmographic fit (40 pts)
        if self._IDEAL_COMPANY_SIZE_MIN <= company_size <= self._IDEAL_COMPANY_SIZE_MAX:
            firmographic = 40.0
        elif company_size > self._IDEAL_COMPANY_SIZE_MAX:
            firmographic = 35.0  # enterprise — still good but needs different motion
        elif company_size > 10:
            firmographic = 20.0
        else:
            firmographic = 5.0

        # Seniority (35 pts)
        seniority_score = self._SENIORITY_WEIGHTS.get(title_seniority, 0.2) * 35.0

        # Engagement (25 pts) — log-based diminishing returns
        engagement_score = min(25.0, math.log1p(engagement_signals) * 5.5)

        raw_score = firmographic + seniority_score + engagement_score
        score = round(min(100.0, raw_score), 1)

        if score >= 75:
            tier, action = "A — Hot", "Route to AE immediately. Add to Tier-1 sequence."
        elif score >= 55:
            tier, action = "B — Warm", "Enroll in nurture sequence. SDR follow-up within 24 h."
        elif score >= 35:
            tier, action = "C — Cool", "Long-nurture sequence. Marketing-qualified only."
        else:
            tier, action = "D — Unqualified", "Do not work. Return to awareness campaigns."

        return ToolResult(
            success=True,
            data={
                "calc_type": "ilt_score",
                "ilt_score": score,
                "tier": tier,
                "breakdown": {
                    "firmographic_fit_40pts": round(firmographic, 1),
                    "title_seniority_35pts": round(seniority_score, 1),
                    "engagement_signals_25pts": round(engagement_score, 1),
                },
                "recommended_action": action,
                "inputs": {
                    "company_size": company_size,
                    "industry": industry,
                    "title_seniority": title_seniority,
                    "engagement_signals": engagement_signals,
                },
            },
            tool_name=self.name,
        )

    # ------------------------------------------------------------------
    def _bant_qualify(self, **kw) -> ToolResult:
        budget = kw.get("budget_range", "Unknown")
        seniority = kw.get("title_seniority", "Unknown")
        pain_score = min(10, max(0, int(kw.get("pain_score", 0))))
        timeline = float(kw.get("timeline_months", 12))

        b_score = self._BUDGET_WEIGHTS.get(budget, 0.15) * 25
        a_score = self._SENIORITY_WEIGHTS.get(seniority, 0.2) * 25
        n_score = (pain_score / 10.0) * 25

        # Need score (shorter timeline = higher score)
        if timeline <= 1:
            t_score = 25.0
        elif timeline <= 3:
            t_score = 20.0
        elif timeline <= 6:
            t_score = 14.0
        elif timeline <= 12:
            t_score = 8.0
        else:
            t_score = 3.0

        total = round(b_score + a_score + n_score + t_score, 1)
        qualified = total >= 60

        return ToolResult(
            success=True,
            data={
                "calc_type": "bant_qualify",
                "bant_total_score": total,
                "qualified": qualified,
                "qualification_status": "SQL — Sales Qualified Lead" if qualified else "MQL — Needs further nurturing",
                "breakdown": {
                    "Budget_25pts": round(b_score, 1),
                    "Authority_25pts": round(a_score, 1),
                    "Need_25pts": round(n_score, 1),
                    "Timeline_25pts": round(t_score, 1),
                },
                "gaps": [
                    k for k, v in {
                        "Budget clarity": b_score < 10,
                        "Economic buyer confirmed": a_score < 12,
                        "Clear pain identified": n_score < 12,
                        "Active buying timeline": t_score < 8,
                    }.items() if v
                ],
                "next_steps": (
                    "Schedule discovery call to map stakeholders and confirm budget."
                    if not qualified else
                    "Progress to demo / proposal. Assign AE and create deal in CRM."
                ),
            },
            tool_name=self.name,
        )

    # ------------------------------------------------------------------
    def _meddic_score(self, **kw) -> ToolResult:
        pain_score = min(10, max(0, int(kw.get("pain_score", 0))))
        decision_maker = bool(kw.get("decision_maker_confirmed", False))
        champion = bool(kw.get("champion_identified", False))
        budget = kw.get("budget_range", "Unknown")
        engagement = int(kw.get("engagement_signals", 0))

        # MEDDIC components (each ~16-17 pts)
        metrics_score = round((pain_score / 10) * 17, 1)          # Metrics
        econ_buyer_score = 17.0 if decision_maker else 4.0         # Economic Buyer
        decision_criteria = round(min(17, engagement * 1.2), 1)    # Decision Criteria (proxy)
        decision_process = round(min(17, engagement * 0.9), 1)     # Decision Process (proxy)
        identify_pain_score = round((pain_score / 10) * 16, 1)    # Identify Pain
        champion_score = 16.0 if champion else 3.0                 # Champion

        total = round(
            metrics_score + econ_buyer_score + decision_criteria +
            decision_process + identify_pain_score + champion_score, 1
        )
        total = min(100, total)

        return ToolResult(
            success=True,
            data={
                "calc_type": "meddic_score",
                "meddic_total": total,
                "deal_confidence": "High" if total >= 70 else "Medium" if total >= 45 else "Low",
                "breakdown": {
                    "Metrics": metrics_score,
                    "Economic_Buyer": econ_buyer_score,
                    "Decision_Criteria": decision_criteria,
                    "Decision_Process": decision_process,
                    "Identify_Pain": identify_pain_score,
                    "Champion": champion_score,
                },
                "risks": [
                    comp for comp, score in {
                        "No economic buyer confirmed": econ_buyer_score < 10,
                        "Weak pain articulation": identify_pain_score < 8,
                        "No internal champion": champion_score < 8,
                        "Unclear decision process": decision_process < 8,
                    }.items() if score
                ],
            },
            tool_name=self.name,
        )

    # ------------------------------------------------------------------
    def _lead_velocity_rate(self, **kw) -> ToolResult:
        current = int(kw.get("current_month_qualified", 0))
        previous = int(kw.get("previous_month_qualified", 1))

        if previous == 0:
            lvr = 100.0
        else:
            lvr = round(((current - previous) / previous) * 100, 2)

        trend = "Growing" if lvr > 0 else "Declining" if lvr < 0 else "Flat"

        return ToolResult(
            success=True,
            data={
                "calc_type": "lead_velocity_rate",
                "lvr_percent": lvr,
                "trend": trend,
                "current_month": current,
                "previous_month": previous,
                "delta": current - previous,
                "interpretation": (
                    f"Pipeline is {trend.lower()} at {abs(lvr):.1f}% MoM. "
                    + ("Positive indicator for future revenue growth." if lvr > 5
                       else "Investigate top-of-funnel activities." if lvr < 0
                       else "Maintain current lead generation activities.")
                ),
            },
            tool_name=self.name,
        )

    # ------------------------------------------------------------------
    def _conversion_probability(self, **kw) -> ToolResult:
        stage_win_rates: list = kw.get("stage_win_rates", [0.4, 0.6, 0.75, 0.85])
        days_in_stage = float(kw.get("days_in_stage", 10))
        pain_score = min(10, max(0, int(kw.get("pain_score", 5))))

        # Product of stage-by-stage win rates
        base_prob = 1.0
        for rate in stage_win_rates:
            base_prob *= max(0.0, min(1.0, float(rate)))

        # Decay factor for aging deals (after 30 days in stage, probability decreases)
        age_decay = max(0.5, 1.0 - max(0, days_in_stage - 30) * 0.005)

        # Pain multiplier
        pain_multiplier = 0.7 + (pain_score / 10) * 0.3

        adjusted_prob = round(base_prob * age_decay * pain_multiplier * 100, 1)
        adjusted_prob = min(99.0, max(1.0, adjusted_prob))

        return ToolResult(
            success=True,
            data={
                "calc_type": "conversion_probability",
                "conversion_probability_pct": adjusted_prob,
                "risk_level": "Low" if adjusted_prob >= 65 else "Medium" if adjusted_prob >= 35 else "High",
                "base_probability_pct": round(base_prob * 100, 1),
                "age_decay_factor": round(age_decay, 3),
                "pain_multiplier": round(pain_multiplier, 3),
                "recommendation": (
                    "Strong close candidate. Prepare proposal and procurement docs."
                    if adjusted_prob >= 65 else
                    "Mid-funnel risk. Re-engage champion. Validate timeline and budget."
                    if adjusted_prob >= 35 else
                    "At-risk deal. Executive sponsor outreach or reassign to nurture."
                ),
            },
            tool_name=self.name,
        )


# ---------------------------------------------------------------------------
# 2. Campaign Analytics Calculator
# ---------------------------------------------------------------------------

class CampaignAnalyticsCalcTool(BaseTool):
    """
    Calculates core campaign performance metrics: CAC, LTV, ROAS, payback period,
    MRR growth, churn rate, and NPS scores.

    Supported calc_types:
      - cac              : Customer Acquisition Cost
      - ltv              : Customer Lifetime Value
      - roas             : Return on Ad Spend
      - payback_period   : CAC payback period in months
      - mrr_growth       : Monthly Recurring Revenue growth
      - churn_rate       : Customer / revenue churn rate
      - nps_score        : Net Promoter Score calculation
    """

    name = "campaign_analytics_calc"
    description = (
        "Calculates campaign and business performance metrics including CAC, LTV, ROAS, "
        "payback period, MRR growth, churn rate, and NPS. Returns benchmarks and "
        "actionable optimisation recommendations."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "calc_type": {
                "type": "string",
                "enum": ["cac", "ltv", "roas", "payback_period", "mrr_growth", "churn_rate", "nps_score"],
            },
            "ad_spend": {"type": "number", "description": "Total advertising / marketing spend ($)."},
            "new_customers": {"type": "integer", "description": "Number of new customers acquired."},
            "revenue_attributed": {"type": "number", "description": "Revenue attributed to campaign ($)."},
            "average_order_value": {"type": "number", "description": "Average transaction value ($)."},
            "gross_margin_pct": {"type": "number", "description": "Gross margin percentage (0-100)."},
            "monthly_churn_rate_pct": {"type": "number", "description": "Monthly churn rate percentage."},
            "average_purchase_frequency": {"type": "number", "description": "Average purchases per customer per year."},
            "current_mrr": {"type": "number", "description": "Current month MRR ($)."},
            "previous_mrr": {"type": "number", "description": "Previous month MRR ($)."},
            "churned_customers": {"type": "integer", "description": "Customers lost this period."},
            "starting_customers": {"type": "integer", "description": "Customers at start of period."},
            "promoters": {"type": "integer", "description": "NPS promoters (scored 9-10)."},
            "detractors": {"type": "integer", "description": "NPS detractors (scored 0-6)."},
            "total_respondents": {"type": "integer", "description": "Total NPS survey respondents."},
            "sales_overhead_pct": {
                "type": "number",
                "description": "Sales overhead percentage to add to marketing spend for fully-loaded CAC.",
            },
        },
        "required": ["calc_type"],
    }

    def run(self, **kwargs: Any) -> ToolResult:
        calc_type = kwargs.get("calc_type", "")
        try:
            dispatch = {
                "cac": self._cac,
                "ltv": self._ltv,
                "roas": self._roas,
                "payback_period": self._payback_period,
                "mrr_growth": self._mrr_growth,
                "churn_rate": self._churn_rate,
                "nps_score": self._nps_score,
            }
            if calc_type not in dispatch:
                return ToolResult(
                    success=False,
                    error=f"Unknown calc_type '{calc_type}'.",
                    tool_name=self.name,
                )
            return dispatch[calc_type](**kwargs)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc), tool_name=self.name)

    def _cac(self, **kw) -> ToolResult:
        spend = float(kw.get("ad_spend", 0))
        new_customers = max(1, int(kw.get("new_customers", 1)))
        sales_overhead_pct = float(kw.get("sales_overhead_pct", 0))

        marketing_cac = spend / new_customers
        fully_loaded_cac = marketing_cac * (1 + sales_overhead_pct / 100)

        # Benchmark: good CAC is typically LTV/3 or less
        benchmark_note = "Compare to LTV: healthy ratio is LTV:CAC ≥ 3:1."

        return ToolResult(
            success=True,
            data={
                "calc_type": "cac",
                "marketing_cac": round(marketing_cac, 2),
                "fully_loaded_cac": round(fully_loaded_cac, 2),
                "total_spend": spend,
                "new_customers": new_customers,
                "benchmark_note": benchmark_note,
                "optimisation_tip": (
                    "Reduce CAC by improving conversion rate at each funnel stage, "
                    "increasing organic channels, and optimising paid media targeting."
                ),
            },
            tool_name=self.name,
        )

    def _ltv(self, **kw) -> ToolResult:
        aov = float(kw.get("average_order_value", 0))
        freq = float(kw.get("average_purchase_frequency", 1))
        churn = max(0.001, float(kw.get("monthly_churn_rate_pct", 5)) / 100)
        margin = float(kw.get("gross_margin_pct", 70)) / 100

        avg_customer_lifespan_months = 1 / churn
        annual_revenue_per_customer = aov * freq
        monthly_revenue = annual_revenue_per_customer / 12

        ltv = round(monthly_revenue * margin * avg_customer_lifespan_months, 2)
        ltv_simple = round(aov * freq * avg_customer_lifespan_months / 12, 2)

        return ToolResult(
            success=True,
            data={
                "calc_type": "ltv",
                "ltv_margin_adjusted": ltv,
                "ltv_simple": ltv_simple,
                "avg_customer_lifespan_months": round(avg_customer_lifespan_months, 1),
                "annual_revenue_per_customer": round(annual_revenue_per_customer, 2),
                "inputs": {
                    "aov": aov, "freq_per_year": freq,
                    "monthly_churn_pct": kw.get("monthly_churn_rate_pct"),
                    "gross_margin_pct": kw.get("gross_margin_pct"),
                },
                "note": "Reduce churn by 1% to significantly increase LTV. Focus on onboarding and CS.",
            },
            tool_name=self.name,
        )

    def _roas(self, **kw) -> ToolResult:
        spend = max(0.01, float(kw.get("ad_spend", 0)))
        revenue = float(kw.get("revenue_attributed", 0))
        margin = float(kw.get("gross_margin_pct", 70)) / 100

        roas = round(revenue / spend, 2)
        mroas = round((revenue * margin) / spend, 2)

        if roas >= 4:
            rating, note = "Excellent", "Scale this campaign — strong positive ROI."
        elif roas >= 2:
            rating, note = "Good", "Performing above break-even. Test scaling budget 20%."
        elif roas >= 1:
            rating, note = "Break-even", "Covering spend but not profitable after margin. Optimise creative/targeting."
        else:
            rating, note = "Negative ROI", "Pause and audit creative, audience, landing page, and offer."

        return ToolResult(
            success=True,
            data={
                "calc_type": "roas",
                "roas": roas,
                "margin_adjusted_roas": mroas,
                "revenue": revenue,
                "spend": spend,
                "rating": rating,
                "action": note,
                "breakeven_roas": round(1 / margin, 2),
            },
            tool_name=self.name,
        )

    def _payback_period(self, **kw) -> ToolResult:
        spend = float(kw.get("ad_spend", 0))
        new_customers = max(1, int(kw.get("new_customers", 1)))
        aov = float(kw.get("average_order_value", 0))
        freq = float(kw.get("average_purchase_frequency", 12))
        margin = float(kw.get("gross_margin_pct", 70)) / 100

        cac = spend / new_customers
        monthly_gross_profit = (aov * freq / 12) * margin

        if monthly_gross_profit <= 0:
            return ToolResult(
                success=False,
                error="Monthly gross profit must be > 0 to calculate payback period.",
                tool_name=self.name,
            )

        payback_months = round(cac / monthly_gross_profit, 1)

        return ToolResult(
            success=True,
            data={
                "calc_type": "payback_period",
                "payback_period_months": payback_months,
                "cac": round(cac, 2),
                "monthly_gross_profit_per_customer": round(monthly_gross_profit, 2),
                "rating": "Excellent" if payback_months <= 6 else "Good" if payback_months <= 12 else "Needs improvement",
                "benchmark": "SaaS benchmark: <12 months is healthy; <6 months is exceptional.",
            },
            tool_name=self.name,
        )

    def _mrr_growth(self, **kw) -> ToolResult:
        current = float(kw.get("current_mrr", 0))
        previous = max(0.01, float(kw.get("previous_mrr", 0.01)))

        growth_pct = round(((current - previous) / previous) * 100, 2)
        arr = round(current * 12, 2)

        return ToolResult(
            success=True,
            data={
                "calc_type": "mrr_growth",
                "mrr_growth_pct": growth_pct,
                "current_mrr": current,
                "previous_mrr": previous,
                "arr_annualised": arr,
                "trend": "Growing" if growth_pct > 0 else "Declining" if growth_pct < 0 else "Flat",
                "benchmark": "Healthy SaaS growth: 10-15% MoM in early stage; 5-8% in growth stage.",
            },
            tool_name=self.name,
        )

    def _churn_rate(self, **kw) -> ToolResult:
        churned = int(kw.get("churned_customers", 0))
        starting = max(1, int(kw.get("starting_customers", 1)))

        churn_pct = round((churned / starting) * 100, 2)
        retention_pct = round(100 - churn_pct, 2)
        avg_lifespan_months = round(100 / max(churn_pct, 0.1), 1)

        return ToolResult(
            success=True,
            data={
                "calc_type": "churn_rate",
                "monthly_churn_pct": churn_pct,
                "monthly_retention_pct": retention_pct,
                "implied_avg_lifespan_months": avg_lifespan_months,
                "churned_customers": churned,
                "starting_customers": starting,
                "benchmark": "World-class SaaS: <2% monthly churn. Good: 2-5%. Needs work: >5%.",
                "actions": [
                    "Analyse exit surveys to identify top churn reasons.",
                    "Implement 30/60/90-day onboarding health checks.",
                    "Create proactive CSM playbooks for at-risk accounts.",
                ] if churn_pct > 3 else ["Maintain retention programmes and monitor NPS trend."],
            },
            tool_name=self.name,
        )

    def _nps_score(self, **kw) -> ToolResult:
        promoters = int(kw.get("promoters", 0))
        detractors = int(kw.get("detractors", 0))
        total = max(1, int(kw.get("total_respondents", 1)))

        nps = round(((promoters - detractors) / total) * 100, 1)
        passives = total - promoters - detractors

        return ToolResult(
            success=True,
            data={
                "calc_type": "nps_score",
                "nps_score": nps,
                "promoters": promoters,
                "passives": passives,
                "detractors": detractors,
                "total_respondents": total,
                "promoter_pct": round(promoters / total * 100, 1),
                "detractor_pct": round(detractors / total * 100, 1),
                "category": (
                    "World-class (>70)" if nps > 70 else
                    "Excellent (50-70)" if nps > 50 else
                    "Good (30-50)" if nps > 30 else
                    "Needs improvement (<30)"
                ),
                "benchmark": "B2B SaaS average NPS: 30-40. Top-quartile: >50.",
            },
            tool_name=self.name,
        )


# ---------------------------------------------------------------------------
# 3. Content Optimizer
# ---------------------------------------------------------------------------

class ContentOptimizerTool(BaseTool):
    """
    Analyses and scores content assets for SEO and conversion readability.

    Supported calc_types:
      - readability_score      : Flesch-Kincaid readability estimate
      - keyword_density        : Primary keyword density check
      - content_gap_analysis   : Estimated content coverage score
      - meta_score             : Meta title + description quality score
      - headline_power_score   : Emotional + power word scoring for headlines
    """

    name = "content_optimizer"
    description = (
        "Analyses content assets for readability, keyword density, SEO meta quality, "
        "headline power score, and content gap coverage. Returns scores 0-100 with "
        "specific improvement recommendations."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "calc_type": {
                "type": "string",
                "enum": [
                    "readability_score",
                    "keyword_density",
                    "content_gap_analysis",
                    "meta_score",
                    "headline_power_score",
                ],
            },
            "word_count": {"type": "integer", "description": "Total word count of the content."},
            "keyword_count": {"type": "integer", "description": "Number of times primary keyword appears."},
            "target_keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of target keywords / topics to cover.",
            },
            "covered_keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Keywords / topics actually covered in the content.",
            },
            "content_type": {
                "type": "string",
                "enum": ["blog_post", "landing_page", "email", "social_post", "video_script", "whitepaper"],
            },
            "avg_sentence_length": {"type": "number", "description": "Average words per sentence."},
            "avg_syllables_per_word": {"type": "number", "description": "Average syllables per word (default 1.5)."},
            "meta_title_length": {"type": "integer", "description": "Character count of meta title."},
            "meta_description_length": {"type": "integer", "description": "Character count of meta description."},
            "meta_title_has_keyword": {"type": "boolean", "description": "Whether primary keyword appears in title."},
            "headline_text": {"type": "string", "description": "The headline text to score."},
            "power_word_count": {"type": "integer", "description": "Number of power / emotional words in headline."},
        },
        "required": ["calc_type"],
    }

    def run(self, **kwargs: Any) -> ToolResult:
        calc_type = kwargs.get("calc_type", "")
        try:
            dispatch = {
                "readability_score": self._readability,
                "keyword_density": self._keyword_density,
                "content_gap_analysis": self._content_gap,
                "meta_score": self._meta_score,
                "headline_power_score": self._headline_power,
            }
            if calc_type not in dispatch:
                return ToolResult(success=False, error=f"Unknown calc_type '{calc_type}'.", tool_name=self.name)
            return dispatch[calc_type](**kwargs)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc), tool_name=self.name)

    def _readability(self, **kw) -> ToolResult:
        word_count = max(1, int(kw.get("word_count", 500)))
        avg_sentence = float(kw.get("avg_sentence_length", 18))
        avg_syllables = float(kw.get("avg_syllables_per_word", 1.5))

        # Flesch Reading Ease approximation
        fre = round(206.835 - (1.015 * avg_sentence) - (84.6 * avg_syllables), 1)
        fre = max(0.0, min(100.0, fre))

        if fre >= 70:
            grade_level = "Easy (6th-8th grade) — Good for broad audience."
        elif fre >= 50:
            grade_level = "Standard (9th-12th grade) — Good for B2B tech content."
        elif fre >= 30:
            grade_level = "Difficult (College level) — Consider simplifying."
        else:
            grade_level = "Very Difficult — Rewrite for clarity."

        # Optimal word counts by content type
        content_type = kw.get("content_type", "blog_post")
        optimal = {
            "blog_post": "1500-2500", "landing_page": "500-1500",
            "email": "150-300", "social_post": "50-150",
            "video_script": "750-1500", "whitepaper": "3000-6000",
        }.get(content_type, "varies")

        return ToolResult(
            success=True,
            data={
                "calc_type": "readability_score",
                "flesch_reading_ease": fre,
                "grade_level": grade_level,
                "word_count": word_count,
                "optimal_word_count_for_type": optimal,
                "recommendations": [
                    f"Shorten sentences to <20 words average." if avg_sentence > 22 else "Sentence length is good.",
                    f"Simplify vocabulary — aim for <1.4 avg syllables/word." if avg_syllables > 1.6 else "Vocabulary complexity is appropriate.",
                ],
            },
            tool_name=self.name,
        )

    def _keyword_density(self, **kw) -> ToolResult:
        words = max(1, int(kw.get("word_count", 500)))
        occurrences = int(kw.get("keyword_count", 0))
        density = round((occurrences / words) * 100, 2)

        if density < 0.5:
            status, tip = "Under-optimised", "Add keyword naturally 2-3 more times."
        elif density <= 2.0:
            status, tip = "Optimal (0.5-2%)", "Good keyword density — maintain balance."
        elif density <= 3.0:
            status, tip = "Slightly over-optimised", "Consider replacing 1-2 instances with synonyms."
        else:
            status, tip = "Keyword stuffing risk", "Reduce occurrences — risk of Google penalty."

        return ToolResult(
            success=True,
            data={
                "calc_type": "keyword_density",
                "keyword_density_pct": density,
                "occurrences": occurrences,
                "word_count": words,
                "status": status,
                "recommendation": tip,
                "optimal_range": "0.5-2.0%",
            },
            tool_name=self.name,
        )

    def _content_gap(self, **kw) -> ToolResult:
        target = kw.get("target_keywords", [])
        covered = kw.get("covered_keywords", [])

        target_set = set(str(k).lower() for k in target)
        covered_set = set(str(k).lower() for k in covered)
        gaps = sorted(target_set - covered_set)
        coverage_pct = round(len(covered_set & target_set) / max(1, len(target_set)) * 100, 1)

        return ToolResult(
            success=True,
            data={
                "calc_type": "content_gap_analysis",
                "coverage_pct": coverage_pct,
                "total_target_topics": len(target_set),
                "covered_topics": len(covered_set & target_set),
                "gap_topics": gaps,
                "score_rating": "Comprehensive" if coverage_pct >= 80 else "Adequate" if coverage_pct >= 60 else "Significant gaps",
                "action": f"Add sections covering: {', '.join(gaps[:5])}{'...' if len(gaps) > 5 else ''}." if gaps else "All target topics are covered.",
            },
            tool_name=self.name,
        )

    def _meta_score(self, **kw) -> ToolResult:
        title_len = int(kw.get("meta_title_length", 0))
        desc_len = int(kw.get("meta_description_length", 0))
        has_keyword = bool(kw.get("meta_title_has_keyword", False))

        score = 0
        issues = []

        # Title: 50-60 chars is optimal
        if 50 <= title_len <= 60:
            score += 40
        elif 40 <= title_len <= 70:
            score += 25
            issues.append(f"Title length {title_len} chars — optimal is 50-60.")
        else:
            score += 10
            issues.append(f"Title length {title_len} chars is outside optimal range (50-60).")

        # Description: 120-155 chars
        if 120 <= desc_len <= 155:
            score += 35
        elif 100 <= desc_len <= 170:
            score += 20
            issues.append(f"Description {desc_len} chars — optimal is 120-155.")
        else:
            score += 5
            issues.append(f"Description {desc_len} chars is outside optimal range.")

        # Keyword in title
        if has_keyword:
            score += 25
        else:
            issues.append("Primary keyword missing from meta title — add it near the front.")

        return ToolResult(
            success=True,
            data={
                "calc_type": "meta_score",
                "meta_score": score,
                "rating": "Excellent" if score >= 85 else "Good" if score >= 65 else "Needs improvement",
                "issues": issues if issues else ["All meta fields are well-optimised."],
                "title_length": title_len,
                "description_length": desc_len,
                "keyword_in_title": has_keyword,
            },
            tool_name=self.name,
        )

    def _headline_power(self, **kw) -> ToolResult:
        headline = str(kw.get("headline_text", ""))
        words = headline.split()
        word_count = len(words)
        power_words = int(kw.get("power_word_count", 0))

        # Scoring components
        length_score = 30 if 6 <= word_count <= 12 else 20 if word_count <= 16 else 10
        power_score = min(35, power_words * 10)

        # Check for number (specificity)
        has_number = any(c.isdigit() for c in headline)
        number_score = 20 if has_number else 5

        # Check for question or "how-to"
        trigger_score = 15 if headline.strip().endswith("?") or "how" in headline.lower() else 0

        total = min(100, length_score + power_score + number_score + trigger_score)

        return ToolResult(
            success=True,
            data={
                "calc_type": "headline_power_score",
                "headline_power_score": total,
                "headline": headline,
                "word_count": word_count,
                "power_words_detected": power_words,
                "rating": "High impact" if total >= 70 else "Average" if total >= 45 else "Weak",
                "tips": [
                    "Add a specific number (e.g. '7 Ways...' or '$50K in 90 days')." if not has_number else "Good — headline contains a specific number.",
                    "Include power/emotional words: 'proven', 'secret', 'ultimate', 'guaranteed'." if power_words < 2 else "Good power word usage.",
                    "Aim for 6-12 word headlines for maximum click-through." if word_count < 6 or word_count > 12 else "Headline length is optimal.",
                ],
            },
            tool_name=self.name,
        )


# ---------------------------------------------------------------------------
# 4. SEO Analyzer
# ---------------------------------------------------------------------------

class SEOAnalyzerTool(BaseTool):
    """
    Estimates SEO metrics for keyword and domain strategy.

    Supported calc_types:
      - domain_authority_estimate  : DA score estimate based on age + backlinks
      - keyword_difficulty         : Keyword ranking difficulty score (0-100)
      - traffic_potential          : Estimated monthly organic traffic
      - backlink_velocity          : Backlink growth rate assessment
      - rank_probability           : Probability of ranking on page 1
    """

    name = "seo_analyzer"
    description = (
        "Analyses SEO opportunity metrics: domain authority estimate, keyword difficulty, "
        "monthly traffic potential, backlink velocity, and page-1 rank probability. "
        "Returns strategy recommendations for content and link building."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "calc_type": {
                "type": "string",
                "enum": [
                    "domain_authority_estimate",
                    "keyword_difficulty",
                    "traffic_potential",
                    "backlink_velocity",
                    "rank_probability",
                ],
            },
            "keyword": {"type": "string", "description": "Target keyword or phrase."},
            "search_volume": {"type": "integer", "description": "Monthly search volume for the keyword."},
            "competition_score": {"type": "number", "description": "Competition score 0-1 (0=low, 1=high)."},
            "domain_age_years": {"type": "number", "description": "Age of the domain in years."},
            "referring_domains": {"type": "integer", "description": "Number of unique referring domains."},
            "total_backlinks": {"type": "integer", "description": "Total backlink count."},
            "current_da": {"type": "number", "description": "Current or estimated Domain Authority (0-100)."},
            "top_ranking_da_avg": {"type": "number", "description": "Average DA of top-10 ranking pages for this keyword."},
            "new_backlinks_this_month": {"type": "integer", "description": "Backlinks acquired this month."},
            "new_backlinks_last_month": {"type": "integer", "description": "Backlinks acquired last month."},
            "content_quality_score": {"type": "number", "description": "Content quality score 0-100."},
            "ctr_estimate_pct": {"type": "number", "description": "Estimated CTR for target position (%)."},
        },
        "required": ["calc_type"],
    }

    def run(self, **kwargs: Any) -> ToolResult:
        calc_type = kwargs.get("calc_type", "")
        try:
            dispatch = {
                "domain_authority_estimate": self._da_estimate,
                "keyword_difficulty": self._keyword_difficulty,
                "traffic_potential": self._traffic_potential,
                "backlink_velocity": self._backlink_velocity,
                "rank_probability": self._rank_probability,
            }
            if calc_type not in dispatch:
                return ToolResult(success=False, error=f"Unknown calc_type '{calc_type}'.", tool_name=self.name)
            return dispatch[calc_type](**kwargs)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc), tool_name=self.name)

    def _da_estimate(self, **kw) -> ToolResult:
        age_years = float(kw.get("domain_age_years", 1))
        referring_domains = int(kw.get("referring_domains", 0))
        total_backlinks = int(kw.get("total_backlinks", 0))

        # Simplified DA model: log-based scoring
        age_factor = min(20, math.log1p(age_years) * 7)
        rd_factor = min(50, math.log1p(referring_domains) * 8)
        bl_factor = min(30, math.log1p(total_backlinks) * 4)

        da = round(age_factor + rd_factor + bl_factor, 1)
        da = min(99.0, da)

        return ToolResult(
            success=True,
            data={
                "calc_type": "domain_authority_estimate",
                "estimated_da": da,
                "tier": "High authority (DA 60+)" if da >= 60 else "Medium authority (DA 30-60)" if da >= 30 else "Low authority (DA <30)",
                "age_contribution": round(age_factor, 1),
                "referring_domains_contribution": round(rd_factor, 1),
                "backlinks_contribution": round(bl_factor, 1),
                "growth_tip": "Focus on earning 5-10 new high-quality referring domains per month to accelerate DA growth.",
            },
            tool_name=self.name,
        )

    def _keyword_difficulty(self, **kw) -> ToolResult:
        competition = min(1.0, max(0.0, float(kw.get("competition_score", 0.5))))
        search_volume = int(kw.get("search_volume", 0))

        # Difficulty increases with competition; high volume keywords are more competitive
        volume_factor = min(30, math.log1p(search_volume) * 2.5)
        kd = round(competition * 70 + volume_factor, 1)
        kd = min(100.0, kd)

        if kd >= 70:
            label, strategy = "Hard", "Target long-tail variants first. Build authority over 12+ months."
        elif kd >= 40:
            label, strategy = "Medium", "Competitive but achievable in 6-12 months with quality content + links."
        else:
            label, strategy = "Easy", "Quick win — create comprehensive content and expect results in 2-4 months."

        return ToolResult(
            success=True,
            data={
                "calc_type": "keyword_difficulty",
                "keyword": kw.get("keyword", ""),
                "keyword_difficulty_score": kd,
                "difficulty_label": label,
                "strategy": strategy,
                "search_volume": search_volume,
                "competition_score": competition,
            },
            tool_name=self.name,
        )

    def _traffic_potential(self, **kw) -> ToolResult:
        search_volume = int(kw.get("search_volume", 0))
        ctr_pct = float(kw.get("ctr_estimate_pct", 5.0))

        # CTR by position benchmarks
        ctr_by_position = {1: 28.5, 2: 15.7, 3: 11.0, 4: 8.0, 5: 7.2, 6: 5.1, 7: 4.0, 8: 3.2, 9: 2.8, 10: 2.5}

        traffic_by_position = {
            pos: round(search_volume * ctr / 100) for pos, ctr in ctr_by_position.items()
        }
        estimated_traffic = round(search_volume * ctr_pct / 100)

        return ToolResult(
            success=True,
            data={
                "calc_type": "traffic_potential",
                "search_volume": search_volume,
                "estimated_traffic_at_input_ctr": estimated_traffic,
                "ctr_used_pct": ctr_pct,
                "traffic_by_ranking_position": traffic_by_position,
                "recommendation": f"Ranking #1 would yield ~{traffic_by_position[1]:,} monthly visitors. "
                                  f"Even position #5 delivers ~{traffic_by_position[5]:,} visits.",
            },
            tool_name=self.name,
        )

    def _backlink_velocity(self, **kw) -> ToolResult:
        this_month = int(kw.get("new_backlinks_this_month", 0))
        last_month = max(1, int(kw.get("new_backlinks_last_month", 1)))

        velocity_pct = round(((this_month - last_month) / last_month) * 100, 1)

        return ToolResult(
            success=True,
            data={
                "calc_type": "backlink_velocity",
                "velocity_pct_mom": velocity_pct,
                "this_month": this_month,
                "last_month": last_month,
                "trend": "Accelerating" if velocity_pct > 10 else "Growing" if velocity_pct > 0 else "Declining",
                "note": (
                    "Natural, steady backlink growth signals quality to search engines. "
                    "Sudden spikes (>200% MoM) can trigger spam filters."
                ),
            },
            tool_name=self.name,
        )

    def _rank_probability(self, **kw) -> ToolResult:
        current_da = float(kw.get("current_da", 20))
        top_da = float(kw.get("top_ranking_da_avg", 60))
        content_quality = min(100, max(0, float(kw.get("content_quality_score", 50))))

        da_ratio = min(1.0, current_da / max(1, top_da))
        content_factor = content_quality / 100

        prob = round((da_ratio * 0.55 + content_factor * 0.45) * 100, 1)
        prob = min(95.0, max(2.0, prob))

        return ToolResult(
            success=True,
            data={
                "calc_type": "rank_probability",
                "page1_rank_probability_pct": prob,
                "current_da": current_da,
                "competitor_avg_da": top_da,
                "content_quality_score": content_quality,
                "recommendation": (
                    "Strong chance to rank. Publish and promote actively."
                    if prob >= 60 else
                    "Moderate chance. Invest in link building and content depth before targeting."
                    if prob >= 35 else
                    "Low probability currently. Build DA and improve content before targeting this keyword."
                ),
            },
            tool_name=self.name,
        )


# ---------------------------------------------------------------------------
# 5. Email Campaign Manager
# ---------------------------------------------------------------------------

class EmailCampaignManagerTool(BaseTool):
    """
    Analyses and scores email campaign performance and strategy.

    Supported calc_types:
      - deliverability_score    : Inbox placement health score
      - open_rate_benchmark     : Open rate vs industry benchmark
      - click_rate_benchmark    : CTR vs industry benchmark
      - revenue_per_email       : Revenue generated per email sent
      - list_health_score       : List quality and hygiene score
      - sequence_roi            : Full email sequence ROI calculation
    """

    name = "email_campaign_manager"
    description = (
        "Analyses email campaign health and performance: deliverability scoring, open/click "
        "benchmarking, revenue per email, list health scoring, and sequence ROI. "
        "Provides actionable deliverability and engagement improvement recommendations."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "calc_type": {
                "type": "string",
                "enum": [
                    "deliverability_score",
                    "open_rate_benchmark",
                    "click_rate_benchmark",
                    "revenue_per_email",
                    "list_health_score",
                    "sequence_roi",
                ],
            },
            "list_size": {"type": "integer", "description": "Total email list size."},
            "bounce_rate_pct": {"type": "number", "description": "Hard + soft bounce rate percentage."},
            "spam_complaint_rate_pct": {"type": "number", "description": "Spam complaint rate percentage."},
            "open_rate_pct": {"type": "number", "description": "Email open rate percentage."},
            "click_rate_pct": {"type": "number", "description": "Click-through rate percentage."},
            "conversion_rate_pct": {"type": "number", "description": "Email-to-conversion rate percentage."},
            "average_order_value": {"type": "number", "description": "Average order value per conversion ($)."},
            "emails_sent": {"type": "integer", "description": "Total emails sent in campaign."},
            "unsubscribe_rate_pct": {"type": "number", "description": "Unsubscribe rate percentage."},
            "industry": {
                "type": "string",
                "enum": ["SaaS", "E-commerce", "B2B Services", "Media", "Healthcare", "Finance", "Other"],
            },
            "sequence_emails": {"type": "integer", "description": "Number of emails in the sequence."},
            "cost_per_email_send": {"type": "number", "description": "Cost per email sent (ESP cost in $ per email)."},
            "sequence_conversions": {"type": "integer", "description": "Total conversions from the sequence."},
            "has_spf": {"type": "boolean"},
            "has_dkim": {"type": "boolean"},
            "has_dmarc": {"type": "boolean"},
            "list_age_months": {"type": "integer", "description": "Age of the email list in months."},
        },
        "required": ["calc_type"],
    }

    # Industry open rate benchmarks
    _OPEN_BENCHMARKS = {
        "SaaS": 21.5, "E-commerce": 15.7, "B2B Services": 20.1,
        "Media": 22.3, "Healthcare": 23.4, "Finance": 20.5, "Other": 19.0,
    }
    _CLICK_BENCHMARKS = {
        "SaaS": 3.1, "E-commerce": 2.3, "B2B Services": 3.4,
        "Media": 4.2, "Healthcare": 3.8, "Finance": 2.9, "Other": 2.6,
    }

    def run(self, **kwargs: Any) -> ToolResult:
        calc_type = kwargs.get("calc_type", "")
        try:
            dispatch = {
                "deliverability_score": self._deliverability,
                "open_rate_benchmark": self._open_rate_benchmark,
                "click_rate_benchmark": self._click_rate_benchmark,
                "revenue_per_email": self._revenue_per_email,
                "list_health_score": self._list_health,
                "sequence_roi": self._sequence_roi,
            }
            if calc_type not in dispatch:
                return ToolResult(success=False, error=f"Unknown calc_type '{calc_type}'.", tool_name=self.name)
            return dispatch[calc_type](**kwargs)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc), tool_name=self.name)

    def _deliverability(self, **kw) -> ToolResult:
        bounce = float(kw.get("bounce_rate_pct", 0))
        spam = float(kw.get("spam_complaint_rate_pct", 0))
        has_spf = bool(kw.get("has_spf", False))
        has_dkim = bool(kw.get("has_dkim", False))
        has_dmarc = bool(kw.get("has_dmarc", False))

        score = 100.0
        issues = []

        # Authentication (30 pts total)
        auth_score = (10 if has_spf else 0) + (10 if has_dkim else 0) + (10 if has_dmarc else 0)
        score = score - 30 + auth_score
        if not has_spf: issues.append("Set up SPF record to authenticate sending domain.")
        if not has_dkim: issues.append("Enable DKIM signing in your ESP.")
        if not has_dmarc: issues.append("Publish a DMARC policy (start with p=none for monitoring).")

        # Bounce rate (35 pts)
        if bounce <= 0.5:
            bounce_score = 35
        elif bounce <= 2.0:
            bounce_score = 25
            issues.append(f"Bounce rate {bounce}% is elevated. Clean list with email verification.")
        elif bounce <= 5.0:
            bounce_score = 12
            issues.append(f"High bounce rate {bounce}% — urgent list cleaning required.")
        else:
            bounce_score = 0
            issues.append(f"Critical bounce rate {bounce}% — ESPs will block sending. Pause and clean.")
        score = score - 35 + bounce_score

        # Spam complaint rate (35 pts)
        if spam <= 0.08:
            spam_score = 35
        elif spam <= 0.2:
            spam_score = 20
            issues.append(f"Spam complaints {spam}% approaching danger zone. Review content and list quality.")
        else:
            spam_score = 5
            issues.append(f"Spam complaint rate {spam}% is critical — ISPs will blacklist your domain.")
        score = score - 35 + spam_score

        score = max(0, min(100, round(score, 1)))

        return ToolResult(
            success=True,
            data={
                "calc_type": "deliverability_score",
                "deliverability_score": score,
                "rating": "Excellent" if score >= 85 else "Good" if score >= 65 else "At risk" if score >= 40 else "Critical",
                "authentication": {"SPF": has_spf, "DKIM": has_dkim, "DMARC": has_dmarc},
                "bounce_rate_pct": bounce,
                "spam_complaint_rate_pct": spam,
                "issues": issues if issues else ["Deliverability health is excellent."],
            },
            tool_name=self.name,
        )

    def _open_rate_benchmark(self, **kw) -> ToolResult:
        actual = float(kw.get("open_rate_pct", 0))
        industry = kw.get("industry", "Other")
        benchmark = self._OPEN_BENCHMARKS.get(industry, 19.0)
        delta = round(actual - benchmark, 1)

        return ToolResult(
            success=True,
            data={
                "calc_type": "open_rate_benchmark",
                "actual_open_rate_pct": actual,
                "industry_benchmark_pct": benchmark,
                "industry": industry,
                "delta_vs_benchmark": delta,
                "performance": "Above benchmark" if delta >= 0 else "Below benchmark",
                "tips": [
                    "A/B test subject lines with curiosity, urgency, or personalisation." if actual < benchmark else "Maintain subject line strategy.",
                    "Segment list by engagement level — send re-engagement campaign to cold subscribers.",
                    "Test send times: Tue-Thu, 10 AM or 2 PM recipient local time typically outperform.",
                ],
            },
            tool_name=self.name,
        )

    def _click_rate_benchmark(self, **kw) -> ToolResult:
        actual = float(kw.get("click_rate_pct", 0))
        industry = kw.get("industry", "Other")
        benchmark = self._CLICK_BENCHMARKS.get(industry, 2.6)
        delta = round(actual - benchmark, 1)

        return ToolResult(
            success=True,
            data={
                "calc_type": "click_rate_benchmark",
                "actual_click_rate_pct": actual,
                "industry_benchmark_pct": benchmark,
                "industry": industry,
                "delta_vs_benchmark": delta,
                "performance": "Above benchmark" if delta >= 0 else "Below benchmark",
                "tips": [
                    "Use a single, prominent CTA button rather than multiple text links.",
                    "Add urgency: 'Offer expires in 48 hours' or 'Only 3 spots remaining'.",
                    "Personalise email content using segmentation data.",
                ] if actual < benchmark else ["CTR is performing well. Test adding a secondary CTA."],
            },
            tool_name=self.name,
        )

    def _revenue_per_email(self, **kw) -> ToolResult:
        emails_sent = max(1, int(kw.get("emails_sent", 1)))
        conversion_rate = float(kw.get("conversion_rate_pct", 1)) / 100
        aov = float(kw.get("average_order_value", 0))

        conversions = round(emails_sent * conversion_rate)
        total_revenue = round(conversions * aov, 2)
        rpe = round(total_revenue / emails_sent, 4)

        return ToolResult(
            success=True,
            data={
                "calc_type": "revenue_per_email",
                "revenue_per_email": rpe,
                "total_revenue": total_revenue,
                "estimated_conversions": conversions,
                "emails_sent": emails_sent,
                "conversion_rate_pct": kw.get("conversion_rate_pct"),
                "aov": aov,
                "benchmark": "Strong email programmes generate $0.05-$0.20 RPE. World-class: >$1.00 RPE.",
            },
            tool_name=self.name,
        )

    def _list_health(self, **kw) -> ToolResult:
        list_size = max(1, int(kw.get("list_size", 1)))
        bounce = float(kw.get("bounce_rate_pct", 0))
        spam = float(kw.get("spam_complaint_rate_pct", 0))
        unsubscribe = float(kw.get("unsubscribe_rate_pct", 0))
        open_rate = float(kw.get("open_rate_pct", 0))
        age_months = int(kw.get("list_age_months", 12))

        score = 100.0
        recommendations = []

        if bounce > 2: score -= 25; recommendations.append("Run list through email verification service (ZeroBounce, NeverBounce).")
        elif bounce > 0.5: score -= 10

        if spam > 0.1: score -= 25; recommendations.append("High spam complaints — suppress unengaged contacts, improve targeting.")
        elif spam > 0.05: score -= 10

        if unsubscribe > 0.5: score -= 20; recommendations.append("High unsubscribes — check send frequency and content relevance.")
        elif unsubscribe > 0.2: score -= 8

        if open_rate < 10: score -= 20; recommendations.append("Very low engagement — segment and re-permission cold contacts.")
        elif open_rate < 15: score -= 8

        if age_months > 24: score -= 10; recommendations.append("Old list — run re-engagement campaign and remove non-responders.")

        score = max(0, round(score, 1))

        return ToolResult(
            success=True,
            data={
                "calc_type": "list_health_score",
                "list_health_score": score,
                "list_size": list_size,
                "health_rating": "Healthy" if score >= 75 else "Fair" if score >= 50 else "At risk",
                "recommendations": recommendations if recommendations else ["List health is excellent. Maintain regular cleaning cadence."],
            },
            tool_name=self.name,
        )

    def _sequence_roi(self, **kw) -> ToolResult:
        list_size = max(1, int(kw.get("list_size", 1)))
        sequence_emails = max(1, int(kw.get("sequence_emails", 5)))
        cost_per_send = float(kw.get("cost_per_email_send", 0.001))
        conversions = int(kw.get("sequence_conversions", 0))
        aov = float(kw.get("average_order_value", 0))

        total_sends = list_size * sequence_emails
        total_cost = round(total_sends * cost_per_send, 2)
        total_revenue = round(conversions * aov, 2)
        roi = round(((total_revenue - total_cost) / max(0.01, total_cost)) * 100, 1)
        rpe = round(total_revenue / max(1, total_sends), 4)

        return ToolResult(
            success=True,
            data={
                "calc_type": "sequence_roi",
                "sequence_roi_pct": roi,
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "net_profit": round(total_revenue - total_cost, 2),
                "revenue_per_email": rpe,
                "total_sends": total_sends,
                "conversions": conversions,
                "rating": "Excellent" if roi >= 500 else "Good" if roi >= 200 else "Acceptable" if roi >= 50 else "Needs improvement",
            },
            tool_name=self.name,
        )


# ---------------------------------------------------------------------------
# 6. Market Segmentation Tool
# ---------------------------------------------------------------------------

class MarketSegmentationTool(BaseTool):
    """
    Estimates market sizing and segmentation opportunities.

    Supported calc_types:
      - tam_estimate            : Total Addressable Market
      - sam_estimate            : Serviceable Addressable Market
      - som_estimate            : Serviceable Obtainable Market
      - market_penetration_rate : Current market penetration percentage
      - ideal_segment_score     : ICP segment attractiveness score
    """

    name = "market_segmentation"
    description = (
        "Estimates TAM, SAM, and SOM for market sizing. Calculates market penetration rate "
        "and scores segment attractiveness for ICP prioritisation. Supports top-down and "
        "bottom-up sizing approaches."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "calc_type": {
                "type": "string",
                "enum": [
                    "tam_estimate",
                    "sam_estimate",
                    "som_estimate",
                    "market_penetration_rate",
                    "ideal_segment_score",
                ],
            },
            "industry": {"type": "string"},
            "geography": {"type": "string", "description": "Market geography (e.g. 'US', 'Global', 'EMEA')."},
            "company_size_range": {
                "type": "string",
                "enum": ["1-10", "11-50", "51-200", "201-1000", "1001-5000", "5001+"],
            },
            "total_companies_in_market": {"type": "integer", "description": "Total number of target companies."},
            "average_deal_value": {"type": "number", "description": "Average annual contract value ($)."},
            "serviceable_fraction_pct": {
                "type": "number",
                "description": "Percentage of TAM that is serviceable given go-to-market model.",
            },
            "obtainable_fraction_pct": {
                "type": "number",
                "description": "Realistic market share percentage achievable in 3-5 years.",
            },
            "current_customers": {"type": "integer"},
            "segment_growth_rate_pct": {"type": "number", "description": "Annual segment growth rate %."},
            "avg_deal_cycle_days": {"type": "number"},
            "competition_intensity": {
                "type": "string",
                "enum": ["Low", "Medium", "High", "Extremely High"],
            },
            "differentiation_score": {"type": "number", "description": "0-10 — how differentiated is the offering."},
        },
        "required": ["calc_type"],
    }

    def run(self, **kwargs: Any) -> ToolResult:
        calc_type = kwargs.get("calc_type", "")
        try:
            dispatch = {
                "tam_estimate": self._tam,
                "sam_estimate": self._sam,
                "som_estimate": self._som,
                "market_penetration_rate": self._penetration,
                "ideal_segment_score": self._segment_score,
            }
            if calc_type not in dispatch:
                return ToolResult(success=False, error=f"Unknown calc_type '{calc_type}'.", tool_name=self.name)
            return dispatch[calc_type](**kwargs)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc), tool_name=self.name)

    def _tam(self, **kw) -> ToolResult:
        companies = int(kw.get("total_companies_in_market", 0))
        adv = float(kw.get("average_deal_value", 0))
        tam = round(companies * adv, 2)

        return ToolResult(
            success=True,
            data={
                "calc_type": "tam_estimate",
                "tam_dollars": tam,
                "tam_formatted": f"${tam / 1_000_000:.1f}M" if tam >= 1_000_000 else f"${tam / 1_000:.0f}K",
                "total_companies": companies,
                "average_deal_value": adv,
                "note": "TAM = total revenue opportunity if you captured 100% of the market.",
            },
            tool_name=self.name,
        )

    def _sam(self, **kw) -> ToolResult:
        companies = int(kw.get("total_companies_in_market", 0))
        adv = float(kw.get("average_deal_value", 0))
        serviceable_pct = float(kw.get("serviceable_fraction_pct", 30))
        tam = companies * adv
        sam = round(tam * serviceable_pct / 100, 2)

        return ToolResult(
            success=True,
            data={
                "calc_type": "sam_estimate",
                "sam_dollars": sam,
                "sam_formatted": f"${sam / 1_000_000:.1f}M" if sam >= 1_000_000 else f"${sam / 1_000:.0f}K",
                "tam_dollars": round(tam, 2),
                "serviceable_pct": serviceable_pct,
                "note": "SAM = the portion of TAM your current GTM model can reach.",
            },
            tool_name=self.name,
        )

    def _som(self, **kw) -> ToolResult:
        companies = int(kw.get("total_companies_in_market", 0))
        adv = float(kw.get("average_deal_value", 0))
        serviceable_pct = float(kw.get("serviceable_fraction_pct", 30))
        obtainable_pct = float(kw.get("obtainable_fraction_pct", 5))
        sam = companies * adv * serviceable_pct / 100
        som = round(sam * obtainable_pct / 100, 2)

        return ToolResult(
            success=True,
            data={
                "calc_type": "som_estimate",
                "som_dollars": som,
                "som_formatted": f"${som / 1_000_000:.1f}M" if som >= 1_000_000 else f"${som / 1_000:.0f}K",
                "sam_dollars": round(sam, 2),
                "obtainable_pct": obtainable_pct,
                "target_customers": round(companies * serviceable_pct / 100 * obtainable_pct / 100),
                "note": "SOM = realistic revenue target achievable with current resources in 3-5 years.",
            },
            tool_name=self.name,
        )

    def _penetration(self, **kw) -> ToolResult:
        current = int(kw.get("current_customers", 0))
        total = max(1, int(kw.get("total_companies_in_market", 1)))
        penetration = round((current / total) * 100, 3)

        return ToolResult(
            success=True,
            data={
                "calc_type": "market_penetration_rate",
                "penetration_rate_pct": penetration,
                "current_customers": current,
                "total_addressable_companies": total,
                "interpretation": (
                    "Market leader position." if penetration > 30
                    else "Strong penetration — focus on expansion revenue." if penetration > 10
                    else "Growth stage — significant greenfield opportunity remains." if penetration > 2
                    else "Early stage — prioritise acquisition and product-market fit signals."
                ),
            },
            tool_name=self.name,
        )

    def _segment_score(self, **kw) -> ToolResult:
        growth = float(kw.get("segment_growth_rate_pct", 5))
        deal_cycle = float(kw.get("avg_deal_cycle_days", 90))
        competition = kw.get("competition_intensity", "Medium")
        differentiation = min(10, max(0, float(kw.get("differentiation_score", 5))))

        comp_penalty = {"Low": 0, "Medium": 10, "High": 20, "Extremely High": 35}.get(competition, 10)
        growth_score = min(30, growth * 1.5)
        cycle_score = max(0, 25 - deal_cycle / 10)
        diff_score = differentiation * 2.0  # max 20
        base_score = 25.0  # baseline attractiveness

        total = round(base_score + growth_score + cycle_score + diff_score - comp_penalty, 1)
        total = max(0, min(100, total))

        return ToolResult(
            success=True,
            data={
                "calc_type": "ideal_segment_score",
                "segment_attractiveness_score": total,
                "rating": "Priority segment" if total >= 70 else "Secondary segment" if total >= 45 else "Low priority",
                "breakdown": {
                    "growth_score": round(growth_score, 1),
                    "deal_cycle_score": round(cycle_score, 1),
                    "differentiation_score": round(diff_score, 1),
                    "competition_penalty": -comp_penalty,
                    "baseline": base_score,
                },
                "recommendation": (
                    "Prioritise this segment in next quarter's GTM plan."
                    if total >= 70 else
                    "Include in product roadmap and secondary marketing campaigns."
                    if total >= 45 else
                    "Deprioritise — low growth, high competition, or long cycles."
                ),
            },
            tool_name=self.name,
        )


# ---------------------------------------------------------------------------
# 7. ROI Calculator
# ---------------------------------------------------------------------------

class ROICalculatorTool(BaseTool):
    """
    Calculates ROI across multiple marketing channels and investment types.

    Supported calc_types:
      - marketing_roi        : Overall marketing programme ROI
      - content_roi          : Content marketing ROI
      - seo_roi              : Organic search ROI
      - paid_media_roi       : Paid advertising ROI
      - influencer_roi       : Influencer / partnership ROI
      - event_roi            : Event / trade show ROI
      - overall_marketing_mix_roi : Blended multi-channel ROI
    """

    name = "roi_calculator"
    description = (
        "Calculates ROI for individual marketing channels (content, SEO, paid media, "
        "influencer, events) and blended marketing mix ROI. Returns payback analysis "
        "and channel efficiency rankings."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "calc_type": {
                "type": "string",
                "enum": [
                    "marketing_roi",
                    "content_roi",
                    "seo_roi",
                    "paid_media_roi",
                    "influencer_roi",
                    "event_roi",
                    "overall_marketing_mix_roi",
                ],
            },
            "investment": {"type": "number", "description": "Total investment/spend in this channel ($)."},
            "revenue_attributed": {"type": "number", "description": "Revenue attributed to this channel ($)."},
            "time_period_months": {"type": "integer", "description": "Evaluation period in months."},
            "attribution_model": {
                "type": "string",
                "enum": ["last_touch", "first_touch", "linear", "time_decay", "data_driven"],
            },
            "gross_margin_pct": {"type": "number"},
            "organic_traffic_increase": {"type": "integer", "description": "Monthly organic session increase from SEO."},
            "conversion_rate_pct": {"type": "number"},
            "average_order_value": {"type": "number"},
            "content_pieces_produced": {"type": "integer"},
            "cost_per_content_piece": {"type": "number"},
            "influencer_reach": {"type": "integer", "description": "Total audience reach of influencer campaign."},
            "event_attendees": {"type": "integer"},
            "leads_from_event": {"type": "integer"},
            "cost_per_attendee": {"type": "number"},
            "channel_investments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string"},
                        "investment": {"type": "number"},
                        "revenue": {"type": "number"},
                    },
                },
                "description": "Array of channel investments for blended ROI calculation.",
            },
        },
        "required": ["calc_type"],
    }

    def run(self, **kwargs: Any) -> ToolResult:
        calc_type = kwargs.get("calc_type", "")
        try:
            dispatch = {
                "marketing_roi": self._marketing_roi,
                "content_roi": self._content_roi,
                "seo_roi": self._seo_roi,
                "paid_media_roi": self._paid_media_roi,
                "influencer_roi": self._influencer_roi,
                "event_roi": self._event_roi,
                "overall_marketing_mix_roi": self._mix_roi,
            }
            if calc_type not in dispatch:
                return ToolResult(success=False, error=f"Unknown calc_type '{calc_type}'.", tool_name=self.name)
            return dispatch[calc_type](**kwargs)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc), tool_name=self.name)

    def _calc_roi(self, investment: float, revenue: float, margin_pct: float = 100) -> tuple:
        margin = margin_pct / 100
        gross_profit = revenue * margin
        net_profit = gross_profit - investment
        roi_pct = round((net_profit / max(0.01, investment)) * 100, 1)
        return round(gross_profit, 2), round(net_profit, 2), roi_pct

    def _marketing_roi(self, **kw) -> ToolResult:
        inv = float(kw.get("investment", 0))
        rev = float(kw.get("revenue_attributed", 0))
        margin = float(kw.get("gross_margin_pct", 100))
        months = int(kw.get("time_period_months", 12))
        attribution = kw.get("attribution_model", "last_touch")

        gross_profit, net_profit, roi = self._calc_roi(inv, rev, margin)
        monthly_roi = round(roi / months, 1)

        return ToolResult(
            success=True,
            data={
                "calc_type": "marketing_roi",
                "roi_pct": roi,
                "monthly_roi_pct": monthly_roi,
                "net_profit": net_profit,
                "gross_profit": gross_profit,
                "investment": inv,
                "revenue_attributed": rev,
                "time_period_months": months,
                "attribution_model": attribution,
                "rating": "Excellent" if roi >= 300 else "Good" if roi >= 100 else "Marginal" if roi >= 0 else "Negative",
            },
            tool_name=self.name,
        )

    def _content_roi(self, **kw) -> ToolResult:
        inv = float(kw.get("investment", 0))
        rev = float(kw.get("revenue_attributed", 0))
        pieces = max(1, int(kw.get("content_pieces_produced", 1)))
        margin = float(kw.get("gross_margin_pct", 100))
        months = int(kw.get("time_period_months", 12))

        _, net_profit, roi = self._calc_roi(inv, rev, margin)
        roi_per_piece = round(net_profit / pieces, 2)

        return ToolResult(
            success=True,
            data={
                "calc_type": "content_roi",
                "roi_pct": roi,
                "net_profit": net_profit,
                "cost_per_piece": round(inv / pieces, 2),
                "roi_per_content_piece": roi_per_piece,
                "content_pieces": pieces,
                "time_period_months": months,
                "note": (
                    "Content ROI compounds over time — a blog post published today "
                    "can generate traffic for 2-5 years. Consider 24-month ROI window."
                ),
            },
            tool_name=self.name,
        )

    def _seo_roi(self, **kw) -> ToolResult:
        inv = float(kw.get("investment", 0))
        traffic_increase = int(kw.get("organic_traffic_increase", 0))
        conv_rate = float(kw.get("conversion_rate_pct", 2)) / 100
        aov = float(kw.get("average_order_value", 0))
        margin = float(kw.get("gross_margin_pct", 70))
        months = int(kw.get("time_period_months", 12))

        monthly_revenue = traffic_increase * conv_rate * aov
        total_revenue = monthly_revenue * months
        _, net_profit, roi = self._calc_roi(inv, total_revenue, margin)

        return ToolResult(
            success=True,
            data={
                "calc_type": "seo_roi",
                "roi_pct": roi,
                "net_profit": net_profit,
                "monthly_organic_revenue": round(monthly_revenue, 2),
                "total_attributed_revenue": round(total_revenue, 2),
                "investment": inv,
                "monthly_traffic_increase": traffic_increase,
                "time_period_months": months,
                "note": "SEO ROI is underestimated — organic traffic has no per-click cost. Consider 3-year NPV.",
            },
            tool_name=self.name,
        )

    def _paid_media_roi(self, **kw) -> ToolResult:
        inv = float(kw.get("investment", 0))
        rev = float(kw.get("revenue_attributed", 0))
        margin = float(kw.get("gross_margin_pct", 70))

        roas = round(rev / max(0.01, inv), 2)
        _, net_profit, roi = self._calc_roi(inv, rev, margin)
        breakeven_roas = round(100 / margin, 2)

        return ToolResult(
            success=True,
            data={
                "calc_type": "paid_media_roi",
                "roi_pct": roi,
                "roas": roas,
                "breakeven_roas": breakeven_roas,
                "net_profit": net_profit,
                "investment": inv,
                "revenue": rev,
                "recommendation": (
                    f"ROAS {roas}x {'exceeds' if roas > breakeven_roas else 'is below'} "
                    f"breakeven of {breakeven_roas}x. "
                    + ("Scale budget 20% and monitor CPA." if roas > breakeven_roas * 1.5
                       else "Optimise creative, audience, and landing page before scaling.")
                ),
            },
            tool_name=self.name,
        )

    def _influencer_roi(self, **kw) -> ToolResult:
        inv = float(kw.get("investment", 0))
        rev = float(kw.get("revenue_attributed", 0))
        reach = max(1, int(kw.get("influencer_reach", 1)))
        margin = float(kw.get("gross_margin_pct", 70))

        cpm = round((inv / reach) * 1000, 2)
        _, net_profit, roi = self._calc_roi(inv, rev, margin)

        return ToolResult(
            success=True,
            data={
                "calc_type": "influencer_roi",
                "roi_pct": roi,
                "net_profit": net_profit,
                "cpm_cost": cpm,
                "influencer_reach": reach,
                "investment": inv,
                "revenue_attributed": rev,
                "benchmark": "Good influencer CPM: $5-$20 for B2C. B2B micro-influencers: $20-$50 CPM but higher conversion intent.",
            },
            tool_name=self.name,
        )

    def _event_roi(self, **kw) -> ToolResult:
        inv = float(kw.get("investment", 0))
        attendees = max(1, int(kw.get("event_attendees", 1)))
        leads = int(kw.get("leads_from_event", 0))
        rev = float(kw.get("revenue_attributed", 0))
        margin = float(kw.get("gross_margin_pct", 70))

        cost_per_attendee = round(inv / attendees, 2)
        cost_per_lead = round(inv / max(1, leads), 2)
        _, net_profit, roi = self._calc_roi(inv, rev, margin)

        return ToolResult(
            success=True,
            data={
                "calc_type": "event_roi",
                "roi_pct": roi,
                "net_profit": net_profit,
                "cost_per_attendee": cost_per_attendee,
                "cost_per_lead": cost_per_lead,
                "leads_generated": leads,
                "attendees": attendees,
                "investment": inv,
                "revenue_attributed": rev,
                "benchmark": "B2B event benchmark: $150-$500 cost per lead. <$200 is excellent for trade shows.",
            },
            tool_name=self.name,
        )

    def _mix_roi(self, **kw) -> ToolResult:
        channels: list = kw.get("channel_investments", [])
        margin = float(kw.get("gross_margin_pct", 70))

        if not channels:
            return ToolResult(
                success=False,
                error="Provide 'channel_investments' array with channel, investment, and revenue for each channel.",
                tool_name=self.name,
            )

        total_inv = sum(float(c.get("investment", 0)) for c in channels)
        total_rev = sum(float(c.get("revenue", 0)) for c in channels)
        _, net_profit, blended_roi = self._calc_roi(total_inv, total_rev, margin)

        channel_details = sorted(
            [
                {
                    "channel": c.get("channel", "Unknown"),
                    "investment": float(c.get("investment", 0)),
                    "revenue": float(c.get("revenue", 0)),
                    "roi_pct": round(
                        ((float(c.get("revenue", 0)) * margin / 100 - float(c.get("investment", 0))) /
                         max(0.01, float(c.get("investment", 0)))) * 100, 1
                    ),
                }
                for c in channels
            ],
            key=lambda x: x["roi_pct"],
            reverse=True,
        )

        return ToolResult(
            success=True,
            data={
                "calc_type": "overall_marketing_mix_roi",
                "blended_roi_pct": blended_roi,
                "total_investment": round(total_inv, 2),
                "total_revenue": round(total_rev, 2),
                "net_profit": net_profit,
                "channel_breakdown": channel_details,
                "top_performing_channel": channel_details[0]["channel"] if channel_details else "N/A",
                "worst_performing_channel": channel_details[-1]["channel"] if channel_details else "N/A",
                "optimisation_tip": (
                    f"Reallocate budget from '{channel_details[-1]['channel']}' "
                    f"(ROI: {channel_details[-1]['roi_pct']}%) to "
                    f"'{channel_details[0]['channel']}' "
                    f"(ROI: {channel_details[0]['roi_pct']}%) for higher blended returns."
                ) if len(channel_details) >= 2 else "Add more channels for mix optimisation.",
            },
            tool_name=self.name,
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_TOOLS: dict[str, BaseTool] = {}


def _register(tool: BaseTool) -> None:
    _TOOLS[tool.name] = tool


def get_tool(name: str) -> BaseTool | None:
    return _TOOLS.get(name)


def list_tools() -> list[str]:
    return sorted(_TOOLS.keys())


def all_tools() -> list[BaseTool]:
    return list(_TOOLS.values())


# Auto-register all tools at import time
_register(LeadScoringCalcTool())
_register(CampaignAnalyticsCalcTool())
_register(ContentOptimizerTool())
_register(SEOAnalyzerTool())
_register(EmailCampaignManagerTool())
_register(MarketSegmentationTool())
_register(ROICalculatorTool())
