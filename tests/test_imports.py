"""Smoke tests for Sales & Marketing Nanobot Swarm."""
import pytest


def test_nanobot_import():
    import nanobot
    assert nanobot.__version__ == "1.0.0"


def test_agent_teams_import():
    from nanobot.scheduler.agent_teams import list_teams, TEAM_REGISTRY
    # Built-in teams should be registered
    assert len(TEAM_REGISTRY) >= 5


def test_salesmarketing_teams_import():
    from nanobot.teams import salesmarketing_teams  # noqa: F401
    from nanobot.scheduler.agent_teams import TEAM_REGISTRY
    # Domain teams should be registered
    domain_teams = [
        "lead-generation-engine",
        "content-marketing-team",
        "email-campaign-manager",
        "social-media-strategist",
        "campaign-analytics-hub",
        "competitive-intelligence",
    ]
    for t in domain_teams:
        assert t in TEAM_REGISTRY, f"Team '{t}' not found in registry"


def test_salesmarketing_tools_import():
    from nanobot.tools.salesmarketing_tools import (
        LeadScoringCalcTool,
        CampaignAnalyticsCalcTool,
        ContentOptimizerTool,
        SEOAnalyzerTool,
        EmailCampaignManagerTool,
        MarketSegmentationTool,
        ROICalculatorTool,
    )
    tools = [
        LeadScoringCalcTool(),
        CampaignAnalyticsCalcTool(),
        ContentOptimizerTool(),
        SEOAnalyzerTool(),
        EmailCampaignManagerTool(),
        MarketSegmentationTool(),
        ROICalculatorTool(),
    ]
    for tool in tools:
        assert tool.name
        assert tool.description
        schema = tool.to_anthropic_schema()
        assert "name" in schema
        assert "input_schema" in schema


def test_team_roles():
    from nanobot.scheduler.agent_teams import list_teams
    teams = list_teams()
    assert len(teams) >= 10
    for team in teams:
        assert "name" in team
        assert "description" in team
        assert "mode" in team
        assert team["mode"] in ("hierarchical", "flat")
