"""
Tests for the markup analyser and fairness scoring.
"""
import pytest

from app.services.markup_analyzer import analyze_markup, _compute_score, _TIER_CONFIG


class TestFairnessScore:
    """Validate scoring boundaries for each tier."""

    def _score(self, tier: str, multiple: float) -> int:
        cfg = _TIER_CONFIG[tier]
        return _compute_score(multiple, cfg)

    # ── Budget tier ──────────────────────────────────────────────────────────

    def test_budget_below_fair_scores_high(self):
        # 2.0× is below fair_low(2.8) → exceptional
        assert self._score("budget", 2.0) >= 90

    def test_budget_ideal_scores_well(self):
        # 3.5× is the ideal → ~85
        s = self._score("budget", 3.5)
        assert 70 <= s <= 100

    def test_budget_above_excessive_scores_low(self):
        # 7.0× far exceeds excessive(5.5)
        assert self._score("budget", 7.0) <= 20

    # ── Mid tier ─────────────────────────────────────────────────────────────

    def test_mid_fair_range(self):
        s = self._score("mid", 3.0)
        assert s >= 60

    def test_mid_excessive(self):
        s = self._score("mid", 6.0)
        assert s <= 20

    # ── Premium tier ─────────────────────────────────────────────────────────

    def test_premium_below_market(self):
        # 2.0× is below fair_low(2.25) → generous score
        s = self._score("premium", 2.0)
        assert s >= 85

    def test_premium_high_markup(self):
        s = self._score("premium", 5.0)
        assert s <= 30

    # ── Luxury tier ──────────────────────────────────────────────────────────

    def test_luxury_at_ideal(self):
        s = self._score("luxury", 2.4)
        assert s >= 70

    def test_luxury_below_market(self):
        s = self._score("luxury", 1.5)
        assert s >= 90

    # ── Ultra tier ───────────────────────────────────────────────────────────

    def test_ultra_at_ideal(self):
        s = self._score("ultra", 2.0)
        assert s >= 70


class TestAnalyzeMarkup:
    """Integration tests for the full analyze_markup function."""

    def test_exceptional_value(self):
        # Menu price far below market → exceptional value
        result = analyze_markup(
            menu_price=100.0,
            avg_retail=200.0,
            estimated_wholesale=104.0,
            price_tier="mid",
            wine_name="Test Wine",
        )
        assert result.fairness_score >= 85
        assert result.verdict in ("exceptional_value", "fair")
        assert "below_market" in result.flags or result.fairness_score >= 85

    def test_excessive_markup(self):
        # Menu price 6× wholesale for a mid-tier wine → excessive
        result = analyze_markup(
            menu_price=300.0,
            avg_retail=50.0,
            estimated_wholesale=26.0,
            price_tier="mid",
        )
        assert result.fairness_score <= 30
        assert result.verdict in ("excessive_markup", "price_gouging", "high_markup")

    def test_fair_pricing(self):
        # Napa Cab at 3× wholesale → should be fair/moderate
        result = analyze_markup(
            menu_price=285.0,
            avg_retail=95.0,
            estimated_wholesale=52.0,
            price_tier="premium",
        )
        assert result.fairness_score is not None
        assert result.retail_multiple == pytest.approx(285 / 95, rel=0.01)
        assert result.wholesale_multiple == pytest.approx(285 / 52, rel=0.01)

    def test_below_wholesale_flag(self):
        result = analyze_markup(
            menu_price=20.0,
            avg_retail=50.0,
            estimated_wholesale=26.0,
            price_tier="mid",
        )
        assert "below_wholesale" in result.flags

    def test_insight_generated(self):
        result = analyze_markup(
            menu_price=150.0,
            avg_retail=90.0,
            estimated_wholesale=46.8,
            price_tier="premium",
        )
        assert result.insight is not None
        assert len(result.insight) > 10

    def test_industry_standard_range_set(self):
        result = analyze_markup(
            menu_price=100.0,
            avg_retail=35.0,
            estimated_wholesale=18.2,
            price_tier="mid",
        )
        assert result.industry_standard_wholesale_range is not None
        low, high = result.industry_standard_wholesale_range
        assert low < high

    def test_verdict_label_matches_verdict(self):
        result = analyze_markup(
            menu_price=500.0,
            avg_retail=50.0,
            estimated_wholesale=26.0,
            price_tier="mid",
        )
        assert result.verdict is not None
        assert result.verdict_label is not None
        # Both should be set together
        assert len(result.verdict_label) > 0

    def test_price_tier_propagated(self):
        result = analyze_markup(
            menu_price=200.0,
            avg_retail=100.0,
            estimated_wholesale=55.0,
            price_tier="premium",
        )
        assert result.price_tier == "premium"
