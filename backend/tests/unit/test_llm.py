"""Unit tests for LLM prompt building."""

from app.llm.prompts import (
    SYSTEM_PROMPT,
    build_portfolio_context,
    build_user_message,
)


class TestSystemPrompt:
    """Tests for system prompt."""

    def test_prompt_exists(self):
        """Test system prompt is defined."""
        assert len(SYSTEM_PROMPT) > 100

    def test_prompt_contains_key_elements(self):
        """Test system prompt includes essential guidance."""
        prompt_lower = SYSTEM_PROMPT.lower()

        # Should mention ESG domain
        assert "esg" in prompt_lower
        assert "climate" in prompt_lower

        # Should mention key frameworks
        assert "tcfd" in prompt_lower
        assert "sbti" in prompt_lower

        # Should mention risk types
        assert "transition" in prompt_lower
        assert "physical" in prompt_lower


class TestBuildPortfolioContext:
    """Tests for portfolio context building."""

    def test_basic_context(self):
        """Test building context with minimal data."""
        assets = [
            {
                "name": "Test Asset",
                "sector": "Utilities",
                "region": "North America",
                "revenue_usd_m": 1000,
                "scope1_tco2e": 500000,
                "scope2_tco2e": 100000,
                "green_revenue_pct": 10,
                "controversies": 1,
            }
        ]
        scores = {
            "overall_score": 75,
            "climate_risk": 45,
            "transition_risk": 50,
            "physical_risk": 38,
            "opportunity_score": 16,
            "top_risks": ["High emissions intensity"],
            "quick_wins": ["Improve efficiency"],
            "sector_breakdown": {"Utilities": 65.0},
        }
        scenarios = {"Net Zero": {"carbon_price": 120, "revenue_shock": -1.8}}

        context = build_portfolio_context(assets, scores, scenarios)

        # Should contain portfolio data
        assert "Test Asset" in context
        assert "Utilities" in context
        assert "75" in context  # overall score

        # Should contain table headers
        assert "Asset" in context
        assert "Sector" in context
        assert "Revenue" in context

        # Should contain scenario info
        assert "Net Zero" in context
        assert "120" in context  # carbon price

    def test_empty_assets(self):
        """Test context with empty assets list."""
        context = build_portfolio_context([], {}, {})
        assert "Portfolio Context" in context
        assert "Holdings" in context

    def test_intensity_calculation(self):
        """Test emissions intensity is calculated in context."""
        assets = [
            {
                "name": "High Intensity Co",
                "sector": "Materials",
                "region": "Europe",
                "revenue_usd_m": 100,
                "scope1_tco2e": 100000,
                "scope2_tco2e": 50000,
                "green_revenue_pct": 5,
                "controversies": 2,
            }
        ]
        context = build_portfolio_context(assets, {}, {})

        # Intensity = (100000 + 50000) / 100 = 1500
        assert "1500" in context or "1,500" in context


class TestBuildUserMessage:
    """Tests for user message building."""

    def test_message_structure(self):
        """Test user message includes context and question."""
        context = "## Portfolio Context\nTest data here"
        question = "What are my biggest risks?"

        message = build_user_message(question, context)

        # Should include context
        assert "Portfolio Context" in message
        assert "Test data here" in message

        # Should include question
        assert "What are my biggest risks?" in message

        # Should have clear sections
        assert "User Question" in message

    def test_empty_question(self):
        """Test handling empty question."""
        message = build_user_message("", "Some context")
        assert "Some context" in message
