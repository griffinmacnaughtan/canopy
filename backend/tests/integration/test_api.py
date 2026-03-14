"""Integration tests for API endpoints."""

import io
import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_health_basic(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_live(self, async_client: AsyncClient):
        response = await async_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "live"

    @pytest.mark.asyncio
    async def test_request_id_header_present(self, async_client: AsyncClient):
        """Every response must carry an X-Request-ID header."""
        response = await async_client.get("/health/live")
        assert "x-request-id" in response.headers

    @pytest.mark.asyncio
    async def test_request_id_echoed_back(self, async_client: AsyncClient):
        """If the client sends X-Request-ID the same value is echoed."""
        custom_id = "test-trace-abc123"
        response = await async_client.get(
            "/health/live", headers={"X-Request-ID": custom_id}
        )
        assert response.headers["x-request-id"] == custom_id


# ---------------------------------------------------------------------------
# App Info
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAppInfo:
    @pytest.mark.asyncio
    async def test_app_info(self, async_client: AsyncClient):
        response = await async_client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Canopy"
        assert "version" in data
        assert "environment" in data


# ---------------------------------------------------------------------------
# Portfolio List / Get
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPortfolioListGet:
    @pytest.mark.asyncio
    async def test_list_portfolios(self, async_client: AsyncClient):
        response = await async_client.get("/portfolios")
        assert response.status_code == 200
        data = response.json()
        assert "portfolios" in data
        assert len(data["portfolios"]) >= 1

    @pytest.mark.asyncio
    async def test_list_portfolios_has_is_sample_flag(self, async_client: AsyncClient):
        response = await async_client.get("/portfolios")
        data = response.json()
        for p in data["portfolios"]:
            assert "is_sample" in p

    @pytest.mark.asyncio
    async def test_get_portfolio(self, async_client: AsyncClient):
        response = await async_client.get("/portfolio")
        assert response.status_code == 200
        portfolio = response.json()
        assert "id" in portfolio
        assert "assets" in portfolio
        assert len(portfolio["assets"]) > 0

    @pytest.mark.asyncio
    async def test_list_assets(self, async_client: AsyncClient):
        response = await async_client.get("/assets")
        assert response.status_code == 200
        assets = response.json()
        assert isinstance(assets, list)
        assert len(assets) > 0
        first = assets[0]
        for field in ("id", "name", "sector", "region", "revenue_usd_m", "scope1_tco2e", "scope2_tco2e"):
            assert field in first


# ---------------------------------------------------------------------------
# Portfolio CRUD
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPortfolioCrud:
    @pytest.mark.asyncio
    async def test_create_portfolio(self, async_client: AsyncClient):
        response = await async_client.post(
            "/portfolios",
            json={
                "name": "Integration Test Portfolio",
                "description": "Created by integration test",
                "assets": [
                    {
                        "id": "asset-1",
                        "name": "Test Corp",
                        "sector": "Information Technology",
                        "region": "North America",
                        "revenue_usd_m": 5000,
                        "scope1_tco2e": 10000,
                        "scope2_tco2e": 5000,
                        "green_revenue_pct": 30,
                        "controversies": 0,
                    }
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["portfolio"]["name"] == "Integration Test Portfolio"
        assert data["portfolio"]["asset_count"] == 1
        assert data["portfolio"]["is_sample"] is False
        return data["portfolio"]["id"]

    @pytest.mark.asyncio
    async def test_create_portfolio_rejects_empty_name(self, async_client: AsyncClient):
        response = await async_client.post(
            "/portfolios",
            json={
                "name": "   ",
                "assets": [
                    {
                        "id": "a1", "name": "X", "sector": "Energy",
                        "region": "EU", "revenue_usd_m": 1000,
                        "scope1_tco2e": 0, "scope2_tco2e": 0,
                        "green_revenue_pct": 0, "controversies": 0,
                    }
                ],
            },
        )
        assert response.status_code == 422  # Pydantic validation

    @pytest.mark.asyncio
    async def test_create_and_delete_portfolio(self, async_client: AsyncClient):
        # Create
        create_resp = await async_client.post(
            "/portfolios",
            json={
                "name": "Temp Delete Portfolio",
                "assets": [
                    {
                        "id": "a1", "name": "DeleteMe", "sector": "Healthcare",
                        "region": "EU", "revenue_usd_m": 500,
                        "scope1_tco2e": 1000, "scope2_tco2e": 500,
                        "green_revenue_pct": 10, "controversies": 0,
                    }
                ],
            },
        )
        assert create_resp.status_code == 200
        portfolio_id = create_resp.json()["portfolio"]["id"]

        # Delete
        del_resp = await async_client.delete(f"/portfolios/{portfolio_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["success"] is True

        # Confirm gone
        get_resp = await async_client.get(f"/portfolios/{portfolio_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_sample_portfolio_rejected(self, async_client: AsyncClient):
        """Sample portfolios must be protected from deletion."""
        portfolios = (await async_client.get("/portfolios")).json()["portfolios"]
        sample = next((p for p in portfolios if p.get("is_sample")), None)
        if sample is None:
            pytest.skip("No sample portfolio found in test database")

        response = await async_client.delete(f"/portfolios/{sample['id']}")
        assert response.status_code == 400
        assert "cannot be deleted" in response.json()["message"].lower()


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_portfolio_not_found(self, async_client: AsyncClient):
        response = await async_client.get("/portfolios/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert response.json()["error"] == "PORTFOLIO_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_invalid_portfolio_id(self, async_client: AsyncClient):
        response = await async_client.get("/portfolios/not-a-uuid")
        assert response.status_code == 400
        assert response.json()["error"] == "INVALID_PORTFOLIO_ID"


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestScoring:
    @pytest.mark.asyncio
    async def test_portfolio_score(self, async_client: AsyncClient):
        response = await async_client.get("/score")
        assert response.status_code == 200
        score = response.json()

        for field in (
            "portfolio_id", "overall_score", "climate_risk", "transition_risk",
            "physical_risk", "opportunity_score", "top_risks", "quick_wins", "sector_breakdown",
        ):
            assert field in score

        assert 0 <= score["climate_risk"] <= 100
        assert 0 <= score["transition_risk"] <= 100
        assert 0 <= score["physical_risk"] <= 100

    @pytest.mark.asyncio
    async def test_list_scenarios(self, async_client: AsyncClient):
        response = await async_client.get("/scenarios")
        assert response.status_code == 200
        scenarios = response.json()
        assert isinstance(scenarios, dict)
        assert len(scenarios) >= 3

    @pytest.mark.asyncio
    async def test_run_scenario(self, async_client: AsyncClient):
        response = await async_client.post("/scenario", json={"scenario": "Net Zero 2050"})
        assert response.status_code == 200
        result = response.json()
        for field in ("portfolio_id", "scenario", "impact_summary", "est_ebitda_impact_pct"):
            assert field in result

    @pytest.mark.asyncio
    async def test_run_custom_scenario(self, async_client: AsyncClient):
        response = await async_client.post(
            "/scenario",
            json={"scenario": "Custom", "carbon_price_usd": 150, "revenue_shock_pct": -2.5},
        )
        assert response.status_code == 200
        assert "150" in response.json()["impact_summary"]


# ---------------------------------------------------------------------------
# Portfolio Comparison
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPortfolioComparison:
    @pytest.mark.asyncio
    async def test_compare_two_portfolios(self, async_client: AsyncClient):
        portfolios = (await async_client.get("/portfolios")).json()["portfolios"]
        if len(portfolios) < 2:
            pytest.skip("Need at least 2 portfolios for comparison test")

        a_id = portfolios[0]["id"]
        b_id = portfolios[1]["id"]

        response = await async_client.get(
            f"/portfolios/compare/diff?a={a_id}&b={b_id}"
        )
        assert response.status_code == 200
        data = response.json()

        assert "portfolio_a" in data
        assert "portfolio_b" in data
        assert "delta" in data
        assert "recommendation" in data

        # Delta must contain the right keys
        for key in ("overall_score", "climate_risk", "transition_risk", "physical_risk"):
            assert key in data["delta"]

        # Recommendation is a non-empty string
        assert isinstance(data["recommendation"], str)
        assert len(data["recommendation"]) > 10

    @pytest.mark.asyncio
    async def test_compare_same_portfolio_rejected(self, async_client: AsyncClient):
        portfolios = (await async_client.get("/portfolios")).json()["portfolios"]
        pid = portfolios[0]["id"]

        response = await async_client.get(f"/portfolios/compare/diff?a={pid}&b={pid}")
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Portfolio Export
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPortfolioExport:
    @pytest.mark.asyncio
    async def test_export_portfolio_report(self, async_client: AsyncClient):
        portfolios = (await async_client.get("/portfolios")).json()["portfolios"]
        pid = portfolios[0]["id"]

        response = await async_client.get(f"/portfolios/{pid}/export")
        assert response.status_code == 200
        report = response.json()

        required_fields = (
            "generated_at", "portfolio_id", "portfolio_name",
            "asset_count", "overall_score", "climate_risk",
            "assets", "scenario_impacts",
        )
        for field in required_fields:
            assert field in report, f"Missing field: {field}"

        # generated_at should be a valid ISO timestamp
        from datetime import datetime
        datetime.fromisoformat(report["generated_at"].replace("Z", "+00:00"))

        # Assets have the computed emissions_intensity field
        assert len(report["assets"]) > 0
        assert "emissions_intensity_tco2e_per_m_revenue" in report["assets"][0]

        # Scenario impacts run for all stored scenarios
        assert len(report["scenario_impacts"]) >= 3


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestCsvImport:
    @pytest.mark.asyncio
    async def test_import_valid_csv(self, async_client: AsyncClient):
        csv_content = (
            "name,ticker,sector,region,revenue_usd_m,scope1_tco2e,scope2_tco2e,green_revenue_pct,controversies\n"
            "Acme Solar,ACME,Energy,North America,2500,80000,20000,60,1\n"
            "GreenTech Inc,,Information Technology,Europe,1200,5000,15000,75,0\n"
        )
        files = {"file": ("test_portfolio.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = await async_client.post(
            "/portfolios/import/csv?name=CSV+Test+Portfolio",
            files=files,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["rows_imported"] == 2
        assert data["rows_skipped"] == 0
        assert data["portfolio"]["name"] == "CSV Test Portfolio"
        assert data["portfolio"]["asset_count"] == 2

    @pytest.mark.asyncio
    async def test_import_csv_skips_bad_rows(self, async_client: AsyncClient):
        csv_content = (
            "name,sector,region,revenue_usd_m,scope1_tco2e,scope2_tco2e,green_revenue_pct,controversies\n"
            "Good Corp,Energy,North America,1000,50000,10000,20,0\n"
            ",Energy,North America,500,1000,500,10,0\n"          # missing name
            "Bad Revenue,Utilities,Europe,INVALID,0,0,5,0\n"     # bad float
        )
        files = {"file": ("portfolio.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = await async_client.post("/portfolios/import/csv", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["rows_imported"] == 1
        assert data["rows_skipped"] == 2
        assert len(data["warnings"]) == 2

    @pytest.mark.asyncio
    async def test_import_non_csv_rejected(self, async_client: AsyncClient):
        files = {"file": ("report.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}
        response = await async_client.post("/portfolios/import/csv", files=files)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_import_missing_columns_rejected(self, async_client: AsyncClient):
        csv_content = "name,sector\nFoo,Energy\n"
        files = {"file": ("bad.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = await async_client.post("/portfolios/import/csv", files=files)
        assert response.status_code == 400
        assert "missing required columns" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_import_uses_filename_as_default_name(self, async_client: AsyncClient):
        csv_content = (
            "name,sector,region,revenue_usd_m,scope1_tco2e,scope2_tco2e,green_revenue_pct,controversies\n"
            "Corp A,Healthcare,North America,300,1000,500,5,0\n"
        )
        files = {"file": ("my_fund.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = await async_client.post("/portfolios/import/csv", files=files)
        assert response.status_code == 200
        assert response.json()["portfolio"]["name"] == "my fund"


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestDocumentEndpoints:
    @pytest.mark.asyncio
    async def test_list_documents_empty(self, async_client: AsyncClient):
        await async_client.delete("/documents")
        response = await async_client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total_chars"] == 0

    @pytest.mark.asyncio
    async def test_clear_documents(self, async_client: AsyncClient):
        response = await async_client.delete("/documents")
        assert response.status_code == 200
        assert response.json()["success"] is True
