"""
Tests for the wine identifier / fuzzy matching engine.
"""
import pytest

from app.services.wine_identifier import identify_wine, search_wines


class TestExactAndHighConfidenceMatches:
    def test_chateau_margaux_exact(self):
        best, alts = identify_wine("Chateau Margaux 2019")
        assert best is not None
        assert best.wine.id == "chateau-margaux"
        assert best.score >= 0.85

    def test_chateau_margaux_with_price(self):
        best, _ = identify_wine("2018 Chateau Margaux, Margaux $850")
        assert best is not None
        assert best.wine.id == "chateau-margaux"

    def test_drc_la_tache_abbreviation(self):
        best, _ = identify_wine("DRC La Tache 2015")
        assert best is not None
        assert best.wine.id == "drc-la-tache"

    def test_dom_perignon(self):
        best, _ = identify_wine("Dom Perignon 2013")
        assert best is not None
        assert best.wine.id == "dom-perignon"

    def test_screaming_eagle_abbreviated(self):
        best, _ = identify_wine("Screaming Eagle Cab 2018 Napa")
        assert best is not None
        assert best.wine.id == "screaming-eagle"

    def test_penfolds_grange(self):
        best, _ = identify_wine("Penfolds Grange Shiraz 2016")
        assert best is not None
        assert best.wine.id == "penfolds-grange"

    def test_opus_one_number(self):
        best, _ = identify_wine("Opus 1 Napa 2019")
        assert best is not None
        assert best.wine.id == "opus-one"

    def test_kim_crawford(self):
        best, _ = identify_wine("Kim Crawford Sauvignon Blanc 2022")
        assert best is not None
        assert best.wine.id == "kim-crawford-sauvignon-blanc"

    def test_petrus(self):
        best, _ = identify_wine("Petrus Pomerol 2018")
        assert best is not None
        assert best.wine.id == "chateau-petrus"

    def test_sassicaia(self):
        best, _ = identify_wine("Sassicaia Bolgheri 2019")
        assert best is not None
        assert best.wine.id == "sassicaia"

    def test_tignanello(self):
        best, _ = identify_wine("Tignanello 2018 Antinori Tuscany")
        assert best is not None
        assert best.wine.id == "tignanello"

    def test_vega_sicilia_unico(self):
        best, _ = identify_wine("Vega Sicilia Unico 2011")
        assert best is not None
        assert best.wine.id == "vega-sicilia-unico"


class TestFuzzyAndPartialMatches:
    def test_misspelling_lafite(self):
        best, _ = identify_wine("Chateau Laffite Rothschild 2016")
        assert best is not None
        assert best.wine.id == "chateau-lafite-rothschild"

    def test_diacritics_stripped(self):
        best, _ = identify_wine("Château Pétrus 2019")
        assert best is not None
        assert best.wine.id == "chateau-petrus"

    def test_partial_name_margaux(self):
        best, _ = identify_wine("Margaux 2018")
        # Could match Chateau Margaux or Palmer (both in Margaux appellation)
        assert best is not None
        assert best.wine.appellation is not None
        # Should at least be in Margaux appellation
        assert "Margaux" in (best.wine.appellation or "") or "Margaux" in (best.wine.region or "")

    def test_whispering_angel(self):
        best, _ = identify_wine("Whispering Angel Rose")
        assert best is not None
        assert best.wine.id == "whispering-angel-rose"

    def test_alternatives_returned(self):
        best, alts = identify_wine("Chateau Margaux 2019")
        assert best is not None
        assert isinstance(alts, list)
        # Alternatives should not include the best match itself
        alt_ids = [a.wine.id for a in alts]
        assert "chateau-margaux" not in alt_ids


class TestNoMatch:
    def test_gibberish_returns_none(self):
        best, _ = identify_wine("zzz totally unknown xyzqwerty wine")
        assert best is None

    def test_very_short_query(self):
        # Should not crash
        best, _ = identify_wine("red")
        # May or may not match; what matters is no exception


class TestSearchWines:
    def test_search_returns_results(self):
        results = search_wines("chateau margaux")
        assert len(results) > 0
        assert results[0].wine.id == "chateau-margaux"

    def test_search_filter_wine_type(self):
        results = search_wines("krug", wine_type="sparkling")
        assert all(r.wine.wine_type == "sparkling" for r in results)

    def test_search_filter_country(self):
        results = search_wines("penfolds", country="Australia")
        assert all(r.wine.country == "Australia" for r in results)

    def test_search_limit(self):
        results = search_wines("chateau", limit=3)
        assert len(results) <= 3

    def test_search_empty_string_raises(self):
        # Min-length is 2 characters; not tested here (schema validation)
        results = search_wines("bo")
        assert isinstance(results, list)
