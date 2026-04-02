"""
Tests for the wine text parser.
"""
import pytest

from app.services.text_parser import parse_wine_text, normalize_text


class TestVintageExtraction:
    def test_vintage_in_prefix(self):
        p = parse_wine_text("2019 Chateau Margaux")
        assert p.vintage == 2019

    def test_vintage_in_suffix(self):
        p = parse_wine_text("Chateau Margaux 2015")
        assert p.vintage == 2015

    def test_no_vintage(self):
        p = parse_wine_text("Chateau Margaux")
        assert p.vintage is None

    def test_nv_flag(self):
        p = parse_wine_text("Krug Grande Cuvée NV")
        assert p.non_vintage is True
        assert p.vintage is None

    def test_nv_dot_notation(self):
        p = parse_wine_text("Dom Perignon N.V.")
        assert p.non_vintage is True

    def test_vintage_not_confused_with_price(self):
        p = parse_wine_text("Opus One 2018 $250")
        assert p.vintage == 2018

    def test_four_digit_not_vintage_out_of_range(self):
        p = parse_wine_text("Random 1200 Wine")
        assert p.vintage is None


class TestVarietalDetection:
    def test_cabernet_sauvignon_full(self):
        p = parse_wine_text("Jordan Cabernet Sauvignon 2019")
        assert p.varietal == "cabernet sauvignon"

    def test_cabernet_abbreviated(self):
        p = parse_wine_text("Screaming Eagle Cab 2018")
        assert p.varietal == "cabernet sauvignon"

    def test_pinot_noir(self):
        p = parse_wine_text("Meiomi Pinot Noir California")
        assert p.varietal == "pinot noir"

    def test_chardonnay(self):
        p = parse_wine_text("Rombauer Chard Carneros")
        assert p.varietal == "chardonnay"

    def test_sauvignon_blanc(self):
        p = parse_wine_text("Kim Crawford Sauvignon Blanc")
        assert p.varietal == "sauvignon blanc"

    def test_shiraz_maps_to_syrah(self):
        p = parse_wine_text("Penfolds Grange Shiraz")
        assert p.varietal == "syrah"


class TestRegionDetection:
    def test_pauillac(self):
        p = parse_wine_text("Chateau Latour Pauillac 2016")
        assert p.region == "bordeaux"

    def test_napa(self):
        p = parse_wine_text("Opus One Napa Valley 2018")
        assert p.region == "napa"

    def test_champagne(self):
        p = parse_wine_text("Dom Perignon Champagne")
        assert p.region == "champagne"

    def test_barolo(self):
        p = parse_wine_text("Giacomo Conterno Barolo Monfortino")
        assert p.region == "piedmont"

    def test_no_region(self):
        p = parse_wine_text("Random Red Wine")
        assert p.region is None


class TestWineTypeDetection:
    def test_sparkling_champagne(self):
        p = parse_wine_text("Krug Grande Cuvée Champagne")
        assert p.wine_type == "sparkling"

    def test_sparkling_prosecco(self):
        p = parse_wine_text("La Marca Prosecco DOC")
        assert p.wine_type == "sparkling"

    def test_dessert_sauternes(self):
        p = parse_wine_text("Chateau d'Yquem Sauternes")
        assert p.wine_type == "dessert"

    def test_rose(self):
        p = parse_wine_text("Whispering Angel Rosé Provence")
        assert p.wine_type == "rose"


class TestFormatDetection:
    def test_magnum(self):
        p = parse_wine_text("Opus One 2018 Magnum")
        assert p.format_ml == 1500

    def test_750ml(self):
        p = parse_wine_text("Silver Oak Napa 2019 750ml")
        assert p.format_ml == 750

    def test_no_format(self):
        p = parse_wine_text("Caymus Cabernet 2020")
        assert p.format_ml is None


class TestAbbreviationExpansion:
    def test_chateau_abbreviation(self):
        n = normalize_text("Ch. Margaux")
        assert "chateau" in n

    def test_domaine_abbreviation(self):
        n = normalize_text("Dom. Leroy")
        assert "domaine" in n

    def test_drc_expansion(self):
        n = normalize_text("DRC La Tâche")
        assert "domaine de la romanee conti" in n


class TestNormalization:
    def test_diacritics_removed(self):
        n = normalize_text("Château Pétrus Côte-Rôtie")
        assert "château" not in n
        assert "chateau" in n

    def test_lowercase(self):
        n = normalize_text("SCREAMING EAGLE")
        assert n == n.lower()

    def test_extra_spaces_collapsed(self):
        n = normalize_text("  Opus   One  ")
        assert "  " not in n
