"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_basic(self, async_client: AsyncClient):
        """Test basic health endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_live(self, async_client: AsyncClient):
        """Test liveness probe."""
        response = await async_client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "live"


@pytest.mark.integration
class TestAssetEndpoints:
    """Tests for asset-related endpoints."""

    @pytest.mark.asyncio
    async def test_list_assets(self, async_client: AsyncClient):
        """Test listing all assets."""
        response = await async_client.get("/assets")
        assert response.status_code == 200
        assets = response.json()
        assert isinstance(assets, list)
        assert len(assets) > 0

        # Check asset structure
        asset = assets[0]
        assert "id" in asset
        assert "name" in asset
        assert "sector" in asset
        assert "region" in asset
        assert "revenue_usd_m" in asset
        assert "scope1_tco2e" in asset
        assert "scope2_tco2e" in asset

    @pytest.mark.asyncio
    async def test_get_portfolio(self, async_client: AsyncClient):
        """Test getting the full portfolio."""
        response = await async_client.get("/portfolio")
        assert response.status_code == 200
        portfolio = response.json()

        assert "id" in portfolio
        assert "name" in portfolio
        assert "assets" in portfolio
        assert len(portfolio["assets"]) > 0


@pytest.mark.integration
class TestScoreEndpoints:
    """Tests for scoring endpoints."""

    @pytest.mark.asyncio
    async def test_portfolio_score(self, async_client: AsyncClient):
        """Test portfolio scoring endpoint."""
        response = await async_client.get("/score")
        assert response.status_code == 200
        score = response.json()

        # Check all expected fields
        assert "portfolio_id" in score
        assert "overall_score" in score
        assert "climate_risk" in score
        assert "transition_risk" in score
        assert "physical_risk" in score
        assert "opportunity_score" in score
        assert "top_risks" in score
        assert "quick_wins" in score
        assert "sector_breakdown" in score

        # Validate ranges
        assert 0 <= score["climate_risk"] <= 100
        assert 0 <= score["transition_risk"] <= 100
        assert 0 <= score["physical_risk"] <= 100


@pytest.mark.integration
class TestScenarioEndpoints:
    """Tests for scenario endpoints."""

    @pytest.mark.asyncio
    async def test_list_scenarios(self, async_client: AsyncClient):
        """Test listing available scenarios."""
        response = await async_client.get("/scenarios")
        assert response.status_code == 200
        scenarios = response.json()

        assert isinstance(scenarios, dict)
        assert len(scenarios) >= 3  # At least 3 default scenarios

    @pytest.mark.asyncio
    async def test_run_scenario(self, async_client: AsyncClient):
        """Test running a scenario."""
        response = await async_client.post(
            "/scenario",
            json={
                "scenario": "Net Zero 2050",
            },
        )
        assert response.status_code == 200
        result = response.json()

        assert "portfolio_id" in result
        assert "scenario" in result
        assert "impact_summary" in result
        assert "est_ebitda_impact_pct" in result
        assert "emissions_delta_pct" in result
        assert "hotspots" in result

    @pytest.mark.asyncio
    async def test_run_custom_scenario(self, async_client: AsyncClient):
        """Test running a custom scenario."""
        response = await async_client.post(
            "/scenario",
            json={
                "scenario": "Custom",
                "carbon_price_usd": 150,
                "revenue_shock_pct": -2.5,
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert "150" in result["impact_summary"]


@pytest.mark.integration
class TestCopilotEndpoints:
    """Tests for copilot endpoints."""

    @pytest.mark.asyncio
    async def test_copilot_basic(self, async_client: AsyncClient):
        """Test basic copilot endpoint."""
        response = await async_client.post(
            "/copilot",
            json={
                "question": "What are my top risks?",
            },
        )
        assert response.status_code == 200
        result = response.json()

        assert "portfolio_id" in result
        assert "answer" in result
        assert "citations" in result
        assert len(result["answer"]) > 0

    @pytest.mark.asyncio
    async def test_copilot_stream_endpoint_exists(self, async_client: AsyncClient):
        """Test that streaming endpoint exists and accepts requests."""
        response = await async_client.post(
            "/copilot/stream",
            json={"question": "What are my top risks?"},
        )
        # Should return 200 with SSE content type
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_copilot_stream_empty_question(self, async_client: AsyncClient):
        """Test streaming endpoint rejects empty questions."""
        response = await async_client.post(
            "/copilot/stream",
            json={"question": "   "},
        )
        assert response.status_code == 400


@pytest.mark.integration
class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_portfolio_not_found(self, async_client: AsyncClient):
        """Test 404 for non-existent portfolio."""
        response = await async_client.get("/portfolios/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "PORTFOLIO_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_invalid_portfolio_id(self, async_client: AsyncClient):
        """Test 400 for invalid portfolio ID format."""
        response = await async_client.get("/portfolios/not-a-uuid")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "INVALID_PORTFOLIO_ID"

    @pytest.mark.asyncio
    async def test_app_info(self, async_client: AsyncClient):
        """Test application info endpoint."""
        response = await async_client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Canopy"
        assert "version" in data
        assert "environment" in data


@pytest.mark.integration
class TestPortfolioManagement:
    """Tests for portfolio CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_portfolios(self, async_client: AsyncClient):
        """Test listing all portfolios."""
        response = await async_client.get("/portfolios")
        assert response.status_code == 200
        data = response.json()
        assert "portfolios" in data
        assert len(data["portfolios"]) >= 1

    @pytest.mark.asyncio
    async def test_create_portfolio(self, async_client: AsyncClient):
        """Test creating a new portfolio."""
        response = await async_client.post(
            "/portfolios",
            json={
                "name": "Test Portfolio",
                "description": "A test portfolio",
                "assets": [
                    {
                        "id": "test-asset-1",
                        "name": "Test Company",
                        "sector": "Technology",
                        "region": "North America",
                        "revenue_usd_m": 1000,
                        "scope1_tco2e": 5000,
                        "scope2_tco2e": 3000,
                        "green_revenue_pct": 25,
                        "controversies": 0,
                    }
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["portfolio"]["name"] == "Test Portfolio"
        assert data["portfolio"]["asset_count"] == 1


@pytest.mark.integration
class TestDocumentEndpoints:
    """Tests for document upload endpoints."""

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, async_client: AsyncClient):
        """Test listing documents when none uploaded."""
        # Clear first
        await async_client.delete("/documents")

        response = await async_client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total_chars"] == 0

    @pytest.mark.asyncio
    async def test_clear_documents(self, async_client: AsyncClient):
        """Test clearing all documents."""
        response = await async_client.delete("/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
