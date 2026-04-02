"""
End-to-end API tests (no real DB or Redis required – the app works with mocks).
"""
import pytest
import pytest_asyncio


pytestmark = pytest.mark.asyncio


class TestHealthCheck:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestAnalyzeEndpoint:
    async def test_analyze_known_wine(self, client):
        resp = await client.post(
            "/analyze",
            json={"menu_text": "Chateau Margaux 2019", "menu_price": 850.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["identification"]["matched"] is True
        assert data["identification"]["wine_id"] == "chateau-margaux"
        assert data["identification"]["confidence"] >= 0.85
        assert data["pricing"] is not None
        assert data["markup_analysis"] is not None
        assert data["markup_analysis"]["fairness_score"] is not None

    async def test_analyze_without_price_no_markup(self, client):
        resp = await client.post(
            "/analyze",
            json={"menu_text": "Opus One 2018"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["identification"]["matched"] is True
        assert data["markup_analysis"] is None

    async def test_analyze_unknown_wine(self, client):
        resp = await client.post(
            "/analyze",
            json={"menu_text": "zzz totally unknown xyzqwerty wine 2020", "menu_price": 50.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["identification"]["matched"] is False
        assert data["identification"]["confidence_level"] == "none"

    async def test_analyze_with_vintage_override(self, client):
        resp = await client.post(
            "/analyze",
            json={"menu_text": "Screaming Eagle Cabernet", "menu_price": 5000.0, "vintage": 2016},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["identification"]["matched"] is True
        assert data["identification"]["vintage"] == 2016

    async def test_analyze_champagne_nv(self, client):
        resp = await client.post(
            "/analyze",
            json={"menu_text": "Krug Grande Cuvée NV", "menu_price": 400.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        ident = data["identification"]
        assert ident["matched"] is True
        assert ident["wine_id"] == "krug-grande-cuvee"

    async def test_analyze_drc_abbreviation(self, client):
        resp = await client.post(
            "/analyze",
            json={"menu_text": "DRC La Tache 2015", "menu_price": 8000.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["identification"]["wine_id"] == "drc-la-tache"

    async def test_analyze_response_has_metadata(self, client):
        resp = await client.post("/analyze", json={"menu_text": "Penfolds Grange 2018"})
        data = resp.json()
        assert "metadata" in data
        assert "analyzed_at" in data["metadata"]
        assert data["metadata"]["processing_time_ms"] >= 0

    async def test_analyze_short_text_raises_422(self, client):
        resp = await client.post("/analyze", json={"menu_text": "x"})
        assert resp.status_code == 422

    async def test_analyze_negative_price_raises_422(self, client):
        resp = await client.post(
            "/analyze",
            json={"menu_text": "Opus One 2019", "menu_price": -10},
        )
        assert resp.status_code == 422


class TestBatchAnalyzeEndpoint:
    async def test_batch_multiple_wines(self, client):
        resp = await client.post(
            "/analyze/batch",
            json={
                "items": [
                    {"menu_text": "Chateau Margaux 2019", "menu_price": 850.0},
                    {"menu_text": "Kim Crawford Sauvignon Blanc", "menu_price": 45.0},
                    {"menu_text": "Dom Perignon 2013", "menu_price": 350.0},
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["results"]) == 3
        for r in data["results"]:
            assert "identification" in r

    async def test_batch_empty_raises_422(self, client):
        resp = await client.post("/analyze/batch", json={"items": []})
        assert resp.status_code == 422

    async def test_batch_venue_id_propagated(self, client):
        resp = await client.post(
            "/analyze/batch",
            json={
                "items": [{"menu_text": "Opus One 2018", "menu_price": 300}],
                "venue_id": "restaurant-abc",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["venue_id"] == "restaurant-abc"


class TestSearchEndpoint:
    async def test_search_returns_results(self, client):
        resp = await client.get("/search?q=chateau+margaux")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        assert data["results"][0]["id"] == "chateau-margaux"

    async def test_search_with_wine_type_filter(self, client):
        resp = await client.get("/search?q=krug&wine_type=sparkling")
        assert resp.status_code == 200
        data = resp.json()
        for r in data["results"]:
            assert r["wine_type"] == "sparkling"

    async def test_search_with_limit(self, client):
        resp = await client.get("/search?q=chateau&limit=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) <= 3

    async def test_search_match_score_present(self, client):
        resp = await client.get("/search?q=opus+one")
        data = resp.json()
        for r in data["results"]:
            assert "match_score" in r
            assert 0.0 <= r["match_score"] <= 1.0

    async def test_search_too_short_raises_422(self, client):
        resp = await client.get("/search?q=x")
        assert resp.status_code == 422


class TestPricingEndpoint:
    async def test_known_wine_pricing(self, client):
        resp = await client.get("/wine/opus-one/pricing")
        assert resp.status_code == 200
        data = resp.json()
        assert data["wine_id"] == "opus-one"
        assert data["pricing"]["avg_retail"] is not None
        assert data["pricing"]["estimated_wholesale"] is not None

    async def test_pricing_with_vintage(self, client):
        resp = await client.get("/wine/chateau-margaux/pricing?vintage=2019")
        assert resp.status_code == 200
        data = resp.json()
        assert data["vintage"] == 2019

    async def test_unknown_wine_returns_404(self, client):
        resp = await client.get("/wine/nonexistent-wine-xyz/pricing")
        assert resp.status_code == 404

    async def test_pricing_sources_list(self, client):
        resp = await client.get("/wine/penfolds-grange/pricing")
        data = resp.json()
        assert "sources" in data["pricing"]
        assert isinstance(data["pricing"]["sources"], list)
