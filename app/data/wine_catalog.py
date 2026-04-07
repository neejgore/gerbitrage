"""
Canonical wine catalog used as the fuzzy-matching knowledge base.

avg_retail_price is the typical USD retail price for a standard vintage.
price_tier is derived automatically from avg_retail_price so it can never drift:
  budget (<=$25) | mid ($25–$75) | premium ($75–$200) | luxury ($200–$600) | ultra (>$600)
"""
from dataclasses import dataclass, field


def _derive_price_tier(price: float) -> str:
    """Deterministically derive price tier from retail price."""
    if price <= 25:
        return "budget"
    if price <= 75:
        return "mid"
    if price <= 200:
        return "premium"
    if price <= 600:
        return "luxury"
    return "ultra"


@dataclass
class WineCatalogEntry:
    id: str
    name: str
    producer: str
    region: str
    country: str
    appellation: str
    varietal: str
    wine_type: str          # red | white | rose | sparkling | dessert | fortified
    avg_retail_price: float
    price_tier: str         # set at construction; overridden by __post_init__ from price
    aliases: list[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        # Always derive tier from price so static catalog values can never drift.
        self.price_tier = _derive_price_tier(self.avg_retail_price)


# ---------------------------------------------------------------------------
# BORDEAUX – Left Bank
# ---------------------------------------------------------------------------
BORDEAUX_LEFT = [
    WineCatalogEntry(
        id="chateau-margaux",
        name="Chateau Margaux",
        producer="Chateau Margaux",
        region="Margaux, Bordeaux, France",
        country="France",
        appellation="Margaux",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=890.0,
        price_tier="ultra",
        aliases=["Ch Margaux", "Cht Margaux", "Château Margaux", "Margaux Premier Grand Cru"],
        description="First Growth estate producing one of Bordeaux's most elegant and refined reds.",
    ),
    WineCatalogEntry(
        id="chateau-latour",
        name="Chateau Latour",
        producer="Chateau Latour",
        region="Pauillac, Bordeaux, France",
        country="France",
        appellation="Pauillac",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=950.0,
        price_tier="ultra",
        aliases=["Ch Latour", "Château Latour", "Latour Pauillac"],
        description="Iconic First Growth famous for power and longevity.",
    ),
    WineCatalogEntry(
        id="chateau-lafite-rothschild",
        name="Chateau Lafite Rothschild",
        producer="Domaines Barons de Rothschild",
        region="Pauillac, Bordeaux, France",
        country="France",
        appellation="Pauillac",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=980.0,
        price_tier="ultra",
        aliases=["Lafite", "Chateau Lafite", "Château Lafite Rothschild", "Ch Lafite", "Lafite Rothschild"],
        description="The most celebrated of Bordeaux's First Growths, renowned for its finesse.",
    ),
    WineCatalogEntry(
        id="chateau-mouton-rothschild",
        name="Chateau Mouton Rothschild",
        producer="Baron Philippe de Rothschild",
        region="Pauillac, Bordeaux, France",
        country="France",
        appellation="Pauillac",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=920.0,
        price_tier="ultra",
        aliases=["Mouton Rothschild", "Mouton", "Ch Mouton Rothschild", "Château Mouton Rothschild"],
        description="First Growth known for its artist label series and opulent Cabernet.",
    ),
    WineCatalogEntry(
        id="chateau-haut-brion",
        name="Chateau Haut-Brion",
        producer="Domaine Clarence Dillon",
        region="Pessac-Léognan, Bordeaux, France",
        country="France",
        appellation="Pessac-Léognan",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=780.0,
        price_tier="ultra",
        aliases=["Haut Brion", "Haut-Brion", "Ch Haut-Brion", "Château Haut-Brion"],
        description="The only non-Médoc estate in the 1855 classification; earthy, complex First Growth.",
    ),
    WineCatalogEntry(
        id="chateau-cos-destournel",
        name="Chateau Cos d'Estournel",
        producer="Château Cos d'Estournel",
        region="Saint-Estèphe, Bordeaux, France",
        country="France",
        appellation="Saint-Estèphe",
        varietal="Cabernet Sauvignon, Merlot blend",
        wine_type="red",
        avg_retail_price=175.0,
        price_tier="luxury",
        aliases=["Cos d'Estournel", "Cos Estournel", "Ch Cos d'Estournel"],
        description="Super Second producing structured, opulent wines from Saint-Estèphe.",
    ),
    WineCatalogEntry(
        id="chateau-lynch-bages",
        name="Chateau Lynch-Bages",
        producer="Jean-Michel Cazes",
        region="Pauillac, Bordeaux, France",
        country="France",
        appellation="Pauillac",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=110.0,
        price_tier="premium",
        aliases=["Lynch Bages", "Lynch-Bages", "Ch Lynch-Bages"],
        description="Fifth Growth consistently delivering First-Growth quality; rich and generous.",
    ),
    WineCatalogEntry(
        id="chateau-pichon-baron",
        name="Chateau Pichon Baron",
        producer="AXA Millésimes",
        region="Pauillac, Bordeaux, France",
        country="France",
        appellation="Pauillac",
        varietal="Cabernet Sauvignon, Merlot blend",
        wine_type="red",
        avg_retail_price=130.0,
        price_tier="premium",
        aliases=["Pichon Baron", "Pichon-Baron", "Ch Pichon Baron", "Chateau Pichon-Longueville Baron"],
        description="Second Growth in Pauillac known for power and depth.",
    ),
    WineCatalogEntry(
        id="chateau-leoville-las-cases",
        name="Chateau Leoville Las Cases",
        producer="Château Léoville Las Cases",
        region="Saint-Julien, Bordeaux, France",
        country="France",
        appellation="Saint-Julien",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=240.0,
        price_tier="luxury",
        aliases=["Leoville Las Cases", "Léoville Las Cases", "Super Second Saint-Julien"],
        description="Often called the 'Super Second' of Saint-Julien; structured and ageworthy.",
    ),
    WineCatalogEntry(
        id="chateau-ducru-beaucaillou",
        name="Chateau Ducru-Beaucaillou",
        producer="Château Ducru-Beaucaillou",
        region="Saint-Julien, Bordeaux, France",
        country="France",
        appellation="Saint-Julien",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=190.0,
        price_tier="luxury",
        aliases=["Ducru Beaucaillou", "Ducru-Beaucaillou", "Ch Ducru-Beaucaillou"],
        description="Second Growth Saint-Julien celebrated for elegance and precision.",
    ),
    WineCatalogEntry(
        id="chateau-palmer",
        name="Chateau Palmer",
        producer="Château Palmer",
        region="Margaux, Bordeaux, France",
        country="France",
        appellation="Margaux",
        varietal="Cabernet Sauvignon, Merlot blend",
        wine_type="red",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Palmer", "Ch Palmer", "Château Palmer"],
        description="Third Growth regularly outperforming its classification; silky and perfumed.",
    ),
    WineCatalogEntry(
        id="chateau-montrose",
        name="Chateau Montrose",
        producer="Château Montrose",
        region="Saint-Estèphe, Bordeaux, France",
        country="France",
        appellation="Saint-Estèphe",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=120.0,
        price_tier="premium",
        aliases=["Montrose", "Ch Montrose"],
        description="Second Growth known for deep, tannic, age-worthy Saint-Estèphe.",
    ),
    WineCatalogEntry(
        id="chateau-smith-haut-lafitte",
        name="Chateau Smith Haut Lafitte",
        producer="Château Smith Haut Lafitte",
        region="Pessac-Léognan, Bordeaux, France",
        country="France",
        appellation="Pessac-Léognan",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=85.0,
        price_tier="premium",
        aliases=["Smith Haut Lafitte", "Ch Smith Haut Lafitte"],
        description="Benchmark Pessac-Léognan producing outstanding red and white.",
    ),
    WineCatalogEntry(
        id="chateau-smith-haut-lafitte-blanc",
        name="Chateau Smith Haut Lafitte Blanc",
        producer="Château Smith Haut Lafitte",
        region="Pessac-Léognan, Bordeaux, France",
        country="France",
        appellation="Pessac-Léognan",
        varietal="Sauvignon Blanc, Sauvignon Gris blend",
        wine_type="white",
        avg_retail_price=115.0,
        price_tier="premium",
        aliases=["Smith Haut Lafitte White", "Ch Smith Haut Lafitte Blanc"],
        description="One of Bordeaux's finest white wines; rich and aromatic.",
    ),
    WineCatalogEntry(
        id="chateau-dyquem",
        name="Chateau d'Yquem",
        producer="Château d'Yquem",
        region="Sauternes, Bordeaux, France",
        country="France",
        appellation="Sauternes",
        varietal="Sémillon, Sauvignon Blanc",
        wine_type="dessert",
        avg_retail_price=430.0,
        price_tier="ultra",
        aliases=["d'Yquem", "Yquem", "Chateau Yquem", "Ch d'Yquem", "D Yquem"],
        description="The world's greatest dessert wine; Premier Cru Supérieur Sauternes.",
    ),
]

# ---------------------------------------------------------------------------
# BORDEAUX – Right Bank
# ---------------------------------------------------------------------------
BORDEAUX_RIGHT = [
    WineCatalogEntry(
        id="chateau-petrus",
        name="Chateau Petrus",
        producer="Ets Jean-Pierre Moueix",
        region="Pomerol, Bordeaux, France",
        country="France",
        appellation="Pomerol",
        varietal="Merlot",
        wine_type="red",
        avg_retail_price=4200.0,
        price_tier="ultra",
        aliases=["Petrus", "Château Petrus", "Ch Petrus"],
        description="The most sought-after wine of Pomerol; virtually pure Merlot on clay soils.",
    ),
    WineCatalogEntry(
        id="le-pin",
        name="Le Pin",
        producer="Thienpont Family",
        region="Pomerol, Bordeaux, France",
        country="France",
        appellation="Pomerol",
        varietal="Merlot",
        wine_type="red",
        avg_retail_price=3800.0,
        price_tier="ultra",
        aliases=["Pin Pomerol"],
        description="Tiny, cult Pomerol estate; hedonistic and extraordinarily rare.",
    ),
    WineCatalogEntry(
        id="chateau-cheval-blanc",
        name="Chateau Cheval Blanc",
        producer="Château Cheval Blanc",
        region="Saint-Émilion, Bordeaux, France",
        country="France",
        appellation="Saint-Émilion Grand Cru Classé A",
        varietal="Cabernet Franc, Merlot blend",
        wine_type="red",
        avg_retail_price=700.0,
        price_tier="ultra",
        aliases=["Cheval Blanc", "Ch Cheval Blanc", "Château Cheval-Blanc"],
        description="Premier Grand Cru Classé A; unique Cabernet Franc-dominant blend.",
    ),
    WineCatalogEntry(
        id="chateau-ausone",
        name="Chateau Ausone",
        producer="Château Ausone",
        region="Saint-Émilion, Bordeaux, France",
        country="France",
        appellation="Saint-Émilion Grand Cru Classé A",
        varietal="Merlot, Cabernet Franc blend",
        wine_type="red",
        avg_retail_price=820.0,
        price_tier="ultra",
        aliases=["Ausone", "Ch Ausone"],
        description="Historic estate on the limestone plateau of Saint-Émilion; refined and age-worthy.",
    ),
    WineCatalogEntry(
        id="chateau-angelus",
        name="Chateau Angelus",
        producer="Château Angélus",
        region="Saint-Émilion, Bordeaux, France",
        country="France",
        appellation="Saint-Émilion Grand Cru Classé A",
        varietal="Merlot, Cabernet Franc blend",
        wine_type="red",
        avg_retail_price=360.0,
        price_tier="ultra",
        aliases=["Angelus", "Angélus", "Ch Angelus", "Château Angélus"],
        description="Premier Grand Cru Classé A; opulent, modern-style Saint-Émilion.",
    ),
    WineCatalogEntry(
        id="chateau-pavie",
        name="Chateau Pavie",
        producer="Gérard Perse",
        region="Saint-Émilion, Bordeaux, France",
        country="France",
        appellation="Saint-Émilion Grand Cru Classé A",
        varietal="Merlot, Cabernet Franc, Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=320.0,
        price_tier="ultra",
        aliases=["Pavie", "Ch Pavie"],
        description="Premier Grand Cru Classé A; rich, powerful, and controversial.",
    ),
    WineCatalogEntry(
        id="vieux-chateau-certan",
        name="Vieux Chateau Certan",
        producer="Thienpont Family",
        region="Pomerol, Bordeaux, France",
        country="France",
        appellation="Pomerol",
        varietal="Merlot, Cabernet Franc blend",
        wine_type="red",
        avg_retail_price=250.0,
        price_tier="luxury",
        aliases=["VCC", "Vieux Certan", "Vieux Château Certan"],
        description="Historic Pomerol estate; elegant, structured, and relatively undervalued.",
    ),
]

# ---------------------------------------------------------------------------
# BURGUNDY – Grand Cru Red
# ---------------------------------------------------------------------------
BURGUNDY_RED = [
    WineCatalogEntry(
        id="drc-romanee-conti",
        name="Domaine de la Romanée-Conti Romanée-Conti",
        producer="Domaine de la Romanée-Conti",
        region="Vosne-Romanée, Burgundy, France",
        country="France",
        appellation="Romanée-Conti Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=22000.0,
        price_tier="ultra",
        aliases=["DRC Romanée-Conti", "DRC RC", "Romanee Conti", "Romanée-Conti DRC"],
        description="The world's most valuable wine; monopole Grand Cru in Vosne-Romanée.",
    ),
    WineCatalogEntry(
        id="drc-la-tache",
        name="Domaine de la Romanée-Conti La Tâche",
        producer="Domaine de la Romanée-Conti",
        region="Vosne-Romanée, Burgundy, France",
        country="France",
        appellation="La Tâche Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=5500.0,
        price_tier="ultra",
        aliases=["DRC La Tache", "La Tache DRC", "La Tâche"],
        description="DRC's second monopole; complex, spicy, and supremely age-worthy.",
    ),
    WineCatalogEntry(
        id="drc-richebourg",
        name="Domaine de la Romanée-Conti Richebourg",
        producer="Domaine de la Romanée-Conti",
        region="Vosne-Romanée, Burgundy, France",
        country="France",
        appellation="Richebourg Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=3200.0,
        price_tier="ultra",
        aliases=["DRC Richebourg", "Richebourg DRC"],
        description="Grand Cru producing DRC's most voluptuous and hedonistic Pinot Noir.",
    ),
    WineCatalogEntry(
        id="drc-echezeaux",
        name="Domaine de la Romanée-Conti Echezeaux",
        producer="Domaine de la Romanée-Conti",
        region="Flagey-Échezeaux, Burgundy, France",
        country="France",
        appellation="Échezeaux Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=1400.0,
        price_tier="ultra",
        aliases=["DRC Echezeaux", "DRC Échezeaux", "Echezeaux DRC"],
        description="The most approachable (and affordable) of the DRC Grand Crus.",
    ),
    WineCatalogEntry(
        id="armand-rousseau-chambertin",
        name="Armand Rousseau Chambertin",
        producer="Domaine Armand Rousseau",
        region="Gevrey-Chambertin, Burgundy, France",
        country="France",
        appellation="Chambertin Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=2200.0,
        price_tier="ultra",
        aliases=["Rousseau Chambertin", "A Rousseau Chambertin"],
        description="The benchmark Chambertin; deep, savory, and beautifully structured.",
    ),
    WineCatalogEntry(
        id="leroy-musigny",
        name="Domaine Leroy Musigny",
        producer="Domaine Leroy",
        region="Chambolle-Musigny, Burgundy, France",
        country="France",
        appellation="Musigny Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=15000.0,
        price_tier="ultra",
        aliases=["Leroy Musigny", "Dom Leroy Musigny"],
        description="Arguably the finest Musigny; biodynamic farming producing tiny quantities.",
    ),
    WineCatalogEntry(
        id="comte-de-vogue-musigny",
        name="Comte Georges de Vogüé Musigny Vieilles Vignes",
        producer="Domaine Comte Georges de Vogüé",
        region="Chambolle-Musigny, Burgundy, France",
        country="France",
        appellation="Musigny Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=1800.0,
        price_tier="ultra",
        aliases=["de Vogüé Musigny", "Vogue Musigny", "Vogüé Musigny Vieilles Vignes"],
        description="The reference-point Musigny; the quintessence of Chambolle elegance.",
    ),
    WineCatalogEntry(
        id="dujac-clos-de-la-roche",
        name="Domaine Dujac Clos de la Roche",
        producer="Domaine Dujac",
        region="Morey-Saint-Denis, Burgundy, France",
        country="France",
        appellation="Clos de la Roche Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=900.0,
        price_tier="ultra",
        aliases=["Dujac Clos de la Roche", "Domaine Dujac CDR"],
        description="Feminine, whole-cluster-influenced Clos de la Roche from Dujac.",
    ),
    WineCatalogEntry(
        id="rousseau-clos-saint-jacques",
        name="Armand Rousseau Gevrey-Chambertin Clos Saint-Jacques",
        producer="Domaine Armand Rousseau",
        region="Gevrey-Chambertin, Burgundy, France",
        country="France",
        appellation="Gevrey-Chambertin 1er Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=1100.0,
        price_tier="ultra",
        aliases=["Rousseau Clos Saint-Jacques", "Clos St Jacques Rousseau"],
        description="Premier Cru of Grand Cru quality; consistently one of Burgundy's top wines.",
    ),
    WineCatalogEntry(
        id="ponsot-clos-saint-denis",
        name="Domaine Ponsot Clos Saint-Denis",
        producer="Domaine Ponsot",
        region="Morey-Saint-Denis, Burgundy, France",
        country="France",
        appellation="Clos Saint-Denis Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=700.0,
        price_tier="ultra",
        aliases=["Ponsot Clos Saint Denis"],
        description="Grand Cru bottled only in great vintages; ethereal, age-defying Pinot Noir.",
    ),
]

# ---------------------------------------------------------------------------
# BURGUNDY – Grand Cru / Premier Cru White
# ---------------------------------------------------------------------------
BURGUNDY_WHITE = [
    WineCatalogEntry(
        id="coche-dury-meursault-perrieres",
        name="Coche-Dury Meursault Perrières",
        producer="Domaine Coche-Dury",
        region="Meursault, Burgundy, France",
        country="France",
        appellation="Meursault 1er Cru Perrières",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=3500.0,
        price_tier="ultra",
        aliases=["Coche Dury Perrieres", "JF Coche-Dury Meursault"],
        description="The most coveted white Burgundy from one of the appellation's greatest producers.",
    ),
    WineCatalogEntry(
        id="domaine-leflaive-montrachet",
        name="Domaine Leflaive Montrachet",
        producer="Domaine Leflaive",
        region="Puligny-Montrachet, Burgundy, France",
        country="France",
        appellation="Montrachet Grand Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=3800.0,
        price_tier="ultra",
        aliases=["Leflaive Montrachet", "Dom Leflaive Montrachet"],
        description="Grand Cru Montrachet from the most celebrated white Burgundy domaine.",
    ),
    WineCatalogEntry(
        id="domaine-leflaive-chevalier-montrachet",
        name="Domaine Leflaive Chevalier-Montrachet",
        producer="Domaine Leflaive",
        region="Puligny-Montrachet, Burgundy, France",
        country="France",
        appellation="Chevalier-Montrachet Grand Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=1800.0,
        price_tier="ultra",
        aliases=["Leflaive Chevalier", "Leflaive Chevalier-Montrachet"],
        description="Mineral, precise Grand Cru Chevalier-Montrachet of extraordinary finesse.",
    ),
    WineCatalogEntry(
        id="ramonet-montrachet",
        name="Domaine Ramonet Montrachet",
        producer="Domaine Ramonet",
        region="Chassagne-Montrachet, Burgundy, France",
        country="France",
        appellation="Montrachet Grand Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=4200.0,
        price_tier="ultra",
        aliases=["Ramonet Montrachet"],
        description="Rich, powerful Montrachet produced by the legendary Ramonet family.",
    ),
    WineCatalogEntry(
        id="coche-dury-corton-charlemagne",
        name="Coche-Dury Corton-Charlemagne",
        producer="Domaine Coche-Dury",
        region="Corton, Burgundy, France",
        country="France",
        appellation="Corton-Charlemagne Grand Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=4800.0,
        price_tier="ultra",
        aliases=["Coche Dury Corton Charlemagne", "JF Coche-Dury Corton"],
        description="The single most sought-after Corton-Charlemagne; astronomically rare.",
    ),
    WineCatalogEntry(
        id="domaine-leflaive-puligny-folatières",
        name="Domaine Leflaive Puligny-Montrachet Les Folatières",
        producer="Domaine Leflaive",
        region="Puligny-Montrachet, Burgundy, France",
        country="France",
        appellation="Puligny-Montrachet 1er Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Leflaive Folatières", "Leflaive Les Folatières"],
        description="Premier Cru from Leflaive; quintessential mineral and floral Puligny.",
    ),
]

# ---------------------------------------------------------------------------
# RHÔNE VALLEY
# ---------------------------------------------------------------------------
RHONE = [
    WineCatalogEntry(
        id="guigal-la-mouline",
        name="E. Guigal Côte-Rôtie La Mouline",
        producer="E. Guigal",
        region="Côte-Rôtie, Northern Rhône, France",
        country="France",
        appellation="Côte-Rôtie",
        varietal="Syrah, Viognier",
        wine_type="red",
        avg_retail_price=550.0,
        price_tier="ultra",
        aliases=["Guigal La Mouline", "La Mouline Guigal", "Guigal Cote Rotie La Mouline"],
        description="One of the 'La Las' single-vineyard Côte-Rôties; silky and perfumed.",
    ),
    WineCatalogEntry(
        id="guigal-la-landonne",
        name="E. Guigal Côte-Rôtie La Landonne",
        producer="E. Guigal",
        region="Côte-Rôtie, Northern Rhône, France",
        country="France",
        appellation="Côte-Rôtie",
        varietal="Syrah",
        wine_type="red",
        avg_retail_price=520.0,
        price_tier="ultra",
        aliases=["Guigal La Landonne", "La Landonne Guigal"],
        description="Dark, tannic, and powerful La Las; the most structured of the three.",
    ),
    WineCatalogEntry(
        id="guigal-la-turque",
        name="E. Guigal Côte-Rôtie La Turque",
        producer="E. Guigal",
        region="Côte-Rôtie, Northern Rhône, France",
        country="France",
        appellation="Côte-Rôtie",
        varietal="Syrah, Viognier",
        wine_type="red",
        avg_retail_price=580.0,
        price_tier="ultra",
        aliases=["Guigal La Turque", "La Turque Guigal"],
        description="The rarest and most exotic of the Guigal La Las single-vineyards.",
    ),
    WineCatalogEntry(
        id="chapoutier-ermitage-le-pavillon",
        name="M. Chapoutier Ermitage Le Pavillon",
        producer="M. Chapoutier",
        region="Hermitage, Northern Rhône, France",
        country="France",
        appellation="Hermitage",
        varietal="Syrah",
        wine_type="red",
        avg_retail_price=480.0,
        price_tier="ultra",
        aliases=["Chapoutier Le Pavillon", "Ermitage Le Pavillon"],
        description="Biodynamic Hermitage from one of Rhône's most celebrated estates.",
    ),
    WineCatalogEntry(
        id="chateau-rayas",
        name="Chateau Rayas Châteauneuf-du-Pape",
        producer="Château Rayas",
        region="Châteauneuf-du-Pape, Southern Rhône, France",
        country="France",
        appellation="Châteauneuf-du-Pape",
        varietal="Grenache",
        wine_type="red",
        avg_retail_price=650.0,
        price_tier="ultra",
        aliases=["Rayas", "Château Rayas", "Ch Rayas Châteauneuf"],
        description="Legendary Châteauneuf produced entirely from old-vine Grenache; ethereal.",
    ),
    WineCatalogEntry(
        id="domaine-beaucastel",
        name="Château Beaucastel Châteauneuf-du-Pape",
        producer="Château Beaucastel",
        region="Châteauneuf-du-Pape, Southern Rhône, France",
        country="France",
        appellation="Châteauneuf-du-Pape",
        varietal="Grenache, Mourvèdre, Syrah blend",
        wine_type="red",
        avg_retail_price=95.0,
        price_tier="premium",
        aliases=["Beaucastel", "Château Beaucastel", "Beaucastel CDP"],
        description="Traditional, complex Châteauneuf with exceptional aging potential.",
    ),
    WineCatalogEntry(
        id="domaine-vieux-telegraphe",
        name="Domaine du Vieux Télégraphe Châteauneuf-du-Pape",
        producer="Domaine du Vieux Télégraphe",
        region="Châteauneuf-du-Pape, Southern Rhône, France",
        country="France",
        appellation="Châteauneuf-du-Pape",
        varietal="Grenache, Syrah, Mourvèdre blend",
        wine_type="red",
        avg_retail_price=65.0,
        price_tier="mid",
        aliases=["Vieux Telegraphe", "Vieux Télégraphe"],
        description="Benchmark Châteauneuf on the Plateau de la Crau; garrigue-scented.",
    ),
    WineCatalogEntry(
        id="guigal-cotes-du-rhone",
        name="E. Guigal Côtes du Rhône",
        producer="E. Guigal",
        region="Rhône Valley, France",
        country="France",
        appellation="Côtes du Rhône",
        varietal="Grenache, Syrah, Mourvèdre blend",
        wine_type="red",
        avg_retail_price=18.0,
        price_tier="budget",
        aliases=["Guigal CDR", "Guigal Cotes du Rhone", "Guigal Rouge"],
        description="Guigal's entry-level Côtes du Rhône; exceptional QPR from a great house.",
    ),
]

# ---------------------------------------------------------------------------
# CHAMPAGNE
# ---------------------------------------------------------------------------
CHAMPAGNE = [
    WineCatalogEntry(
        id="dom-perignon",
        name="Dom Pérignon",
        producer="Moët & Chandon",
        region="Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay, Pinot Noir blend",
        wine_type="sparkling",
        avg_retail_price=220.0,
        price_tier="luxury",
        aliases=["Dom Perignon", "DP", "Dom P", "Dom Pérignon Brut", "Moët Dom Perignon"],
        description="Iconic prestige cuvée from Moët; only produced in declared vintages.",
    ),
    WineCatalogEntry(
        id="krug-grande-cuvee",
        name="Krug Grande Cuvée",
        producer="Krug",
        region="Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay, Pinot Noir, Pinot Meunier blend",
        wine_type="sparkling",
        avg_retail_price=235.0,
        price_tier="luxury",
        aliases=["Krug GC", "Krug Grande Cuvee NV", "Krug NV"],
        description="Krug's multi-vintage prestige Champagne; complex, rich, and layered.",
    ),
    WineCatalogEntry(
        id="krug-vintage",
        name="Krug Vintage",
        producer="Krug",
        region="Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay, Pinot Noir blend",
        wine_type="sparkling",
        avg_retail_price=380.0,
        price_tier="ultra",
        aliases=["Krug Millésimé", "Krug Millesime", "Krug Vintage Champagne"],
        description="Krug's single-vintage Champagne; only made in the finest years.",
    ),
    WineCatalogEntry(
        id="cristal",
        name="Louis Roederer Cristal",
        producer="Louis Roederer",
        region="Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay, Pinot Noir blend",
        wine_type="sparkling",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Cristal Champagne", "Roederer Cristal", "Louis Roederer Cristal Brut"],
        description="Prestige cuvée in iconic flat-bottomed, clear-glass bottle.",
    ),
    WineCatalogEntry(
        id="salon-le-mesnil",
        name="Salon Le Mesnil Blanc de Blancs",
        producer="Salon",
        region="Le Mesnil-sur-Oger, Champagne, France",
        country="France",
        appellation="Champagne Blanc de Blancs",
        varietal="Chardonnay",
        wine_type="sparkling",
        avg_retail_price=550.0,
        price_tier="ultra",
        aliases=["Salon", "Salon Champagne", "Salon Blanc de Blancs Le Mesnil"],
        description="Single-vineyard, single-varietal, single-vintage Champagne; only made in ~38 years per century.",
    ),
    WineCatalogEntry(
        id="bollinger-rд",
        name="Bollinger R.D.",
        producer="Bollinger",
        region="Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Pinot Noir, Chardonnay blend",
        wine_type="sparkling",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Bollinger RD", "Bollinger Recently Disgorged", "Bollinger R.D. Brut"],
        description="Recently Disgorged Champagne; rich, oxidative, and extraordinarily complex.",
    ),
    WineCatalogEntry(
        id="taittinger-comtes",
        name="Taittinger Comtes de Champagne Blanc de Blancs",
        producer="Taittinger",
        region="Champagne, France",
        country="France",
        appellation="Champagne Blanc de Blancs",
        varietal="Chardonnay",
        wine_type="sparkling",
        avg_retail_price=155.0,
        price_tier="luxury",
        aliases=["Comtes de Champagne", "Taittinger Comtes", "Taittinger Blanc de Blancs"],
        description="One of the finest Blanc de Blancs; pure, mineral, and elegant.",
    ),
    WineCatalogEntry(
        id="veuve-clicquot-yellow-label",
        name="Veuve Clicquot Yellow Label Brut",
        producer="Veuve Clicquot",
        region="Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Pinot Noir, Chardonnay, Pinot Meunier blend",
        wine_type="sparkling",
        avg_retail_price=62.0,
        price_tier="mid",
        aliases=["Veuve Clicquot", "Yellow Label Champagne", "Clicquot NV", "VC Yellow Label"],
        description="The iconic Champagne in the yellow label; Pinot Noir-dominant NV.",
    ),
    WineCatalogEntry(
        id="moet-brut-imperial",
        name="Moët & Chandon Brut Impérial",
        producer="Moët & Chandon",
        region="Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Pinot Noir, Chardonnay, Pinot Meunier blend",
        wine_type="sparkling",
        avg_retail_price=52.0,
        price_tier="mid",
        aliases=["Moët Brut", "Moet Chandon", "Moët & Chandon NV", "Moet Imperial"],
        description="The world's best-selling Champagne; fresh, bright, and accessible.",
    ),
    WineCatalogEntry(
        id="perrier-jouet-belle-epoque",
        name="Perrier-Jouët Belle Époque",
        producer="Perrier-Jouët",
        region="Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay, Pinot Noir blend",
        wine_type="sparkling",
        avg_retail_price=145.0,
        price_tier="luxury",
        aliases=["Belle Epoque", "Perrier Jouet Belle Epoque", "Flower Bottle Champagne"],
        description="The famous flower-painted bottle; elegant, floral, and Chardonnay-driven.",
    ),
    WineCatalogEntry(
        id="billecart-salmon-blanc-de-blancs",
        name="Billecart-Salmon Blanc de Blancs",
        producer="Billecart-Salmon",
        region="Champagne, France",
        country="France",
        appellation="Champagne Blanc de Blancs",
        varietal="Chardonnay",
        wine_type="sparkling",
        avg_retail_price=95.0,
        price_tier="premium",
        aliases=["Billecart Blanc de Blancs", "Billecart-Salmon BdB"],
        description="Refined, mineral Blanc de Blancs from the beloved family house.",
    ),
]

# ---------------------------------------------------------------------------
# CALIFORNIA
# ---------------------------------------------------------------------------
CALIFORNIA = [
    WineCatalogEntry(
        id="screaming-eagle",
        name="Screaming Eagle Cabernet Sauvignon",
        producer="Screaming Eagle",
        region="Oakville, Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=5500.0,
        price_tier="ultra",
        aliases=["Screaming Eagle Cab", "SE Cabernet", "Screaming Eagle Napa"],
        description="California's most coveted cult Cabernet; 500-case production, mailing-list only.",
    ),
    WineCatalogEntry(
        id="harlan-estate",
        name="Harlan Estate",
        producer="Harlan Estate",
        region="Oakville, Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=1100.0,
        price_tier="ultra",
        aliases=["Harlan", "Harlan Napa", "Harlan Estate Cabernet"],
        description="Napa's Petrus equivalent; structured, age-worthy, and extraordinarily complex.",
    ),
    WineCatalogEntry(
        id="opus-one",
        name="Opus One",
        producer="Opus One Winery",
        region="Oakville, Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=290.0,
        price_tier="luxury",
        aliases=["Opus 1", "Opus One Napa", "Mondavi Rothschild Opus One"],
        description="The original Mondavi-Rothschild Bordeaux-style collaboration.",
    ),
    WineCatalogEntry(
        id="ridge-monte-bello",
        name="Ridge Vineyards Monte Bello",
        producer="Ridge Vineyards",
        region="Santa Cruz Mountains, California, USA",
        country="USA",
        appellation="Santa Cruz Mountains",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=130.0,
        price_tier="premium",
        aliases=["Ridge Monte Bello", "Monte Bello Cabernet", "Ridge Santa Cruz"],
        description="The 1976 Judgment of Paris winner; complex mountain Cabernet.",
    ),
    WineCatalogEntry(
        id="joseph-phelps-insignia",
        name="Joseph Phelps Insignia",
        producer="Joseph Phelps Vineyards",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=250.0,
        price_tier="luxury",
        aliases=["Phelps Insignia", "Insignia Napa", "JP Insignia"],
        description="California's first Meritage; benchmark Napa Bordeaux blend.",
    ),
    WineCatalogEntry(
        id="caymus-special-selection",
        name="Caymus Special Selection Cabernet Sauvignon",
        producer="Caymus Vineyards",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=135.0,
        price_tier="premium",
        aliases=["Caymus Special Selection", "Caymus Cab Special", "Caymus SS"],
        description="Napa legend; lush, fruit-forward, iconic Special Selection Cab.",
    ),
    WineCatalogEntry(
        id="caymus-napa",
        name="Caymus Napa Valley Cabernet Sauvignon",
        producer="Caymus Vineyards",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=95.0,
        price_tier="premium",
        aliases=["Caymus Cabernet", "Caymus Napa Cab", "Caymus"],
        description="The flagship Napa Cabernet; rich, consistent, and widely loved.",
    ),
    WineCatalogEntry(
        id="silver-oak-alexander-valley",
        name="Silver Oak Alexander Valley Cabernet Sauvignon",
        producer="Silver Oak Cellars",
        region="Alexander Valley, Sonoma, California, USA",
        country="USA",
        appellation="Alexander Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=70.0,
        price_tier="mid",
        aliases=["Silver Oak AV", "Silver Oak Alexander Valley Cab", "Silver Oak Sonoma"],
        description="The approachable, American-oak-aged Cabernet from Silver Oak.",
    ),
    WineCatalogEntry(
        id="silver-oak-napa",
        name="Silver Oak Napa Valley Cabernet Sauvignon",
        producer="Silver Oak Cellars",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=110.0,
        price_tier="premium",
        aliases=["Silver Oak Napa", "Silver Oak Napa Cab"],
        description="Richer, more complex Napa iteration of Silver Oak's signature style.",
    ),
    WineCatalogEntry(
        id="rombauer-chardonnay",
        name="Rombauer Vineyards Chardonnay",
        producer="Rombauer Vineyards",
        region="Carneros, Napa Valley, California, USA",
        country="USA",
        appellation="Carneros",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=45.0,
        price_tier="mid",
        aliases=["Rombauer Chard", "Rombauer Chardonnay Carneros"],
        description="America's most popular high-end Chardonnay; lush, buttery, and tropical.",
    ),
    WineCatalogEntry(
        id="chateau-montelena-chardonnay",
        name="Chateau Montelena Chardonnay",
        producer="Chateau Montelena",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Montelena Chardonnay", "Ch Montelena Chard"],
        description="Winner of the 1976 Judgment of Paris; restrained, Burgundian Chardonnay.",
    ),
    WineCatalogEntry(
        id="kistler-les-noisetiers",
        name="Kistler Vineyards Les Noisetiers Chardonnay",
        producer="Kistler Vineyards",
        region="Sonoma Coast, California, USA",
        country="USA",
        appellation="Sonoma Coast",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=75.0,
        price_tier="mid",
        aliases=["Kistler Chardonnay", "Kistler Les Noisetiers", "Kistler Chard"],
        description="Entry-level Kistler Chardonnay; complex, rich, and terroir-driven.",
    ),
    WineCatalogEntry(
        id="duckhorn-napa-merlot",
        name="Duckhorn Vineyards Napa Valley Merlot",
        producer="Duckhorn Vineyards",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Merlot",
        wine_type="red",
        avg_retail_price=70.0,
        price_tier="mid",
        aliases=["Duckhorn Merlot", "Duckhorn Napa Merlot"],
        description="The definitive California Merlot; velvety, concentrated, and consistent.",
    ),
    WineCatalogEntry(
        id="jordan-cabernet",
        name="Jordan Vineyard Cabernet Sauvignon",
        producer="Jordan Vineyard & Winery",
        region="Alexander Valley, Sonoma, California, USA",
        country="USA",
        appellation="Alexander Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=58.0,
        price_tier="mid",
        aliases=["Jordan Cab", "Jordan Alexander Valley", "Jordan Winery Cabernet"],
        description="Consistent, elegant Bordeaux-style Cabernet from Alexander Valley.",
    ),
    WineCatalogEntry(
        id="meiomi-pinot-noir",
        name="Meiomi Pinot Noir",
        producer="Meiomi Wines",
        region="California, USA",
        country="USA",
        appellation="California",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=22.0,
        price_tier="budget",
        aliases=["Meiomi PN", "Meiomi California Pinot"],
        description="Widely popular, fruit-forward, blended California Pinot Noir.",
    ),
    WineCatalogEntry(
        id="stags-leap-slv",
        name="Stag's Leap Wine Cellars SLV Cabernet Sauvignon",
        producer="Stag's Leap Wine Cellars",
        region="Stags Leap District, Napa Valley, California, USA",
        country="USA",
        appellation="Stags Leap District",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=115.0,
        price_tier="premium",
        aliases=["Stags Leap SLV", "Stag's Leap SLV", "SLWC SLV Cab"],
        description="The 1973 that stunned Paris in 1976; elegant, iron-fist-in-velvet-glove Napa Cab.",
    ),
]

# ---------------------------------------------------------------------------
# TUSCANY
# ---------------------------------------------------------------------------
TUSCANY = [
    WineCatalogEntry(
        id="sassicaia",
        name="Sassicaia",
        producer="Tenuta San Guido",
        region="Bolgheri, Tuscany, Italy",
        country="Italy",
        appellation="Bolgheri Sassicaia DOC",
        varietal="Cabernet Sauvignon, Cabernet Franc blend",
        wine_type="red",
        avg_retail_price=230.0,
        price_tier="luxury",
        aliases=["Sassicaia Bolgheri", "San Guido Sassicaia", "Tenuta San Guido"],
        description="Italy's original Super Tuscan; the archetype of Bolgheri Cabernet.",
    ),
    WineCatalogEntry(
        id="ornellaia",
        name="Ornellaia",
        producer="Tenuta dell'Ornellaia",
        region="Bolgheri, Tuscany, Italy",
        country="Italy",
        appellation="Bolgheri Superiore DOC",
        varietal="Cabernet Sauvignon, Merlot, Cabernet Franc blend",
        wine_type="red",
        avg_retail_price=200.0,
        price_tier="luxury",
        aliases=["Ornellaia Bolgheri", "Tenuta Ornellaia"],
        description="Complex, Merlot-inflected Super Tuscan of world-class status.",
    ),
    WineCatalogEntry(
        id="masseto",
        name="Masseto",
        producer="Tenuta dell'Ornellaia",
        region="Bolgheri, Tuscany, Italy",
        country="Italy",
        appellation="Toscana IGT",
        varietal="Merlot",
        wine_type="red",
        avg_retail_price=620.0,
        price_tier="ultra",
        aliases=["Masseto Merlot", "Masseto Bolgheri"],
        description="Italy's answer to Petrus; 100% Merlot on iron-rich clay soils.",
    ),
    WineCatalogEntry(
        id="tignanello",
        name="Tignanello",
        producer="Antinori",
        region="Tuscany, Italy",
        country="Italy",
        appellation="Toscana IGT",
        varietal="Sangiovese, Cabernet Sauvignon, Cabernet Franc",
        wine_type="red",
        avg_retail_price=90.0,
        price_tier="premium",
        aliases=["Tignanello Antinori", "Tig", "Tignnanello"],
        description="The wine that invented the Super Tuscan category; blends Sangiovese with Cabernets.",
    ),
    WineCatalogEntry(
        id="solaia",
        name="Solaia",
        producer="Antinori",
        region="Tuscany, Italy",
        country="Italy",
        appellation="Toscana IGT",
        varietal="Cabernet Sauvignon, Sangiovese, Cabernet Franc",
        wine_type="red",
        avg_retail_price=200.0,
        price_tier="luxury",
        aliases=["Solaia Antinori", "Antinori Solaia"],
        description="Antinori's Cabernet-dominant flagship; the 'big brother' of Tignanello.",
    ),
    WineCatalogEntry(
        id="biondi-santi-brunello",
        name="Biondi-Santi Brunello di Montalcino",
        producer="Biondi-Santi",
        region="Montalcino, Tuscany, Italy",
        country="Italy",
        appellation="Brunello di Montalcino DOCG",
        varietal="Sangiovese Grosso (Brunello)",
        wine_type="red",
        avg_retail_price=380.0,
        price_tier="ultra",
        aliases=["Biondi Santi Brunello", "Brunello Biondi-Santi"],
        description="The founding estate of Brunello di Montalcino; traditional, age-worthy.",
    ),
    WineCatalogEntry(
        id="giacomo-conterno-barolo-monfortino",
        name="Giacomo Conterno Barolo Monfortino",
        producer="Giacomo Conterno",
        region="Serralunga d'Alba, Piedmont, Italy",
        country="Italy",
        appellation="Barolo DOCG",
        varietal="Nebbiolo",
        wine_type="red",
        avg_retail_price=420.0,
        price_tier="ultra",
        aliases=["Conterno Monfortino", "Giacomo Conterno Barolo", "Monfortino Barolo"],
        description="Italy's most legendary Barolo; long-aged, profound, and utterly age-worthy.",
    ),
    WineCatalogEntry(
        id="gaja-barbaresco",
        name="Gaja Barbaresco",
        producer="Gaja",
        region="Barbaresco, Piedmont, Italy",
        country="Italy",
        appellation="Barbaresco DOCG",
        varietal="Nebbiolo",
        wine_type="red",
        avg_retail_price=290.0,
        price_tier="luxury",
        aliases=["Gaja Barbaresco DOC", "Angelo Gaja Barbaresco"],
        description="The wine that introduced Barbaresco to the world stage; modern-style Nebbiolo.",
    ),
    WineCatalogEntry(
        id="giuseppe-quintarelli-amarone",
        name="Giuseppe Quintarelli Amarone della Valpolicella",
        producer="Giuseppe Quintarelli",
        region="Valpolicella, Veneto, Italy",
        country="Italy",
        appellation="Amarone della Valpolicella DOCG",
        varietal="Corvina, Rondinella, Molinara blend",
        wine_type="red",
        avg_retail_price=320.0,
        price_tier="ultra",
        aliases=["Quintarelli Amarone", "Quintarelli Valpolicella"],
        description="The benchmark Amarone; traditional, concentrated, and age-defying.",
    ),
    WineCatalogEntry(
        id="gaja-sori-tildin",
        name="Gaja Sori Tildìn",
        producer="Gaja",
        region="Barbaresco, Piedmont, Italy",
        country="Italy",
        appellation="Langhe Nebbiolo DOC",
        varietal="Nebbiolo",
        wine_type="red",
        avg_retail_price=650.0,
        price_tier="ultra",
        aliases=["Sori Tildin", "Gaja Sorì Tildìn"],
        description="Single-vineyard Barbaresco declassified to Langhe; stunning age-worthy Nebbiolo.",
    ),
]

# ---------------------------------------------------------------------------
# SPAIN
# ---------------------------------------------------------------------------
SPAIN = [
    WineCatalogEntry(
        id="vega-sicilia-unico",
        name="Vega Sicilia Único",
        producer="Bodegas Vega Sicilia",
        region="Ribera del Duero, Spain",
        country="Spain",
        appellation="Ribera del Duero DO",
        varietal="Tempranillo, Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=320.0,
        price_tier="ultra",
        aliases=["Vega Sicilia Unico", "Único", "Unico Vega Sicilia"],
        description="Spain's most famous wine; aged 10+ years before release.",
    ),
    WineCatalogEntry(
        id="pingus",
        name="Dominio de Pingus",
        producer="Dominio de Pingus",
        region="Ribera del Duero, Spain",
        country="Spain",
        appellation="Ribera del Duero DO",
        varietal="Tempranillo (Tinto Fino)",
        wine_type="red",
        avg_retail_price=750.0,
        price_tier="ultra",
        aliases=["Pingus", "Dominio Pingus"],
        description="Spain's rarest cult wine; old-vine Tempranillo by Peter Sisseck.",
    ),
    WineCatalogEntry(
        id="alvaro-palacios-lermita",
        name="Álvaro Palacios L'Ermita",
        producer="Álvaro Palacios",
        region="Priorat, Catalonia, Spain",
        country="Spain",
        appellation="Priorat DOCa",
        varietal="Garnacha, Cabernet Sauvignon blend",
        wine_type="red",
        avg_retail_price=600.0,
        price_tier="ultra",
        aliases=["Palacios L'Ermita", "L Ermita Priorat", "Ermita Palacios"],
        description="Spain's answer to Petrus; old-vine Garnacha on schist soils.",
    ),
    WineCatalogEntry(
        id="la-rioja-alta-890",
        name="La Rioja Alta Gran Reserva 890",
        producer="La Rioja Alta",
        region="Rioja, Spain",
        country="Spain",
        appellation="Rioja DOCa",
        varietal="Tempranillo blend",
        wine_type="red",
        avg_retail_price=95.0,
        price_tier="premium",
        aliases=["Gran Reserva 890", "Rioja Alta 890", "La Rioja Alta GR 890"],
        description="Iconic traditional Rioja Gran Reserva; aged decades before release.",
    ),
    WineCatalogEntry(
        id="muga-prado-enea",
        name="Muga Prado Enea Gran Reserva",
        producer="Bodegas Muga",
        region="Rioja, Spain",
        country="Spain",
        appellation="Rioja DOCa",
        varietal="Tempranillo, Garnacha blend",
        wine_type="red",
        avg_retail_price=75.0,
        price_tier="mid",
        aliases=["Prado Enea", "Muga Gran Reserva", "Muga Prado Enea GR"],
        description="Traditionalist Rioja Gran Reserva of elegance and complexity.",
    ),
    WineCatalogEntry(
        id="torres-mas-la-plana",
        name="Torres Mas La Plana",
        producer="Bodegas Torres",
        region="Penedès, Catalonia, Spain",
        country="Spain",
        appellation="Penedès DO",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Mas La Plana", "Torres Black Label", "Gran Coronas Black Label"],
        description="The 1970 vintage famously beat First Growths in Paris; elegant Spanish Cabernet.",
    ),
]

# ---------------------------------------------------------------------------
# AUSTRALIA
# ---------------------------------------------------------------------------
AUSTRALIA = [
    WineCatalogEntry(
        id="penfolds-grange",
        name="Penfolds Grange",
        producer="Penfolds",
        region="South Australia, Australia",
        country="Australia",
        appellation="South Australia",
        varietal="Shiraz",
        wine_type="red",
        avg_retail_price=680.0,
        price_tier="ultra",
        aliases=["Grange", "Penfolds Grange Hermitage", "Grange Shiraz"],
        description="Australia's First Growth; monumental, age-defying Shiraz.",
    ),
    WineCatalogEntry(
        id="henschke-hill-of-grace",
        name="Henschke Hill of Grace",
        producer="Henschke",
        region="Eden Valley, South Australia, Australia",
        country="Australia",
        appellation="Eden Valley",
        varietal="Shiraz",
        wine_type="red",
        avg_retail_price=780.0,
        price_tier="ultra",
        aliases=["Hill of Grace", "Henschke HoG", "Hill of Grace Shiraz"],
        description="Old-vine, single-vineyard Shiraz; Australia's most celebrated terroir wine.",
    ),
    WineCatalogEntry(
        id="penfolds-bin-389",
        name="Penfolds Bin 389 Cabernet Shiraz",
        producer="Penfolds",
        region="South Australia, Australia",
        country="Australia",
        appellation="South Australia",
        varietal="Cabernet Sauvignon, Shiraz blend",
        wine_type="red",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Bin 389", "Penfolds 389", "Poor Man's Grange"],
        description="Often called the 'Poor Man's Grange'; outstanding QPR Cabernet-Shiraz.",
    ),
    WineCatalogEntry(
        id="penfolds-bin-407",
        name="Penfolds Bin 407 Cabernet Sauvignon",
        producer="Penfolds",
        region="South Australia, Australia",
        country="Australia",
        appellation="South Australia",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=45.0,
        price_tier="mid",
        aliases=["Bin 407", "Penfolds 407 Cab"],
        description="Multi-regional Cabernet Sauvignon; consistent and expressive.",
    ),
    WineCatalogEntry(
        id="torbreck-runrig",
        name="Torbreck RunRig",
        producer="Torbreck Vintners",
        region="Barossa Valley, South Australia, Australia",
        country="Australia",
        appellation="Barossa Valley",
        varietal="Shiraz, Viognier",
        wine_type="red",
        avg_retail_price=180.0,
        price_tier="luxury",
        aliases=["RunRig", "Torbreck Run Rig", "Torbreck Barossa"],
        description="Old-vine Barossa Shiraz co-fermented with Viognier; opulent and profound.",
    ),
    WineCatalogEntry(
        id="two-hands-ares",
        name="Two Hands Ares Shiraz",
        producer="Two Hands Wines",
        region="Barossa Valley, South Australia, Australia",
        country="Australia",
        appellation="Barossa Valley",
        varietal="Shiraz",
        wine_type="red",
        avg_retail_price=130.0,
        price_tier="premium",
        aliases=["Two Hands Ares", "Ares Shiraz"],
        description="Single-vineyard Barossa Shiraz of concentration and complexity.",
    ),
]

# ---------------------------------------------------------------------------
# NEW ZEALAND
# ---------------------------------------------------------------------------
NEW_ZEALAND = [
    WineCatalogEntry(
        id="cloudy-bay-sauvignon-blanc",
        name="Cloudy Bay Sauvignon Blanc",
        producer="Cloudy Bay Vineyards",
        region="Marlborough, New Zealand",
        country="New Zealand",
        appellation="Marlborough",
        varietal="Sauvignon Blanc",
        wine_type="white",
        avg_retail_price=28.0,
        price_tier="mid",
        aliases=["Cloudy Bay SB", "Cloudy Bay Marlborough"],
        description="The wine that put Marlborough on the world map; vibrant and herbaceous.",
    ),
    WineCatalogEntry(
        id="felton-road-pinot-noir",
        name="Felton Road Pinot Noir",
        producer="Felton Road",
        region="Central Otago, New Zealand",
        country="New Zealand",
        appellation="Central Otago",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Felton Road PN", "Felton Road Bannockburn"],
        description="Benchmark Central Otago Pinot Noir; biodynamic, precise, and age-worthy.",
    ),
    WineCatalogEntry(
        id="villa-maria-private-bin-sauv-blanc",
        name="Villa Maria Private Bin Sauvignon Blanc",
        producer="Villa Maria Estate",
        region="Marlborough, New Zealand",
        country="New Zealand",
        appellation="Marlborough",
        varietal="Sauvignon Blanc",
        wine_type="white",
        avg_retail_price=18.0,
        price_tier="budget",
        aliases=["Villa Maria SB", "Villa Maria Marlborough"],
        description="Dependable, well-priced Marlborough Sauvignon Blanc.",
    ),
]

# ---------------------------------------------------------------------------
# GERMANY / AUSTRIA
# ---------------------------------------------------------------------------
GERMANY_AUSTRIA = [
    WineCatalogEntry(
        id="jj-prum-wehlener-sonnenuhr-auslese",
        name="J.J. Prüm Wehlener Sonnenuhr Riesling Auslese",
        producer="Weingut J.J. Prüm",
        region="Mosel, Germany",
        country="Germany",
        appellation="Mosel",
        varietal="Riesling",
        wine_type="white",
        avg_retail_price=95.0,
        price_tier="premium",
        aliases=["JJ Prum Riesling", "JJ Prum Auslese", "Prüm Wehlener Sonnenuhr"],
        description="Reference Mosel Riesling Auslese; off-dry, ethereal, ages for decades.",
    ),
    WineCatalogEntry(
        id="egon-muller-scharzhofberger-auslese",
        name="Egon Müller Scharzhofberger Riesling Auslese",
        producer="Egon Müller",
        region="Saar, Mosel, Germany",
        country="Germany",
        appellation="Saar-Mosel",
        varietal="Riesling",
        wine_type="white",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Egon Mueller Auslese", "Egon Müller Scharzhofberger", "Scharzhofberger Auslese"],
        description="The most celebrated Saar Riesling estate; crystalline purity.",
    ),
    WineCatalogEntry(
        id="prager-gruner-veltliner-smaragd",
        name="Prager Grüner Veltliner Smaragd",
        producer="Weingut Prager",
        region="Wachau, Austria",
        country="Austria",
        appellation="Wachau",
        varietal="Grüner Veltliner",
        wine_type="white",
        avg_retail_price=65.0,
        price_tier="mid",
        aliases=["Prager GV", "Prager Gruner Veltliner", "Prager Wachau"],
        description="Excellent Smaragd-level Grüner Veltliner from the Wachau.",
    ),
]

# ---------------------------------------------------------------------------
# PROVENCE / LOIRE / OTHER FRANCE
# ---------------------------------------------------------------------------
OTHER_FRANCE = [
    WineCatalogEntry(
        id="whispering-angel-rose",
        name="Château d'Esclans Whispering Angel Rosé",
        producer="Château d'Esclans",
        region="Provence, France",
        country="France",
        appellation="Côtes de Provence",
        varietal="Grenache, Cinsault, Rolle blend",
        wine_type="rose",
        avg_retail_price=32.0,
        price_tier="mid",
        aliases=["Whispering Angel", "Whispering Angel Rosé", "Chateau d'Esclans Rose"],
        description="The most famous Provence rosé; pale, dry, and widely enjoyed.",
    ),
    WineCatalogEntry(
        id="henri-bourgeois-sancerre",
        name="Henri Bourgeois Sancerre La Bourgeoise",
        producer="Henri Bourgeois",
        region="Sancerre, Loire Valley, France",
        country="France",
        appellation="Sancerre AOC",
        varietal="Sauvignon Blanc",
        wine_type="white",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Bourgeois Sancerre", "Henri Bourgeois La Bourgeoise", "Sancerre La Bourgeoise"],
        description="Rich, complex Sancerre from the Loire's top Sauvignon Blanc producer.",
    ),
    WineCatalogEntry(
        id="dagueneau-pouilly-fume-silex",
        name="Didier Dagueneau Pouilly-Fumé Silex",
        producer="Didier Dagueneau",
        region="Pouilly-Fumé, Loire Valley, France",
        country="France",
        appellation="Pouilly-Fumé AOC",
        varietal="Sauvignon Blanc",
        wine_type="white",
        avg_retail_price=130.0,
        price_tier="premium",
        aliases=["Dagueneau Silex", "Silex Pouilly Fume"],
        description="The cult Pouilly-Fumé; flint-mineral, age-worthy Sauvignon Blanc.",
    ),
    WineCatalogEntry(
        id="domaine-trimbach-clos-sainte-hune",
        name="Domaine Trimbach Riesling Clos Sainte Hune",
        producer="Trimbach",
        region="Alsace, France",
        country="France",
        appellation="Alsace AOC",
        varietal="Riesling",
        wine_type="white",
        avg_retail_price=200.0,
        price_tier="luxury",
        aliases=["Trimbach Clos Sainte Hune", "Clos Sainte Hune", "Trimbach CSH"],
        description="One of the world's great Rieslings; mineral, structured, ages for 30+ years.",
    ),
]

# ---------------------------------------------------------------------------
# ENTRY-LEVEL / WIDELY DISTRIBUTED (important for markup testing)
# ---------------------------------------------------------------------------
ENTRY_LEVEL = [
    WineCatalogEntry(
        id="kim-crawford-sauvignon-blanc",
        name="Kim Crawford Sauvignon Blanc",
        producer="Kim Crawford Wines",
        region="Marlborough, New Zealand",
        country="New Zealand",
        appellation="Marlborough",
        varietal="Sauvignon Blanc",
        wine_type="white",
        avg_retail_price=18.0,
        price_tier="budget",
        aliases=["Kim Crawford SB", "KC Sauvignon Blanc", "Kim Crawford Marlborough"],
        description="Perennially popular New Zealand Sauvignon Blanc; crisp and citrusy.",
    ),
    WineCatalogEntry(
        id="kendall-jackson-chardonnay",
        name="Kendall-Jackson Vintner's Reserve Chardonnay",
        producer="Kendall-Jackson",
        region="California, USA",
        country="USA",
        appellation="California",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=20.0,
        price_tier="budget",
        aliases=["KJ Chardonnay", "K-J Chard", "Kendall Jackson Chard VR"],
        description="America's best-selling Chardonnay; soft, off-dry, lightly oaked.",
    ),
    WineCatalogEntry(
        id="la-marca-prosecco",
        name="La Marca Prosecco",
        producer="La Marca",
        region="Veneto, Italy",
        country="Italy",
        appellation="Prosecco DOC",
        varietal="Glera",
        wine_type="sparkling",
        avg_retail_price=17.0,
        price_tier="budget",
        aliases=["La Marca", "La Marca Prosecco DOC"],
        description="Widely distributed, crowd-pleasing Italian Prosecco.",
    ),
    WineCatalogEntry(
        id="josh-cabernet",
        name="Josh Cellars Cabernet Sauvignon",
        producer="Josh Cellars",
        region="California, USA",
        country="USA",
        appellation="California",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=17.0,
        price_tier="budget",
        aliases=["Josh Cab", "Josh Cabernet"],
        description="Popular, everyday-drinking California Cabernet Sauvignon.",
    ),
    WineCatalogEntry(
        id="chateau-ste-michelle-riesling",
        name="Chateau Ste. Michelle Riesling",
        producer="Chateau Ste. Michelle",
        region="Columbia Valley, Washington, USA",
        country="USA",
        appellation="Columbia Valley",
        varietal="Riesling",
        wine_type="white",
        avg_retail_price=14.0,
        price_tier="budget",
        aliases=["Ste Michelle Riesling", "CSM Riesling", "Chateau Ste Michelle Columbia Valley Riesling"],
        description="Washington state's best-value Riesling; off-dry and widely available.",
    ),
    WineCatalogEntry(
        id="santa-margherita-pinot-grigio",
        name="Santa Margherita Pinot Grigio",
        producer="Santa Margherita",
        region="Alto Adige, Italy",
        country="Italy",
        appellation="Alto Adige DOC",
        varietal="Pinot Grigio",
        wine_type="white",
        avg_retail_price=25.0,
        price_tier="mid",
        aliases=["Santa Margherita PG", "Santa Margherita Alto Adige"],
        description="The wine that popularized Pinot Grigio in the US; clean and crisp.",
    ),
    WineCatalogEntry(
        id="malbec-catena",
        name="Catena Zapata Adrianna Vineyard Malbec",
        producer="Catena Zapata",
        region="Mendoza, Argentina",
        country="Argentina",
        appellation="Mendoza",
        varietal="Malbec",
        wine_type="red",
        avg_retail_price=180.0,
        price_tier="luxury",
        aliases=["Catena Adrianna Malbec", "Adrianna Vineyard Malbec", "Catena Zapata Adrianna"],
        description="Argentina's most prestigious single-vineyard Malbec at high altitude.",
    ),
    WineCatalogEntry(
        id="zuccardi-valle-de-uco",
        name="Zuccardi Valle de Uco Malbec",
        producer="Familia Zuccardi",
        region="Mendoza, Argentina",
        country="Argentina",
        appellation="Valle de Uco",
        varietal="Malbec",
        wine_type="red",
        avg_retail_price=38.0,
        price_tier="mid",
        aliases=["Zuccardi Malbec", "Zuccardi Uco Valley"],
        description="Outstanding high-altitude Malbec from Mendoza's Valle de Uco.",
    ),
]

# ---------------------------------------------------------------------------
# BURGUNDY – Additional micro-producers
# ---------------------------------------------------------------------------
BURGUNDY_CULT = [
    # Jean-Yves Bizot
    WineCatalogEntry(
        id="bizot-vosne-romanee",
        name="Bizot Vosne-Romanée",
        producer="Jean-Yves Bizot",
        region="Vosne-Romanée, Burgundy, France",
        country="France",
        appellation="Vosne-Romanée",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=5653.0,
        price_tier="ultra",
        aliases=["Bizot Vosne", "JY Bizot Vosne-Romanée", "Domaine Bizot Vosne-Romanée"],
        description="Micro-négociant Jean-Yves Bizot produces some of Vosne-Romanée's most coveted village wines. Tiny production, allocation only.",
    ),
    WineCatalogEntry(
        id="bizot-echezeaux",
        name="Bizot Echézeaux",
        producer="Jean-Yves Bizot",
        region="Flagey-Échézeaux, Burgundy, France",
        country="France",
        appellation="Echézeaux Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=7871.0,
        price_tier="ultra",
        aliases=["Bizot Echezeaux", "JY Bizot Echezeaux", "Domaine Bizot Echézeaux"],
        description="Grand Cru Echézeaux from Bizot's micro-domaine; among Burgundy's most sought-after allocations.",
    ),
    # Frédéric Mugnier
    WineCatalogEntry(
        id="mugnier-musigny",
        name="Domaine Mugnier Musigny",
        producer="Domaine Jacques-Frédéric Mugnier",
        region="Chambolle-Musigny, Burgundy, France",
        country="France",
        appellation="Musigny Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=2200.0,
        price_tier="ultra",
        aliases=["Mugnier Musigny", "Jacques-Frederic Mugnier Musigny", "JF Mugnier Musigny"],
        description="Frederic Mugnier's Musigny is considered one of the finest expressions of the grand cru; tiny production of around 500 cases.",
    ),
    WineCatalogEntry(
        id="mugnier-chambolle",
        name="Domaine Mugnier Chambolle-Musigny Les Amoureuses",
        producer="Domaine Jacques-Frédéric Mugnier",
        region="Chambolle-Musigny, Burgundy, France",
        country="France",
        appellation="Chambolle-Musigny Premier Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=900.0,
        price_tier="ultra",
        aliases=["Mugnier Amoureuses", "Mugnier Les Amoureuses", "JF Mugnier Amoureuses"],
        description="Les Amoureuses is arguably Burgundy's finest premier cru; Mugnier's version commands grand cru prices.",
    ),
    # Georges Roumier
    WineCatalogEntry(
        id="roumier-musigny",
        name="Domaine Georges Roumier Musigny",
        producer="Domaine Georges Roumier",
        region="Chambolle-Musigny, Burgundy, France",
        country="France",
        appellation="Musigny Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=8000.0,
        price_tier="ultra",
        aliases=["Roumier Musigny", "Georges Roumier Musigny"],
        description="Roumier's Musigny from a tiny 0.1-hectare parcel is one of the rarest and most expensive Burgundies produced.",
    ),
    WineCatalogEntry(
        id="roumier-amoureuses",
        name="Domaine Georges Roumier Chambolle-Musigny Les Amoureuses",
        producer="Domaine Georges Roumier",
        region="Chambolle-Musigny, Burgundy, France",
        country="France",
        appellation="Chambolle-Musigny Premier Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=2800.0,
        price_tier="ultra",
        aliases=["Roumier Amoureuses", "Georges Roumier Amoureuses"],
        description="Roumier's Les Amoureuses consistently exceeds grand cru prices at auction.",
    ),
    # Méo-Camuzet
    WineCatalogEntry(
        id="meo-camuzet-cros-parantoux",
        name="Méo-Camuzet Vosne-Romanée Cros Parantoux",
        producer="Domaine Méo-Camuzet",
        region="Vosne-Romanée, Burgundy, France",
        country="France",
        appellation="Vosne-Romanée Premier Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=3500.0,
        price_tier="ultra",
        aliases=["Meo-Camuzet Cros Parantoux", "Meo Camuzet Cros Parantoux", "Cros Parantoux Meo"],
        description="Cros Parantoux was made famous by Henri Jayer; Méo-Camuzet now farms it producing one of Burgundy's most coveted premier crus.",
    ),
    WineCatalogEntry(
        id="meo-camuzet-vosne",
        name="Méo-Camuzet Vosne-Romanée Les Chaumes",
        producer="Domaine Méo-Camuzet",
        region="Vosne-Romanée, Burgundy, France",
        country="France",
        appellation="Vosne-Romanée Premier Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=380.0,
        price_tier="luxury",
        aliases=["Meo-Camuzet Chaumes", "Meo Camuzet Les Chaumes"],
        description="Village premier cru from one of Vosne-Romanée's leading domaines.",
    ),
    # Emmanuel Rouget
    WineCatalogEntry(
        id="rouget-cros-parantoux",
        name="Emmanuel Rouget Vosne-Romanée Cros Parantoux",
        producer="Emmanuel Rouget",
        region="Vosne-Romanée, Burgundy, France",
        country="France",
        appellation="Vosne-Romanée Premier Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=2800.0,
        price_tier="ultra",
        aliases=["Rouget Cros Parantoux", "Emmanuel Rouget Cros Parantoux"],
        description="Henri Jayer's nephew Emmanuel Rouget carries on the legacy at Cros Parantoux; prices approach those of grand crus.",
    ),
    # Sylvain Cathiard
    WineCatalogEntry(
        id="cathiard-romanee-saint-vivant",
        name="Domaine Sylvain Cathiard Romanée-Saint-Vivant",
        producer="Domaine Sylvain Cathiard",
        region="Vosne-Romanée, Burgundy, France",
        country="France",
        appellation="Romanée-Saint-Vivant Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=3200.0,
        price_tier="ultra",
        aliases=["Cathiard Romanee Saint Vivant", "Cathiard RSV"],
        description="Cathiard's Romanée-Saint-Vivant is a cult favourite: pure, precise, and made in tiny quantities.",
    ),
    WineCatalogEntry(
        id="cathiard-malconsorts",
        name="Domaine Sylvain Cathiard Vosne-Romanée Les Malconsorts",
        producer="Domaine Sylvain Cathiard",
        region="Vosne-Romanée, Burgundy, France",
        country="France",
        appellation="Vosne-Romanée Premier Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=1200.0,
        price_tier="ultra",
        aliases=["Cathiard Malconsorts", "Cathiard Les Malconsorts"],
        description="Les Malconsorts borders La Tâche; Cathiard's version commands some of Burgundy's highest premier cru prices.",
    ),
    # Domaine Roulot
    WineCatalogEntry(
        id="roulot-meursault-perrieres",
        name="Domaine Roulot Meursault Perrières",
        producer="Domaine Roulot",
        region="Meursault, Burgundy, France",
        country="France",
        appellation="Meursault Premier Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=750.0,
        price_tier="ultra",
        aliases=["Roulot Perrieres", "Roulot Meursault Perrieres", "Jean-Marc Roulot Perrieres"],
        description="Jean-Marc Roulot's Meursault Perrières is the benchmark for the appellation; regularly fetches two to three times release price.",
    ),
    WineCatalogEntry(
        id="roulot-meursault-charmes",
        name="Domaine Roulot Meursault Charmes",
        producer="Domaine Roulot",
        region="Meursault, Burgundy, France",
        country="France",
        appellation="Meursault Premier Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=450.0,
        price_tier="luxury",
        aliases=["Roulot Charmes", "Roulot Meursault Charmes"],
        description="One of Meursault's most sought-after premiers crus from Burgundy's most acclaimed white wine domaine.",
    ),
    # Domaine des Comtes Lafon
    WineCatalogEntry(
        id="comtes-lafon-montrachet",
        name="Domaine des Comtes Lafon Montrachet",
        producer="Domaine des Comtes Lafon",
        region="Puligny-Montrachet, Burgundy, France",
        country="France",
        appellation="Montrachet Grand Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=3200.0,
        price_tier="ultra",
        aliases=["Comtes Lafon Montrachet", "Lafon Montrachet"],
        description="Domaine des Comtes Lafon's Montrachet is among the handful of great white Burgundy grand crus.",
    ),
    WineCatalogEntry(
        id="comtes-lafon-meursault-perrieres",
        name="Domaine des Comtes Lafon Meursault Perrières",
        producer="Domaine des Comtes Lafon",
        region="Meursault, Burgundy, France",
        country="France",
        appellation="Meursault Premier Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=600.0,
        price_tier="ultra",
        aliases=["Lafon Perrieres", "Comtes Lafon Perrieres"],
        description="Considered the finest premier cru in Meursault; Lafon's version is one of the most sought-after.",
    ),
    # Pierre-Yves Colin-Morey
    WineCatalogEntry(
        id="colin-morey-puligny",
        name="Pierre-Yves Colin-Morey Puligny-Montrachet Les Demoiselles",
        producer="Pierre-Yves Colin-Morey",
        region="Puligny-Montrachet, Burgundy, France",
        country="France",
        appellation="Puligny-Montrachet Premier Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=380.0,
        price_tier="luxury",
        aliases=["Colin-Morey Puligny", "PYCM Puligny Demoiselles", "PYCM Demoiselles"],
        description="Pierre-Yves Colin-Morey is one of Burgundy's most celebrated young winemakers; cult following for his precision whites.",
    ),
    # Domaine Marquis d'Angerville
    WineCatalogEntry(
        id="dangerville-volnay-champans",
        name="Domaine Marquis d'Angerville Volnay Champans",
        producer="Domaine Marquis d'Angerville",
        region="Volnay, Burgundy, France",
        country="France",
        appellation="Volnay Premier Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=350.0,
        price_tier="luxury",
        aliases=["Angerville Champans", "Marquis d'Angerville Champans", "D'Angerville Volnay"],
        description="Marquis d'Angerville is Volnay's reference domaine; Champans is their flagship premier cru.",
    ),
    # Jean-Marie Fourrier
    WineCatalogEntry(
        id="fourrier-gevrey-chambertin",
        name="Domaine Fourrier Gevrey-Chambertin Clos Saint-Jacques",
        producer="Domaine Fourrier",
        region="Gevrey-Chambertin, Burgundy, France",
        country="France",
        appellation="Gevrey-Chambertin Premier Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=600.0,
        price_tier="ultra",
        aliases=["Fourrier Clos Saint-Jacques", "Fourrier Gevrey", "Jean-Marie Fourrier Gevrey"],
        description="Jean-Marie Fourrier's Clos Saint-Jacques is one of Gevrey's finest premiers crus, commanding grand cru prices.",
    ),
    # Domaine d'Auvenay
    WineCatalogEntry(
        id="dauvenay-bonnes-mares",
        name="Domaine d'Auvenay Bonnes-Mares",
        producer="Domaine d'Auvenay",
        region="Chambolle-Musigny, Burgundy, France",
        country="France",
        appellation="Bonnes-Mares Grand Cru",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=6500.0,
        price_tier="ultra",
        aliases=["D'Auvenay Bonnes-Mares", "Auvenay Bonnes Mares", "Lalou Bize Leroy Bonnes Mares"],
        description="Lalou Bize-Leroy's personal domaine; among the most expensive and sought-after Burgundies produced.",
    ),
    # Etienne Sauzet
    WineCatalogEntry(
        id="sauzet-puligny",
        name="Domaine Etienne Sauzet Puligny-Montrachet Les Combettes",
        producer="Domaine Etienne Sauzet",
        region="Puligny-Montrachet, Burgundy, France",
        country="France",
        appellation="Puligny-Montrachet Premier Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Sauzet Combettes", "Etienne Sauzet Puligny", "Sauzet Puligny Combettes"],
        description="One of the great white Burgundy producers; Les Combettes is a powerful, age-worthy premier cru.",
    ),
    # Bonneau du Martray
    WineCatalogEntry(
        id="bonneau-du-martray-corton-charlemagne",
        name="Bonneau du Martray Corton-Charlemagne",
        producer="Bonneau du Martray",
        region="Corton, Burgundy, France",
        country="France",
        appellation="Corton-Charlemagne Grand Cru",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=350.0,
        price_tier="luxury",
        aliases=["Bonneau du Martray Corton", "Martray Corton-Charlemagne"],
        description="The only domaine to own nothing but Corton-Charlemagne; a singular expression of the grand cru. Purchased by Stan Kroenke in 2017.",
    ),
]

# ---------------------------------------------------------------------------
# CHAMPAGNE – Grower producers (Récoltant-Manipulant)
# ---------------------------------------------------------------------------
CHAMPAGNE_GROWERS = [
    WineCatalogEntry(
        id="selosse-substance",
        name="Jacques Selosse Substance Blanc de Blancs",
        producer="Jacques Selosse",
        region="Avize, Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay",
        wine_type="sparkling",
        avg_retail_price=500.0,
        price_tier="ultra",
        aliases=["Selosse Substance", "Jacques Selosse Blanc de Blancs", "Anselme Selosse"],
        description="Anselme Selosse's Substance is a perpetual solera Blanc de Blancs; the most influential grower Champagne and the reference for the RM movement.",
    ),
    WineCatalogEntry(
        id="selosse-initial",
        name="Jacques Selosse Initial Blanc de Blancs",
        producer="Jacques Selosse",
        region="Avize, Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay",
        wine_type="sparkling",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Selosse Initial", "Jacques Selosse NV Blanc de Blancs"],
        description="Selosse's entry-level expression; one of the most sought-after non-vintage Champagnes.",
    ),
    WineCatalogEntry(
        id="egly-ouriet-grand-cru",
        name="Egly-Ouriet Grand Cru Blanc de Noirs",
        producer="Egly-Ouriet",
        region="Ambonnay, Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Pinot Noir",
        wine_type="sparkling",
        avg_retail_price=180.0,
        price_tier="luxury",
        aliases=["Egly Ouriet Blanc de Noirs", "Egly-Ouriet BdN", "Egly Ouriet NV"],
        description="Francis Egly's Pinot Noir-dominant Champagne from Ambonnay grand cru; powerful, vinous, age-worthy.",
    ),
    WineCatalogEntry(
        id="egly-ouriet-vp",
        name="Egly-Ouriet VP Vieilles Vignes",
        producer="Egly-Ouriet",
        region="Ambonnay, Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Pinot Noir",
        wine_type="sparkling",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Egly-Ouriet Vieilles Vignes", "Egly Ouriet VP"],
        description="Very old vine cuvée from Egly-Ouriet; among the most sought-after grower Champagnes.",
    ),
    WineCatalogEntry(
        id="pierre-peters-cuvee-de-reserve",
        name="Pierre Peters Cuvée de Réserve Blanc de Blancs",
        producer="Pierre Peters",
        region="Le Mesnil-sur-Oger, Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay",
        wine_type="sparkling",
        avg_retail_price=80.0,
        price_tier="premium",
        aliases=["Pierre Peters Blanc de Blancs", "Peters Cuvee de Reserve"],
        description="Classic grower Champagne from one of Le Mesnil's finest estates; precise, mineral Blanc de Blancs.",
    ),
    WineCatalogEntry(
        id="larmandier-bernier-longitude",
        name="Larmandier-Bernier Longitude Blanc de Blancs",
        producer="Larmandier-Bernier",
        region="Vertus, Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay",
        wine_type="sparkling",
        avg_retail_price=75.0,
        price_tier="mid",
        aliases=["Larmandier Longitude", "Larmandier Bernier Blanc de Blancs"],
        description="One of the finest biodynamic grower Champagne estates; Longitude showcases the Côte des Blancs terroir.",
    ),
    WineCatalogEntry(
        id="agrapart-7-crus",
        name="Agrapart 7 Crus Blanc de Blancs",
        producer="Agrapart & Fils",
        region="Avize, Champagne, France",
        country="France",
        appellation="Champagne",
        varietal="Chardonnay",
        wine_type="sparkling",
        avg_retail_price=80.0,
        price_tier="premium",
        aliases=["Agrapart 7 Crus", "Agrapart Blanc de Blancs"],
        description="Pascal Agrapart's 7 Crus blends fruit from seven villages; the top grower Champagne estate in Avize.",
    ),
]

# ---------------------------------------------------------------------------
# BORDEAUX – Additional châteaux
# ---------------------------------------------------------------------------
BORDEAUX_ADDITIONS = [
    WineCatalogEntry(
        id="chateau-lafleur",
        name="Château Lafleur",
        producer="Famille Guinaudeau",
        region="Pomerol, Bordeaux, France",
        country="France",
        appellation="Pomerol",
        varietal="Merlot",
        wine_type="red",
        avg_retail_price=2500.0,
        price_tier="ultra",
        aliases=["Lafleur Pomerol", "Chateau Lafleur Pomerol", "Guinaudeau Lafleur"],
        description="Pomerol's other $2,000+ wine; tiny production from a 4.5-hectare plot adjacent to Petrus with a high proportion of old-vine Cabernet Franc.",
    ),
    WineCatalogEntry(
        id="la-mission-haut-brion",
        name="Château La Mission Haut-Brion",
        producer="Domaine Clarence Dillon",
        region="Pessac-Léognan, Bordeaux, France",
        country="France",
        appellation="Pessac-Léognan",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=500.0,
        price_tier="ultra",
        aliases=["La Mission Haut-Brion", "Mission Haut Brion", "LMHB"],
        description="Neighbour and rival to Haut-Brion; produces one of Pessac-Léognan's greatest reds from Clarence Dillon estates.",
    ),
    WineCatalogEntry(
        id="pichon-lalande",
        name="Château Pichon Baron Comtesse de Lalande",
        producer="Champagnes & Châteaux",
        region="Pauillac, Bordeaux, France",
        country="France",
        appellation="Pauillac",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=170.0,
        price_tier="luxury",
        aliases=["Pichon Lalande", "Pichon Comtesse", "Chateau Pichon Lalande"],
        description="One of Pauillac's two Pichon châteaux; often described as the most feminine and perfumed wine in the appellation.",
    ),
    WineCatalogEntry(
        id="pontet-canet",
        name="Château Pontet-Canet",
        producer="Famille Tesseron",
        region="Pauillac, Bordeaux, France",
        country="France",
        appellation="Pauillac",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=140.0,
        price_tier="premium",
        aliases=["Pontet-Canet Pauillac", "Chateau Pontet Canet"],
        description="A Pauillac fifth growth that consistently outperforms its classification; one of Bordeaux's leading biodynamic estates.",
    ),
    WineCatalogEntry(
        id="haut-bailly",
        name="Château Haut-Bailly",
        producer="Famille Wilmers",
        region="Pessac-Léognan, Bordeaux, France",
        country="France",
        appellation="Pessac-Léognan",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=120.0,
        price_tier="premium",
        aliases=["Haut-Bailly", "Chateau Haut Bailly"],
        description="One of Pessac-Léognan's most elegant and consistent performers; known for early approachability and finesse.",
    ),
    WineCatalogEntry(
        id="leoville-barton",
        name="Château Léoville Barton",
        producer="Famille Barton",
        region="Saint-Julien, Bordeaux, France",
        country="France",
        appellation="Saint-Julien",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=100.0,
        price_tier="premium",
        aliases=["Leoville Barton", "Chateau Leoville Barton"],
        description="One of Saint-Julien's finest wines and arguably the greatest value among Bordeaux's second growths.",
    ),
    WineCatalogEntry(
        id="figeac",
        name="Château Figeac",
        producer="Famille Manoncourt",
        region="Saint-Émilion, Bordeaux, France",
        country="France",
        appellation="Saint-Émilion Grand Cru Classé A",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=320.0,
        price_tier="luxury",
        aliases=["Figeac Saint-Emilion", "Chateau Figeac"],
        description="Recently elevated to Saint-Émilion's highest tier; distinguished by a high Cabernet Sauvignon and Cabernet Franc blend unusual for the Right Bank.",
    ),
]

# ---------------------------------------------------------------------------
# ITALY – Cult producers
# ---------------------------------------------------------------------------
ITALY_CULT = [
    # Barolo / Piedmont
    WineCatalogEntry(
        id="bruno-giacosa-barolo-falletto",
        name="Bruno Giacosa Barolo Falletto",
        producer="Bruno Giacosa",
        region="Serralunga d'Alba, Piedmont, Italy",
        country="Italy",
        appellation="Barolo DOCG",
        varietal="Nebbiolo",
        wine_type="red",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Giacosa Barolo Falletto", "Bruno Giacosa Falletto di Serralunga"],
        description="Bruno Giacosa is considered one of Barolo's greatest producers; Falletto di Serralunga is his most important single-vineyard holding.",
    ),
    WineCatalogEntry(
        id="bruno-giacosa-barolo-reserve",
        name="Bruno Giacosa Barolo Falletto Riserva",
        producer="Bruno Giacosa",
        region="Serralunga d'Alba, Piedmont, Italy",
        country="Italy",
        appellation="Barolo DOCG Riserva",
        varietal="Nebbiolo",
        wine_type="red",
        avg_retail_price=600.0,
        price_tier="ultra",
        aliases=["Giacosa Barolo Riserva", "Bruno Giacosa Red Label"],
        description="Only produced in exceptional vintages (the 'red label'); among Italy's most sought-after wines.",
    ),
    WineCatalogEntry(
        id="bartolo-mascarello-barolo",
        name="Bartolo Mascarello Barolo",
        producer="Bartolo Mascarello",
        region="Barolo, Piedmont, Italy",
        country="Italy",
        appellation="Barolo DOCG",
        varietal="Nebbiolo",
        wine_type="red",
        avg_retail_price=380.0,
        price_tier="luxury",
        aliases=["Mascarello Barolo", "Bartolo Mascarello"],
        description="The legendary traditionalist Barolo producer; a blend of four vineyards, consistently producing one of the greatest Italian reds.",
    ),
    WineCatalogEntry(
        id="giuseppe-mascarello-monprivato",
        name="Giuseppe Mascarello Barolo Monprivato",
        producer="Giuseppe Mascarello e Figlio",
        region="Castiglione Falletto, Piedmont, Italy",
        country="Italy",
        appellation="Barolo DOCG",
        varietal="Nebbiolo",
        wine_type="red",
        avg_retail_price=250.0,
        price_tier="luxury",
        aliases=["Mascarello Monprivato", "Giuseppe Mascarello Barolo", "Monprivato Barolo"],
        description="Monprivato is Mauro Mascarello's monopole vineyard in Castiglione Falletto; one of the most age-worthy Barolos.",
    ),
    WineCatalogEntry(
        id="roberto-voerzio-barolo",
        name="Roberto Voerzio Barolo La Serra",
        producer="Roberto Voerzio",
        region="La Morra, Piedmont, Italy",
        country="Italy",
        appellation="Barolo DOCG",
        varietal="Nebbiolo",
        wine_type="red",
        avg_retail_price=420.0,
        price_tier="luxury",
        aliases=["Voerzio Barolo La Serra", "Roberto Voerzio La Serra"],
        description="Roberto Voerzio's micro-production Barolos are among the most sought-after in the denomination; tiny yields produce intensely concentrated wines.",
    ),
    WineCatalogEntry(
        id="sandrone-barolo-cannubi",
        name="Luciano Sandrone Barolo Cannubi Boschis",
        producer="Luciano Sandrone",
        region="Barolo, Piedmont, Italy",
        country="Italy",
        appellation="Barolo DOCG",
        varietal="Nebbiolo",
        wine_type="red",
        avg_retail_price=220.0,
        price_tier="luxury",
        aliases=["Sandrone Barolo", "Sandrone Cannubi Boschis", "Luciano Sandrone Cannubi"],
        description="Luciano Sandrone's flagship; from the Cannubi Boschis vineyard in the village of Barolo, one of the denomination's most celebrated crus.",
    ),
    # Bolgheri
    WineCatalogEntry(
        id="le-macchiole-messorio",
        name="Le Macchiole Messorio",
        producer="Le Macchiole",
        region="Bolgheri, Tuscany, Italy",
        country="Italy",
        appellation="Bolgheri Rosso DOC",
        varietal="Merlot",
        wine_type="red",
        avg_retail_price=350.0,
        price_tier="luxury",
        aliases=["Macchiole Messorio", "Le Macchiole Merlot"],
        description="100% Merlot from Bolgheri; Le Macchiole's Messorio is Italy's most celebrated Merlot and a Super Tuscan icon.",
    ),
    WineCatalogEntry(
        id="le-macchiole-scrio",
        name="Le Macchiole Scrio",
        producer="Le Macchiole",
        region="Bolgheri, Tuscany, Italy",
        country="Italy",
        appellation="Bolgheri Rosso DOC",
        varietal="Syrah",
        wine_type="red",
        avg_retail_price=320.0,
        price_tier="luxury",
        aliases=["Macchiole Scrio", "Le Macchiole Syrah"],
        description="100% Syrah from Bolgheri; one of Italy's finest and most unique expressions of the grape.",
    ),
    # Valpolicella
    WineCatalogEntry(
        id="dal-forno-amarone",
        name="Dal Forno Romano Amarone della Valpolicella",
        producer="Dal Forno Romano",
        region="Valpolicella, Veneto, Italy",
        country="Italy",
        appellation="Amarone della Valpolicella DOCG",
        varietal="Corvina",
        wine_type="red",
        avg_retail_price=500.0,
        price_tier="ultra",
        aliases=["Dal Forno Amarone", "Romano Dal Forno Amarone"],
        description="Possibly the most concentrated and age-worthy Amarone produced; Romano Dal Forno's wines are in limited supply and much sought-after.",
    ),
    # Chianti
    WineCatalogEntry(
        id="montevertine-pergole-torte",
        name="Montevertine Le Pergole Torte",
        producer="Montevertine",
        region="Radda in Chianti, Tuscany, Italy",
        country="Italy",
        appellation="Toscana IGT",
        varietal="Sangiovese",
        wine_type="red",
        avg_retail_price=110.0,
        price_tier="premium",
        aliases=["Montevertine Le Pergole Torte", "Le Pergole Torte"],
        description="Martinelli's legendary 100% Sangiovese; one of the catalysts for the Super Tuscan movement and a reference wine for Chianti Classico territory.",
    ),
    # Brunello
    WineCatalogEntry(
        id="poggio-di-sotto-brunello",
        name="Poggio di Sotto Brunello di Montalcino",
        producer="Poggio di Sotto",
        region="Montalcino, Tuscany, Italy",
        country="Italy",
        appellation="Brunello di Montalcino DOCG",
        varietal="Sangiovese",
        wine_type="red",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Poggio di Sotto Brunello", "Poggio di Sotto Montalcino"],
        description="One of the great traditional-style Brunello estates; exceptional purity and age-worthiness from certified biodynamic vineyards.",
    ),
]

# ---------------------------------------------------------------------------
# SPAIN – Cult producers
# ---------------------------------------------------------------------------
SPAIN_CULT = [
    WineCatalogEntry(
        id="contador-rioja",
        name="Contador",
        producer="Benjamín Romeo",
        region="Rioja, Spain",
        country="Spain",
        appellation="Rioja DOCa",
        varietal="Tempranillo",
        wine_type="red",
        avg_retail_price=650.0,
        price_tier="ultra",
        aliases=["Benjamin Romeo Contador", "Romeo Contador"],
        description="Benjamín Romeo's Contador is Rioja's most expensive wine; single-vineyard Tempranillo from San Vicente de la Sonsierra, produced in micro quantities.",
    ),
    WineCatalogEntry(
        id="clos-erasmus",
        name="Clos Erasmus",
        producer="Daphne Glorian",
        region="Priorat, Catalonia, Spain",
        country="Spain",
        appellation="Priorat DOCa",
        varietal="Grenache",
        wine_type="red",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Clos Erasmus Priorat", "Erasmus Priorat"],
        description="Daphne Glorian's single-hectare estate is one of Priorat's original cult wines; intense, old-vine Grenache from schist soils.",
    ),
    WineCatalogEntry(
        id="artadi-pagos-viejos",
        name="Artadi Viñas de Gain",
        producer="Bodegas Artadi",
        region="Rioja, Spain",
        country="Spain",
        appellation="Rioja DOCa",
        varietal="Tempranillo",
        wine_type="red",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Artadi Rioja", "Artadi Vinas de Gain"],
        description="One of Rioja's most acclaimed modern producers; single-vineyard wines that led to the movement to reclassify Rioja by cru.",
    ),
    WineCatalogEntry(
        id="aalto-ribera",
        name="Aalto Ribera del Duero",
        producer="Bodegas Aalto",
        region="Ribera del Duero, Spain",
        country="Spain",
        appellation="Ribera del Duero DO",
        varietal="Tempranillo",
        wine_type="red",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Aalto Ribera del Duero", "Bodegas Aalto"],
        description="Founded by the former winemaker of Vega Sicilia; consistently one of Ribera del Duero's finest and most reliable estates.",
    ),
]

# ---------------------------------------------------------------------------
# CALIFORNIA – Cult producers
# ---------------------------------------------------------------------------
CALIFORNIA_CULT = [
    WineCatalogEntry(
        id="scarecrow-cabernet",
        name="Scarecrow Cabernet Sauvignon",
        producer="Scarecrow Wine",
        region="Rutherford, Napa Valley, California, USA",
        country="USA",
        appellation="Rutherford",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=380.0,
        price_tier="luxury",
        aliases=["Scarecrow Napa Cab", "Scarecrow Rutherford"],
        description="One of Napa Valley's most sought-after allocation wines; from the J.J. Cohn Estate in Rutherford, cult following for its intense fruit and longevity.",
    ),
    WineCatalogEntry(
        id="colgin-herb-lamb",
        name="Colgin Herb Lamb Vineyard Cabernet Sauvignon",
        producer="Colgin Cellars",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=460.0,
        price_tier="luxury",
        aliases=["Colgin Cabernet", "Colgin Napa Cab", "Herb Lamb Vineyard Colgin"],
        description="Ann Colgin's wines were among Napa's original cult Cabs; Herb Lamb is her flagship single-vineyard Cabernet Sauvignon.",
    ),
    WineCatalogEntry(
        id="bryant-family-cabernet",
        name="Bryant Family Vineyard Cabernet Sauvignon",
        producer="Bryant Family Vineyard",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=500.0,
        price_tier="ultra",
        aliases=["Bryant Cabernet", "Bryant Family Napa", "Bryant Family"],
        description="One of Napa's original cult wines; production is under 500 cases and secondary market prices often exceed $800.",
    ),
    WineCatalogEntry(
        id="dalla-valle-maya",
        name="Dalla Valle Maya",
        producer="Dalla Valle Vineyards",
        region="Oakville, Napa Valley, California, USA",
        country="USA",
        appellation="Oakville",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=420.0,
        price_tier="luxury",
        aliases=["Dalla Valle Maya Cabernet", "Maya Dalla Valle"],
        description="Naoko Dalla Valle's flagship; a Cabernet Sauvignon / Cabernet Franc blend that is among Napa's most individual and age-worthy wines.",
    ),
    WineCatalogEntry(
        id="hundred-acre-ark",
        name="Hundred Acre Ark Vineyard Cabernet Sauvignon",
        producer="Hundred Acre",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=600.0,
        price_tier="ultra",
        aliases=["Hundred Acre Ark Vineyard", "Hundred Acre Cabernet"],
        description="Jayson Woodbridge's Hundred Acre is one of Napa's most celebrated cult producers; Ark Vineyard is the flagship cuvée.",
    ),
    WineCatalogEntry(
        id="bond-pluribus",
        name="Bond Pluribus",
        producer="Bond Estates",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=350.0,
        price_tier="luxury",
        aliases=["Bond Cabernet", "Bond Estates Pluribus"],
        description="Bill Harlan's Bond portfolio produces single-vineyard Cabernets; Pluribus is a multi-vineyard blend showing the Harlan Estate house style.",
    ),
    WineCatalogEntry(
        id="marcassin-chardonnay",
        name="Marcassin Chardonnay",
        producer="Marcassin",
        region="Sonoma Coast, California, USA",
        country="USA",
        appellation="Sonoma Coast",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=280.0,
        price_tier="luxury",
        aliases=["Marcassin Sonoma Chardonnay", "Helen Turley Marcassin"],
        description="Helen Turley's iconic Sonoma Coast Chardonnay; production is tiny and allocations are extremely competitive.",
    ),
    WineCatalogEntry(
        id="williams-selyem-rochioli",
        name="Williams Selyem Rochioli Riverblock Pinot Noir",
        producer="Williams Selyem",
        region="Russian River Valley, California, USA",
        country="USA",
        appellation="Russian River Valley",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=120.0,
        price_tier="premium",
        aliases=["Williams Selyem Pinot Noir", "Williams Selyem Rochioli", "Williams & Selyem"],
        description="The original cult California Pinot Noir producer; the mailing list wait spans years. Rochioli Riverblock is the most accessible of the sought-after vineyard-designates.",
    ),
    WineCatalogEntry(
        id="kongsgaard-chardonnay",
        name="Kongsgaard Chardonnay",
        producer="Kongsgaard Wine",
        region="Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=180.0,
        price_tier="luxury",
        aliases=["Kongsgaard Napa Chardonnay", "John Kongsgaard Chardonnay"],
        description="John Kongsgaard's barrel-fermented Chardonnay is the American answer to white Burgundy grand cru; wild-fermented, sur-lie aged.",
    ),
    WineCatalogEntry(
        id="shafer-hillside-select",
        name="Shafer Hillside Select Cabernet Sauvignon",
        producer="Shafer Vineyards",
        region="Stags Leap District, Napa Valley, California, USA",
        country="USA",
        appellation="Stags Leap District",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=360.0,
        price_tier="luxury",
        aliases=["Shafer Hillside Select", "Shafer Stags Leap Cab", "Shafer Hillside"],
        description="One of Napa's most age-worthy Cabernet Sauvignons; Hillside Select is 100% Cabernet from the Stags Leap hillside block.",
    ),
    WineCatalogEntry(
        id="spottswoode-cabernet",
        name="Spottswoode Estate Cabernet Sauvignon",
        producer="Spottswoode Estate",
        region="St. Helena, Napa Valley, California, USA",
        country="USA",
        appellation="Napa Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=145.0,
        price_tier="premium",
        aliases=["Spottswoode Napa Cabernet", "Spottswoode Cabernet"],
        description="One of Napa Valley's most consistently excellent and fairly-priced estate Cabernets; certified organic, allocation-only.",
    ),
    WineCatalogEntry(
        id="aubert-chardonnay",
        name="Aubert UV-SL Vineyard Chardonnay",
        producer="Aubert Wines",
        region="Sonoma Coast, California, USA",
        country="USA",
        appellation="Sonoma Coast",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=120.0,
        price_tier="premium",
        aliases=["Aubert Chardonnay", "Aubert UV SL", "Mark Aubert Chardonnay"],
        description="Mark Aubert produces some of California's most sought-after single-vineyard Chardonnays and Pinot Noirs; UV-SL is the flagship.",
    ),
]

# ---------------------------------------------------------------------------
# GERMANY & AUSTRIA – Additions
# ---------------------------------------------------------------------------
GERMANY_AUSTRIA_ADDITIONS = [
    # Keller (Rheinhessen)
    WineCatalogEntry(
        id="keller-g-max",
        name="Keller G-Max Riesling",
        producer="Weingut Keller",
        region="Flörsheim-Dalsheim, Rheinhessen, Germany",
        country="Germany",
        appellation="Rheinhessen",
        varietal="Riesling",
        wine_type="white",
        avg_retail_price=1500.0,
        price_tier="ultra",
        aliases=["Keller G Max", "Klaus Keller G-Max", "Weingut Keller G-Max Riesling"],
        description="Klaus-Peter Keller's G-Max is Germany's most expensive and sought-after dry Riesling; from the Kirchspiel monopole, only ~300 magnums produced annually.",
    ),
    WineCatalogEntry(
        id="keller-kirchspiel",
        name="Keller Dalsheimer Hubacker Riesling GG",
        producer="Weingut Keller",
        region="Flörsheim-Dalsheim, Rheinhessen, Germany",
        country="Germany",
        appellation="Rheinhessen",
        varietal="Riesling",
        wine_type="white",
        avg_retail_price=85.0,
        price_tier="premium",
        aliases=["Keller Hubacker GG", "Keller Riesling GG", "Keller Rheinhessen Riesling"],
        description="Keller's entry point into his GG lineup; still among Germany's most sought-after dry Rieslings.",
    ),
    # Dönnhoff (Nahe)
    WineCatalogEntry(
        id="donnhoff-hermannshohle",
        name="Dönnhoff Niederhäuser Hermannshöhle Riesling GG",
        producer="Weingut Dönnhoff",
        region="Nahe, Germany",
        country="Germany",
        appellation="Nahe",
        varietal="Riesling",
        wine_type="white",
        avg_retail_price=90.0,
        price_tier="premium",
        aliases=["Donnhoff Hermannshohle", "Donnhoff Hermannshöhle GG", "Dönnhoff Nahe Riesling"],
        description="Helmut Dönnhoff's flagship; Hermannshöhle is considered one of Germany's greatest Riesling sites, consistently producing world-class dry wines.",
    ),
    WineCatalogEntry(
        id="donnhoff-oberhausen-brucke",
        name="Dönnhoff Oberhäuser Brücke Riesling Auslese",
        producer="Weingut Dönnhoff",
        region="Nahe, Germany",
        country="Germany",
        appellation="Nahe",
        varietal="Riesling",
        wine_type="dessert",
        avg_retail_price=180.0,
        price_tier="luxury",
        aliases=["Donnhoff Brucke Auslese", "Dönnhoff Brücke Auslese"],
        description="When conditions allow, Dönnhoff produces Spätlese and Auslese from the Brücke monopole; among the world's finest dessert Rieslings.",
    ),
    # FX Pichler (Wachau)
    WineCatalogEntry(
        id="fx-pichler-kellerberg",
        name="F.X. Pichler Ried Kellerberg Grüner Veltliner Smaragd",
        producer="Weingut F.X. Pichler",
        region="Loiben, Wachau, Austria",
        country="Austria",
        appellation="Wachau",
        varietal="Grüner Veltliner",
        wine_type="white",
        avg_retail_price=130.0,
        price_tier="premium",
        aliases=["FX Pichler Kellerberg", "F.X. Pichler Grüner Veltliner", "FX Pichler GV"],
        description="F.X. Pichler is the Wachau's most celebrated producer; Kellerberg Smaragd is the benchmark for great Austrian Grüner Veltliner.",
    ),
    WineCatalogEntry(
        id="fx-pichler-unendlich",
        name="F.X. Pichler Unendlich Grüner Veltliner Smaragd",
        producer="Weingut F.X. Pichler",
        region="Loiben, Wachau, Austria",
        country="Austria",
        appellation="Wachau",
        varietal="Grüner Veltliner",
        wine_type="white",
        avg_retail_price=200.0,
        price_tier="luxury",
        aliases=["FX Pichler Unendlich", "Pichler Unendlich"],
        description="'Unendlich' (infinity) is Pichler's top cuvée; produced only in exceptional vintages from the oldest vines of the Kellerberg.",
    ),
    # Knoll (Wachau)
    WineCatalogEntry(
        id="knoll-loibner-riesling",
        name="Knoll Loibner Riesling Smaragd",
        producer="Weingut Knoll",
        region="Loiben, Wachau, Austria",
        country="Austria",
        appellation="Wachau",
        varietal="Riesling",
        wine_type="white",
        avg_retail_price=65.0,
        price_tier="mid",
        aliases=["Knoll Riesling Smaragd", "Emmerich Knoll Riesling"],
        description="Emmerich Knoll is one of the Wachau's most traditional and revered producers; Loibner Smaragd shows tremendous minerality and longevity.",
    ),
    # Brundlmayer (Kamptal)
    WineCatalogEntry(
        id="brundlmayer-alte-reben",
        name="Bründlmayer Alte Reben Grüner Veltliner",
        producer="Weingut Bründlmayer",
        region="Langenlois, Kamptal, Austria",
        country="Austria",
        appellation="Kamptal DAC",
        varietal="Grüner Veltliner",
        wine_type="white",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Brundlmayer Alte Reben", "Brundlmayer GV", "Bründlmayer Grüner Veltliner"],
        description="Willi Bründlmayer's Alte Reben (old vines) cuvée is one of Kamptal's most complete Grüner Veltliners.",
    ),
]

# ---------------------------------------------------------------------------
# SOUTH AMERICA – Chile
# ---------------------------------------------------------------------------
CHILE = [
    WineCatalogEntry(
        id="almaviva",
        name="Almaviva",
        producer="Almaviva Winery",
        region="Puente Alto, Maipo Valley, Chile",
        country="Chile",
        appellation="Maipo Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=130.0,
        price_tier="premium",
        aliases=["Almaviva Chile", "Almaviva Maipo", "Baron Philippe de Rothschild Almaviva"],
        description="Joint venture between Concha y Toro and Baron Philippe de Rothschild; Chile's most prestigious Cabernet Sauvignon blend.",
    ),
    WineCatalogEntry(
        id="sena",
        name="Seña",
        producer="Viña Seña",
        region="Aconcagua Valley, Chile",
        country="Chile",
        appellation="Aconcagua Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=110.0,
        price_tier="premium",
        aliases=["Sena Chile", "Vina Sena", "Errazuriz Sena"],
        description="Founded by Eduardo Chadwick and Robert Mondavi; one of Chile's finest wines from the high-altitude Aconcagua Valley.",
    ),
    WineCatalogEntry(
        id="don-melchor",
        name="Don Melchor Cabernet Sauvignon",
        producer="Concha y Toro",
        region="Puente Alto, Maipo Valley, Chile",
        country="Chile",
        appellation="Maipo Valley",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=75.0,
        price_tier="mid",
        aliases=["Don Melchor Maipo", "Concha y Toro Don Melchor"],
        description="Concha y Toro's flagship single-vineyard Cabernet; consistently one of South America's finest reds, and one of Chile's most internationally recognised wines.",
    ),
    WineCatalogEntry(
        id="clos-apalta",
        name="Casa Lapostolle Clos Apalta",
        producer="Casa Lapostolle",
        region="Colchagua Valley, Chile",
        country="Chile",
        appellation="Colchagua Valley",
        varietal="Carménère",
        wine_type="red",
        avg_retail_price=120.0,
        price_tier="premium",
        aliases=["Clos Apalta Chile", "Lapostolle Clos Apalta"],
        description="Chile's finest Carménère-dominant wine; Clos Apalta won Wine of the Year from Wine Spectator in 2008.",
    ),
]

# ---------------------------------------------------------------------------
# SOUTH AFRICA
# ---------------------------------------------------------------------------
SOUTH_AFRICA = [
    WineCatalogEntry(
        id="sadie-columella",
        name="Sadie Family Columella",
        producer="Sadie Family Wines",
        region="Swartland, South Africa",
        country="South Africa",
        appellation="Swartland",
        varietal="Syrah",
        wine_type="red",
        avg_retail_price=90.0,
        price_tier="premium",
        aliases=["Sadie Columella", "Eben Sadie Columella"],
        description="Eben Sadie's Columella is South Africa's most critically acclaimed red wine; old-vine Syrah and Mourvèdre from Swartland's granite soils.",
    ),
    WineCatalogEntry(
        id="sadie-palladius",
        name="Sadie Family Palladius",
        producer="Sadie Family Wines",
        region="Swartland, South Africa",
        country="South Africa",
        appellation="Swartland",
        varietal="Chenin Blanc",
        wine_type="white",
        avg_retail_price=80.0,
        price_tier="premium",
        aliases=["Sadie Palladius", "Eben Sadie Palladius"],
        description="A complex multi-variety white blend led by old-vine Chenin Blanc; one of the New World's most extraordinary white wines.",
    ),
    WineCatalogEntry(
        id="mullineux-schist-syrah",
        name="Mullineux Schist Syrah",
        producer="Mullineux & Leeu Family Wines",
        region="Swartland, South Africa",
        country="South Africa",
        appellation="Swartland",
        varietal="Syrah",
        wine_type="red",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Mullineux Syrah", "Mullineux Schist", "Chris Mullineux Syrah"],
        description="Chris and Andrea Mullineux are Swartland's most celebrated winemakers; the soil-specific Syrah series has put South African terroir on the world map.",
    ),
    WineCatalogEntry(
        id="kanonkop-paul-sauer",
        name="Kanonkop Paul Sauer",
        producer="Kanonkop Wine Estate",
        region="Stellenbosch, South Africa",
        country="South Africa",
        appellation="Stellenbosch",
        varietal="Cabernet Sauvignon",
        wine_type="red",
        avg_retail_price=45.0,
        price_tier="mid",
        aliases=["Kanonkop Stellenbosch", "Paul Sauer Kanonkop"],
        description="South Africa's most distinguished Bordeaux-style blend; Paul Sauer is Kanonkop's flagship and a benchmark for South African Cabernet.",
    ),
    WineCatalogEntry(
        id="boekenhoutskloof-syrah",
        name="Boekenhoutskloof Syrah",
        producer="Boekenhoutskloof Winery",
        region="Franschhoek, South Africa",
        country="South Africa",
        appellation="Franschhoek",
        varietal="Syrah",
        wine_type="red",
        avg_retail_price=55.0,
        price_tier="mid",
        aliases=["Boekenhoutskloof Franschhoek Syrah"],
        description="Marc Kent's Syrah from Franschhoek is one of South Africa's most celebrated single-variety wines; small production, age-worthy.",
    ),
]

# ---------------------------------------------------------------------------
# PORTUGAL
# ---------------------------------------------------------------------------
PORTUGAL = [
    WineCatalogEntry(
        id="quinta-vale-meao",
        name="Quinta do Vale Meão",
        producer="Quinta do Vale Meão",
        region="Douro Superior, Portugal",
        country="Portugal",
        appellation="Douro DOC",
        varietal="Touriga Nacional",
        wine_type="red",
        avg_retail_price=90.0,
        price_tier="premium",
        aliases=["Vale Meao Douro", "Quinta do Vale Meao"],
        description="The original Barca Velha estate; now independently owned, Quinta do Vale Meão produces one of Portugal's most prestigious red wines.",
    ),
    WineCatalogEntry(
        id="niepoort-batuta",
        name="Niepoort Batuta",
        producer="Niepoort",
        region="Cima Corgo, Douro, Portugal",
        country="Portugal",
        appellation="Douro DOC",
        varietal="Touriga Nacional",
        wine_type="red",
        avg_retail_price=110.0,
        price_tier="premium",
        aliases=["Niepoort Batuta Douro", "Dirk Niepoort Batuta"],
        description="Dirk Niepoort's flagship unfortified Douro; from very old mixed-variety field-blend vines, one of Portugal's most individual wines.",
    ),
    WineCatalogEntry(
        id="barca-velha",
        name="Barca Velha",
        producer="Ferreira",
        region="Douro Superior, Portugal",
        country="Portugal",
        appellation="Douro DOC",
        varietal="Touriga Nacional",
        wine_type="red",
        avg_retail_price=450.0,
        price_tier="luxury",
        aliases=["Ferreira Barca Velha", "Barca Velha Douro"],
        description="Portugal's most legendary wine; only produced in exceptional vintages (roughly every 3–5 years). Created in 1952 by Fernando Nicolau de Almeida.",
    ),
    WineCatalogEntry(
        id="quinta-noval-nacional",
        name="Quinta do Noval Nacional Vintage Port",
        producer="Quinta do Noval",
        region="Cima Corgo, Douro, Portugal",
        country="Portugal",
        appellation="Port DOC",
        varietal="Touriga Nacional",
        wine_type="fortified",
        avg_retail_price=1800.0,
        price_tier="ultra",
        aliases=["Noval Nacional Port", "Quinta do Noval Nacional"],
        description="The rarest and most expensive Vintage Port; from a small plot of ungrafted pre-phylloxera vines. Only produced in the finest years in tiny quantities.",
    ),
]

# ---------------------------------------------------------------------------
# AUSTRALIA – Additions
# ---------------------------------------------------------------------------
AUSTRALIA_ADDITIONS = [
    WineCatalogEntry(
        id="giaconda-chardonnay",
        name="Giaconda Chardonnay",
        producer="Giaconda",
        region="Beechworth, Victoria, Australia",
        country="Australia",
        appellation="Beechworth",
        varietal="Chardonnay",
        wine_type="white",
        avg_retail_price=200.0,
        price_tier="luxury",
        aliases=["Giaconda Beechworth Chardonnay", "Rick Kinzbrunner Giaconda"],
        description="Rick Kinzbrunner's Giaconda Chardonnay is Australia's most acclaimed white wine; Burgundian in style, tiny production, mailing list only.",
    ),
    WineCatalogEntry(
        id="bass-phillip-reserve-pinot",
        name="Bass Phillip Reserve Pinot Noir",
        producer="Bass Phillip",
        region="Leongatha South, Gippsland, Victoria, Australia",
        country="Australia",
        appellation="Gippsland",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=260.0,
        price_tier="luxury",
        aliases=["Bass Phillip Pinot Noir", "Phillip Jones Bass Phillip"],
        description="Phillip Jones's Bass Phillip is Australia's most Burgundian Pinot Noir producer; Reserve is the top cuvée, made in tiny quantities from very old vines.",
    ),
    WineCatalogEntry(
        id="by-farr-sangreal",
        name="By Farr Sangreal Pinot Noir",
        producer="By Farr",
        region="Geelong, Victoria, Australia",
        country="Australia",
        appellation="Geelong",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=90.0,
        price_tier="premium",
        aliases=["By Farr Pinot Noir", "Nick Farr Sangreal", "Farr Sangreal"],
        description="Nick Farr carries on his father Gary's legacy; Sangreal is the flagship Pinot from one of Australia's most revered cool-climate estates.",
    ),
    WineCatalogEntry(
        id="ata-rangi-pinot-noir",
        name="Ata Rangi Pinot Noir",
        producer="Ata Rangi",
        region="Martinborough, New Zealand",
        country="New Zealand",
        appellation="Martinborough",
        varietal="Pinot Noir",
        wine_type="red",
        avg_retail_price=60.0,
        price_tier="mid",
        aliases=["Ata Rangi Martinborough", "Ata Rangi NZ Pinot"],
        description="New Zealand's most storied Pinot Noir producer; Clive Paton's estate in Martinborough was instrumental in establishing the region's reputation.",
    ),
]

# ---------------------------------------------------------------------------
# CHAMPAGNE – More grower producers (RM)
# ---------------------------------------------------------------------------
CHAMPAGNE_RM = [
    WineCatalogEntry(id="chartogne-taillet-sainte-anne", name="Chartogne-Taillet Sainte Anne Brut NV", producer="Chartogne-Taillet", region="Merfy, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=65.0, price_tier="mid", aliases=["Chartogne Taillet Sainte Anne", "Chartogne-Taillet NV"], description="Alexandre Chartogne's entry-level cuvée; one of the most popular grower Champagnes in natural wine circles."),
    WineCatalogEntry(id="chartogne-taillet-les-barres", name="Chartogne-Taillet Les Barres Blanc de Noirs Extra Brut", producer="Chartogne-Taillet", region="Merfy, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir", wine_type="sparkling", avg_retail_price=110.0, price_tier="premium", aliases=["Chartogne Taillet Les Barres", "Chartogne Les Barres"], description="Single-vineyard Blanc de Noirs; one of Chartogne-Taillet's finest single-lieu cuvées."),
    WineCatalogEntry(id="chartogne-taillet-orizeaux", name="Chartogne-Taillet Orizeaux Blanc de Noirs Extra Brut", producer="Chartogne-Taillet", region="Merfy, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir", wine_type="sparkling", avg_retail_price=110.0, price_tier="premium", aliases=["Chartogne Taillet Orizeaux"], description="Single-parcel Blanc de Noirs from Chartogne-Taillet; intense and structured."),
    WineCatalogEntry(id="tarlant-zero", name="Tarlant Zero Brut Nature NV", producer="Tarlant", region="Oeuilly, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=65.0, price_tier="mid", aliases=["Tarlant Brut Nature NV", "Tarlant Zero NV"], description="Benoît Tarlant's flagship Brut Nature; a blend of Chardonnay, Meunier, and Pinot Noir with zero dosage."),
    WineCatalogEntry(id="tarlant-la-vigne-dor", name="Tarlant La Vigne d'Or Blanc de Noirs Brut Nature", producer="Tarlant", region="Oeuilly, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Meunier", wine_type="sparkling", avg_retail_price=160.0, price_tier="premium", aliases=["Tarlant Vigne d'Or", "Tarlant La Vigne Or"], description="Single-vineyard Blanc de Noirs from pre-phylloxera Meunier vines; one of Champagne's great single-vineyard expressions."),
    WineCatalogEntry(id="tarlant-bam", name="Tarlant BAM Blanc de Blancs Brut Nature NV", producer="Tarlant", region="Oeuilly, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=180.0, price_tier="luxury", aliases=["Tarlant BAM Blanc de Blancs", "Tarlant BAM Champagne"], description="Blanc de Blancs from Arbane, Petit Meslier, and other ancient Champagne varietals; a wine of rare character."),
    WineCatalogEntry(id="laherte-ultradition", name="Laherte Frères Ultradition Extra Brut NV", producer="Laherte Frères", region="Chavot-Courcourt, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=65.0, price_tier="mid", aliases=["Laherte Ultradition", "Laherte Freres Ultradition", "Laherte Extra Brut"], description="Aurélien Laherte's entry-level cuvée; exemplifies the domaine's precise, mineral style."),
    WineCatalogEntry(id="laherte-les-grandes-crayeres", name="Laherte Frères Les Grandes Crayères Blanc de Blancs Extra Brut", producer="Laherte Frères", region="Chavot-Courcourt, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=160.0, price_tier="premium", aliases=["Laherte Les Grandes Crayeres", "Laherte Grandes Crayeres"], description="Single-vineyard Blanc de Blancs from chalky soils; Laherte's most prestigious cuvée."),
    WineCatalogEntry(id="vouette-et-sorbee-fidele", name="Vouette & Sorbée Fidèle Brut Nature NV", producer="Vouette & Sorbée", region="Buxières-sur-Arce, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir", wine_type="sparkling", avg_retail_price=110.0, price_tier="premium", aliases=["Vouette Sorbee Fidele", "Vouette et Sorbee Fidele"], description="Bertrand Gautherot's biodynamic estate produces some of Champagne's most sought-after natural wines; Fidèle is the Pinot Noir-dominant NV."),
    WineCatalogEntry(id="vouette-et-sorbee-blanc-dargile", name="Vouette & Sorbée Blanc d'Argile Brut Nature NV", producer="Vouette & Sorbée", region="Buxières-sur-Arce, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=140.0, price_tier="premium", aliases=["Vouette Sorbee Blanc d'Argile", "Blanc d'Argile Champagne"], description="100% Chardonnay from clay soils; one of Champagne's purest and most mineral expressions."),
    WineCatalogEntry(id="ulysse-collin-les-maillons", name="Ulysse-Collin Les Maillons Blanc de Noirs Extra Brut NV", producer="Ulysse-Collin", region="Congy, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir", wine_type="sparkling", avg_retail_price=280.0, price_tier="luxury", aliases=["Ulysse Collin Les Maillons", "Olivier Collin Les Maillons"], description="Olivier Collin's Les Maillons is one of the most sought-after grower Champagnes; commands cult prices on the secondary market."),
    WineCatalogEntry(id="ulysse-collin-les-pierrieres", name="Ulysse-Collin Les Pierrières Blanc de Blancs Extra Brut NV", producer="Ulysse-Collin", region="Congy, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=300.0, price_tier="luxury", aliases=["Ulysse Collin Les Pierrieres", "Olivier Collin Pierrieres"], description="Blanc de Blancs from mineral chalk; Ulysse-Collin's signature white wine site."),
    WineCatalogEntry(id="cedric-bouchard-roses-de-jeanne", name="Cédric Bouchard Roses de Jeanne Val Vilaine Blanc de Noirs NV", producer="Cédric Bouchard", region="Celles-sur-Ource, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir", wine_type="sparkling", avg_retail_price=160.0, price_tier="premium", aliases=["Cedric Bouchard Val Vilaine", "Bouchard Roses de Jeanne", "Cedric Bouchard Champagne"], description="Cédric Bouchard produces single-vineyard Blanc de Noirs from the Côte des Bar; cult following among sommeliers worldwide."),
    WineCatalogEntry(id="benoit-dehu-la-rue-des-noyers", name="Benoît Déhu La Rue des Noyers Brut Nature", producer="Benoît Déhu", region="Fossoy, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Meunier", wine_type="sparkling", avg_retail_price=110.0, price_tier="premium", aliases=["Benoit Dehu La Rue des Noyers", "Dehu La Rue des Noyers"], description="Benoît Déhu specialises in Pinot Meunier; La Rue des Noyers is a serious, mineral single-vineyard statement."),
    WineCatalogEntry(id="marguet-shaman", name="Marguet Shaman Grand Cru Extra Brut NV", producer="Marguet", region="Ambonnay, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir", wine_type="sparkling", avg_retail_price=65.0, price_tier="mid", aliases=["Marguet Shaman NV", "Benoit Marguet Shaman"], description="Benoît Marguet's biodynamic Ambonnay Grand Cru; Shaman is the signature non-vintage."),
    WineCatalogEntry(id="savart-louverture", name="Savart L'Ouverture Premier Cru Extra Brut NV", producer="Savart", region="Écueil, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir", wine_type="sparkling", avg_retail_price=80.0, price_tier="premium", aliases=["Savart L'Ouverture", "Emmanuel Savart Ouverture"], description="Emmanuel Savart's Premier Cru is one of the finest values in grower Champagne; rich, food-friendly style."),
    WineCatalogEntry(id="jacquesson-746", name="Jacquesson Cuvée 746 Extra Brut NV", producer="Jacquesson", region="Dizy, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=80.0, price_tier="premium", aliases=["Jacquesson Cuvee 746", "Jacquesson Extra Brut NV", "Jacquesson NV"], description="Jacquesson's numbered series NV is one of the finest Champagnes for the price; each release number reflects the harvest year."),
    WineCatalogEntry(id="gaston-chiquet-special-club", name="Gaston-Chiquet Special Club Brut Premier Cru", producer="Gaston-Chiquet", region="Dizy, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir", wine_type="sparkling", avg_retail_price=90.0, price_tier="premium", aliases=["Gaston Chiquet Special Club", "Chiquet Special Club"], description="One of the great Special Club Champagnes; Gaston-Chiquet's Dizy Premier Cru site produces richly textured wines."),
    WineCatalogEntry(id="francis-boulard-les-murgiers", name="Francis Boulard Les Murgiers Brut Nature NV", producer="Francis Boulard", region="Cauroy-lès-Hermonville, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Meunier", wine_type="sparkling", avg_retail_price=75.0, price_tier="mid", aliases=["Francis Boulard Murgiers", "Boulard Les Murgiers", "Boulard Brut Nature"], description="Mathieu Boulard's Brut Nature is one of the Montagne de Reims's finest small-producer Champagnes."),
    WineCatalogEntry(id="pertois-moriset-hauts-daillierand", name="Pertois-Moriset Les Hauts d'Aillierand Blanc de Blancs Grand Cru Extra Brut", producer="Pertois-Moriset", region="Le Mesnil-sur-Oger, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=85.0, price_tier="premium", aliases=["Pertois Moriset Hauts d'Aillierand", "Pertois-Moriset Blanc de Blancs"], description="Single-vineyard Blanc de Blancs from Le Mesnil; Pertois-Moriset is one of that village's finest small growers."),
    WineCatalogEntry(id="emmanuel-brochet-le-mont-benoit", name="Emmanuel Brochet Le Mont Benoît Premier Cru Extra Brut", producer="Emmanuel Brochet", region="Villers-aux-Nœuds, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Meunier", wine_type="sparkling", avg_retail_price=200.0, price_tier="luxury", aliases=["Emmanuel Brochet Mont Benoit", "Brochet Le Mont Benoit", "Brochet Premier Cru"], description="Emmanuel Brochet's single-vineyard Premier Cru is one of Champagne's great Meunier-dominant wines."),
    WineCatalogEntry(id="lilbert-fils-perle", name="Lilbert-Fils Perle Blanc de Blancs Grand Cru NV", producer="Lilbert-Fils", region="Cramant, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=75.0, price_tier="mid", aliases=["Lilbert Perle", "Lilbert Fils Perle Blanc de Blancs"], description="One of Cramant's finest small growers; Perle is a classic, precise Blanc de Blancs at an honest price."),
    WineCatalogEntry(id="corbon-grand-millesime", name="Corbon Grand Millésime Blanc de Blancs Avize Grand Cru", producer="Corbon", region="Avize, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=100.0, price_tier="premium", aliases=["Corbon Avize Grand Cru", "Corbon Grand Millesime"], description="A small Avize grower producing some of the finest and most ageworthy Blanc de Blancs in Champagne."),
    WineCatalogEntry(id="pierre-paillard-les-parcelles", name="Pierre Paillard Les Parcelles Extra Brut Grand Cru NV", producer="Pierre Paillard", region="Bouzy, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir", wine_type="sparkling", avg_retail_price=80.0, price_tier="premium", aliases=["Pierre Paillard Bouzy", "Paillard Les Parcelles"], description="From the Grand Cru village of Bouzy; Pierre Paillard is one of the Montagne de Reims's most respected small growers."),
    WineCatalogEntry(id="guiborat-prisme", name="Guiborat Prisme Blanc de Blancs Grand Cru Extra Brut NV", producer="Guiborat", region="Cramant, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=75.0, price_tier="mid", aliases=["Guiborat Prisme Blanc de Blancs", "Guiborat Cramant"], description="A rising Cramant estate with a cult following; Prisme is a mineral, precise Blanc de Blancs."),
]

# ---------------------------------------------------------------------------
# ITALY – Campania & South
# ---------------------------------------------------------------------------
ITALY_CAMPANIA = [
    WineCatalogEntry(id="pietracupa-fiano", name="Pietracupa Fiano di Avellino", producer="Pietracupa", region="Montefredane, Campania, Italy", country="Italy", appellation="Fiano di Avellino DOCG", varietal="Fiano", wine_type="white", avg_retail_price=40.0, price_tier="mid", aliases=["Pietracupa Fiano Avellino", "Pietracupa Avellino Fiano"], description="Sabino Loffredo's Pietracupa produces some of Campania's finest and most mineral Fiano di Avellino."),
    WineCatalogEntry(id="pietracupa-greco", name="Pietracupa Greco di Tufo", producer="Pietracupa", region="Montefredane, Campania, Italy", country="Italy", appellation="Greco di Tufo DOCG", varietal="Greco", wine_type="white", avg_retail_price=40.0, price_tier="mid", aliases=["Pietracupa Greco Tufo", "Pietracupa Greco"], description="Pietracupa's Greco di Tufo is similarly precise and mineral; a benchmark for the appellation."),
    WineCatalogEntry(id="ciro-picariello-906", name="Ciro Picariello 906 Fiano di Avellino", producer="Ciro Picariello", region="Summonte, Campania, Italy", country="Italy", appellation="Fiano di Avellino DOCG", varietal="Fiano", wine_type="white", avg_retail_price=42.0, price_tier="mid", aliases=["Picariello 906 Fiano", "Ciro Picariello Fiano Avellino"], description="Ciro Picariello's 906 is one of Campania's most sought-after Fiano di Avellino; complex and age-worthy."),
    WineCatalogEntry(id="ciro-picariello-taurasi", name="Ciro Picariello O Pilota Taurasi", producer="Ciro Picariello", region="Summonte, Campania, Italy", country="Italy", appellation="Taurasi DOCG", varietal="Aglianico", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Picariello Taurasi", "Ciro Picariello Aglianico"], description="Taurasi from one of Campania's most respected producers; powerful, structured Aglianico with great aging potential."),
    WineCatalogEntry(id="quintodecimo-taurasi", name="Quintodecimo Vigna Quinto Decimo Taurasi", producer="Quintodecimo", region="Mirabella Eclano, Campania, Italy", country="Italy", appellation="Taurasi DOCG", varietal="Aglianico", wine_type="red", avg_retail_price=200.0, price_tier="premium", aliases=["Quintodecimo Taurasi", "Luigi Moio Taurasi"], description="Luigi Moio's flagship Taurasi is the most prestigious wine in Campania; extraordinary depth and complexity from Aglianico."),
    WineCatalogEntry(id="mastroberardino-taurasi-radici", name="Mastroberardino Taurasi Radici Riserva", producer="Mastroberardino", region="Atripalda, Campania, Italy", country="Italy", appellation="Taurasi DOCG", varietal="Aglianico", wine_type="red", avg_retail_price=75.0, price_tier="mid", aliases=["Mastroberardino Radici Taurasi", "Mastroberardino Taurasi"], description="Mastroberardino is the historic house of Taurasi; Radici is their benchmark Riserva."),
    WineCatalogEntry(id="elena-fucci-titolo", name="Elena Fucci Titolo Aglianico del Vulture", producer="Elena Fucci", region="Barile, Basilicata, Italy", country="Italy", appellation="Aglianico del Vulture DOC", varietal="Aglianico", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Elena Fucci Aglianico Vulture", "Fucci Titolo Basilicata"], description="Elena Fucci produces some of Italy's most exciting Aglianico del Vulture; Titolo is her single-vineyard flagship."),
    WineCatalogEntry(id="nanni-cope-sabbie-di-sopra", name="Nanni Copé Sabbie di Sopra il Bosco", producer="Nanni Copé", region="Falciano del Massico, Campania, Italy", country="Italy", appellation="Terre del Volturno IGT", varietal="Pallagrello Nero", wine_type="red", avg_retail_price=140.0, price_tier="premium", aliases=["Nanni Cope Sabbie", "Sabbie di Sopra il Bosco"], description="One of Campania's most enigmatic and sought-after wines; a blend of ancient varieties from volcanic soils near Falerno del Massico."),
    WineCatalogEntry(id="luigi-tecce-satyricon", name="Luigi Tecce Satyricon Irpinia Aglianico", producer="Luigi Tecce", region="Paternopoli, Campania, Italy", country="Italy", appellation="Irpinia Aglianico DOC", varietal="Aglianico", wine_type="red", avg_retail_price=75.0, price_tier="mid", aliases=["Luigi Tecce Aglianico", "Tecce Satyricon"], description="Luigi Tecce is one of Campania's most committed natural winemakers; Satyricon is his powerful, uncompromising Aglianico."),
    WineCatalogEntry(id="de-conciliis-naima", name="De Conciliis Naima Paestum Aglianico", producer="De Conciliis", region="Prignano Cilento, Campania, Italy", country="Italy", appellation="Paestum IGT", varietal="Aglianico", wine_type="red", avg_retail_price=120.0, price_tier="premium", aliases=["De Conciliis Naima Aglianico", "Naima De Conciliis Campania"], description="Bruno De Conciliis's Naima is one of southern Italy's most profound reds; old-vine Aglianico from the Cilento coast."),
    WineCatalogEntry(id="montevetrano", name="Montevetrano Rosso Colli di Salerno", producer="Montevetrano", region="San Cipriano Picentino, Campania, Italy", country="Italy", appellation="Colli di Salerno IGT", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Montevetrano Campania", "Silvia Imparato Montevetrano"], description="Silvia Imparato's Montevetrano was Campania's first Super Tuscan-equivalent; Cabernet Sauvignon, Aglianico, and Merlot."),
    WineCatalogEntry(id="marisa-cuomo-furore-rosso", name="Marisa Cuomo Furore Costa d'Amalfi Rosso", producer="Marisa Cuomo", region="Furore, Campania, Italy", country="Italy", appellation="Costa d'Amalfi DOC", varietal="Aglianico", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Marisa Cuomo Furore Rosso", "Cuomo Costa d'Amalfi Rosso"], description="From the stunning terraced vineyards of the Amalfi Coast; Marisa Cuomo's reds are unique in Italian wine."),
    WineCatalogEntry(id="marisa-cuomo-fiorduva", name="Marisa Cuomo Fiorduva Costa d'Amalfi Bianco", producer="Marisa Cuomo", region="Furore, Campania, Italy", country="Italy", appellation="Costa d'Amalfi DOC", varietal="Fenile", wine_type="white", avg_retail_price=130.0, price_tier="premium", aliases=["Marisa Cuomo Fiorduva", "Cuomo Fiorduva Amalfi"], description="One of Italy's most distinctive whites; from ancient coastal grape varieties (Fenile, Ginestra, Ripoli) on steep Amalfi terraces."),
    WineCatalogEntry(id="contrada-salandra-piedirosso", name="Contrada Salandra Campi Flegrei Piedirosso", producer="Contrada Salandra", region="Pozzuoli, Campania, Italy", country="Italy", appellation="Campi Flegrei DOC", varietal="Piedirosso", wine_type="red", avg_retail_price=35.0, price_tier="mid", aliases=["Salandra Campi Flegrei Piedirosso", "Contrada Salandra Piedirosso"], description="Piedirosso grown on volcanic Campi Flegrei soils; distinctive, mineral, and unlike anything else in Italian wine."),
    WineCatalogEntry(id="vadiaperti-fiano", name="Vadiaperti Fiano di Avellino", producer="Vadiaperti", region="Montefredane, Campania, Italy", country="Italy", appellation="Fiano di Avellino DOCG", varietal="Fiano", wine_type="white", avg_retail_price=35.0, price_tier="mid", aliases=["Vadiaperti Avellino Fiano", "Vadiaperti Fiano"], description="Raffaele Troisi's Vadiaperti is one of the purest and most age-worthy Fiano di Avellino producers."),
    WineCatalogEntry(id="colli-di-lapio-clelia", name="Colli di Lapio Clelia Romano Fiano di Avellino", producer="Colli di Lapio", region="Lapio, Campania, Italy", country="Italy", appellation="Fiano di Avellino DOCG", varietal="Fiano", wine_type="white", avg_retail_price=60.0, price_tier="mid", aliases=["Clelia Romano Fiano", "Colli di Lapio Fiano Avellino"], description="Clelia Romano's Fiano di Avellino is a benchmark for the appellation; smoky, mineral, and complex."),
]

# ---------------------------------------------------------------------------
# ITALY – Sicily & Etna
# ---------------------------------------------------------------------------
ITALY_SICILY = [
    WineCatalogEntry(id="cos-cerasuolo-di-vittoria", name="COS Cerasuolo di Vittoria", producer="COS", region="Vittoria, Sicily, Italy", country="Italy", appellation="Cerasuolo di Vittoria DOCG", varietal="Nero d'Avola", wine_type="red", avg_retail_price=42.0, price_tier="mid", aliases=["COS Cerasuolo Vittoria", "Azienda Agricola COS"], description="COS pioneered natural winemaking in Sicily; Cerasuolo di Vittoria blends Nero d'Avola and Frappato for a uniquely Sicilian red."),
    WineCatalogEntry(id="cos-frappato", name="COS Frappato Terre Siciliane", producer="COS", region="Vittoria, Sicily, Italy", country="Italy", appellation="Terre Siciliane IGT", varietal="Frappato", wine_type="red", avg_retail_price=28.0, price_tier="mid", aliases=["COS Frappato Sicily", "COS Terre Siciliane Frappato"], description="100% Frappato; COS's lighter, more delicate red is a sommelier favourite for its freshness and precision."),
    WineCatalogEntry(id="arianna-occhipinti-sp68", name="Arianna Occhipinti SP68 Terre Siciliane Rosso", producer="Arianna Occhipinti", region="Vittoria, Sicily, Italy", country="Italy", appellation="Terre Siciliane IGT", varietal="Nero d'Avola", wine_type="red", avg_retail_price=30.0, price_tier="mid", aliases=["Occhipinti SP68", "Arianna Occhipinti Frappato SP68"], description="Named for the road past her vineyard; Arianna Occhipinti's SP68 is one of Sicily's most iconic natural wines."),
    WineCatalogEntry(id="arianna-occhipinti-il-frappato", name="Arianna Occhipinti Il Frappato Terre Siciliane Rosso", producer="Arianna Occhipinti", region="Vittoria, Sicily, Italy", country="Italy", appellation="Terre Siciliane IGT", varietal="Frappato", wine_type="red", avg_retail_price=65.0, price_tier="mid", aliases=["Occhipinti Frappato", "Arianna Occhipinti Frappato"], description="Arianna Occhipinti's single-variety Frappato is the benchmark for the grape; delicate, floral, mineral."),
    WineCatalogEntry(id="frank-cornelissen-munjebel", name="Frank Cornelissen Munjebel Bianco Terre Siciliane", producer="Frank Cornelissen", region="Etna, Sicily, Italy", country="Italy", appellation="Terre Siciliane IGT", varietal="Grecanico Dorato", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Frank Cornelissen Munjebel Bianco", "Cornelissen Munjebel White"], description="Frank Cornelissen's entry-level Etna Bianco; volcanic, mineral, and unforgettable."),
    WineCatalogEntry(id="frank-cornelissen-magma", name="Frank Cornelissen Magma Terre Siciliane Rosso", producer="Frank Cornelissen", region="Etna, Sicily, Italy", country="Italy", appellation="Terre Siciliane IGT", varietal="Nerello Mascalese", wine_type="red", avg_retail_price=350.0, price_tier="luxury", aliases=["Cornelissen Magma", "Frank Cornelissen Magma Etna"], description="Frank Cornelissen's flagship; Magma is one of the world's most sought-after natural wines from the slopes of Etna."),
    WineCatalogEntry(id="passopisciaro-contrada", name="Passopisciaro Contrada Chiappemacine Terre Siciliane Rosso", producer="Passopisciaro", region="Castiglione di Sicilia, Etna, Sicily, Italy", country="Italy", appellation="Terre Siciliane IGT", varietal="Nerello Mascalese", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Passopisciaro Chiappemacine", "Passopisciaro Contrada Etna"], description="Andrea Franchetti's Passopisciaro single-contrada wines are benchmarks for Etna's cru system."),
    WineCatalogEntry(id="girolamo-russo-feudo", name="Girolamo Russo Feudo Etna Rosso", producer="Girolamo Russo", region="Castiglione di Sicilia, Etna, Sicily, Italy", country="Italy", appellation="Etna Rosso DOC", varietal="Nerello Mascalese", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Russo Feudo Etna", "Girolamo Russo Etna Rosso"], description="Giuseppe Russo's Etna estate is one of the volcano's most celebrated; Feudo is the approachable entry-level Etna Rosso."),
    WineCatalogEntry(id="girolamo-russo-san-lorenzo", name="Girolamo Russo San Lorenzo Etna Rosso", producer="Girolamo Russo", region="Castiglione di Sicilia, Etna, Sicily, Italy", country="Italy", appellation="Etna Rosso DOC", varietal="Nerello Mascalese", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Russo San Lorenzo Etna", "Girolamo Russo San Lorenzo"], description="Single-vineyard Etna Rosso from the Contrada San Lorenzo; one of Etna's greatest site expressions."),
    WineCatalogEntry(id="benanti-etna-bianco", name="Benanti Etna Bianco", producer="Benanti", region="Viagrande, Etna, Sicily, Italy", country="Italy", appellation="Etna Bianco DOC", varietal="Carricante", wine_type="white", avg_retail_price=32.0, price_tier="mid", aliases=["Benanti Etna Bianco DOC", "Benanti White Etna"], description="One of the pioneers of the Etna wine renaissance; entry-level Etna Bianco from a historic estate."),
    WineCatalogEntry(id="benanti-pietra-marina", name="Benanti Pietra Marina Etna Bianco Superiore", producer="Benanti", region="Viagrande, Etna, Sicily, Italy", country="Italy", appellation="Etna Bianco Superiore DOC", varietal="Carricante", wine_type="white", avg_retail_price=175.0, price_tier="luxury", aliases=["Benanti Pietra Marina", "Pietra Marina Etna Superiore"], description="Benanti's flagship Etna Bianco Superiore from very old Carricante vines; one of Italy's most distinctive whites."),
    WineCatalogEntry(id="palmento-costanzo-bianco-di-sei", name="Palmento Costanzo Bianco di Sei Etna Bianco", producer="Palmento Costanzo", region="Castiglione di Sicilia, Etna, Sicily, Italy", country="Italy", appellation="Etna Bianco DOC", varietal="Carricante", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Palmento Costanzo Bianco", "Bianco di Sei Etna", "Costanzo Bianco di Sei"], description="One of Etna's more recent boutique estates; Bianco di Sei is a precise, age-worthy Carricante."),
    WineCatalogEntry(id="terra-costantino-blandano", name="Terra Costantino Contrada Blandano Etna Bianco", producer="Terra Costantino", region="Viagrande, Etna, Sicily, Italy", country="Italy", appellation="Etna Bianco DOC", varietal="Carricante", wine_type="white", avg_retail_price=50.0, price_tier="mid", aliases=["Terra Costantino Etna", "Costantino Blandano Etna Bianco"], description="Single-contrada Etna Bianco from Blandano; Terra Costantino is one of the emerging stars of Etna."),
    WineCatalogEntry(id="palari-faro", name="Palari Faro", producer="Palari", region="Santo Stefano Briga, Messina, Sicily, Italy", country="Italy", appellation="Faro DOC", varietal="Nerello Mascalese", wine_type="red", avg_retail_price=120.0, price_tier="premium", aliases=["Palari Faro Sicilia", "Salvatore Geraci Palari"], description="Palari's Faro is the flagship of Sicily's rarest DOC near Messina; Nerello Mascalese and other ancient varieties."),
    WineCatalogEntry(id="marco-de-bartoli-vecchio-samperi", name="Marco de Bartoli Vecchio Samperi Marsala Superiore", producer="Marco de Bartoli", region="Marsala, Sicily, Italy", country="Italy", appellation="Marsala DOC", varietal="Grillo", wine_type="fortified", avg_retail_price=80.0, price_tier="premium", aliases=["De Bartoli Vecchio Samperi", "Marco de Bartoli Marsala"], description="The wine that revived interest in serious Marsala; Marco de Bartoli's Vecchio Samperi is a benchmark for oxidative Sicilian wine."),
    WineCatalogEntry(id="feudo-montoni-vrucara", name="Feudo Montoni Vrucara Nero d'Avola", producer="Feudo Montoni", region="Cammarata, Sicily, Italy", country="Italy", appellation="Sicilia DOC", varietal="Nero d'Avola", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Feudo Montoni Vrucara", "Montoni Nero d'Avola Vrucara"], description="Old-vine Nero d'Avola from inland Sicily; Feudo Montoni's Vrucara is one of the grape's finest expressions."),
]

# ---------------------------------------------------------------------------
# ITALY – Abruzzo & Central Italy
# ---------------------------------------------------------------------------
ITALY_CENTRAL = [
    WineCatalogEntry(id="tiberio-trebbiano-abruzzo", name="Tiberio Trebbiano d'Abruzzo", producer="Tiberio", region="Cugnoli, Abruzzo, Italy", country="Italy", appellation="Trebbiano d'Abruzzo DOC", varietal="Trebbiano Abruzzese", wine_type="white", avg_retail_price=30.0, price_tier="mid", aliases=["Tiberio Trebbiano", "Cristiana Tiberio Trebbiano Abruzzo"], description="Cristiana Tiberio is the leading voice for Abruzzo's ancient Trebbiano Abruzzese clone; mineral, serious white wine."),
    WineCatalogEntry(id="tiberio-pecorino", name="Tiberio Pecorino", producer="Tiberio", region="Cugnoli, Abruzzo, Italy", country="Italy", appellation="Abruzzo DOC", varietal="Pecorino", wine_type="white", avg_retail_price=25.0, price_tier="mid", aliases=["Tiberio Pecorino Abruzzo", "Cristiana Tiberio Pecorino"], description="One of Italy's finest Pecorino wines; crisp, aromatic, and expressive of this ancient central Italian grape."),
    WineCatalogEntry(id="tiberio-archivio", name="Tiberio Archivio Montepulciano d'Abruzzo", producer="Tiberio", region="Cugnoli, Abruzzo, Italy", country="Italy", appellation="Montepulciano d'Abruzzo DOC", varietal="Montepulciano", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Tiberio Archivio Montepulciano", "Tiberio Archivio Abruzzo"], description="Tiberio's rare single-vineyard Montepulciano from four ancestral biotypes; one of Abruzzo's most thought-provoking reds."),
    WineCatalogEntry(id="valentini-trebbiano", name="Valentini Trebbiano d'Abruzzo", producer="Valentini", region="Loreto Aprutino, Abruzzo, Italy", country="Italy", appellation="Trebbiano d'Abruzzo DOC", varietal="Trebbiano Abruzzese", wine_type="white", avg_retail_price=180.0, price_tier="luxury", aliases=["Edoardo Valentini Trebbiano", "Valentini Abruzzo Trebbiano"], description="Edoardo Valentini's legendary estate; his Trebbiano d'Abruzzo is considered one of Italy's greatest white wines, capable of decades of aging."),
    WineCatalogEntry(id="valentini-montepulciano", name="Valentini Montepulciano d'Abruzzo", producer="Valentini", region="Loreto Aprutino, Abruzzo, Italy", country="Italy", appellation="Montepulciano d'Abruzzo DOC", varietal="Montepulciano", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["Edoardo Valentini Montepulciano", "Valentini Abruzzo Rosso"], description="Valentini's Montepulciano d'Abruzzo is one of Italy's great reds; only released in the finest vintages."),
    WineCatalogEntry(id="emidio-pepe-trebbiano", name="Emidio Pepe Trebbiano d'Abruzzo", producer="Emidio Pepe", region="Torano Nuovo, Abruzzo, Italy", country="Italy", appellation="Trebbiano d'Abruzzo DOC", varietal="Trebbiano Abruzzese", wine_type="white", avg_retail_price=150.0, price_tier="premium", aliases=["Emidio Pepe Trebbiano Abruzzo", "Pepe Trebbiano d'Abruzzo"], description="Emidio Pepe is one of Italy's most cult natural wine producers; his Trebbiano d'Abruzzo ages for decades."),
    WineCatalogEntry(id="emidio-pepe-montepulciano", name="Emidio Pepe Montepulciano d'Abruzzo", producer="Emidio Pepe", region="Torano Nuovo, Abruzzo, Italy", country="Italy", appellation="Montepulciano d'Abruzzo DOC", varietal="Montepulciano", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Emidio Pepe Montepulciano Abruzzo", "Pepe Montepulciano d'Abruzzo"], description="One of the icons of Italian natural wine; Emidio Pepe's Montepulciano d'Abruzzo is deceptively delicate and intensely mineral."),
    WineCatalogEntry(id="valle-reale-vigneto-di-popoli", name="Valle Reale Vigneto di Popoli Montepulciano d'Abruzzo", producer="Valle Reale", region="Popoli, Abruzzo, Italy", country="Italy", appellation="Montepulciano d'Abruzzo DOC", varietal="Montepulciano", wine_type="red", avg_retail_price=30.0, price_tier="mid", aliases=["Valle Reale Popoli Montepulciano", "Valle Reale Abruzzo"], description="Valle Reale produces some of Abruzzo's most reliable and terroir-driven Montepulciano from hillside vineyards near Popoli."),
    WineCatalogEntry(id="paolo-bea-san-valentino", name="Paolo Bea San Valentino Umbria Rosso", producer="Paolo Bea", region="Montefalco, Umbria, Italy", country="Italy", appellation="Umbria IGT", varietal="Sagrantino", wine_type="red", avg_retail_price=75.0, price_tier="mid", aliases=["Paolo Bea San Valentino", "Bea San Valentino Umbria"], description="The Bea family are Sagrantino's greatest champions; San Valentino is a Sangiovese-dominant red with Sagrantino and Montepulciano."),
    WineCatalogEntry(id="paolo-bea-arboreus", name="Paolo Bea Arboreus Trebbiano Spoletino", producer="Paolo Bea", region="Montefalco, Umbria, Italy", country="Italy", appellation="Umbria IGT", varietal="Trebbiano Spoletino", wine_type="white", avg_retail_price=70.0, price_tier="mid", aliases=["Bea Arboreus Trebbiano", "Paolo Bea Trebbiano Spoletino"], description="Bea's 'Arboreus' grows Trebbiano Spoletino on trees in the ancient manner; one of Italy's most distinctive and long-lived whites."),
    WineCatalogEntry(id="la-stoppa-ageno", name="La Stoppa Ageno Emilia Bianco", producer="La Stoppa", region="Rivergaro, Emilia-Romagna, Italy", country="Italy", appellation="Emilia IGT", varietal="Malvasia di Candia Aromatica", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["La Stoppa Ageno", "Elena Pantaleoni Ageno"], description="Elena Pantaleoni's La Stoppa is one of Italy's most historic natural wine estates; Ageno is an orange wine classic."),
    WineCatalogEntry(id="amorotti-montepulciano", name="Amorotti Montepulciano d'Abruzzo", producer="Amorotti", region="Abruzzo, Italy", country="Italy", appellation="Montepulciano d'Abruzzo DOC", varietal="Montepulciano", wine_type="red", avg_retail_price=50.0, price_tier="mid", aliases=["Amorotti Abruzzo Rosso", "Amorotti Montepulciano"], description="One of Abruzzo's finest emerging estates; precise, savoury Montepulciano with real aging potential."),
    WineCatalogEntry(id="guastaferro-memini", name="Guastaferro Memini Irpinia Aglianico", producer="Guastaferro", region="Taurasi, Campania, Italy", country="Italy", appellation="Irpinia Aglianico DOC", varietal="Aglianico", wine_type="red", avg_retail_price=35.0, price_tier="mid", aliases=["Guastaferro Irpinia Aglianico", "Guastaferro Aglianico"], description="A small Irpinia estate producing excellent-value Aglianico; Memini is youthful and vibrant."),
    WineCatalogEntry(id="monastero-suore-cistercensi-coenobium", name="Monastero Suore Cistercensi Coenobium Lazio Bianco", producer="Monastero Suore Cistercensi", region="Vitorchiano, Lazio, Italy", country="Italy", appellation="Lazio Bianco IGT", varietal="Trebbiano", wine_type="white", avg_retail_price=35.0, price_tier="mid", aliases=["Coenobium Monastery White", "Monastero Cistercensi Coenobium", "Coenobium Lazio"], description="Made by Cistercian nuns with advice from Giampiero Bea; Coenobium is one of Italy's most beloved natural whites."),
]

# ---------------------------------------------------------------------------
# ITALY – Piedmont (additional)
# ---------------------------------------------------------------------------
ITALY_PIEDMONT = [
    WineCatalogEntry(id="aldo-conterno-barolo", name="Aldo Conterno Barolo Gran Bussia", producer="Aldo Conterno", region="Monforte d'Alba, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=220.0, price_tier="luxury", aliases=["Aldo Conterno Gran Bussia", "Aldo Conterno Barolo"], description="One of Barolo's most revered traditional producers; Gran Bussia is a blend of old vines from the Bussia subzone."),
    WineCatalogEntry(id="vietti-barolo-rocche", name="Vietti Barolo Rocche di Castiglione", producer="Vietti", region="Castiglione Falletto, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=160.0, price_tier="premium", aliases=["Vietti Rocche di Castiglione", "Vietti Barolo Castiglione"], description="One of Barolo's great cru wines from Castiglione Falletto; Vietti is among the denomination's most consistent producers."),
    WineCatalogEntry(id="paolo-scavino-barolo", name="Paolo Scavino Barolo Bric dël Fiasc", producer="Paolo Scavino", region="Castiglione Falletto, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Scavino Bric del Fiasc", "Paolo Scavino Barolo"], description="Paolo Scavino's signature single-vineyard Barolo from the prestigious Bric dël Fiasc cru."),
    WineCatalogEntry(id="prunotto-bussia", name="Prunotto Barolo Bussia", producer="Prunotto", region="Alba, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Prunotto Barolo", "Prunotto Barolo Bussia"], description="Now owned by Antinori, Prunotto continues to produce reliable, traditionally-styled Barolo from the Bussia cru."),
    WineCatalogEntry(id="marchesi-di-barolo-barolo", name="Marchesi di Barolo Barolo", producer="Marchesi di Barolo", region="Barolo, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Marchesi di Barolo", "Marchesi Barolo Commune"], description="The historic house of Barolo; Marchesi di Barolo produces one of the most representative and fairly-priced classic Barolos."),
    WineCatalogEntry(id="roagna-barolo", name="Roagna Barolo La Pira", producer="Roagna", region="Castiglione Falletto, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["Roagna La Pira Barolo", "Luca Roagna Barolo"], description="Luca Roagna's La Pira is one of the most sought-after traditional-style Barolos from Castiglione Falletto."),
    WineCatalogEntry(id="giacomo-fenocchio-barolo", name="Giacomo Fenocchio Barolo Cannubi", producer="Giacomo Fenocchio", region="Monforte d'Alba, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Fenocchio Barolo Cannubi", "Giacomo Fenocchio Cannubi"], description="Giacomo Fenocchio is one of Barolo's most underrated traditional producers; Cannubi is one of the denomination's most prestigious crus."),
    WineCatalogEntry(id="gaja-sori-san-lorenzo", name="Gaja Sorì San Lorenzo Langhe Nebbiolo", producer="Gaja", region="Barbaresco, Piedmont, Italy", country="Italy", appellation="Langhe Nebbiolo DOC", varietal="Nebbiolo", wine_type="red", avg_retail_price=750.0, price_tier="ultra", aliases=["Gaja Sori San Lorenzo", "Gaja San Lorenzo Barbaresco"], description="Angelo Gaja's Sorì San Lorenzo is one of Piedmont's most legendary single-vineyard Nebbiolos; now labelled as Langhe DOC."),
    WineCatalogEntry(id="la-spinetta-barbaresco", name="La Spinetta Barbaresco Starderi", producer="La Spinetta", region="Barbaresco, Piedmont, Italy", country="Italy", appellation="Barbaresco DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=120.0, price_tier="premium", aliases=["La Spinetta Starderi Barbaresco", "Giorgio Rivetti Barbaresco"], description="Giorgio Rivetti's La Spinetta produces powerful, modern-style Barbaresco from top single vineyards."),
    WineCatalogEntry(id="ceretto-bricco-rocche", name="Ceretto Bricco Rocche Barolo", producer="Ceretto", region="Castiglione Falletto, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["Ceretto Bricco Rocche", "Ceretto Barolo"], description="Ceretto's Bricco Rocche is their flagship single-vineyard Barolo; one of the denomination's most consistently excellent wines."),
    WineCatalogEntry(id="massolino-barolo-sori-vigna-rionda", name="Massolino Barolo Vigna Rionda Riserva", producer="Massolino", region="Serralunga d'Alba, Piedmont, Italy", country="Italy", appellation="Barolo DOCG Riserva", varietal="Nebbiolo", wine_type="red", avg_retail_price=350.0, price_tier="luxury", aliases=["Massolino Vigna Rionda", "Massolino Barolo Riserva"], description="Massolino's Vigna Rionda Riserva is the benchmark for Serralunga's stern, austere style of Barolo."),
]

# ---------------------------------------------------------------------------
# ITALY – Tuscany (additional)
# ---------------------------------------------------------------------------
ITALY_TUSCANY_ADD = [
    WineCatalogEntry(id="soldera-case-basse", name="Soldera Case Basse Toscana Rosso", producer="Soldera", region="Montalcino, Tuscany, Italy", country="Italy", appellation="Toscana IGT", varietal="Sangiovese", wine_type="red", avg_retail_price=650.0, price_tier="ultra", aliases=["Case Basse Soldera", "Gianfranco Soldera Case Basse"], description="Gianfranco Soldera's Case Basse is one of Italy's most extraordinary wines and a cult object; tiny production, never released until deemed ready."),
    WineCatalogEntry(id="salvioni-brunello", name="Salvioni Brunello di Montalcino", producer="Salvioni", region="Montalcino, Tuscany, Italy", country="Italy", appellation="Brunello di Montalcino DOCG", varietal="Sangiovese", wine_type="red", avg_retail_price=280.0, price_tier="luxury", aliases=["Cerbaiola Salvioni Brunello", "Salvioni Cerbaiola"], description="Giulio Salvioni's tiny estate is one of Montalcino's most beloved; his Brunello from the Cerbaiola vineyard is profoundly elegant."),
    WineCatalogEntry(id="il-marroneto-madonna-delle-grazie", name="Il Marroneto Madonna delle Grazie Brunello di Montalcino", producer="Il Marroneto", region="Montalcino, Tuscany, Italy", country="Italy", appellation="Brunello di Montalcino DOCG", varietal="Sangiovese", wine_type="red", avg_retail_price=500.0, price_tier="ultra", aliases=["Marroneto Madonna delle Grazie", "Il Marroneto Madonna"], description="Il Marroneto's single-vineyard cru is Montalcino's most coveted wine after Soldera; tiny production, allocation only."),
    WineCatalogEntry(id="casanova-di-neri-cerretalto", name="Casanova di Neri Cerretalto Brunello di Montalcino", producer="Casanova di Neri", region="Montalcino, Tuscany, Italy", country="Italy", appellation="Brunello di Montalcino DOCG", varietal="Sangiovese", wine_type="red", avg_retail_price=500.0, price_tier="ultra", aliases=["Casanova Neri Cerretalto", "Cerretalto Brunello"], description="Casanova di Neri's Cerretalto is a single-vineyard Brunello of extraordinary concentration; scored 100 points by Robert Parker."),
    WineCatalogEntry(id="grattamacco-bolgheri-rosso", name="Grattamacco Bolgheri Rosso", producer="Grattamacco", region="Bolgheri, Tuscany, Italy", country="Italy", appellation="Bolgheri Rosso DOC", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=40.0, price_tier="mid", aliases=["Grattamacco Bolgheri", "Grattamacco Rosso Bolgheri"], description="One of Bolgheri's original estates; Grattamacco's entry-level red is a reliable, terroir-expressive Bolgheri blend."),
    WineCatalogEntry(id="grattamacco-bolgheri-superiore", name="Grattamacco Bolgheri Superiore", producer="Grattamacco", region="Bolgheri, Tuscany, Italy", country="Italy", appellation="Bolgheri Superiore DOC", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Grattamacco Superiore", "Grattamacco Bolgheri DOC Superiore"], description="Grattamacco's flagship Bolgheri Superiore; a serious Cabernet-dominant blend with real aging potential."),
    WineCatalogEntry(id="caprili-brunello", name="Caprili Brunello di Montalcino", producer="Caprili", region="Montalcino, Tuscany, Italy", country="Italy", appellation="Brunello di Montalcino DOCG", varietal="Sangiovese", wine_type="red", avg_retail_price=70.0, price_tier="mid", aliases=["Caprili Brunello Montalcino", "Caprili Montalcino"], description="One of Montalcino's most consistent and fairly-priced Brunello estates; excellent value in the appellation."),
    WineCatalogEntry(id="felsina-rancia", name="Fèlsina Rancia Chianti Classico Gran Selezione", producer="Fèlsina", region="Castelnuovo Berardenga, Tuscany, Italy", country="Italy", appellation="Chianti Classico DOCG Gran Selezione", varietal="Sangiovese", wine_type="red", avg_retail_price=75.0, price_tier="mid", aliases=["Felsina Rancia Gran Selezione", "Felsina Rancia Chianti"], description="Fèlsina is one of Chianti Classico's leading estates; Rancia is their single-vineyard Gran Selezione from limestone-rich soils."),
    WineCatalogEntry(id="pieve-santa-restituta-sugarille", name="Pieve Santa Restituta Sugarille Brunello di Montalcino", producer="Pieve Santa Restituta", region="Montalcino, Tuscany, Italy", country="Italy", appellation="Brunello di Montalcino DOCG", varietal="Sangiovese", wine_type="red", avg_retail_price=380.0, price_tier="luxury", aliases=["Pieve Santa Restituta Brunello", "Gaja Sugarille Brunello", "Sugarille Brunello Montalcino"], description="Gaja's Montalcino estate; Sugarille is their single-vineyard Brunello, combining Gaja's perfectionism with Montalcino's terroir."),
    WineCatalogEntry(id="petrolo-galatrona", name="Petrolo Galatrona Val d'Arno di Sopra", producer="Petrolo", region="Mercatale Valdarno, Tuscany, Italy", country="Italy", appellation="Val d'Arno di Sopra DOC", varietal="Merlot", wine_type="red", avg_retail_price=150.0, price_tier="premium", aliases=["Petrolo Galatrona Merlot", "Galatrona Petrolo Tuscany"], description="Italy's finest Merlot outside Bolgheri; Petrolo's Galatrona is a cult wine from a little-known Tuscan DOC."),
    WineCatalogEntry(id="tenuta-di-trinoro-le-cupole", name="Tenuta di Trinoro Le Cupole", producer="Tenuta di Trinoro", region="Sarteano, Tuscany, Italy", country="Italy", appellation="Toscana IGT", varietal="Cabernet Franc", wine_type="red", avg_retail_price=45.0, price_tier="mid", aliases=["Trinoro Le Cupole", "Andrea Franchetti Le Cupole"], description="Andrea Franchetti's entry-level Trinoro; Le Cupole is a Bordeaux-variety blend from high-altitude Tuscan vineyards."),
    WineCatalogEntry(id="tenuta-di-valgiano", name="Tenuta di Valgiano Colline Lucchesi Rosso", producer="Tenuta di Valgiano", region="Lucca, Tuscany, Italy", country="Italy", appellation="Colline Lucchesi DOC", varietal="Sangiovese", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Valgiano Colline Lucchesi", "Tenuta di Valgiano Sangiovese"], description="One of Tuscany's most compelling biodynamic estates outside Chianti Classico; the estate wine is deeply expressive."),
]

# ---------------------------------------------------------------------------
# FRANCE – Loire Valley
# ---------------------------------------------------------------------------
LOIRE = [
    WineCatalogEntry(id="henri-bourgeois-sancerre-la-d", name="Henri Bourgeois La D de Henri Sancerre Blanc", producer="Henri Bourgeois", region="Chavignol, Sancerre, Loire Valley, France", country="France", appellation="Sancerre AOC", varietal="Sauvignon Blanc", wine_type="white", avg_retail_price=65.0, price_tier="mid", aliases=["Henri Bourgeois Sancerre La D", "La D de Henri Sancerre"], description="Henri Bourgeois's top-tier Sancerre; from the famous Chavignol 'cul de beaujeu' slope, mineral and complex."),
    WineCatalogEntry(id="lucien-crochet-sancerre", name="Lucien Crochet Sancerre Le Chêne Marchand", producer="Lucien Crochet", region="Bué, Sancerre, Loire Valley, France", country="France", appellation="Sancerre AOC", varietal="Sauvignon Blanc", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Lucien Crochet Sancerre", "Crochet Chene Marchand Sancerre"], description="Lucien Crochet produces some of Sancerre's most consistently excellent Sauvignon Blancs; Le Chêne Marchand is the prestige cuvée."),
    WineCatalogEntry(id="pascal-cotat-sancerre", name="Pascal Cotat Sancerre Les Monts Damnés", producer="Pascal Cotat", region="Chavignol, Sancerre, Loire Valley, France", country="France", appellation="Sancerre AOC", varietal="Sauvignon Blanc", wine_type="white", avg_retail_price=120.0, price_tier="premium", aliases=["Pascal Cotat Les Monts Damnes", "Cotat Sancerre Monts Damnes"], description="Pascal Cotat's Sancerre from Les Monts Damnés is one of the Loire's great cult whites; small production, extraordinary mineral depth."),
    WineCatalogEntry(id="domaine-vacheron-sancerre", name="Domaine Vacheron Sancerre Blanc", producer="Domaine Vacheron", region="Sancerre, Loire Valley, France", country="France", appellation="Sancerre AOC", varietal="Sauvignon Blanc", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Vacheron Sancerre", "Domaine Vacheron Sancerre Blanc"], description="One of the most respected biodynamic estates in Sancerre; Vacheron's Blanc is a consistent benchmark."),
    WineCatalogEntry(id="edmond-vatan-sancerre", name="Edmond Vatan Sancerre Clos la Néore", producer="Edmond Vatan", region="Chavignol, Sancerre, Loire Valley, France", country="France", appellation="Sancerre AOC", varietal="Sauvignon Blanc", wine_type="white", avg_retail_price=200.0, price_tier="luxury", aliases=["Edmond Vatan Clos la Neore", "Vatan Sancerre Neore"], description="One of Sancerre's most enigmatic cult wines; Vatan's tiny production from old vines in Chavignol fetches high secondary market prices."),
    WineCatalogEntry(id="henry-pellé-morogues", name="Henry Pellé Menetou-Salon Morogues", producer="Henry Pellé", region="Morogues, Menetou-Salon, Loire Valley, France", country="France", appellation="Menetou-Salon AOC", varietal="Sauvignon Blanc", wine_type="white", avg_retail_price=28.0, price_tier="mid", aliases=["Henry Pelle Menetou-Salon", "Pelle Morogues Menetou Salon"], description="Henry Pellé is Menetou-Salon's leading producer; his Sauvignon Blanc is often better value than Sancerre."),
    WineCatalogEntry(id="nicolas-joly-coulee-de-serrant", name="Nicolas Joly Coulée de Serrant", producer="Nicolas Joly", region="Savennières, Loire Valley, France", country="France", appellation="Coulée de Serrant AOC", varietal="Chenin Blanc", wine_type="white", avg_retail_price=100.0, price_tier="premium", aliases=["Joly Coulee de Serrant", "Coulee de Serrant Savennieres"], description="A monopole AOC; Nicolas Joly's biodynamic Coulée de Serrant is one of the world's great white wines, capable of exceptional aging."),
    WineCatalogEntry(id="mark-angeli-les-fougeraies", name="Mark Angeli Les Fougeraies Anjou Blanc", producer="Ferme de la Sansonnière", region="Thouarcé, Anjou, Loire Valley, France", country="France", appellation="Anjou Blanc AOC", varietal="Chenin Blanc", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Mark Angeli Chenin Blanc", "Sansonniere Les Fougeraies", "Ferme de la Sansonniere"], description="Mark Angeli of Ferme de la Sansonnière is one of the Loire's great natural winemakers; his Chenin Blanc is complex and long-lived."),
    WineCatalogEntry(id="domaine-de-la-taille-aux-loups-husseau", name="Domaine de la Taille aux Loups Montlouis-sur-Loire Brut Réserve", producer="Domaine de la Taille aux Loups", region="Husseau, Montlouis-sur-Loire, Loire Valley, France", country="France", appellation="Montlouis-sur-Loire AOC", varietal="Chenin Blanc", wine_type="sparkling", avg_retail_price=35.0, price_tier="mid", aliases=["Taille aux Loups Montlouis Brut", "Taille aux Loups Jacky Blot"], description="Jacky Blot's Taille aux Loups is the reference for quality Montlouis-sur-Loire sparkling; Brut Réserve is a textbook Pétillant de Loire."),
    WineCatalogEntry(id="thierry-puzelat-chinon", name="Thierry Puzelat Vin de France Rouge", producer="Clos du Tue-Boeuf", region="Cheverny, Loire Valley, France", country="France", appellation="Vin de France", varietal="Gamay", wine_type="red", avg_retail_price=30.0, price_tier="mid", aliases=["Puzelat Gamay Loire", "Clos du Tue-Boeuf Rouge"], description="Thierry Puzelat is one of the Loire's most beloved natural producers; his Gamay-based reds are fragrant, juicy, and alive."),
    WineCatalogEntry(id="charles-joguet-chinon", name="Charles Joguet Chinon Clos de la Dioterie", producer="Charles Joguet", region="Sazilly, Chinon, Loire Valley, France", country="France", appellation="Chinon AOC", varietal="Cabernet Franc", wine_type="red", avg_retail_price=65.0, price_tier="mid", aliases=["Joguet Clos de la Dioterie Chinon", "Charles Joguet Chinon"], description="Charles Joguet is regarded as the greatest Chinon producer; Clos de la Dioterie is his flagship single-vineyard Cabernet Franc."),
    WineCatalogEntry(id="domaine-del-olivier-bellanger-sancerre-rouge", name="Henri Bourgeois Sancerre Rouge La Côte des Monts Damnés", producer="Henri Bourgeois", region="Sancerre, Loire Valley, France", country="France", appellation="Sancerre Rouge AOC", varietal="Pinot Noir", wine_type="red", avg_retail_price=50.0, price_tier="mid", aliases=["Bourgeois Sancerre Rouge", "Henri Bourgeois Pinot Noir Sancerre"], description="Sancerre Rouge from one of the appellation's leading estates; Pinot Noir from chalk soils shows fine, mineral character."),
]

# ---------------------------------------------------------------------------
# FRANCE – Beaujolais
# ---------------------------------------------------------------------------
BEAUJOLAIS = [
    WineCatalogEntry(id="lapierre-moulin-a-vent", name="Marcel Lapierre Morgon", producer="Marcel Lapierre", region="Villié-Morgon, Beaujolais, France", country="France", appellation="Morgon AOC", varietal="Gamay", wine_type="red", avg_retail_price=40.0, price_tier="mid", aliases=["Lapierre Morgon", "Marcel Lapierre Beaujolais"], description="The late Marcel Lapierre is the patron saint of natural Beaujolais; his Morgon defined what the region could be."),
    WineCatalogEntry(id="jean-foillard-morgon", name="Jean Foillard Morgon Côte du Py", producer="Jean Foillard", region="Villié-Morgon, Beaujolais, France", country="France", appellation="Morgon AOC", varietal="Gamay", wine_type="red", avg_retail_price=45.0, price_tier="mid", aliases=["Foillard Morgon Cote du Py", "Jean Foillard Cote du Py"], description="Jean Foillard's Côte du Py is one of Beaujolais's most mineral and structured Gamays; the benchmark for serious Morgon."),
    WineCatalogEntry(id="clos-de-la-roilette-fleurie", name="Clos de la Roilette Fleurie", producer="Clos de la Roilette", region="Fleurie, Beaujolais, France", country="France", appellation="Fleurie AOC", varietal="Gamay", wine_type="red", avg_retail_price=38.0, price_tier="mid", aliases=["Roilette Fleurie", "Clos de la Roilette Beaujolais"], description="The reference Fleurie; fragrant, floral, and silky Gamay from the most feminine of Beaujolais crus."),
    WineCatalogEntry(id="yvon-metras-fleurie", name="Yvon Métras Fleurie", producer="Yvon Métras", region="Fleurie, Beaujolais, France", country="France", appellation="Fleurie AOC", varietal="Gamay", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Metras Fleurie", "Yvon Métras Beaujolais"], description="Yvon Métras is one of the Gang of Four; his Fleurie is one of natural wine's most sought-after Gamays."),
    WineCatalogEntry(id="domaine-des-terres-dorees-beaujolais", name="Jean-Paul Brun Beaujolais L'Ancien", producer="Domaine des Terres Dorées", region="Charnay, Beaujolais, France", country="France", appellation="Beaujolais AOC", varietal="Gamay", wine_type="red", avg_retail_price=22.0, price_tier="mid", aliases=["JP Brun Beaujolais L'Ancien", "Terres Dorees L'Ancien"], description="Jean-Paul Brun's L'Ancien is one of the finest values in French wine; old-vine Gamay of serious depth at an accessible price."),
    WineCatalogEntry(id="chateau-thivin-cote-de-brouilly", name="Château Thivin Côte de Brouilly", producer="Château Thivin", region="Odenas, Beaujolais, France", country="France", appellation="Côte de Brouilly AOC", varietal="Gamay", wine_type="red", avg_retail_price=35.0, price_tier="mid", aliases=["Thivin Cote de Brouilly", "Chateau Thivin Beaujolais"], description="One of the finest Côte de Brouilly producers; Château Thivin's volcanic site produces intense, mineral Gamay."),
    WineCatalogEntry(id="domaine-du-vissoux-moulin-a-vent", name="Domaine du Vissoux Moulin-à-Vent Les Trois Roches", producer="Domaine du Vissoux", region="Saint-Vérand, Beaujolais, France", country="France", appellation="Moulin-à-Vent AOC", varietal="Gamay", wine_type="red", avg_retail_price=30.0, price_tier="mid", aliases=["Vissoux Moulin-a-Vent", "Domaine du Vissoux Pierre Chermette"], description="Pierre Chermette's Vissoux is a Beaujolais benchmark; Les Trois Roches is a structured, age-worthy Moulin-à-Vent."),
    WineCatalogEntry(id="guy-breton-morgon", name="Guy Breton Morgon", producer="Guy Breton", region="Villié-Morgon, Beaujolais, France", country="France", appellation="Morgon AOC", varietal="Gamay", wine_type="red", avg_retail_price=38.0, price_tier="mid", aliases=["Guy Breton Beaujolais", "Breton Morgon"], description="Guy Breton is another of the Gang of Four; a natural wine icon producing benchmark Morgon."),
    WineCatalogEntry(id="domaine-de-la-grand-cour-fleurie", name="Domaine de la Grand'Cour Fleurie Cuvée Vieilles Vignes", producer="Domaine de la Grand'Cour", region="Fleurie, Beaujolais, France", country="France", appellation="Fleurie AOC", varietal="Gamay", wine_type="red", avg_retail_price=40.0, price_tier="mid", aliases=["Grand Cour Fleurie", "Jean-Louis Dutraive Fleurie"], description="Jean-Louis Dutraive produces some of Fleurie's most vibrant and pure Gamay from old vines."),
]

# ---------------------------------------------------------------------------
# FRANCE – Jura
# ---------------------------------------------------------------------------
JURA = [
    WineCatalogEntry(id="overnoy-arbois-savagnin", name="Pierre Overnoy Arbois Savagnin", producer="Pierre Overnoy", region="Pupillin, Jura, France", country="France", appellation="Arbois AOC", varietal="Savagnin", wine_type="white", avg_retail_price=280.0, price_tier="luxury", aliases=["Overnoy Savagnin Arbois", "Pierre Overnoy Jura"], description="Pierre Overnoy is a legend of natural wine; his oxidative Savagnin is among the most sought-after bottles in the natural wine world."),
    WineCatalogEntry(id="domaine-ganevat-les-chalasses", name="Domaine Ganevat Les Chalasses Vieilles Vignes", producer="Domaine Ganevat", region="Rotalier, Jura, France", country="France", appellation="Côtes du Jura AOC", varietal="Savagnin", wine_type="white", avg_retail_price=120.0, price_tier="premium", aliases=["Ganevat Les Chalasses", "Jean-François Ganevat Jura"], description="Jean-François Ganevat produces some of Jura's most expressive single-parcel wines; Les Chalasses is a benchmark Savagnin."),
    WineCatalogEntry(id="bornard-arbois-trousseau", name="Philippe Bornard Arbois Trousseau", producer="Philippe Bornard", region="Pupillin, Jura, France", country="France", appellation="Arbois AOC", varietal="Trousseau", wine_type="red", avg_retail_price=65.0, price_tier="mid", aliases=["Bornard Trousseau Arbois", "Philippe Bornard Jura"], description="Philippe Bornard is one of Pupillin's great natural wine producers; his Trousseau is fragrant, elegant, and utterly distinctive."),
    WineCatalogEntry(id="domaine-de-la-tournelle-vin-jaune", name="Domaine de la Tournelle Vin Jaune Arbois", producer="Domaine de la Tournelle", region="Arbois, Jura, France", country="France", appellation="Arbois Vin Jaune AOC", varietal="Savagnin", wine_type="white", avg_retail_price=80.0, price_tier="premium", aliases=["Tournelle Vin Jaune", "Evelyne Tournelle Vin Jaune Arbois"], description="One of the finest and most accessible Vin Jaune producers; Tournelle's version shows the unique flor-aged character of this Jura specialty."),
    WineCatalogEntry(id="tissot-arbois-poulsard", name="Bénédicte et Stéphane Tissot Arbois Poulsard", producer="Domaine Tissot", region="Montigny-lès-Arsures, Jura, France", country="France", appellation="Arbois AOC", varietal="Poulsard", wine_type="red", avg_retail_price=35.0, price_tier="mid", aliases=["Tissot Poulsard Arbois", "Stephane Tissot Jura Poulsard"], description="Stéphane Tissot is Jura's most prominent producer; his Poulsard is the reference for this delicate, hauntingly beautiful Jura red."),
    WineCatalogEntry(id="domaine-des-cavarodes-rouge", name="Domaine des Cavarodes Savagnin Ouillé", producer="Domaine des Cavarodes", region="Cesancey, Jura, France", country="France", appellation="Côtes du Jura AOC", varietal="Savagnin", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Cavarodes Savagnin Ouille", "Domaine des Cavarodes Jura"], description="Etienne Thiébaud's Cavarodes is a rising Jura star; his Savagnin Ouillé (non-oxidative) is a fresh, pure expression of the grape."),
]

# ---------------------------------------------------------------------------
# FRANCE – Languedoc & Roussillon
# ---------------------------------------------------------------------------
LANGUEDOC = [
    WineCatalogEntry(id="domaine-de-la-grange-des-peres", name="Domaine de la Grange des Pères", producer="Domaine de la Grange des Pères", region="Aniane, Hérault, Languedoc, France", country="France", appellation="Vin de Pays de l'Hérault", varietal="Syrah", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Grange des Peres", "Laurent Vaillé Grange des Peres"], description="Laurent Vaillé's Grange des Pères is one of France's greatest wines; a Syrah-dominated blend that rivals the finest Northern Rhône."),
    WineCatalogEntry(id="clos-marie-pic-saint-loup", name="Clos Marie Pic Saint-Loup", producer="Clos Marie", region="Pic Saint-Loup, Languedoc, France", country="France", appellation="Languedoc Pic Saint-Loup AOC", varietal="Grenache", wine_type="red", avg_retail_price=35.0, price_tier="mid", aliases=["Clos Marie Languedoc", "Clos Marie Pic Saint Loup"], description="Christophe Peyrus's Clos Marie is the reference for Pic Saint-Loup; elegant, cool-climate Grenache and Syrah."),
    WineCatalogEntry(id="domaine-olivier-pithon-cote-catalanes", name="Domaine Olivier Pithon La D18 Côtes Catalanes", producer="Domaine Olivier Pithon", region="Calce, Roussillon, France", country="France", appellation="Côtes Catalanes IGP", varietal="Grenache", wine_type="red", avg_retail_price=40.0, price_tier="mid", aliases=["Olivier Pithon Roussillon", "Pithon La D18 Cotes Catalanes"], description="Olivier Pithon's biodynamic estate in Roussillon; La D18 is a rich, old-vine Grenache blend with Southern character."),
    WineCatalogEntry(id="domaine-gauby-muntada", name="Domaine Gauby Muntada", producer="Domaine Gauby", region="Calce, Roussillon, France", country="France", appellation="Côtes Catalanes IGP", varietal="Grenache", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Gauby Muntada Roussillon", "Gérard Gauby Muntada"], description="Gérard Gauby's top red; from ancient vines in Calce, Muntada is one of Roussillon's great wines."),
    WineCatalogEntry(id="mas-jullien-jonquieres", name="Mas Jullien Jonquières Terrasses du Larzac", producer="Mas Jullien", region="Jonquières, Languedoc, France", country="France", appellation="Terrasses du Larzac AOC", varietal="Grenache", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Mas Jullien Languedoc", "Olivier Jullien Mas Jullien"], description="Olivier Jullien is the pioneering figure of the Languedoc's quality revolution; Mas Jullien's red is a benchmark for the region."),
]

# ---------------------------------------------------------------------------
# FRANCE – Alsace (additional)
# ---------------------------------------------------------------------------
ALSACE = [
    WineCatalogEntry(id="zind-humbrecht-riesling-brand", name="Zind-Humbrecht Riesling Brand Grand Cru", producer="Zind-Humbrecht", region="Turckheim, Alsace, France", country="France", appellation="Alsace Grand Cru Brand AOC", varietal="Riesling", wine_type="white", avg_retail_price=90.0, price_tier="premium", aliases=["Zind Humbrecht Brand Riesling", "Humbrecht Riesling Brand Grand Cru"], description="Zind-Humbrecht is Alsace's most celebrated producer; Brand is a granite grand cru producing exceptional Riesling."),
    WineCatalogEntry(id="weinbach-clos-des-capucins", name="Domaine Weinbach Riesling Clos des Capucins", producer="Domaine Weinbach", region="Kaysersberg, Alsace, France", country="France", appellation="Alsace AOC", varietal="Riesling", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Weinbach Clos des Capucins", "Weinbach Riesling Alsace"], description="Domaine Weinbach is one of Alsace's most consistent estates; Clos des Capucins is their reliable, food-friendly Riesling."),
    WineCatalogEntry(id="josmeyer-le-kottabe-riesling", name="Josmeyer Le Kottabé Riesling", producer="Josmeyer", region="Wintzenheim, Alsace, France", country="France", appellation="Alsace AOC", varietal="Riesling", wine_type="white", avg_retail_price=35.0, price_tier="mid", aliases=["Josmeyer Riesling Le Kottabe", "Josmeyer Alsace Riesling"], description="Josmeyer is a serious biodynamic Alsace producer; Le Kottabé is a reliable, mineral Riesling at an honest price."),
    WineCatalogEntry(id="dirler-cade-saering", name="Dirler-Cadé Saering Grand Cru Riesling", producer="Dirler-Cadé", region="Bergholtz, Alsace, France", country="France", appellation="Alsace Grand Cru Saering AOC", varietal="Riesling", wine_type="white", avg_retail_price=50.0, price_tier="mid", aliases=["Dirler Cade Saering Riesling", "Dirler Saering Grand Cru"], description="A small, biodynamic Alsace producer; Saering is a limestone-rich grand cru producing delicate, floral Riesling."),
    WineCatalogEntry(id="marc-kreydenweiss-kritt", name="Marc Kreydenweiss Kritt Alsace Pinot Blanc", producer="Marc Kreydenweiss", region="Andlau, Alsace, France", country="France", appellation="Alsace AOC", varietal="Pinot Blanc", wine_type="white", avg_retail_price=28.0, price_tier="mid", aliases=["Kreydenweiss Pinot Blanc", "Marc Kreydenweiss Alsace"], description="Marc Kreydenweiss's biodynamic estate produces some of Alsace's most honest and terroir-expressive whites."),
]

# ---------------------------------------------------------------------------
# SPAIN – More regional
# ---------------------------------------------------------------------------
SPAIN_REGIONAL = [
    WineCatalogEntry(id="terroir-al-limit-priorat", name="Terroir al Limit Les Tosses Priorat", producer="Terroir al Limit", region="Torroja del Priorat, Priorat, Catalonia, Spain", country="Spain", appellation="Priorat DOCa", varietal="Grenache", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Terroir al Limit Priorat", "Dominik Huber Priorat"], description="Dominik Huber's Terroir al Limit was instrumental in shifting Priorat toward freshness and minerality; Les Tosses is the entry-level red."),
    WineCatalogEntry(id="clos-mogador-priorat", name="Clos Mogador Priorat", producer="Clos Mogador", region="Gratallops, Priorat, Catalonia, Spain", country="Spain", appellation="Priorat DOCa", varietal="Grenache", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Mogador Priorat", "René Barbier Clos Mogador"], description="René Barbier's Clos Mogador is one of Priorat's original five estates; deeply complex old-vine Grenache and Carignan."),
    WineCatalogEntry(id="descendientes-de-j-palacios-corullon", name="Descendientes de J. Palacios Bierzo Corullón", producer="Descendientes de J. Palacios", region="Bierzo, Castilla y León, Spain", country="Spain", appellation="Bierzo DO", varietal="Mencía", wine_type="red", avg_retail_price=65.0, price_tier="mid", aliases=["Descendientes J Palacios Corullon", "Ricardo Perez Bierzo Corullon", "Corullon Bierzo"], description="Ricardo Pérez Palacios put Bierzo on the map; Corullón is the estate wine, showing the remarkable potential of old-vine Mencía."),
    WineCatalogEntry(id="raul-perez-ultreia", name="Raúl Pérez Ultreia Bierzo", producer="Raúl Pérez", region="Bierzo, Castilla y León, Spain", country="Spain", appellation="Bierzo DO", varietal="Mencía", wine_type="red", avg_retail_price=35.0, price_tier="mid", aliases=["Raul Perez Ultreia Saint Jacques", "Ultreia Bierzo Mencia"], description="Raúl Pérez is Spain's most prolific and respected artisan winemaker; Ultreia is his approachable Bierzo expression."),
    WineCatalogEntry(id="bodegas-roda-sela", name="Bodegas Roda Sela Rioja", producer="Bodegas Roda", region="Haro, Rioja, Spain", country="Spain", appellation="Rioja DOCa", varietal="Tempranillo", wine_type="red", avg_retail_price=30.0, price_tier="mid", aliases=["Roda Sela Rioja", "Bodegas Roda Rioja Sela"], description="Roda is one of Haro's most quality-focused producers; Sela is the entry-level Rioja, a model of modern elegance."),
    WineCatalogEntry(id="bodegas-roda-roda-i", name="Bodegas Roda Roda I Rioja Reserva", producer="Bodegas Roda", region="Haro, Rioja, Spain", country="Spain", appellation="Rioja DOCa Reserva", varietal="Tempranillo", wine_type="red", avg_retail_price=70.0, price_tier="mid", aliases=["Roda I Reserva Rioja", "Bodegas Roda Reserva I"], description="Roda I is one of Rioja's finest Reservas; old-vine Tempranillo with exceptional concentration and finesse."),
    WineCatalogEntry(id="telmo-rodriguez-dehesa-gago", name="Telmo Rodríguez Dehesa Gago Toro", producer="Telmo Rodríguez", region="Toro, Castilla y León, Spain", country="Spain", appellation="Toro DO", varietal="Tinta de Toro", wine_type="red", avg_retail_price=22.0, price_tier="mid", aliases=["Telmo Rodriguez Toro", "Dehesa Gago Toro"], description="Telmo Rodríguez is a champion of Spain's native grapes; Dehesa Gago brings attention to Toro's powerful Tempranillo clones."),
    WineCatalogEntry(id="envinate-lousas-bierzo", name="Envínate Lousas Parcela Camiño Novo", producer="Envínate", region="Ribeira Sacra, Galicia, Spain", country="Spain", appellation="Ribeira Sacra DO", varietal="Mencía", wine_type="red", avg_retail_price=45.0, price_tier="mid", aliases=["Envinate Lousas", "Envinate Ribeira Sacra Lousas"], description="Envínate is the most exciting young wine project in Spain; Lousas is their Mencía from steep schist terraces in Ribeira Sacra."),
    WineCatalogEntry(id="do-ferreiro-albarino", name="Do Ferreiro Albariño Rías Baixas", producer="Do Ferreiro", region="Meaño, Rías Baixas, Galicia, Spain", country="Spain", appellation="Rías Baixas DO", varietal="Albariño", wine_type="white", avg_retail_price=28.0, price_tier="mid", aliases=["Do Ferreiro Rias Baixas", "Do Ferreiro Albarino Galicia"], description="Gerardo Méndez produces some of Rías Baixas's most complex and long-lived Albariños from very old vines."),
    WineCatalogEntry(id="pazo-senorans-albarino", name="Pazo Señorans Albariño Rías Baixas", producer="Pazo Señorans", region="Meis, Rías Baixas, Galicia, Spain", country="Spain", appellation="Rías Baixas DO", varietal="Albariño", wine_type="white", avg_retail_price=30.0, price_tier="mid", aliases=["Pazo Senorans Albarino", "Pazo Señorans Rias Baixas"], description="One of Rías Baixas's most respected producers; a benchmark for aromatic, crisp, food-friendly Albariño."),
]

# ---------------------------------------------------------------------------
# GERMANY – More producers
# ---------------------------------------------------------------------------
GERMANY_ADD = [
    WineCatalogEntry(id="jj-christoffel-mosel-riesling", name="J.J. Christoffel Ürziger Würzgarten Riesling Spätlese", producer="J.J. Christoffel", region="Ürzig, Mosel, Germany", country="Germany", appellation="Mosel", varietal="Riesling", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["JJ Christoffel Urziger Wurzgarten", "Christoffel Urziger Wurzgarten Riesling"], description="J.J. Christoffel's Ürziger Würzgarten Spätlese is one of the Mosel's most exciting and lively Rieslings from volcanic red slate soils."),
    WineCatalogEntry(id="selbach-oster-zeltinger-sonnenuhr", name="Selbach-Oster Zeltinger Sonnenuhr Riesling Spätlese", producer="Selbach-Oster", region="Zeltingen, Mosel, Germany", country="Germany", appellation="Mosel", varietal="Riesling", wine_type="white", avg_retail_price=40.0, price_tier="mid", aliases=["Selbach Oster Zeltinger", "Johannes Selbach Spatlese"], description="Selbach-Oster consistently produces some of the Mosel's finest Rieslings; Zeltinger Sonnenuhr is a brilliant, age-worthy Spätlese."),
    WineCatalogEntry(id="van-volxem-scharzhofberger", name="Van Volxem Scharzhofberger Pergentsknopp Riesling", producer="Van Volxem", region="Wiltingen, Saar, Germany", country="Germany", appellation="Mosel", varietal="Riesling", wine_type="white", avg_retail_price=75.0, price_tier="mid", aliases=["Van Volxem Scharzhofberger GG", "Roman Niewodniczanski Van Volxem"], description="Roman Niewodniczański's Van Volxem produces some of the Saar's most powerful and mineral Rieslings from historic sites."),
    WineCatalogEntry(id="emrich-schonleber-halenberg", name="Emrich-Schönleber Halenberg Riesling GG", producer="Emrich-Schönleber", region="Monzingen, Nahe, Germany", country="Germany", appellation="Nahe", varietal="Riesling", wine_type="white", avg_retail_price=75.0, price_tier="mid", aliases=["Emrich Schonleber Halenberg GG", "Schonleber Halenberg Riesling Nahe"], description="Werner Schönleber's Halenberg is one of the Nahe's greatest sites; alongside Dönnhoff, this is the reference for Nahe Riesling."),
    WineCatalogEntry(id="fritz-haag-brauneberger-juffer", name="Fritz Haag Brauneberger Juffer Riesling Spätlese", producer="Fritz Haag", region="Brauneberg, Mosel, Germany", country="Germany", appellation="Mosel", varietal="Riesling", wine_type="white", avg_retail_price=50.0, price_tier="mid", aliases=["Fritz Haag Juffer Spatlese", "Haag Brauneberger Juffer"], description="Fritz Haag is a Mosel legend; the Brauneberger Juffer Spätlese is a classic expression of the site's rich, honeyed style."),
    WineCatalogEntry(id="peter-lauer-ayler-kupp", name="Peter Lauer Ayler Kupp Riesling Kabinett", producer="Peter Lauer", region="Ayl, Saar, Germany", country="Germany", appellation="Mosel", varietal="Riesling", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Lauer Ayler Kupp Kabinett", "Peter Lauer Saar Riesling"], description="Florian Lauer produces among the most refined Rieslings on the Saar; Ayler Kupp Kabinett is a perfect expression of light, mineral German Riesling."),
    WineCatalogEntry(id="clemens-busch-marienburg", name="Clemens Busch Pündericher Marienburg Riesling Kabinett", producer="Clemens Busch", region="Pünderich, Mosel, Germany", country="Germany", appellation="Mosel", varietal="Riesling", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Clemens Busch Marienburg", "Busch Pundericher Marienburg Riesling"], description="Clemens Busch is among the Mosel's most thoughtful biodynamic producers; Marienburg is a benchmark for mineral, low-alcohol Mosel Riesling."),
]

# ---------------------------------------------------------------------------
# CHABLIS – Essential grand cru / premier cru producers
# ---------------------------------------------------------------------------
CHABLIS_CLASSICS = [
    WineCatalogEntry(id="raveneau-chablis-village", name="Domaine Raveneau Chablis", producer="Domaine Raveneau", region="Chablis, Burgundy, France", country="France", appellation="Chablis", varietal="Chardonnay", wine_type="white", avg_retail_price=95.0, price_tier="premium", aliases=["Raveneau Chablis", "Jean-Marie Raveneau Chablis Village"], description="Raveneau is the reference domaine of Chablis; even the village bottling shows extraordinary mineral precision from old vines on Kimmeridgian limestone."),
    WineCatalogEntry(id="raveneau-montee-de-tonnerre", name="Domaine Raveneau Chablis Montée de Tonnerre 1er Cru", producer="Domaine Raveneau", region="Chablis, Burgundy, France", country="France", appellation="Chablis Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=220.0, price_tier="luxury", aliases=["Raveneau Montee de Tonnerre", "Raveneau Montée Tonnerre Premier Cru"], description="Montée de Tonnerre is widely considered Chablis's greatest Premier Cru; Raveneau's version is the standard-bearer for the appellation."),
    WineCatalogEntry(id="raveneau-valmur", name="Domaine Raveneau Chablis Valmur Grand Cru", producer="Domaine Raveneau", region="Chablis, Burgundy, France", country="France", appellation="Chablis Grand Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=500.0, price_tier="ultra-luxury", aliases=["Raveneau Valmur GC", "Raveneau Valmur Grand Cru Chablis"], description="Valmur Grand Cru from Raveneau is one of the most sought-after Chablis in existence; it ages for decades and achieves transcendent complexity."),
    WineCatalogEntry(id="raveneau-butteaux", name="Domaine Raveneau Chablis Butteaux 1er Cru", producer="Domaine Raveneau", region="Chablis, Burgundy, France", country="France", appellation="Chablis Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=250.0, price_tier="luxury", aliases=["Raveneau Butteaux", "Raveneau Montée de Tonnerre Butteaux"], description="Butteaux is a sub-climat of Montée de Tonnerre; Raveneau's parcels produce a richer, more textured Chablis Premier Cru with great longevity."),
    WineCatalogEntry(id="dauvissat-chablis-village", name="Vincent Dauvissat Chablis", producer="Vincent Dauvissat", region="Chablis, Burgundy, France", country="France", appellation="Chablis", varietal="Chardonnay", wine_type="white", avg_retail_price=90.0, price_tier="premium", aliases=["Dauvissat Chablis", "Vincent Dauvissat Village Chablis", "Rene et Vincent Dauvissat"], description="Vincent Dauvissat's village Chablis is a benchmark for the appellation: taut, mineral, and loaded with oyster-shell and lemon-cream character."),
    WineCatalogEntry(id="dauvissat-la-forest", name="Vincent Dauvissat Chablis La Forest 1er Cru", producer="Vincent Dauvissat", region="Chablis, Burgundy, France", country="France", appellation="Chablis Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=210.0, price_tier="luxury", aliases=["Dauvissat La Forest", "Dauvissat Forest Premier Cru"], description="La Forest Premier Cru from Dauvissat shows more body and depth than the village; a wine that bridges the gap between Premier and Grand Cru."),
    WineCatalogEntry(id="dauvissat-les-clos", name="Vincent Dauvissat Chablis Les Clos Grand Cru", producer="Vincent Dauvissat", region="Chablis, Burgundy, France", country="France", appellation="Chablis Grand Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=460.0, price_tier="ultra-luxury", aliases=["Dauvissat Les Clos GC", "Dauvissat Chablis Les Clos Grand Cru"], description="Les Clos is Chablis's most celebrated Grand Cru; Dauvissat's version rivals Raveneau's in prestige and is among the world's greatest white wines."),
    WineCatalogEntry(id="dauvissat-vaillons", name="Vincent Dauvissat Chablis Vaillons 1er Cru", producer="Vincent Dauvissat", region="Chablis, Burgundy, France", country="France", appellation="Chablis Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=190.0, price_tier="luxury", aliases=["Dauvissat Vaillons", "Dauvissat Vaillons Premier Cru"], description="Vaillons is one of Chablis's most important left-bank Premier Crus; Dauvissat's version is sleek and mineral with wonderful saline tension."),
    WineCatalogEntry(id="william-fevre-chablis", name="William Fèvre Chablis", producer="William Fèvre", region="Chablis, Burgundy, France", country="France", appellation="Chablis", varietal="Chardonnay", wine_type="white", avg_retail_price=35.0, price_tier="mid", aliases=["William Fevre Chablis Village", "Fevre Chablis"], description="William Fèvre is one of Chablis's largest quality estates; the village Chablis is clean, brisk, and a reliable restaurant staple."),
    WineCatalogEntry(id="william-fevre-montee-de-tonnerre", name="William Fèvre Chablis Montée de Tonnerre 1er Cru", producer="William Fèvre", region="Chablis, Burgundy, France", country="France", appellation="Chablis Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=85.0, price_tier="premium", aliases=["William Fevre Montee de Tonnerre", "Fevre Montée Tonnerre 1er Cru"], description="Fèvre's Montée de Tonnerre is a textbook Premier Cru Chablis: flinty and precise with great freshness."),
    WineCatalogEntry(id="william-fevre-les-clos", name="William Fèvre Chablis Les Clos Grand Cru", producer="William Fèvre", region="Chablis, Burgundy, France", country="France", appellation="Chablis Grand Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=185.0, price_tier="luxury", aliases=["William Fevre Les Clos Grand Cru", "Fevre Chablis Les Clos GC"], description="Fèvre's Les Clos is the most powerful and mineral of their Grand Cru bottlings, with excellent aging potential."),
    WineCatalogEntry(id="christian-moreau-chablis", name="Christian Moreau Père et Fils Chablis", producer="Christian Moreau Père et Fils", region="Chablis, Burgundy, France", country="France", appellation="Chablis", varietal="Chardonnay", wine_type="white", avg_retail_price=35.0, price_tier="mid", aliases=["Christian Moreau Chablis", "Moreau Chablis Village"], description="Christian Moreau is a family domaine with old vines on multiple Grand Cru sites; the village Chablis is an honest introduction to the appellation."),
    WineCatalogEntry(id="patrick-piuze-montee-de-tonnerre", name="Patrick Piuze Chablis Montée de Tonnerre 1er Cru", producer="Patrick Piuze", region="Chablis, Burgundy, France", country="France", appellation="Chablis Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=70.0, price_tier="premium", aliases=["Piuze Montee de Tonnerre", "Patrick Piuze 1er Cru Chablis"], description="Patrick Piuze is one of Chablis's most skilled modern vigneron-négociants; his Montée de Tonnerre is precise and compelling."),
    WineCatalogEntry(id="julien-brocard-chablis", name="Julien Brocard Chablis Boissonneuse", producer="Julien Brocard", region="Chablis, Burgundy, France", country="France", appellation="Chablis", varietal="Chardonnay", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Brocard Chablis Boissonneuse", "Julien Brocard Chablis Village"], description="Julien Brocard is a leading proponent of biodynamic viticulture in Chablis; his Boissonneuse bottling shows vivid terroir character."),
]

# ---------------------------------------------------------------------------
# MÂCONNAIS / POUILLY-FUISSÉ – Key terroir estates
# ---------------------------------------------------------------------------
MACONNAIS = [
    WineCatalogEntry(id="jules-desjourneys-pouilly-fuisse", name="Jules Desjourneys Pouilly-Fuissé Les Bouthières", producer="Jules Desjourneys", region="Pouilly-Fuissé, Burgundy, France", country="France", appellation="Pouilly-Fuissé", varietal="Chardonnay", wine_type="white", avg_retail_price=95.0, price_tier="premium", aliases=["Desjourneys Les Bouthieres", "Jules Desjourneys Pouilly Fuisse"], description="Jules Desjourneys is one of the most sought-after micro-producers in Mâconnais; tiny quantities of precise, age-worthy Pouilly-Fuissé."),
    WineCatalogEntry(id="barraud-pouilly-fuisse-vv", name="Daniel et Julien Barraud Pouilly-Fuissé Vieilles Vignes", producer="Daniel et Julien Barraud", region="Pouilly-Fuissé, Burgundy, France", country="France", appellation="Pouilly-Fuissé", varietal="Chardonnay", wine_type="white", avg_retail_price=80.0, price_tier="premium", aliases=["Barraud Pouilly Fuisse VV", "Daniel Julien Barraud Vieilles Vignes"], description="Barraud is a leading family domaine in Vergisson; their Vieilles Vignes bottling is among the most complex examples of Pouilly-Fuissé."),
    WineCatalogEntry(id="heritiers-comte-lafon-macon", name="Héritiers du Comte Lafon Mâcon-Milly-Lamartine", producer="Héritiers du Comte Lafon", region="Mâconnais, Burgundy, France", country="France", appellation="Mâcon-Villages", varietal="Chardonnay", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Heritiers Comte Lafon Macon", "Comtes Lafon Macon Milly Lamartine"], description="The Lafon family's Mâconnais project produces some of the region's most refined and mineral Chardonnay from biodynamically farmed vines."),
    WineCatalogEntry(id="heritiers-comte-lafon-vire-clesse", name="Héritiers du Comte Lafon Viré-Clessé", producer="Héritiers du Comte Lafon", region="Viré-Clessé, Burgundy, France", country="France", appellation="Viré-Clessé", varietal="Chardonnay", wine_type="white", avg_retail_price=58.0, price_tier="mid", aliases=["Heritiers Comte Lafon Vire Clesse", "Comtes Lafon Vire Clesse"], description="Viré-Clessé from Héritiers du Comte Lafon is a step up in texture and depth from their village Mâcon; one of the region's most reliable whites."),
    WineCatalogEntry(id="chateau-fuisse-le-clos", name="Château Fuissé Pouilly-Fuissé Le Clos", producer="Château Fuissé", region="Pouilly-Fuissé, Burgundy, France", country="France", appellation="Pouilly-Fuissé", varietal="Chardonnay", wine_type="white", avg_retail_price=70.0, price_tier="premium", aliases=["Chateau Fuisse Le Clos", "Fuisse Pouilly Fuisse Le Clos"], description="Château Fuissé's Le Clos is one of Pouilly-Fuissé's iconic single-vineyard bottlings, with opulent fruit and superb aging potential."),
    WineCatalogEntry(id="bret-brothers-pouilly-fuisse", name="Domaine Bret Brothers Pouilly-Fuissé Les Crays", producer="Domaine Bret Brothers", region="Pouilly-Fuissé, Burgundy, France", country="France", appellation="Pouilly-Fuissé", varietal="Chardonnay", wine_type="white", avg_retail_price=65.0, price_tier="premium", aliases=["Bret Brothers Les Crays", "Bret Brothers Pouilly Fuisse"], description="The Bret Brothers are key figures in the Mâconnais natural wine scene; Les Crays is their benchmark cuvée from old vines in Vinzelles."),
    WineCatalogEntry(id="jean-marc-boillot-puligny", name="Jean-Marc Boillot Puligny-Montrachet", producer="Jean-Marc Boillot", region="Puligny-Montrachet, Burgundy, France", country="France", appellation="Puligny-Montrachet", varietal="Chardonnay", wine_type="white", avg_retail_price=100.0, price_tier="premium", aliases=["JM Boillot Puligny Montrachet", "Jean Marc Boillot Puligny"], description="Jean-Marc Boillot is one of Puligny's most consistent producers; his village Puligny combines elegance and precision."),
    WineCatalogEntry(id="olivier-leflaive-puligny", name="Olivier Leflaive Puligny-Montrachet Les Folatières 1er Cru", producer="Olivier Leflaive", region="Puligny-Montrachet, Burgundy, France", country="France", appellation="Puligny-Montrachet Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=85.0, price_tier="premium", aliases=["Olivier Leflaive Folatières", "Olivier Leflaive 1er Cru Puligny"], description="Olivier Leflaive's négociant house consistently over-delivers for the price; Les Folatières is one of Puligny's finest Premier Crus."),
]

# ---------------------------------------------------------------------------
# WHITE BURGUNDY – Additional cuvées for depth
# ---------------------------------------------------------------------------
BURGUNDY_WHITE_EXTRA = [
    WineCatalogEntry(id="coche-dury-bourgogne-blanc", name="Domaine Coche-Dury Bourgogne Blanc", producer="Domaine Coche-Dury", region="Meursault, Burgundy, France", country="France", appellation="Bourgogne", varietal="Chardonnay", wine_type="white", avg_retail_price=450.0, price_tier="ultra-luxury", aliases=["Coche Dury Bourgogne Blanc", "Coche-Dury Bourgogne Chardonnay"], description="Coche-Dury's Bourgogne Blanc is the most sought-after village Bourgogne in existence; tiny production and extraordinary winemaking command Grand Cru prices."),
    WineCatalogEntry(id="coche-dury-meursault-village", name="Domaine Coche-Dury Meursault", producer="Domaine Coche-Dury", region="Meursault, Burgundy, France", country="France", appellation="Meursault", varietal="Chardonnay", wine_type="white", avg_retail_price=850.0, price_tier="ultra-luxury", aliases=["Coche Dury Meursault", "Jean-François Coche-Dury Meursault"], description="Coche-Dury's village Meursault is among the world's most expensive village-level whites; it rivals many Premiers Crus in quality and commands extraordinary prices."),
    WineCatalogEntry(id="coche-dury-puligny-enseigneres", name="Domaine Coche-Dury Puligny-Montrachet Les Enseignères", producer="Domaine Coche-Dury", region="Puligny-Montrachet, Burgundy, France", country="France", appellation="Puligny-Montrachet", varietal="Chardonnay", wine_type="white", avg_retail_price=1800.0, price_tier="ultra-luxury", aliases=["Coche Dury Puligny Enseigneres", "Coche-Dury Les Enseignères Puligny"], description="Coche-Dury's Puligny-Montrachet Les Enseignères is a village-level wine of astonishing concentration; one of Burgundy's most mythical bottles."),
    WineCatalogEntry(id="comtes-lafon-meursault-charmes", name="Domaine des Comtes Lafon Meursault Charmes 1er Cru", producer="Domaine des Comtes Lafon", region="Meursault, Burgundy, France", country="France", appellation="Meursault Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=500.0, price_tier="ultra-luxury", aliases=["Comtes Lafon Meursault Charmes", "Lafon Charmes Meursault"], description="Comtes Lafon's Charmes 1er Cru is the richest and most generous of their Premier Cru range; a classic voluptuous Meursault."),
    WineCatalogEntry(id="comtes-lafon-meursault-clos-barre", name="Domaine des Comtes Lafon Meursault Clos de la Barre", producer="Domaine des Comtes Lafon", region="Meursault, Burgundy, France", country="France", appellation="Meursault", varietal="Chardonnay", wine_type="white", avg_retail_price=400.0, price_tier="ultra-luxury", aliases=["Lafon Clos de la Barre", "Comtes Lafon Clos Barre Meursault"], description="Clos de la Barre is the Lafon domaine's home vineyard; a richer, more textured Meursault village-level wine with excellent cellaring potential."),
    WineCatalogEntry(id="ramonet-chassagne-ruchottes", name="Domaine Ramonet Chassagne-Montrachet Les Ruchottes 1er Cru", producer="Domaine Ramonet", region="Chassagne-Montrachet, Burgundy, France", country="France", appellation="Chassagne-Montrachet Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=200.0, price_tier="luxury", aliases=["Ramonet Chassagne Ruchottes", "Ramonet Les Ruchottes 1er Cru"], description="Les Ruchottes is one of Chassagne's premier crus closest to Bâtard-Montrachet; Ramonet's bottling is one of the appellation's finest."),
    WineCatalogEntry(id="ramonet-batard-montrachet", name="Domaine Ramonet Bâtard-Montrachet Grand Cru", producer="Domaine Ramonet", region="Chassagne-Montrachet, Burgundy, France", country="France", appellation="Bâtard-Montrachet", varietal="Chardonnay", wine_type="white", avg_retail_price=700.0, price_tier="ultra-luxury", aliases=["Ramonet Batard Montrachet", "Ramonet Bâtard Grand Cru"], description="Ramonet's Bâtard-Montrachet is among Burgundy's most revered Grand Crus; it demonstrates extraordinary richness and longevity."),
    WineCatalogEntry(id="roulot-meursault-caillerets", name="Domaine Roulot Meursault Caillerets 1er Cru", producer="Domaine Roulot", region="Meursault, Burgundy, France", country="France", appellation="Meursault Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=350.0, price_tier="ultra-luxury", aliases=["Roulot Meursault Caillerets", "Jean-Marc Roulot Caillerets"], description="Caillerets is one of Meursault's most prized Premier Crus; Roulot's bottling is strikingly tense and mineral compared to the richer Charmes."),
    WineCatalogEntry(id="roulot-meursault-tillets", name="Domaine Roulot Meursault Les Tillets", producer="Domaine Roulot", region="Meursault, Burgundy, France", country="France", appellation="Meursault", varietal="Chardonnay", wine_type="white", avg_retail_price=200.0, price_tier="luxury", aliases=["Roulot Les Tillets Meursault", "Jean-Marc Roulot Meursault Village"], description="Les Tillets is one of Roulot's village-level Meursaults, showing the extraordinary precision that defines even their entry-level wines."),
    WineCatalogEntry(id="sauzet-batard-montrachet", name="Domaine Etienne Sauzet Bâtard-Montrachet Grand Cru", producer="Domaine Etienne Sauzet", region="Puligny-Montrachet, Burgundy, France", country="France", appellation="Bâtard-Montrachet", varietal="Chardonnay", wine_type="white", avg_retail_price=680.0, price_tier="ultra-luxury", aliases=["Sauzet Batard Montrachet", "Etienne Sauzet Bâtard Grand Cru"], description="Sauzet's Bâtard-Montrachet is one of their greatest Grand Cru wines; a massive, complex white Burgundy of extraordinary depth."),
    WineCatalogEntry(id="leflaive-batard-montrachet", name="Domaine Leflaive Bâtard-Montrachet Grand Cru", producer="Domaine Leflaive", region="Puligny-Montrachet, Burgundy, France", country="France", appellation="Bâtard-Montrachet", varietal="Chardonnay", wine_type="white", avg_retail_price=650.0, price_tier="ultra-luxury", aliases=["Leflaive Batard Montrachet", "Domaine Leflaive Bâtard GC"], description="Domaine Leflaive's Bâtard-Montrachet is one of their flagship Grand Crus; biodynamic farming produces wines of immense purity and potential."),
    WineCatalogEntry(id="leflaive-puligny-clavoillon", name="Domaine Leflaive Puligny-Montrachet Clavoillon 1er Cru", producer="Domaine Leflaive", region="Puligny-Montrachet, Burgundy, France", country="France", appellation="Puligny-Montrachet Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=280.0, price_tier="luxury", aliases=["Leflaive Clavoillon", "Domaine Leflaive Puligny Clavoillon"], description="Clavoillon is Domaine Leflaive's largest Premier Cru holding; the wine shows elegant, delicate Puligny character with excellent aging ability."),
    WineCatalogEntry(id="pycm-saint-aubin-en-remilly", name="Pierre-Yves Colin-Morey Saint-Aubin En Remilly 1er Cru", producer="Pierre-Yves Colin-Morey", region="Saint-Aubin, Burgundy, France", country="France", appellation="Saint-Aubin Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=120.0, price_tier="luxury", aliases=["PYCM Saint Aubin En Remilly", "Colin-Morey En Remilly Saint Aubin"], description="En Remilly is the jewel of Saint-Aubin; Pierre-Yves Colin-Morey's version is one of Burgundy's greatest value-to-quality propositions."),
    WineCatalogEntry(id="pycm-chassagne-montrachet", name="Pierre-Yves Colin-Morey Chassagne-Montrachet", producer="Pierre-Yves Colin-Morey", region="Chassagne-Montrachet, Burgundy, France", country="France", appellation="Chassagne-Montrachet", varietal="Chardonnay", wine_type="white", avg_retail_price=130.0, price_tier="luxury", aliases=["PYCM Chassagne Montrachet", "Colin-Morey Chassagne Village"], description="PYCM's Chassagne-Montrachet village bottling is extraordinary value; the combination of low yields and expert élévage produces Grand Cru-quality juice."),
    WineCatalogEntry(id="benoit-ente-puligny", name="Domaine Benoît Ente Puligny-Montrachet", producer="Domaine Benoît Ente", region="Puligny-Montrachet, Burgundy, France", country="France", appellation="Puligny-Montrachet", varietal="Chardonnay", wine_type="white", avg_retail_price=220.0, price_tier="luxury", aliases=["Benoit Ente Puligny Montrachet", "Benoît Ente Puligny"], description="Benoît Ente is one of Puligny's quieter stars; tiny production from old vines produces wines of extraordinary purity and mineral depth."),
    WineCatalogEntry(id="bernard-moreau-chassagne", name="Bernard Moreau et Fils Chassagne-Montrachet Les Charmes 1er Cru", producer="Bernard Moreau et Fils", region="Chassagne-Montrachet, Burgundy, France", country="France", appellation="Chassagne-Montrachet Premier Cru", varietal="Chardonnay", wine_type="white", avg_retail_price=120.0, price_tier="luxury", aliases=["Bernard Moreau Chassagne Les Charmes", "Moreau et Fils Chassagne Charmes"], description="Bernard Moreau is one of Chassagne's most consistent producers; Les Charmes 1er Cru shows the appellation's characteristic richness and precision."),
]

# ---------------------------------------------------------------------------
# RED BURGUNDY – Additional cuvées for depth + Arnoux-Lachaux, Mugneret-Gibourg
# ---------------------------------------------------------------------------
BURGUNDY_RED_EXTRA = [
    WineCatalogEntry(id="leroy-vosne-romanee", name="Domaine Leroy Vosne-Romanée", producer="Domaine Leroy", region="Vosne-Romanée, Burgundy, France", country="France", appellation="Vosne-Romanée", varietal="Pinot Noir", wine_type="red", avg_retail_price=900.0, price_tier="ultra-luxury", aliases=["Leroy Vosne-Romanée Village", "Lalou Bize Leroy Vosne"], description="Even Domaine Leroy's village Vosne-Romanée trades at Grand Cru prices; biodynamic farming and incredibly low yields produce wines of breathtaking intensity."),
    WineCatalogEntry(id="leroy-chambolle-musigny", name="Domaine Leroy Chambolle-Musigny", producer="Domaine Leroy", region="Chambolle-Musigny, Burgundy, France", country="France", appellation="Chambolle-Musigny", varietal="Pinot Noir", wine_type="red", avg_retail_price=700.0, price_tier="ultra-luxury", aliases=["Leroy Chambolle Musigny Village", "Domaine Leroy Chambolle"], description="Domaine Leroy's Chambolle-Musigny demonstrates the extraordinary level of terroir expression possible with biodynamic viticulture and tiny yields."),
    WineCatalogEntry(id="leroy-gevrey-chambertin", name="Domaine Leroy Gevrey-Chambertin", producer="Domaine Leroy", region="Gevrey-Chambertin, Burgundy, France", country="France", appellation="Gevrey-Chambertin", varietal="Pinot Noir", wine_type="red", avg_retail_price=750.0, price_tier="ultra-luxury", aliases=["Leroy Gevrey Chambertin Village", "Domaine Leroy Gevrey"], description="Leroy's Gevrey-Chambertin village shows great depth and structure; it ranks above most producers' Premiers Crus in quality."),
    WineCatalogEntry(id="dujac-morey-saint-denis", name="Domaine Dujac Morey-Saint-Denis", producer="Domaine Dujac", region="Morey-Saint-Denis, Burgundy, France", country="France", appellation="Morey-Saint-Denis", varietal="Pinot Noir", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Dujac Morey Saint Denis", "Jacques Seysses Dujac Morey"], description="Dujac's village Morey-Saint-Denis is the estate's most accessible entry point; whole-cluster vinification produces wines of extraordinary fragrance and depth."),
    WineCatalogEntry(id="dujac-gevrey-combottes", name="Domaine Dujac Gevrey-Chambertin Aux Combottes 1er Cru", producer="Domaine Dujac", region="Gevrey-Chambertin, Burgundy, France", country="France", appellation="Gevrey-Chambertin Premier Cru", varietal="Pinot Noir", wine_type="red", avg_retail_price=550.0, price_tier="ultra-luxury", aliases=["Dujac Aux Combottes", "Domaine Dujac Combottes Gevrey"], description="Aux Combottes is adjacent to Latricières-Chambertin; Dujac's version is one of the most spice-laden and complex of their Premier Cru range."),
    WineCatalogEntry(id="rousseau-chambertin-clos-beze", name="Domaine Armand Rousseau Chambertin Clos de Bèze Grand Cru", producer="Domaine Armand Rousseau", region="Gevrey-Chambertin, Burgundy, France", country="France", appellation="Chambertin-Clos de Bèze", varietal="Pinot Noir", wine_type="red", avg_retail_price=3500.0, price_tier="ultra-luxury", aliases=["Rousseau Chambertin Clos de Beze", "Armand Rousseau Clos Beze GC"], description="Rousseau's Clos de Bèze is one of Burgundy's most iconic Grand Crus; a wine of unparalleled depth, structure, and longevity."),
    WineCatalogEntry(id="rousseau-charmes-chambertin", name="Domaine Armand Rousseau Charmes-Chambertin Grand Cru", producer="Domaine Armand Rousseau", region="Gevrey-Chambertin, Burgundy, France", country="France", appellation="Charmes-Chambertin", varietal="Pinot Noir", wine_type="red", avg_retail_price=800.0, price_tier="ultra-luxury", aliases=["Rousseau Charmes Chambertin", "Armand Rousseau Charmes GC"], description="Rousseau's Charmes-Chambertin is the most hedonistic of their Grand Crus; lush and sensuous but with the firm structure for long aging."),
    WineCatalogEntry(id="rousseau-gevrey-village", name="Domaine Armand Rousseau Gevrey-Chambertin", producer="Domaine Armand Rousseau", region="Gevrey-Chambertin, Burgundy, France", country="France", appellation="Gevrey-Chambertin", varietal="Pinot Noir", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["Rousseau Gevrey Chambertin Village", "Armand Rousseau Gevrey Village"], description="Even Rousseau's village Gevrey is among Burgundy's finest; it offers extraordinary depth and complexity at an entry-level price for the domaine."),
    WineCatalogEntry(id="meo-camuzet-nuits-murgers", name="Domaine Méo-Camuzet Nuits-Saint-Georges Aux Murgers 1er Cru", producer="Domaine Méo-Camuzet", region="Nuits-Saint-Georges, Burgundy, France", country="France", appellation="Nuits-Saint-Georges Premier Cru", varietal="Pinot Noir", wine_type="red", avg_retail_price=500.0, price_tier="ultra-luxury", aliases=["Meo Camuzet Nuits Murgers", "Méo-Camuzet Aux Murgers Nuits"], description="Aux Murgers is one of Nuits-Saint-Georges' finest Premier Crus; Méo-Camuzet's version shows the power and spice typical of their winemaking."),
    WineCatalogEntry(id="meo-camuzet-clos-vougeot", name="Domaine Méo-Camuzet Clos Vougeot Grand Cru", producer="Domaine Méo-Camuzet", region="Clos Vougeot, Burgundy, France", country="France", appellation="Clos de Vougeot", varietal="Pinot Noir", wine_type="red", avg_retail_price=650.0, price_tier="ultra-luxury", aliases=["Meo Camuzet Clos Vougeot", "Méo-Camuzet Vougeot GC"], description="Méo-Camuzet's Clos Vougeot Grand Cru is from the prestigious upper section of the clos; it combines power, elegance, and extraordinary aromatic complexity."),
    WineCatalogEntry(id="mugnier-chambolle-village", name="Domaine Jacques-Frédéric Mugnier Chambolle-Musigny", producer="Domaine Jacques-Frédéric Mugnier", region="Chambolle-Musigny, Burgundy, France", country="France", appellation="Chambolle-Musigny", varietal="Pinot Noir", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["Mugnier Chambolle Musigny Village", "Frédéric Mugnier Chambolle Village"], description="Mugnier's village Chambolle is the finest entry point to this remarkable domaine; precise, floral, and complex beyond its appellation status."),
    WineCatalogEntry(id="arnoux-lachaux-vosne-village", name="Domaine Arnoux-Lachaux Vosne-Romanée", producer="Domaine Arnoux-Lachaux", region="Vosne-Romanée, Burgundy, France", country="France", appellation="Vosne-Romanée", varietal="Pinot Noir", wine_type="red", avg_retail_price=400.0, price_tier="ultra-luxury", aliases=["Arnoux-Lachaux Vosne Romanee Village", "Arnoux Lachaux Vosne Village"], description="Arnoux-Lachaux's village Vosne-Romanée commands prices that rival many domaines' Premiers Crus; the wines are opulent and deep."),
    WineCatalogEntry(id="arnoux-lachaux-vosne-chaumes", name="Domaine Arnoux-Lachaux Vosne-Romanée Les Chaumes 1er Cru", producer="Domaine Arnoux-Lachaux", region="Vosne-Romanée, Burgundy, France", country="France", appellation="Vosne-Romanée Premier Cru", varietal="Pinot Noir", wine_type="red", avg_retail_price=800.0, price_tier="ultra-luxury", aliases=["Arnoux-Lachaux Les Chaumes", "Arnoux Lachaux Vosne Chaumes Premier Cru"], description="Les Chaumes is one of Vosne's most powerful Premier Crus; Arnoux-Lachaux's version is among the finest expressions of this terroir."),
    WineCatalogEntry(id="arnoux-lachaux-echezeaux", name="Domaine Arnoux-Lachaux Échezeaux Grand Cru", producer="Domaine Arnoux-Lachaux", region="Flagey-Échezeaux, Burgundy, France", country="France", appellation="Échezeaux", varietal="Pinot Noir", wine_type="red", avg_retail_price=1500.0, price_tier="ultra-luxury", aliases=["Arnoux Lachaux Echezeaux Grand Cru", "Arnoux Lachaux Echezeaux GC"], description="Arnoux-Lachaux's Échezeaux is one of Burgundy's most collectible Grand Crus; combining the power of the estate with the elegance of this historic vineyard."),
    WineCatalogEntry(id="cathiard-vosne-village", name="Domaine Sylvain Cathiard Vosne-Romanée", producer="Domaine Sylvain Cathiard", region="Vosne-Romanée, Burgundy, France", country="France", appellation="Vosne-Romanée", varietal="Pinot Noir", wine_type="red", avg_retail_price=350.0, price_tier="ultra-luxury", aliases=["Cathiard Vosne Romanee Village", "Sylvain Cathiard Vosne Village"], description="Cathiard's village Vosne is already extraordinary; the domaine's meticulous care ensures even this entry-level wine achieves remarkable complexity."),
    WineCatalogEntry(id="mugneret-gibourg-chambolle", name="Georges Mugneret-Gibourg Chambolle-Musigny", producer="Georges Mugneret-Gibourg", region="Chambolle-Musigny, Burgundy, France", country="France", appellation="Chambolle-Musigny", varietal="Pinot Noir", wine_type="red", avg_retail_price=300.0, price_tier="luxury", aliases=["Mugneret-Gibourg Chambolle Musigny", "Mugneret Gibourg Chambolle Village"], description="Georges Mugneret-Gibourg is one of Burgundy's most beloved family estates; their Chambolle-Musigny is a stunning expression of this floral village."),
    WineCatalogEntry(id="mugneret-gibourg-ruchottes", name="Georges Mugneret-Gibourg Ruchottes-Chambertin Grand Cru", producer="Georges Mugneret-Gibourg", region="Gevrey-Chambertin, Burgundy, France", country="France", appellation="Ruchottes-Chambertin", varietal="Pinot Noir", wine_type="red", avg_retail_price=800.0, price_tier="ultra-luxury", aliases=["Mugneret-Gibourg Ruchottes Chambertin", "Mugneret Gibourg Ruchottes GC"], description="One of the most elegant and energetic Grand Crus from Gevrey; Mugneret-Gibourg's Ruchottes-Chambertin is celebrated for its extraordinary freshness."),
    WineCatalogEntry(id="mugneret-gibourg-nuits", name="Georges Mugneret-Gibourg Nuits-Saint-Georges", producer="Georges Mugneret-Gibourg", region="Nuits-Saint-Georges, Burgundy, France", country="France", appellation="Nuits-Saint-Georges", varietal="Pinot Noir", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Mugneret Gibourg Nuits Saint Georges", "Mugneret-Gibourg NSG"], description="Mugneret-Gibourg's Nuits-Saint-Georges village is a well-priced entry point to this extraordinary domaine; earthy and precise."),
    WineCatalogEntry(id="chandon-briailles-corton", name="Chandon de Briailles Corton Grand Cru", producer="Chandon de Briailles", region="Corton, Burgundy, France", country="France", appellation="Corton", varietal="Pinot Noir", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Chandon de Briailles Corton GC", "Domaine Chandon de Briailles Corton"], description="Chandon de Briailles is one of Corton's most important estates; their Grand Cru wines are precise, structured, and require long aging."),
    WineCatalogEntry(id="roumier-chambolle-village", name="Domaine Georges Roumier Chambolle-Musigny", producer="Domaine Georges Roumier", region="Chambolle-Musigny, Burgundy, France", country="France", appellation="Chambolle-Musigny", varietal="Pinot Noir", wine_type="red", avg_retail_price=350.0, price_tier="ultra-luxury", aliases=["Georges Roumier Chambolle Musigny Village", "Roumier Chambolle Village"], description="Roumier's village Chambolle-Musigny is the most accessible entry to this legendary domaine; the wines are always ethereally fragrant and complex."),
    WineCatalogEntry(id="roumier-morey-clos-bussiere", name="Domaine Georges Roumier Morey-Saint-Denis Clos de la Bussière 1er Cru", producer="Domaine Georges Roumier", region="Morey-Saint-Denis, Burgundy, France", country="France", appellation="Morey-Saint-Denis Premier Cru", varietal="Pinot Noir", wine_type="red", avg_retail_price=280.0, price_tier="luxury", aliases=["Roumier Clos de la Bussière", "Roumier Morey Clos Bussière"], description="Roumier's monopole Clos de la Bussière is one of Morey-Saint-Denis's most distinctive Premier Crus; robust and mineral with excellent aging capacity."),
]

# ---------------------------------------------------------------------------
# CHAMPAGNE – Prestige cuvées + key grower additions
# ---------------------------------------------------------------------------
CHAMPAGNE_PRESTIGE = [
    WineCatalogEntry(id="dom-perignon-vintage", name="Dom Pérignon Vintage Brut", producer="Dom Pérignon", region="Épernay, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay/Pinot Noir", wine_type="sparkling", avg_retail_price=200.0, price_tier="luxury", aliases=["Dom Perignon Vintage Brut", "Dom Pérignon Millesime", "DP Vintage"], description="Dom Pérignon Vintage is one of the world's most iconic Champagnes; only made in declared vintages, it combines power, finesse, and extraordinary aging potential."),
    WineCatalogEntry(id="dom-perignon-p2", name="Dom Pérignon P2 Plénitude Deuxième", producer="Dom Pérignon", region="Épernay, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay/Pinot Noir", wine_type="sparkling", avg_retail_price=450.0, price_tier="ultra-luxury", aliases=["Dom Perignon P2", "Dom Pérignon Plenitude 2eme", "DP P2"], description="Dom Pérignon P2 represents the second plénitude of aging; released after 15+ years on the lees, it achieves extraordinary complexity and depth."),
    WineCatalogEntry(id="bollinger-rd", name="Bollinger R.D. Extra Brut", producer="Bollinger", region="Aÿ, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir/Chardonnay", wine_type="sparkling", avg_retail_price=280.0, price_tier="luxury", aliases=["Bollinger RD", "Bollinger Recently Disgorged", "Bollinger R.D. Vintage"], description="Bollinger R.D. (Récemment Dégorgé) is aged for 8+ years on the lees before late disgorgement; it achieves extraordinary depth and autolytic complexity."),
    WineCatalogEntry(id="bollinger-special-cuvee", name="Bollinger Special Cuvée Brut NV", producer="Bollinger", region="Aÿ, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir/Chardonnay", wine_type="sparkling", avg_retail_price=75.0, price_tier="premium", aliases=["Bollinger NV", "Bollinger Special Cuvee NV", "Bollinger Brut NV"], description="Bollinger Special Cuvée is one of Champagne's most substantial non-vintage wines; rich, toasty, and deeply flavored from high Pinot Noir content."),
    WineCatalogEntry(id="pol-roger-winston-churchill", name="Pol Roger Cuvée Sir Winston Churchill", producer="Pol Roger", region="Épernay, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir/Chardonnay", wine_type="sparkling", avg_retail_price=260.0, price_tier="luxury", aliases=["Pol Roger Winston Churchill", "Pol Roger Cuvee Churchill", "Churchill Champagne Pol Roger"], description="Pol Roger's tribute to their most famous fan is a Prestige Cuvée of extraordinary richness and complexity; one of Champagne's benchmark vintage wines."),
    WineCatalogEntry(id="pol-roger-brut-reserve", name="Pol Roger Brut Réserve NV", producer="Pol Roger", region="Épernay, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Noir/Chardonnay/Pinot Meunier", wine_type="sparkling", avg_retail_price=65.0, price_tier="premium", aliases=["Pol Roger Brut NV", "Pol Roger Reserve NV", "Pol Roger White Foil"], description="Pol Roger Brut Réserve is a consistently excellent NV Champagne; elegant and food-friendly, it's one of the most respected wines in its category."),
    WineCatalogEntry(id="jerome-prevost-closerie", name="Jérôme Prévost La Closerie Les Béguines", producer="Jérôme Prévost", region="Gueux, Champagne, France", country="France", appellation="Champagne", varietal="Pinot Meunier", wine_type="sparkling", avg_retail_price=350.0, price_tier="ultra-luxury", aliases=["Jerome Prevost La Closerie", "Prevost Les Béguines", "La Closerie Les Beguines"], description="Jérôme Prévost's single-vineyard La Closerie is one of Champagne's most sought-after grower wines; pure Pinot Meunier of extraordinary depth and complexity."),
    WineCatalogEntry(id="charles-heidsieck-blanc-millenaires", name="Charles Heidsieck Blanc des Millénaires", producer="Charles Heidsieck", region="Reims, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=200.0, price_tier="luxury", aliases=["Charles Heidsieck Blanc des Millenaires", "Heidsieck Blanc Millenaires BdB"], description="Blanc des Millénaires is Charles Heidsieck's flagship Blanc de Blancs vintage prestige cuvée; one of Champagne's most underrated yet majestic wines."),
    WineCatalogEntry(id="piper-heidsieck-rare", name="Piper-Heidsieck Champagne Rare Millésimé", producer="Piper-Heidsieck", region="Reims, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay/Pinot Noir", wine_type="sparkling", avg_retail_price=250.0, price_tier="luxury", aliases=["Piper Heidsieck Rare", "Piper Heidsieck Rare Vintage", "Rare Champagne"], description="Piper-Heidsieck Rare is an exceptional prestige cuvée produced only in the finest vintages; rich and vinous with extraordinary complexity."),
    WineCatalogEntry(id="ruinart-dom-ruinart", name="Ruinart Dom Ruinart Blanc de Blancs", producer="Ruinart", region="Reims, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=200.0, price_tier="luxury", aliases=["Dom Ruinart Blanc de Blancs", "Dom Ruinart BdB Vintage", "Ruinart Dom Ruinart"], description="Dom Ruinart Blanc de Blancs is the prestige cuvée from Champagne's oldest house; all Grand Cru Chardonnay, it achieves extraordinary finesse and longevity."),
    WineCatalogEntry(id="ruinart-blanc-de-blancs", name="Ruinart Blanc de Blancs NV", producer="Ruinart", region="Reims, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=80.0, price_tier="premium", aliases=["Ruinart BdB NV", "Ruinart Blanc de Blancs Non-Vintage"], description="Ruinart Blanc de Blancs NV is one of Champagne's finest non-vintage wines; crisp, precise, and loaded with citrus and chalk character from Grand Cru Chardonnay."),
    WineCatalogEntry(id="gosset-celebris", name="Gosset Celebris Extra Brut Vintage", producer="Gosset", region="Aÿ, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay/Pinot Noir", wine_type="sparkling", avg_retail_price=180.0, price_tier="luxury", aliases=["Gosset Celebris Vintage", "Gosset Célébris Extra Brut"], description="Gosset Célébris is the prestige cuvée from one of Champagne's oldest and most underrated houses; the Extra Brut version is particularly age-worthy."),
    WineCatalogEntry(id="krug-clos-du-mesnil", name="Krug Clos du Mesnil Blanc de Blancs", producer="Krug", region="Le Mesnil-sur-Oger, Champagne, France", country="France", appellation="Champagne", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=1200.0, price_tier="ultra-luxury", aliases=["Krug Clos Mesnil", "Krug Clos du Mesnil Vintage", "Krug Mesnil BdB"], description="Krug Clos du Mesnil is one of Champagne's rarest and most prestigious single-vineyard wines; a 1.84-hectare walled garden in Le Mesnil produces an iconic Blanc de Blancs."),
]

# ---------------------------------------------------------------------------
# NORTHERN RHÔNE – Essential producers missing from catalog
# ---------------------------------------------------------------------------
RHONE_NORTH = [
    WineCatalogEntry(id="chave-hermitage-rouge", name="Jean-Louis Chave Hermitage Rouge", producer="Jean-Louis Chave", region="Hermitage, Rhône, France", country="France", appellation="Hermitage", varietal="Syrah", wine_type="red", avg_retail_price=700.0, price_tier="ultra-luxury", aliases=["Jean Louis Chave Hermitage", "JL Chave Hermitage Rouge", "Domaine Chave Hermitage"], description="Jean-Louis Chave's Hermitage is arguably the greatest Syrah in the world; a seamlessly blended wine from multiple parcels that requires decades to show its true depth."),
    WineCatalogEntry(id="chave-hermitage-blanc", name="Jean-Louis Chave Hermitage Blanc", producer="Jean-Louis Chave", region="Hermitage, Rhône, France", country="France", appellation="Hermitage", varietal="Marsanne/Roussanne", wine_type="white", avg_retail_price=600.0, price_tier="ultra-luxury", aliases=["Jean Louis Chave Hermitage Blanc", "JL Chave Hermitage White", "Chave Hermitage Marsanne"], description="Chave's white Hermitage is one of the world's greatest whites; a blend of Marsanne and Roussanne that becomes extraordinary with 15+ years of aging."),
    WineCatalogEntry(id="chave-mon-coeur-crozes", name="Jean-Louis Chave Mon Coeur Crozes-Hermitage", producer="Jean-Louis Chave", region="Crozes-Hermitage, Rhône, France", country="France", appellation="Crozes-Hermitage", varietal="Syrah", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Chave Mon Coeur Crozes", "JL Chave Crozes Hermitage Mon Coeur"], description="Mon Coeur is Chave's entry point into the Rhône; a seriously structured Crozes-Hermitage that over-delivers for its appellation level."),
    WineCatalogEntry(id="allemand-cornas-chaillot", name="Thierry Allemand Cornas Chaillot", producer="Thierry Allemand", region="Cornas, Rhône, France", country="France", appellation="Cornas", varietal="Syrah", wine_type="red", avg_retail_price=500.0, price_tier="ultra-luxury", aliases=["Thierry Allemand Chaillot", "Allemand Cornas Chaillot Syrah"], description="Thierry Allemand's Cornas is among the world's most sought-after wines; Chaillot is the more mineral, tighter expression from young-vine granite soils."),
    WineCatalogEntry(id="allemand-cornas-reynard", name="Thierry Allemand Cornas Reynard", producer="Thierry Allemand", region="Cornas, Rhône, France", country="France", appellation="Cornas", varietal="Syrah", wine_type="red", avg_retail_price=600.0, price_tier="ultra-luxury", aliases=["Thierry Allemand Reynard", "Allemand Cornas Reynard Vieilles Vignes"], description="Reynard is Allemand's flagship Cornas, from 80-100 year old vines; it combines savage power with extraordinary aromatic complexity and longevity."),
    WineCatalogEntry(id="clape-cornas", name="Auguste Clape Cornas", producer="Auguste Clape", region="Cornas, Rhône, France", country="France", appellation="Cornas", varietal="Syrah", wine_type="red", avg_retail_price=300.0, price_tier="luxury", aliases=["Clape Cornas", "Auguste Clape Cornas Syrah", "Domaine Clape Cornas"], description="Auguste Clape's Cornas is the standard by which all Cornas is measured; old vines on steep granite terraces produce one of the Rhône's greatest wines."),
    WineCatalogEntry(id="clape-renaissance-cornas", name="Auguste Clape Cornas Renaissance", producer="Auguste Clape", region="Cornas, Rhône, France", country="France", appellation="Cornas", varietal="Syrah", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Clape Cornas Renaissance", "Clape Renaissance Entry Level Cornas"], description="Renaissance is Clape's entry-level Cornas, made from younger vines; it offers accessible entry into this formidable appellation and the Clape style."),
    WineCatalogEntry(id="ogier-cote-rotie-lancement", name="Ogier Côte-Rôtie La Belle Hélène", producer="Ogier", region="Côte-Rôtie, Rhône, France", country="France", appellation="Côte-Rôtie", varietal="Syrah", wine_type="red", avg_retail_price=400.0, price_tier="ultra-luxury", aliases=["Ogier La Belle Helene Cote Rotie", "Michel Stephane Ogier Belle Helene", "Stéphane Ogier La Belle Hélène"], description="La Belle Hélène is Stéphane Ogier's single-vineyard flagship from La Landonne; one of Côte-Rôtie's most complex and age-worthy expressions."),
    WineCatalogEntry(id="ogier-cote-rotie-village", name="Ogier Côte-Rôtie", producer="Ogier", region="Côte-Rôtie, Rhône, France", country="France", appellation="Côte-Rôtie", varietal="Syrah", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Stéphane Ogier Côte Rôtie", "Michel Ogier Cote Rotie Village"], description="Ogier's appellation-level Côte-Rôtie is a consistently excellent introduction to the AC; it offers aromatic complexity and mineral depth at a fair price."),
    WineCatalogEntry(id="rostaing-cote-rotie-blonde", name="René Rostaing Côte-Rôtie Côte Blonde", producer="René Rostaing", region="Côte-Rôtie, Rhône, France", country="France", appellation="Côte-Rôtie", varietal="Syrah", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Rostaing Cote Blonde", "Rene Rostaing Côte Blonde Cote Rotie"], description="René Rostaing's Côte Blonde is perhaps the most elegant expression of Côte-Rôtie; floral, refined, and age-worthy."),
    WineCatalogEntry(id="rostaing-cote-rotie-landonne", name="René Rostaing Côte-Rôtie La Landonne", producer="René Rostaing", region="Côte-Rôtie, Rhône, France", country="France", appellation="Côte-Rôtie", varietal="Syrah", wine_type="red", avg_retail_price=400.0, price_tier="ultra-luxury", aliases=["Rostaing La Landonne Cote Rotie", "Rene Rostaing Landonne"], description="La Landonne is one of Côte-Rôtie's greatest single-vineyard sites; Rostaing's version stands alongside Guigal's in demonstrating the sheer power of this lieu-dit."),
    WineCatalogEntry(id="villard-condrieu", name="François Villard Condrieu Terrasses du Palat", producer="François Villard", region="Condrieu, Rhône, France", country="France", appellation="Condrieu", varietal="Viognier", wine_type="white", avg_retail_price=85.0, price_tier="premium", aliases=["Francois Villard Condrieu", "Villard Terrasses du Palat Condrieu", "Villard Condrieu Viognier"], description="François Villard is one of Condrieu's most acclaimed producers; Terrasses du Palat is a benchmark for the opulent, floral style of this appellation."),
    WineCatalogEntry(id="villard-saint-joseph", name="François Villard Saint-Joseph Mairlant", producer="François Villard", region="Saint-Joseph, Rhône, France", country="France", appellation="Saint-Joseph", varietal="Syrah", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Villard Saint Joseph Mairlant", "Francois Villard St Joseph"], description="Villard's Saint-Joseph Mairlant is a serious wine from old vines on granite; concentrated Syrah with the savory, peppery character of the Northern Rhône."),
    WineCatalogEntry(id="faury-saint-joseph", name="Domaine Faury Saint-Joseph", producer="Domaine Faury", region="Saint-Joseph, Rhône, France", country="France", appellation="Saint-Joseph", varietal="Syrah", wine_type="red", avg_retail_price=48.0, price_tier="mid", aliases=["Faury Saint Joseph", "Philippe Faury Saint Joseph Syrah"], description="Domaine Faury is one of Saint-Joseph's most reliable producers; their Syrah consistently shows the appellation's meaty, mineral character."),
    WineCatalogEntry(id="faury-condrieu", name="Domaine Faury Condrieu", producer="Domaine Faury", region="Condrieu, Rhône, France", country="France", appellation="Condrieu", varietal="Viognier", wine_type="white", avg_retail_price=65.0, price_tier="premium", aliases=["Faury Condrieu Viognier", "Philippe Faury Condrieu"], description="Faury's Condrieu is a beautiful expression of Viognier from the granitic soils of this storied appellation; floral and textured."),
    WineCatalogEntry(id="vincent-paris-cornas-30", name="Domaine Vincent Paris Cornas Granit 30", producer="Domaine Vincent Paris", region="Cornas, Rhône, France", country="France", appellation="Cornas", varietal="Syrah", wine_type="red", avg_retail_price=65.0, price_tier="premium", aliases=["Vincent Paris Granit 30", "Domaine Vincent Paris Cornas Granit"], description="Vincent Paris's Granit 30 represents the younger-vine Cornas (30-year-old vines); an accessible entry to this serious appellation."),
    WineCatalogEntry(id="vincent-paris-cornas-60", name="Domaine Vincent Paris Cornas Granit 60", producer="Domaine Vincent Paris", region="Cornas, Rhône, France", country="France", appellation="Cornas", varietal="Syrah", wine_type="red", avg_retail_price=85.0, price_tier="premium", aliases=["Vincent Paris Granit 60", "Vincent Paris Cornas 60 Year Old Vines"], description="Granit 60 is from 60-year-old vines in Cornas; showing greater complexity and concentration than the 30, it is one of the region's best value propositions."),
    WineCatalogEntry(id="chapoutier-ermitage-le-meal", name="M. Chapoutier Ermitage Le Méal", producer="M. Chapoutier", region="Hermitage, Rhône, France", country="France", appellation="Hermitage", varietal="Syrah", wine_type="red", avg_retail_price=300.0, price_tier="luxury", aliases=["Chapoutier Le Meal Hermitage", "Chapoutier Ermitage Le Meal", "M Chapoutier Le Meal"], description="Le Méal is one of Hermitage's greatest single plots; Chapoutier's biodynamic version is a massive, age-worthy Syrah of extraordinary depth."),
]

# ---------------------------------------------------------------------------
# SOUTHERN RHÔNE + BANDOL – Key additions
# ---------------------------------------------------------------------------
RHONE_SOUTH_BANDOL = [
    WineCatalogEntry(id="rayas-chateauneuf-blanc", name="Château Rayas Châteauneuf-du-Pape Blanc", producer="Château Rayas", region="Châteauneuf-du-Pape, Rhône, France", country="France", appellation="Châteauneuf-du-Pape", varietal="Grenache Blanc/Clairette", wine_type="white", avg_retail_price=600.0, price_tier="ultra-luxury", aliases=["Rayas CdP Blanc", "Château Rayas Blanc Chateauneuf"], description="Rayas Blanc is perhaps the world's greatest white Châteauneuf-du-Pape; aged in old wood, it achieves extraordinary richness and can outlast most red Burgundies."),
    WineCatalogEntry(id="beaucastel-chateauneuf-rouge", name="Château Beaucastel Châteauneuf-du-Pape Rouge", producer="Château Beaucastel", region="Châteauneuf-du-Pape, Rhône, France", country="France", appellation="Châteauneuf-du-Pape", varietal="Grenache/Mourvèdre", wine_type="red", avg_retail_price=85.0, price_tier="premium", aliases=["Beaucastel CdP Rouge", "Château Beaucastel Chateauneuf Rouge"], description="Beaucastel's flagship Châteauneuf-du-Pape uses all 13 permitted varieties; a wine of extraordinary complexity and one of the appellation's most age-worthy examples."),
    WineCatalogEntry(id="beaucastel-hommage-perrin", name="Château Beaucastel Hommage à Jacques Perrin", producer="Château Beaucastel", region="Châteauneuf-du-Pape, Rhône, France", country="France", appellation="Châteauneuf-du-Pape", varietal="Mourvèdre", wine_type="red", avg_retail_price=320.0, price_tier="luxury", aliases=["Beaucastel Hommage Jacques Perrin", "Hommage à Jacques Perrin", "Beaucastel Hommage"], description="Hommage à Jacques Perrin is a special cuvée from the oldest Mourvèdre vines; made only in exceptional vintages, it is one of the Southern Rhône's greatest wines."),
    WineCatalogEntry(id="vieux-telegraphe-la-crau", name="Domaine du Vieux Télégraphe La Crau", producer="Domaine du Vieux Télégraphe", region="Châteauneuf-du-Pape, Rhône, France", country="France", appellation="Châteauneuf-du-Pape", varietal="Grenache/Syrah/Mourvèdre", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Vieux Telegraphe La Crau CdP", "Vieux Télégraphe Chateauneuf du Pape"], description="La Crau is Vieux Télégraphe's flagship Châteauneuf from the galets roulés plateau; one of the appellation's most consistent and age-worthy wines."),
    WineCatalogEntry(id="tempier-bandol-rouge", name="Domaine Tempier Bandol Rouge", producer="Domaine Tempier", region="Bandol, Provence, France", country="France", appellation="Bandol", varietal="Mourvèdre/Grenache", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Tempier Bandol Classic Rouge", "Domaine Tempier Bandol Red"], description="Domaine Tempier is the historic reference for Bandol; the classic rouge is a compelling, age-worthy Mourvèdre-based wine that improves dramatically with a decade of cellaring."),
    WineCatalogEntry(id="tempier-bandol-rose", name="Domaine Tempier Bandol Rosé", producer="Domaine Tempier", region="Bandol, Provence, France", country="France", appellation="Bandol", varietal="Mourvèdre/Grenache/Cinsault", wine_type="rosé", avg_retail_price=48.0, price_tier="mid", aliases=["Tempier Bandol Rosé", "Domaine Tempier Rose Bandol"], description="Tempier's Bandol Rosé is one of Provence's most respected; vinified with serious intent from Mourvèdre-dominant blends to produce a rosé of genuine depth."),
    WineCatalogEntry(id="tempier-bandol-la-tourtine", name="Domaine Tempier Bandol La Tourtine", producer="Domaine Tempier", region="Bandol, Provence, France", country="France", appellation="Bandol", varietal="Mourvèdre", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Tempier La Tourtine Bandol", "Domaine Tempier Tourtine"], description="La Tourtine is one of Tempier's single-vineyard Bandols; from a cooler, north-facing site, it produces a more elegant and restrained expression of Mourvèdre."),
    WineCatalogEntry(id="pibarnon-bandol-rouge", name="Château de Pibarnon Bandol Rouge", producer="Château de Pibarnon", region="Bandol, Provence, France", country="France", appellation="Bandol", varietal="Mourvèdre", wine_type="red", avg_retail_price=60.0, price_tier="premium", aliases=["Pibarnon Bandol Rouge", "Château Pibarnon Bandol Red"], description="Pibarnon sits at Bandol's highest elevation; the wine shows more refinement and freshness than most Bandols due to the cooler microclimate."),
    WineCatalogEntry(id="barroche-chateauneuf-fiancee", name="Domaine de la Barroche Châteauneuf-du-Pape Fiancée", producer="Domaine de la Barroche", region="Châteauneuf-du-Pape, Rhône, France", country="France", appellation="Châteauneuf-du-Pape", varietal="Grenache", wine_type="red", avg_retail_price=150.0, price_tier="luxury", aliases=["La Barroche Fiancee CdP", "Barroche Fiancée Châteauneuf"], description="Fiancée is La Barroche's prestige cuvée from the estate's oldest Grenache vines; a concentrated, opulent Châteauneuf-du-Pape of great depth."),
]

# ---------------------------------------------------------------------------
# LOIRE VALLEY – Clos Rougeard + key Muscadet / Anjou additions
# ---------------------------------------------------------------------------
LOIRE_ADDITIONS = [
    WineCatalogEntry(id="clos-rougeard-les-poyeux", name="Clos Rougeard Saumur-Champigny Les Poyeux", producer="Clos Rougeard", region="Saumur-Champigny, Loire, France", country="France", appellation="Saumur-Champigny", varietal="Cabernet Franc", wine_type="red", avg_retail_price=380.0, price_tier="ultra-luxury", aliases=["Clos Rougeard Poyeux", "Foucault Les Poyeux", "Rougeard Saumur Champigny Les Poyeux"], description="Clos Rougeard's Les Poyeux is among the Loire's most collectible wines; a profound Cabernet Franc of extraordinary depth from the Foucault brothers' legendary domaine."),
    WineCatalogEntry(id="clos-rougeard-le-bourg", name="Clos Rougeard Saumur-Champigny Le Bourg", producer="Clos Rougeard", region="Saumur-Champigny, Loire, France", country="France", appellation="Saumur-Champigny", varietal="Cabernet Franc", wine_type="red", avg_retail_price=500.0, price_tier="ultra-luxury", aliases=["Clos Rougeard Le Bourg", "Foucault Saumur Champigny Le Bourg", "Rougeard Le Bourg"], description="Le Bourg is Clos Rougeard's rarest and most celebrated cuvée; a wine of stunning complexity that rivals red Burgundy Grand Crus in both quality and price."),
    WineCatalogEntry(id="sanzay-saumur-champigny", name="Antoine Sanzay Saumur-Champigny Les Poyeux", producer="Antoine Sanzay", region="Saumur-Champigny, Loire, France", country="France", appellation="Saumur-Champigny", varietal="Cabernet Franc", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Antoine Sanzay Les Poyeux", "Sanzay Saumur Champigny"], description="Antoine Sanzay is the new-generation inheritor of the Clos Rougeard tradition in Saumur; his Les Poyeux is a mineral, age-worthy Cabernet Franc of great precision."),
    WineCatalogEntry(id="filliatreau-saumur-champigny", name="Domaine Filliatreau Saumur-Champigny Vieilles Vignes", producer="Domaine Filliatreau", region="Saumur-Champigny, Loire, France", country="France", appellation="Saumur-Champigny", varietal="Cabernet Franc", wine_type="red", avg_retail_price=45.0, price_tier="mid", aliases=["Filliatreau Saumur Champigny VV", "Filliatreau Vieilles Vignes Loire"], description="Domaine Filliatreau is one of Saumur-Champigny's most historic estates; the Vieilles Vignes bottling from very old Cabernet Franc vines is one of the region's classics."),
    WineCatalogEntry(id="jo-landron-muscadet", name="Jo Landron Muscadet Sèvre-et-Maine Les Houx", producer="Jo Landron", region="Muscadet Sèvre-et-Maine, Loire, France", country="France", appellation="Muscadet Sèvre-et-Maine sur Lie", varietal="Melon de Bourgogne", wine_type="white", avg_retail_price=30.0, price_tier="value", aliases=["Landron Les Houx Muscadet", "Jo Landron Amphibolite Muscadet", "Domaine de la Louvetrie"], description="Jo Landron is a leading proponent of high-quality Muscadet; Les Houx from old-vine Melon de Bourgogne on gneiss soils offers remarkable texture and mineral depth."),
    WineCatalogEntry(id="de-pallus-touraine", name="Domaine de Pallus Chinon Les Pensées de Pallus", producer="Domaine de Pallus", region="Chinon, Loire, France", country="France", appellation="Chinon", varietal="Cabernet Franc", wine_type="red", avg_retail_price=50.0, price_tier="mid", aliases=["Pallus Chinon Les Pensées", "Domaine Pallus Chinon"], description="Domaine de Pallus is one of Chinon's most serious producers; Les Pensées de Pallus is a concentrated, mineral Cabernet Franc of genuine complexity."),
]

# ---------------------------------------------------------------------------
# BORDEAUX – More first and second growth entries + Right Bank additions
# ---------------------------------------------------------------------------
BORDEAUX_EXTRA = [
    WineCatalogEntry(id="chateau-haut-bailly-pessac", name="Château Haut-Bailly Pessac-Léognan Grand Cru Classé", producer="Château Haut-Bailly", region="Pessac-Léognan, Bordeaux, France", country="France", appellation="Pessac-Léognan", varietal="Cabernet Sauvignon/Merlot", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Haut Bailly Pessac Leognan", "Chateau Haut-Bailly Cru Classé"], description="Haut-Bailly is one of Pessac-Léognan's most beloved châteaux; silky and elegant with a restrained, classical style that is immediately distinctive."),
    WineCatalogEntry(id="chateau-pichon-lalande", name="Château Pichon Lalande Pauillac 2ème Grand Cru Classé", producer="Château Pichon Lalande", region="Pauillac, Bordeaux, France", country="France", appellation="Pauillac", varietal="Merlot/Cabernet Sauvignon", wine_type="red", avg_retail_price=220.0, price_tier="luxury", aliases=["Pichon Lalande", "Pichon Comtesse de Lalande", "Château Pichon-Longueville Comtesse de Lalande"], description="Pichon Lalande is one of Bordeaux's most consistently brilliant seconds; a Merlot-influenced Pauillac of extraordinary elegance and early accessibility."),
    WineCatalogEntry(id="chateau-leoville-barton", name="Château Léoville-Barton Saint-Julien 2ème Grand Cru Classé", producer="Famille Barton", region="Saint-Julien, Bordeaux, France", country="France", appellation="Saint-Julien", varietal="Cabernet Sauvignon/Merlot", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Leoville Barton", "Léoville Barton Saint Julien", "Chateau Leoville Barton"], description="Léoville-Barton is one of Bordeaux's most reliable and fairly-priced Second Growths; traditional winemaking in aging cellars produces wines of remarkable longevity."),
    WineCatalogEntry(id="chateau-canon-saint-emilion", name="Château Canon Saint-Émilion 1er Grand Cru Classé B", producer="Château Canon", region="Saint-Émilion, Bordeaux, France", country="France", appellation="Saint-Émilion Grand Cru Classé", varietal="Merlot/Cabernet Franc", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Chateau Canon Saint-Emilion", "Canon Saint Emilion 1er Cru"], description="Château Canon is one of Saint-Émilion's great historic châteaux; elegant and perfumed, with the finesse that distinguishes the limestone plateau style."),
    WineCatalogEntry(id="la-conseillante-pomerol", name="Château La Conseillante Pomerol", producer="Famille Nicolas", region="Pomerol, Bordeaux, France", country="France", appellation="Pomerol", varietal="Merlot/Cabernet Franc", wine_type="red", avg_retail_price=350.0, price_tier="ultra-luxury", aliases=["La Conseillante Pomerol", "Chateau La Conseillante"], description="La Conseillante sits on Pomerol's finest gravel and clay soils adjacent to Pétrus; its Merlot-based wines are seductive, perfumed, and complex."),
    WineCatalogEntry(id="chateau-clinet-pomerol", name="Château Clinet Pomerol", producer="Château Clinet", region="Pomerol, Bordeaux, France", country="France", appellation="Pomerol", varietal="Merlot/Cabernet Sauvignon", wine_type="red", avg_retail_price=170.0, price_tier="luxury", aliases=["Clinet Pomerol", "Chateau Clinet Pomerol"], description="Clinet is one of Pomerol's most consistently impressive châteaux; opulent and hedonistic, it's one of the appellation's most reliable performers."),
    WineCatalogEntry(id="le-pin-pomerol", name="Le Pin Pomerol", producer="Famille Thienpont", region="Pomerol, Bordeaux, France", country="France", appellation="Pomerol", varietal="Merlot", wine_type="red", avg_retail_price=3500.0, price_tier="ultra-luxury", aliases=["Le Pin", "Pomerol Le Pin", "Le Pin Jacques Thienpont"], description="Le Pin is one of the world's most expensive wines; from just 2 hectares of very old Merlot, Jacques Thienpont produces a wine of extraordinary hedonism and rarity."),
    WineCatalogEntry(id="chateau-branaire-ducru", name="Château Branaire-Ducru Saint-Julien 4ème Grand Cru Classé", producer="Château Branaire-Ducru", region="Saint-Julien, Bordeaux, France", country="France", appellation="Saint-Julien", varietal="Cabernet Sauvignon/Merlot", wine_type="red", avg_retail_price=70.0, price_tier="premium", aliases=["Branaire Ducru Saint Julien", "Branaire-Ducru 4ème Cru"], description="Branaire-Ducru is one of the Médoc's most undervalued estates; consistently producing elegant, aromatic Saint-Julien with exceptional value for a classed growth."),
    WineCatalogEntry(id="chateau-grand-puy-lacoste", name="Château Grand-Puy-Lacoste Pauillac 5ème Grand Cru Classé", producer="Château Grand-Puy-Lacoste", region="Pauillac, Bordeaux, France", country="France", appellation="Pauillac", varietal="Cabernet Sauvignon/Merlot", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Grand Puy Lacoste Pauillac", "GPL Pauillac 5eme Cru"], description="Grand-Puy-Lacoste is among Pauillac's most classic and consistent Fifth Growths; producing textbook Pauillac with great aging potential at fair prices."),
    WineCatalogEntry(id="chateau-lagrange-saint-julien", name="Château Lagrange Saint-Julien 3ème Grand Cru Classé", producer="Château Lagrange", region="Saint-Julien, Bordeaux, France", country="France", appellation="Saint-Julien", varietal="Cabernet Sauvignon/Merlot", wine_type="red", avg_retail_price=70.0, price_tier="premium", aliases=["Lagrange Saint Julien", "Chateau Lagrange 3ème Cru"], description="Château Lagrange has been substantially improved since the 1980s; it now produces one of Saint-Julien's most consistent and approachable Grand Crus."),
    WineCatalogEntry(id="chateau-la-mission-haut-brion", name="Château La Mission Haut-Brion Pessac-Léognan Grand Cru Classé", producer="Domaine Clarence Dillon", region="Pessac-Léognan, Bordeaux, France", country="France", appellation="Pessac-Léognan", varietal="Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=600.0, price_tier="ultra-luxury", aliases=["La Mission Haut-Brion", "Chateau La Mission Haut Brion", "LMHB Pessac"], description="La Mission Haut-Brion is the great rival of Haut-Brion itself; a more powerful and structured wine that some prefer to its famous neighbor."),
    WineCatalogEntry(id="chateau-pape-clement", name="Château Pape Clément Pessac-Léognan Grand Cru Classé", producer="Gérard Perse", region="Pessac-Léognan, Bordeaux, France", country="France", appellation="Pessac-Léognan", varietal="Cabernet Sauvignon/Merlot", wine_type="red", avg_retail_price=150.0, price_tier="luxury", aliases=["Pape Clement Pessac", "Château Pape-Clément"], description="Pape Clément is one of Pessac-Léognan's oldest properties; under Gérard Perse's ownership it has become one of the appellation's most opulent and sought-after wines."),
]

# ---------------------------------------------------------------------------
# CALIFORNIA – Napa Valley additional cuvées and cult estates
# ---------------------------------------------------------------------------
CALIFORNIA_NAPA_EXTRA = [
    WineCatalogEntry(id="colgin-cariad", name="Colgin Cellars Cariad", producer="Colgin Cellars", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=500.0, price_tier="ultra-luxury", aliases=["Colgin Cariad Napa", "Colgin Cellars Cariad Red Wine"], description="Cariad is Colgin's most expressive and opulent cuvée; a Bordeaux-style blend from various Napa vineyards that showcases Ann Colgin's vision of the valley."),
    WineCatalogEntry(id="bond-quella", name="Bond Quella Cabernet Sauvignon", producer="Bond Estates", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=650.0, price_tier="ultra-luxury", aliases=["Bond Quella Napa Cab", "Bond Estates Quella Vineyard"], description="Quella is one of Bond's single-vineyard bottlings from an estate on the eastern hills of Napa; it demonstrates the intensity and mineralogy of this distinctive site."),
    WineCatalogEntry(id="abreu-madrona-ranch", name="Abreu Vineyard Madrona Ranch Cabernet Sauvignon", producer="Abreu Vineyard", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=700.0, price_tier="ultra-luxury", aliases=["Abreu Madrona Ranch", "David Abreu Madrona Ranch Napa"], description="Abreu Vineyard's Madrona Ranch is one of Napa's most sought-after wines; viticulturalist David Abreu's meticulously farmed estate produces Cabernet of extraordinary precision."),
    WineCatalogEntry(id="lokoya-mount-veeder", name="Lokoya Mount Veeder Cabernet Sauvignon", producer="Lokoya", region="Mount Veeder, Napa Valley, California, USA", country="USA", appellation="Mount Veeder", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=420.0, price_tier="ultra-luxury", aliases=["Lokoya Mount Veeder Cab", "Lokoya Winery Mount Veeder"], description="Lokoya's Mount Veeder is a powerful, high-elevation Napa Cabernet; the volcanic soils impart a distinctive mineral intensity and structure."),
    WineCatalogEntry(id="dominus-napa", name="Dominus Estate Napa Valley", producer="Dominus Estate", region="Yountville, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon/Cabernet Franc/Petit Verdot", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["Dominus Napa Valley", "Christian Moueix Dominus", "Dominus Estate Red Wine"], description="Dominus Estate is the Napa project of Christian Moueix (of Pétrus fame); a structured, age-worthy Napa red with unmistakable Bordelais sensibility."),
    WineCatalogEntry(id="philip-togni-cabernet", name="Philip Togni Vineyard Cabernet Sauvignon", producer="Philip Togni Vineyard", region="Spring Mountain, Napa Valley, California, USA", country="USA", appellation="Spring Mountain District", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Philip Togni Cab Spring Mountain", "Togni Spring Mountain Cabernet"], description="Philip Togni is a legendary Napa figure; his Spring Mountain Cabernet is among California's most age-worthy and intellectually serious red wines."),
    WineCatalogEntry(id="diamond-creek-volcanic-hill", name="Diamond Creek Vineyards Volcanic Hill Cabernet Sauvignon", producer="Diamond Creek Vineyards", region="Diamond Mountain, Napa Valley, California, USA", country="USA", appellation="Diamond Mountain District", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=280.0, price_tier="luxury", aliases=["Diamond Creek Volcanic Hill Cab", "Diamond Creek Volcanic Hill Napa"], description="Diamond Creek was Napa's first single-vineyard Cabernet; Volcanic Hill from white ash soils is the most structured and mineral of their three distinct vineyard wines."),
    WineCatalogEntry(id="eisele-araujo-cabernet", name="Eisele Vineyard Cabernet Sauvignon", producer="Eisele Vineyard", region="Calistoga, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=500.0, price_tier="ultra-luxury", aliases=["Eisele Vineyard Napa Cab", "Araujo Eisele Cabernet", "Domaine Pinnacle Eisele"], description="Eisele Vineyard is one of Napa's most storied sites; now owned by the Pinault family, it produces one of the valley's most precise, restrained, and long-lived Cabernets."),
    WineCatalogEntry(id="grace-family-cabernet", name="Grace Family Vineyards Cabernet Sauvignon", producer="Grace Family Vineyards", region="St. Helena, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=280.0, price_tier="luxury", aliases=["Grace Family Napa Cabernet", "Grace Family Vineyard Cab", "Dick Grace Cabernet"], description="Grace Family is one of Napa's great cult wines from a tiny one-acre urban vineyard in St. Helena; tiny production and exceptional quality make it highly collectible."),
    WineCatalogEntry(id="peter-michael-les-pavots", name="Peter Michael Winery Les Pavots", producer="Peter Michael Winery", region="Knights Valley, Sonoma, California, USA", country="USA", appellation="Knights Valley", varietal="Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Peter Michael Les Pavots", "Les Pavots Peter Michael Knights Valley"], description="Les Pavots is Peter Michael's iconic Bordeaux-blend from high-elevation Knights Valley; structured, age-worthy, and one of Sonoma's most compelling red wines."),
    WineCatalogEntry(id="peter-michael-point-rouge", name="Peter Michael Winery Mon Plaisir Chardonnay", producer="Peter Michael Winery", region="Knights Valley, Sonoma, California, USA", country="USA", appellation="Knights Valley", varietal="Chardonnay", wine_type="white", avg_retail_price=110.0, price_tier="luxury", aliases=["Peter Michael Mon Plaisir Chardonnay", "Peter Michael Chardonnay Knights Valley"], description="Peter Michael's Mon Plaisir Chardonnay is from high-elevation volcanic soils; one of California's most refined and complex whites with notable aging potential."),
    WineCatalogEntry(id="schrader-cellars-colesworthy", name="Schrader Cellars Colesworthy Beckstoffer To Kalon Cabernet", producer="Schrader Cellars", region="Oakville, Napa Valley, California, USA", country="USA", appellation="Oakville", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=350.0, price_tier="ultra-luxury", aliases=["Schrader Colesworthy Cabernet", "Schrader To Kalon Cabernet"], description="Schrader Cellars makes some of Napa's most hedonistic Cabernets from premier vineyards; Colesworthy from To Kalon shows extraordinary richness and opulence."),
    WineCatalogEntry(id="chappellet-signature-cabernet", name="Chappellet Signature Cabernet Sauvignon", producer="Chappellet Vineyard", region="Pritchard Hill, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=110.0, price_tier="luxury", aliases=["Chappellet Signature Cab", "Chappellet Winery Pritchard Hill", "Chappellet Napa Cabernet"], description="Chappellet is one of Napa's oldest and most historic wineries; their Signature Cabernet from Pritchard Hill is precise, structured, and built for long aging."),
    WineCatalogEntry(id="la-jota-howell-mountain", name="La Jota Vineyard Co. Cabernet Sauvignon Howell Mountain", producer="La Jota Vineyard Co.", region="Howell Mountain, Napa Valley, California, USA", country="USA", appellation="Howell Mountain", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=150.0, price_tier="luxury", aliases=["La Jota Howell Mountain Cab", "La Jota Vineyard Cabernet"], description="La Jota is one of Howell Mountain's historic wineries; the high-elevation volcanic soils produce structured, tannic Cabernets that age magnificently."),
]

# ---------------------------------------------------------------------------
# CALIFORNIA – Pinot Noir specialists + Syrah / Rhône varieties
# ---------------------------------------------------------------------------
CALIFORNIA_PINOT_SYRAH = [
    WineCatalogEntry(id="kosta-browne-rrv-pinot", name="Kosta Browne Russian River Valley Pinot Noir", producer="Kosta Browne", region="Russian River Valley, Sonoma, California, USA", country="USA", appellation="Russian River Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Kosta Browne RRV Pinot Noir", "KB Russian River Pinot", "Kosta Browne Pinot"], description="Kosta Browne is one of California's most sought-after Pinot Noir producers; their RRV bottling is opulent, deeply fruited, and quintessentially Californian."),
    WineCatalogEntry(id="kosta-browne-sonoma-coast", name="Kosta Browne Sonoma Coast Pinot Noir", producer="Kosta Browne", region="Sonoma Coast, California, USA", country="USA", appellation="Sonoma Coast", varietal="Pinot Noir", wine_type="red", avg_retail_price=85.0, price_tier="premium", aliases=["Kosta Browne Sonoma Coast Pinot", "KB Sonoma Coast Pinot Noir"], description="Kosta Browne's Sonoma Coast bottling blends multiple vineyard sources to create a consistently expressive, site-driven Pinot Noir."),
    WineCatalogEntry(id="hirsch-san-andreas-fault", name="Hirsch Vineyards San Andreas Fault Pinot Noir", producer="Hirsch Vineyards", region="Fort Ross-Seaview, Sonoma Coast, California, USA", country="USA", appellation="Fort Ross-Seaview", varietal="Pinot Noir", wine_type="red", avg_retail_price=85.0, price_tier="premium", aliases=["Hirsch San Andreas Fault Pinot", "Hirsch Vineyards Sonoma Coast Pinot"], description="Hirsch Vineyards occupies one of California's most dramatic coastal sites; the San Andreas Fault bottling shows the estate's signature savory, mineral Pinot Noir character."),
    WineCatalogEntry(id="mount-eden-estate-pinot", name="Mount Eden Vineyards Estate Pinot Noir", producer="Mount Eden Vineyards", region="Santa Cruz Mountains, California, USA", country="USA", appellation="Santa Cruz Mountains", varietal="Pinot Noir", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Mount Eden Estate Pinot", "Mount Eden Santa Cruz Pinot Noir", "Mount Eden Vineyards Pinot"], description="Mount Eden is a historic high-elevation estate in the Santa Cruz Mountains; the Estate Pinot Noir is one of California's most structured and age-worthy, with Burgundian precision."),
    WineCatalogEntry(id="mount-eden-estate-chardonnay", name="Mount Eden Vineyards Estate Chardonnay", producer="Mount Eden Vineyards", region="Santa Cruz Mountains, California, USA", country="USA", appellation="Santa Cruz Mountains", varietal="Chardonnay", wine_type="white", avg_retail_price=110.0, price_tier="luxury", aliases=["Mount Eden Estate Chardonnay", "Mount Eden Santa Cruz Chardonnay"], description="Mount Eden's Estate Chardonnay is among California's most Burgundian whites; from high-altitude clay-limestone soils, it ages for 10-20 years."),
    WineCatalogEntry(id="sea-smoke-southing-pinot", name="Sea Smoke Vineyards Southing Pinot Noir", producer="Sea Smoke Vineyards", region="Sta. Rita Hills, Santa Barbara, California, USA", country="USA", appellation="Sta. Rita Hills", varietal="Pinot Noir", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Sea Smoke Southing Pinot", "Sea Smoke Sta Rita Hills Pinot"], description="Sea Smoke Vineyards produces some of the Sta. Rita Hills' most powerful Pinot Noirs; Southing is their most concentrated and opulent bottling."),
    WineCatalogEntry(id="dumol-russian-river-pinot", name="DuMol Russian River Valley Pinot Noir", producer="DuMol", region="Russian River Valley, Sonoma, California, USA", country="USA", appellation="Russian River Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["DuMol Pinot Noir RRV", "DuMol Winery Russian River Pinot"], description="DuMol is one of Russian River Valley's most acclaimed producers; their Pinot Noir is graceful, aromatic, and shows impressive depth and length."),
    WineCatalogEntry(id="dumol-russian-river-chardonnay", name="DuMol Russian River Valley Chardonnay", producer="DuMol", region="Russian River Valley, Sonoma, California, USA", country="USA", appellation="Russian River Valley", varietal="Chardonnay", wine_type="white", avg_retail_price=90.0, price_tier="premium", aliases=["DuMol Chardonnay RRV", "DuMol Winery Russian River Chardonnay"], description="DuMol's Chardonnay is among Russian River Valley's finest; it balances California generosity with Burgundian restraint and mineral precision."),
    WineCatalogEntry(id="cayuse-vineyards-cailloux", name="Cayuse Vineyards Cailloux Vineyard Syrah", producer="Cayuse Vineyards", region="Walla Walla Valley, Washington, USA", country="USA", appellation="Walla Walla Valley", varietal="Syrah", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Cayuse Cailloux Syrah", "Cayuse Vineyards Walla Walla Syrah", "Cayuse Cailloux Vineyard"], description="Cayuse's Cailloux Vineyard Syrah is from stones-over-cobbles soils in Walla Walla; one of the Pacific Northwest's most collectible and ageworthy Syrahs."),
    WineCatalogEntry(id="cayuse-vineyards-bionic-frog", name="Cayuse Vineyards Bionic Frog Syrah", producer="Cayuse Vineyards", region="Walla Walla Valley, Washington, USA", country="USA", appellation="Walla Walla Valley", varietal="Syrah", wine_type="red", avg_retail_price=300.0, price_tier="luxury", aliases=["Cayuse Bionic Frog Walla Walla", "Bionic Frog Cayuse Syrah"], description="Bionic Frog is Cayuse's most powerful and hedonistic Syrah cuvée; from biodynamically farmed cobblestone soils, it achieves extraordinary concentration and complexity."),
    WineCatalogEntry(id="sine-qua-non-syrah", name="Sine Qua Non Syrah", producer="Sine Qua Non", region="Ventura County, California, USA", country="USA", appellation="California", varietal="Syrah", wine_type="red", avg_retail_price=400.0, price_tier="ultra-luxury", aliases=["SQN Syrah", "Sine Qua Non California Syrah", "Manfred Krankl Syrah"], description="Sine Qua Non is one of California's most collectible cult estates; Manfred Krankl's limited Syrahs change names each vintage but consistently achieve extraordinary complexity."),
    WineCatalogEntry(id="tablas-creek-esprit", name="Tablas Creek Vineyard Esprit de Tablas", producer="Tablas Creek Vineyard", region="Paso Robles, California, USA", country="USA", appellation="Paso Robles", varietal="Mourvèdre/Syrah/Grenache", wine_type="red", avg_retail_price=65.0, price_tier="premium", aliases=["Tablas Creek Esprit de Tablas", "Esprit Tablas Paso Robles", "Tablas Creek Rhone Red"], description="Esprit de Tablas is the flagship blend from Tablas Creek, the Paso Robles estate founded with Château de Beaucastel; a serious Rhône-style blend of remarkable complexity."),
    WineCatalogEntry(id="kistler-mccrea-vineyard", name="Kistler Vineyards McCrea Vineyard Chardonnay", producer="Kistler Vineyards", region="Sonoma Mountain, California, USA", country="USA", appellation="Sonoma Mountain", varietal="Chardonnay", wine_type="white", avg_retail_price=100.0, price_tier="premium", aliases=["Kistler McCrea Vineyard Chardonnay", "Kistler Sonoma Mountain Chardonnay"], description="Kistler's McCrea Vineyard Chardonnay is from one of their finest mountain sites; it demonstrates extraordinary richness and the potential for long-term aging."),
    WineCatalogEntry(id="marcassin-sea-section", name="Marcassin Sea Section Chardonnay", producer="Marcassin", region="Sonoma Coast, California, USA", country="USA", appellation="Sonoma Coast", varietal="Chardonnay", wine_type="white", avg_retail_price=500.0, price_tier="ultra-luxury", aliases=["Marcassin Sea Section", "Helen Turley Marcassin Chardonnay"], description="Marcassin is California's most sought-after Chardonnay estate; Helen Turley's tiny production wines from extreme coastal sites are among California's most age-worthy whites."),
]

# ---------------------------------------------------------------------------
# OREGON + WASHINGTON STATE – Key estates
# ---------------------------------------------------------------------------
OREGON_WASHINGTON = [
    WineCatalogEntry(id="antica-terra-botanica-pinot", name="Antica Terra Botanica Pinot Noir", producer="Antica Terra", region="Willamette Valley, Oregon, USA", country="USA", appellation="Willamette Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Antica Terra Botanica", "Antigua Terra Pinot Noir Oregon", "Botanica Pinot Noir Antica Terra"], description="Antica Terra's Botanica is one of Oregon's most collectible Pinot Noirs; from ancient marine soils in the Chehalem Mountains, it achieves Burgundian depth and complexity."),
    WineCatalogEntry(id="bergstrom-de-la-montagne", name="Bergström Wines De la Montagne Pinot Noir", producer="Bergström Wines", region="Willamette Valley, Oregon, USA", country="USA", appellation="Willamette Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Bergström De la Montagne Pinot", "Bergstrom Willamette Valley Pinot Noir"], description="Bergström's De la Montagne is their entry-level Willamette Valley Pinot Noir; it demonstrates the house style of restraint, precision, and mineral depth."),
    WineCatalogEntry(id="bergstrom-cumberland-reserve", name="Bergström Wines Cumberland Reserve Pinot Noir", producer="Bergström Wines", region="Willamette Valley, Oregon, USA", country="USA", appellation="Willamette Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Bergström Cumberland Reserve", "Bergstrom Cumberland Pinot Noir"], description="Cumberland Reserve is Bergström's estate blend Pinot Noir from their home vineyard; it achieves remarkable complexity and precision from the Chehalem Mountains."),
    WineCatalogEntry(id="patricia-green-pinot-reserve", name="Patricia Green Cellars Reserve Pinot Noir", producer="Patricia Green Cellars", region="Ribbon Ridge, Willamette Valley, Oregon, USA", country="USA", appellation="Ribbon Ridge", varietal="Pinot Noir", wine_type="red", avg_retail_price=75.0, price_tier="premium", aliases=["Patricia Green Reserve Pinot", "Pat Green Ribbon Ridge Pinot Noir"], description="Patricia Green Cellars is one of the Ribbon Ridge AVA's most acclaimed producers; the Reserve Pinot shows the distinctive precision of this Yamhill-Carlton sub-appellation."),
    WineCatalogEntry(id="kelley-fox-maresh-pinot", name="Kelley Fox Wines Maresh Vineyard Pinot Noir", producer="Kelley Fox Wines", region="Dundee Hills, Willamette Valley, Oregon, USA", country="USA", appellation="Dundee Hills", varietal="Pinot Noir", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Kelley Fox Maresh Pinot Noir", "Fox Wines Maresh Vineyard Oregon"], description="Kelley Fox is one of Oregon's most admired natural winemakers; Maresh Vineyard from the Dundee Hills is a wine of haunting elegance and mineral depth."),
    WineCatalogEntry(id="domaine-drouhin-oregon-pinot", name="Domaine Drouhin Oregon Pinot Noir", producer="Domaine Drouhin Oregon", region="Dundee Hills, Willamette Valley, Oregon, USA", country="USA", appellation="Dundee Hills", varietal="Pinot Noir", wine_type="red", avg_retail_price=75.0, price_tier="premium", aliases=["Drouhin Oregon Pinot Noir", "DDO Pinot Noir Willamette", "Domaine Drouhin Willamette Valley"], description="Domaine Drouhin Oregon is the American project of the Burgundy family; the estate Pinot Noir reflects classic Drouhin elegance translated to Oregon's Dundee Hills."),
    WineCatalogEntry(id="domaine-drouhin-laurene", name="Domaine Drouhin Oregon Laurène Pinot Noir", producer="Domaine Drouhin Oregon", region="Dundee Hills, Willamette Valley, Oregon, USA", country="USA", appellation="Dundee Hills", varietal="Pinot Noir", wine_type="red", avg_retail_price=150.0, price_tier="luxury", aliases=["Drouhin Laurene Pinot Noir", "DDO Laurène Oregon Pinot"], description="Laurène is Domaine Drouhin Oregon's reserve Pinot Noir, named for Véronique Drouhin-Boss's daughter; a more structured and age-worthy expression of the estate's finest barrels."),
    WineCatalogEntry(id="shea-wine-cellars-estate-pinot", name="Shea Wine Cellars Estate Pinot Noir", producer="Shea Wine Cellars", region="Yamhill-Carlton, Willamette Valley, Oregon, USA", country="USA", appellation="Yamhill-Carlton", varietal="Pinot Noir", wine_type="red", avg_retail_price=85.0, price_tier="premium", aliases=["Shea Wine Cellars Estate", "Shea Vineyard Oregon Pinot Noir"], description="Shea Wine Cellars is from one of Oregon's most celebrated estate vineyards; the estate Pinot is a beautifully balanced, terroir-driven wine from the Yamhill-Carlton AVA."),
    WineCatalogEntry(id="thomas-winery-magdalena-vineyard", name="Thomas Winery Magdalena Vineyard Pinot Noir", producer="Thomas Winery", region="Chehalem Mountains, Willamette Valley, Oregon, USA", country="USA", appellation="Chehalem Mountains", varietal="Pinot Noir", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Thomas Winery Magdalena Pinot", "Bryan Thomas Magdalena Vineyard"], description="Thomas Winery's Magdalena Vineyard is one of the Chehalem Mountains' most celebrated sites; deep, complex Pinot Noir with excellent aging potential."),
    WineCatalogEntry(id="quilceda-creek-cabernet", name="Quilceda Creek Vintners Cabernet Sauvignon", producer="Quilceda Creek Vintners", region="Columbia Valley, Washington, USA", country="USA", appellation="Columbia Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Quilceda Creek Cab Washington", "Quilceda Creek Columbia Valley Cabernet"], description="Quilceda Creek is Washington State's most revered Cabernet Sauvignon producer; their estate wine consistently receives 100-point scores and is one of America's greatest reds."),
    WineCatalogEntry(id="andrew-will-sorella", name="Andrew Will Winery Sorella", producer="Andrew Will Winery", region="Columbia Valley, Washington, USA", country="USA", appellation="Columbia Valley", varietal="Cabernet Sauvignon/Merlot", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Andrew Will Sorella Washington", "Chris Camarda Sorella Red Wine"], description="Sorella is Andrew Will's flagship Bordeaux blend; Chris Camarda's meticulous single-vineyard wines are benchmarks for Washington State winemaking."),
    WineCatalogEntry(id="leonetti-reserve-cabernet", name="Leonetti Cellar Reserve Cabernet Sauvignon", producer="Leonetti Cellar", region="Walla Walla Valley, Washington, USA", country="USA", appellation="Walla Walla Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=150.0, price_tier="luxury", aliases=["Leonetti Reserve Cabernet Walla Walla", "Leonetti Cellars Reserve Cab"], description="Leonetti Cellar is the founding estate of the Walla Walla wine industry; the Reserve Cabernet is Washington's most historic and beloved bottling."),
]

# ---------------------------------------------------------------------------
# ITALY – Mainstream Tuscany + Piedmont additions
# ---------------------------------------------------------------------------
ITALY_EXTRA = [
    WineCatalogEntry(id="ornellaia-bolgheri-superiore", name="Tenuta dell'Ornellaia Ornellaia Bolgheri Superiore", producer="Tenuta dell'Ornellaia", region="Bolgheri, Tuscany, Italy", country="Italy", appellation="Bolgheri Superiore DOC", varietal="Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=220.0, price_tier="luxury", aliases=["Ornellaia Bolgheri", "Ornellaia Tenuta Bolgheri Superiore", "Ornellaia Red Wine"], description="Ornellaia is one of Italy's great 'Super Tuscans'; a Bordeaux-style blend from the Bolgheri coast that consistently ranks among the world's finest red wines."),
    WineCatalogEntry(id="masseto-igt", name="Masseto Toscana IGT", producer="Masseto", region="Bolgheri, Tuscany, Italy", country="Italy", appellation="Toscana IGT", varietal="Merlot", wine_type="red", avg_retail_price=1100.0, price_tier="ultra-luxury", aliases=["Masseto Toscana", "Masseto Merlot Bolgheri", "Masseto Ornellaia Merlot"], description="Masseto is Italy's most collectible Merlot; from a unique clay-rich plot in Bolgheri, it achieves Pomerol-level richness and complexity that commands extraordinary prices."),
    WineCatalogEntry(id="antinori-tignanello", name="Marchesi Antinori Tignanello Toscana IGT", producer="Antinori", region="Tuscany, Italy", country="Italy", appellation="Toscana IGT", varietal="Sangiovese/Cabernet Sauvignon", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Antinori Tignanello", "Tignanello Super Tuscan", "Antinori Tignanello IGT"], description="Tignanello was one of the original 'Super Tuscans'; Antinori's Sangiovese-Cabernet blend pioneered the use of Bordeaux varieties in Tuscany and remains a benchmark."),
    WineCatalogEntry(id="antinori-solaia", name="Marchesi Antinori Solaia Toscana IGT", producer="Antinori", region="Tuscany, Italy", country="Italy", appellation="Toscana IGT", varietal="Cabernet Sauvignon/Sangiovese/Cabernet Franc", wine_type="red", avg_retail_price=280.0, price_tier="luxury", aliases=["Antinori Solaia Super Tuscan", "Solaia Tignanello Antinori"], description="Solaia is Antinori's prestige Super Tuscan; a Cabernet Sauvignon-dominant blend from the same vineyard as Tignanello, it achieves greater concentration and aging potential."),
    WineCatalogEntry(id="le-pergole-torte-montevertine", name="Montevertine Le Pergole Torte Toscana IGT", producer="Montevertine", region="Radda in Chianti, Tuscany, Italy", country="Italy", appellation="Toscana IGT", varietal="Sangiovese", wine_type="red", avg_retail_price=320.0, price_tier="luxury", aliases=["Le Pergole Torte", "Montevertine Pergole Torte Sangiovese", "Sergio Manetti Montevertine"], description="Le Pergole Torte is one of Tuscany's greatest pure Sangiovese wines; from high-altitude Radda, it shows extraordinary complexity and the ability to age for decades."),
    WineCatalogEntry(id="gaja-barbaresco-village", name="Gaja Barbaresco", producer="Gaja", region="Barbaresco, Piedmont, Italy", country="Italy", appellation="Barbaresco DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=280.0, price_tier="luxury", aliases=["Angelo Gaja Barbaresco", "Gaja Barbaresco DOCG", "Gaja Nebbiolo Barbaresco"], description="Gaja's Barbaresco is the most internationally recognized wine from this appellation; the village-level bottling demonstrates Angelo Gaja's perfectionist approach to Nebbiolo."),
    WineCatalogEntry(id="giacomo-conterno-cascina-francia", name="Giacomo Conterno Barolo Cascina Francia", producer="Giacomo Conterno", region="Serralunga d'Alba, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=400.0, price_tier="ultra-luxury", aliases=["Conterno Cascina Francia Barolo", "Giacomo Conterno Francia Barolo"], description="Cascina Francia is Giacomo Conterno's village-level Barolo from their estate in Serralunga; even this 'lesser' wine shows the extraordinary depth and structure of the estate."),
    WineCatalogEntry(id="vietti-rocche-barolo", name="Vietti Barolo Rocche di Castiglione", producer="Vietti", region="Castiglione Falletto, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Vietti Rocche Castiglione Barolo", "Vietti Barolo Rocche di Castiglione"], description="Rocche di Castiglione is one of Barolo's great crus; Vietti's version is one of the most refined and consistently excellent, combining power with notable elegance."),
    WineCatalogEntry(id="ceretto-bricco-rocche-barolo", name="Ceretto Barolo Bricco Rocche", producer="Ceretto", region="Castiglione Falletto, Piedmont, Italy", country="Italy", appellation="Barolo DOCG", varietal="Nebbiolo", wine_type="red", avg_retail_price=220.0, price_tier="luxury", aliases=["Ceretto Bricco Rocche", "Ceretto Barolo Bricco Rocche DOCG"], description="Bricco Rocche is Ceretto's monopole vineyard in Castiglione Falletto; one of Barolo's most celebrated crus, it produces wines of outstanding elegance and complexity."),
]

# ---------------------------------------------------------------------------
# NEW YORK + FINGER LAKES
# ---------------------------------------------------------------------------
NY_FINGER_LAKES = [
    WineCatalogEntry(id="herman-wiemer-riesling-dry", name="Hermann J. Wiemer Vineyard Dry Riesling", producer="Hermann J. Wiemer Vineyard", region="Finger Lakes, New York, USA", country="USA", appellation="Finger Lakes", varietal="Riesling", wine_type="white", avg_retail_price=32.0, price_tier="value", aliases=["Hermann Wiemer Dry Riesling", "HJ Wiemer Finger Lakes Riesling", "Wiemer Vineyard Dry Riesling NY"], description="Hermann J. Wiemer is the patriarch of Finger Lakes winemaking; his Dry Riesling is a benchmark for American Riesling, showing cool-climate precision and ageability."),
    WineCatalogEntry(id="dr-frank-dry-riesling", name="Dr. Konstantin Frank Dry Riesling", producer="Dr. Konstantin Frank", region="Finger Lakes, New York, USA", country="USA", appellation="Finger Lakes", varietal="Riesling", wine_type="white", avg_retail_price=28.0, price_tier="value", aliases=["Konstantin Frank Dry Riesling", "Dr Frank Finger Lakes Riesling NY"], description="Dr. Konstantin Frank pioneered Vitis vinifera in the Finger Lakes; their Dry Riesling remains one of the region's most consistent and food-friendly wines."),
    WineCatalogEntry(id="ravines-argetsinger-riesling", name="Ravines Wine Cellars Argetsinger Vineyard Riesling", producer="Ravines Wine Cellars", region="Finger Lakes, New York, USA", country="USA", appellation="Finger Lakes", varietal="Riesling", wine_type="white", avg_retail_price=35.0, price_tier="value", aliases=["Ravines Argetsinger Riesling", "Ravines Wine Cellars Finger Lakes Riesling"], description="Ravines is one of the Finger Lakes' most respected producers; the Argetsinger Vineyard Riesling shows excellent mineral character from shale soils on Seneca Lake."),
]

# ===========================================================================
# GLOBAL COMPLETENESS EXPANSION
# Every major premium wine-producing region on Earth, systematically added
# ===========================================================================

# ---------------------------------------------------------------------------
# ITALY – Veneto: Amarone / Valpolicella
# ---------------------------------------------------------------------------
ITALY_VENETO = [
    WineCatalogEntry(id="allegrini-amarone", name="Allegrini Amarone della Valpolicella Classico", producer="Allegrini", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Amarone della Valpolicella DOCG", varietal="Corvina/Rondinella/Molinara", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Allegrini Amarone Classico", "Allegrini Valpolicella Amarone"], description="Allegrini is one of the Valpolicella Classico zone's most acclaimed estates; their Amarone is richly textured with dried cherry, bitter chocolate, and remarkable aging potential."),
    WineCatalogEntry(id="allegrini-la-poja", name="Allegrini La Poja Veronese IGT", producer="Allegrini", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Veronese IGT", varietal="Corvina", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Allegrini La Poja Veronese", "La Poja Corvina Veneto"], description="La Poja is Allegrini's iconic single-vineyard 100% Corvina; a bold expression of the Veneto's finest native grape from a sun-drenched amphitheater above the Fumane valley."),
    WineCatalogEntry(id="bertani-amarone-classico", name="Bertani Amarone della Valpolicella Classico", producer="Bertani", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Amarone della Valpolicella DOCG", varietal="Corvina/Rondinella", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Bertani Amarone Classico", "Cav. G.B. Bertani Amarone"], description="Bertani is one of Amarone's historic producers; their Classico is a benchmark for the traditional Veronese style with extended oak aging and extraordinary longevity."),
    WineCatalogEntry(id="masi-costasera-amarone", name="Masi Costasera Amarone della Valpolicella Classico", producer="Masi Agricola", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Amarone della Valpolicella DOCG", varietal="Corvina/Molinara/Rondinella", wine_type="red", avg_retail_price=65.0, price_tier="premium", aliases=["Masi Costasera Amarone", "Masi Agricola Costasera Classico"], description="Masi's Costasera is one of Amarone's most widely distributed and consistently reliable wines; lush with dried fruit, spice, and typical Veronese warmth."),
    WineCatalogEntry(id="masi-campolongo-amarone", name="Masi Campolongo di Torbe Amarone della Valpolicella", producer="Masi Agricola", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Amarone della Valpolicella DOCG", varietal="Corvina/Molinara/Rondinella", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["Masi Campolongo di Torbe", "Masi Single Vineyard Amarone"], description="Campolongo di Torbe is Masi's flagship single-vineyard Amarone from one of the Classico zone's most prized sites; rich, structured, and very long-lived."),
    WineCatalogEntry(id="zenato-amarone-classico", name="Zenato Amarone della Valpolicella Classico Riserva Sergio Zenato", producer="Zenato", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Amarone della Valpolicella DOCG", varietal="Corvina/Rondinella/Oseleta", wine_type="red", avg_retail_price=130.0, price_tier="luxury", aliases=["Zenato Amarone Riserva Sergio Zenato", "Zenato Amarone Classico Riserva"], description="Zenato's Riserva Sergio Zenato is a benchmark luxury Amarone; produced only in exceptional vintages, it shows extraordinary complexity and aging potential."),
    WineCatalogEntry(id="speri-amarone-classico", name="Speri Amarone della Valpolicella Classico", producer="Speri", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Amarone della Valpolicella DOCG", varietal="Corvina/Rondinella", wine_type="red", avg_retail_price=70.0, price_tier="premium", aliases=["Speri Amarone Classico Veneto", "F.lli Speri Amarone"], description="Speri is one of Valpolicella Classico's most respected family estates; their Amarone is elegant and precise with a more restrained style than many peers, showing genuine terroir character."),
    WineCatalogEntry(id="tedeschi-amarone-capitel-monte", name="Tedeschi Amarone della Valpolicella Capitel Monte Olmi", producer="Tedeschi", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Amarone della Valpolicella DOCG", varietal="Corvina/Corvinone/Rondinella", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Tedeschi Capitel Monte Olmi Amarone", "Tedeschi Classico Amarone Capitel"], description="Capitel Monte Olmi is Tedeschi's prestige single-vineyard Amarone from a hilltop site in Pedemonte; dense, structured, and very age-worthy."),
    WineCatalogEntry(id="quintarelli-amarone", name="Giuseppe Quintarelli Amarone della Valpolicella Classico", producer="Giuseppe Quintarelli", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Amarone della Valpolicella DOCG", varietal="Corvina/Rondinella/Nebbiolo/Sangiovese", wine_type="red", avg_retail_price=800.0, price_tier="ultra-luxury", aliases=["Quintarelli Amarone Classico", "Bepi Quintarelli Amarone"], description="Giuseppe Quintarelli's Amarone is the most sought-after and mystical wine from Valpolicella; aged for 7+ years before release, it achieves a complexity that transcends its appellation."),
    WineCatalogEntry(id="tommasi-amarone", name="Tommasi Amarone della Valpolicella Classico", producer="Tommasi Family Estates", region="Valpolicella Classico, Veneto, Italy", country="Italy", appellation="Amarone della Valpolicella DOCG", varietal="Corvina/Corvinone/Rondinella/Oseleta", wine_type="red", avg_retail_price=75.0, price_tier="premium", aliases=["Tommasi Amarone Classico", "Tommasi Family Amarone Veneto"], description="Tommasi is one of Valpolicella's most reliable family estates; their Amarone is consistently excellent value, full-bodied with classic dried cherry and chocolate character."),
]

# ---------------------------------------------------------------------------
# ITALY – Friuli-Venezia Giulia (orange wine + white excellence)
# ---------------------------------------------------------------------------
ITALY_FRIULI = [
    WineCatalogEntry(id="radikon-ribolla-gialla", name="Radikon Ribolla Gialla Oslavia", producer="Radikon", region="Oslavia, Friuli-Venezia Giulia, Italy", country="Italy", appellation="Venezia Giulia IGT", varietal="Ribolla Gialla", wine_type="orange", avg_retail_price=80.0, price_tier="premium", aliases=["Radikon Ribolla Oslavia", "Stanko Radikon Ribolla Gialla Orange Wine"], description="Radikon's Ribolla Gialla is a pioneering orange wine; Stanko Radikon's extended skin maceration produces a wine of extraordinary amber depth, complexity, and longevity."),
    WineCatalogEntry(id="radikon-jakot", name="Radikon Jakot Tocai Friulano", producer="Radikon", region="Oslavia, Friuli-Venezia Giulia, Italy", country="Italy", appellation="Venezia Giulia IGT", varietal="Friulano", wine_type="orange", avg_retail_price=75.0, price_tier="premium", aliases=["Radikon Jakot Friulano", "Stanko Radikon Tocai Jakot"], description="Jakot is Radikon's single-variety Friulano bottling; the playful reverse-spelling of 'Tocai' signals the non-conformist ethos of this groundbreaking orange wine producer."),
    WineCatalogEntry(id="gravner-ribolla-amphora", name="Josko Gravner Ribolla Gialla Anfora", producer="Josko Gravner", region="Oslavia, Friuli-Venezia Giulia, Italy", country="Italy", appellation="Venezia Giulia IGT", varietal="Ribolla Gialla", wine_type="orange", avg_retail_price=120.0, price_tier="luxury", aliases=["Gravner Ribolla Anfora", "Josko Gravner Orange Wine", "Gravner Ribolla Gialla"], description="Josko Gravner is one of the fathers of the modern orange wine movement; his Ribolla Gialla Anfora, fermented and aged in Georgian clay amphorae, is one of Italy's most important wines."),
    WineCatalogEntry(id="livio-felluga-terre-alte", name="Livio Felluga Terre Alte Friuli Colli Orientali", producer="Livio Felluga", region="Friuli Colli Orientali, Friuli-Venezia Giulia, Italy", country="Italy", appellation="Friuli Colli Orientali DOC", varietal="Friulano/Pinot Bianco/Sauvignon", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Livio Felluga Terre Alte Blend", "Felluga Terre Alte Friuli Colli Orientali"], description="Terre Alte is Livio Felluga's iconic white blend; an enduring benchmark for the Colli Orientali, it shows the elegance and complexity of Friuli's finest white wines."),
    WineCatalogEntry(id="vie-di-romans-flors-apalis", name="Vie di Romans Flors di Uis Friuli Isonzo", producer="Vie di Romans", region="Friuli Isonzo, Friuli-Venezia Giulia, Italy", country="Italy", appellation="Friuli Isonzo DOC", varietal="Malvasia Istriana/Tocai Friulano/Riesling", wine_type="white", avg_retail_price=50.0, price_tier="mid", aliases=["Vie di Romans Flors di Uis", "Vie di Romans Isonzo White Blend"], description="Vie di Romans is one of Friuli's most consistently excellent producers; Flors di Uis is their iconic multi-varietal white blend showcasing the diversity of Isonzo's terroir."),
]

# ---------------------------------------------------------------------------
# ITALY – Trentino-Alto Adige + Soave
# ---------------------------------------------------------------------------
ITALY_NORTHEAST = [
    WineCatalogEntry(id="foradori-teroldego", name="Foradori Teroldego Rotaliano", producer="Foradori", region="Trentino, Italy", country="Italy", appellation="Teroldego Rotaliano DOC", varietal="Teroldego", wine_type="red", avg_retail_price=45.0, price_tier="mid", aliases=["Elisabetta Foradori Teroldego", "Foradori Rotaliano Teroldego"], description="Elisabetta Foradori is Italy's most celebrated champion of the Teroldego grape; her biodynamic wines show the unique character of this rare Trentino variety."),
    WineCatalogEntry(id="foradori-granato", name="Foradori Granato Vigneti delle Dolomiti IGT", producer="Foradori", region="Trentino, Italy", country="Italy", appellation="Vigneti delle Dolomiti IGT", varietal="Teroldego", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Foradori Granato IGT Dolomiti", "Elisabetta Foradori Granato"], description="Granato is Foradori's prestige Teroldego from old vines; aged in large Slavonian oak, it achieves a complexity that makes it one of Italy's most serious indigenous variety expressions."),
    WineCatalogEntry(id="alois-lageder-lowengang-chardonnay", name="Alois Lageder Löwengang Chardonnay Alto Adige", producer="Alois Lageder", region="Bolzano, Alto Adige, Italy", country="Italy", appellation="Alto Adige DOC", varietal="Chardonnay", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Lageder Löwengang Chardonnay", "Alois Lageder Alto Adige Chardonnay"], description="Alois Lageder is Alto Adige's premier biodynamic estate; their Löwengang Chardonnay from estate vines is one of Italy's finest expressions of the variety."),
    WineCatalogEntry(id="pieropan-soave-classico-calvarino", name="Pieropan Soave Classico La Rocca", producer="Pieropan", region="Soave Classico, Veneto, Italy", country="Italy", appellation="Soave Classico DOC", varietal="Garganega", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Pieropan La Rocca Soave", "Pieropan Soave Classico La Rocca"], description="Pieropan is the reference for Soave Classico; La Rocca is their single-vineyard bottling from volcanic basalt soils that shows remarkable complexity and aging potential."),
    WineCatalogEntry(id="pra-soave-classico-monte-grande", name="Prà Soave Classico Monte Grande", producer="Prà", region="Soave Classico, Veneto, Italy", country="Italy", appellation="Soave Classico DOC", varietal="Garganega", wine_type="white", avg_retail_price=40.0, price_tier="mid", aliases=["Pra Monte Grande Soave", "Prà Soave Monte Grande Classico"], description="Prà is one of Soave's leading natural wine producers; Monte Grande from a single volcanic basalt vineyard is structured, mineral, and one of the finest examples of serious Soave."),
    WineCatalogEntry(id="inama-soave-classico-vigneti-di-foscarino", name="Inama Soave Classico Superiore Vigneti di Foscarino", producer="Inama", region="Soave Classico, Veneto, Italy", country="Italy", appellation="Soave Classico Superiore DOC", varietal="Garganega", wine_type="white", avg_retail_price=35.0, price_tier="value", aliases=["Inama Foscarino Soave Classico", "Inama Vigneti di Foscarino"], description="Inama produces some of Soave's most mineral and food-friendly wines; Vigneti di Foscarino from volcanic soils shows the purity and freshness that make Soave great."),
]

# ---------------------------------------------------------------------------
# GERMANY – Rheingau, Rheinhessen, Franken
# ---------------------------------------------------------------------------
GERMANY_ADDITIONAL = [
    # Rheingau
    WineCatalogEntry(id="georg-breuer-berg-schlossberg-gg", name="Georg Breuer Berg Schlossberg Riesling GG", producer="Georg Breuer", region="Rüdesheim, Rheingau, Germany", country="Germany", appellation="Rheingau", varietal="Riesling", wine_type="white", avg_retail_price=80.0, price_tier="premium", aliases=["Breuer Berg Schlossberg GG", "Georg Breuer Rüdesheim Riesling"], description="Georg Breuer is one of the Rheingau's most serious estates; Berg Schlossberg Grosses Gewächs is a powerful, mineral dry Riesling from one of the region's greatest sites."),
    WineCatalogEntry(id="weil-kiedrich-grafenberg-gg", name="Weingut Robert Weil Kiedrich Gräfenberg Riesling GG", producer="Weingut Robert Weil", region="Kiedrich, Rheingau, Germany", country="Germany", appellation="Rheingau", varietal="Riesling", wine_type="white", avg_retail_price=90.0, price_tier="premium", aliases=["Robert Weil Grafenberg GG", "Weil Kiedrich Grafenberg Rheingau Riesling"], description="Weingut Robert Weil is one of the Rheingau's most acclaimed estates; the Kiedrich Gräfenberg GG is a benchmark for the region's dry Riesling style with extraordinary finesse and length."),
    WineCatalogEntry(id="leitz-monte-schlossberg-gg", name="Josef Leitz Rüdesheimer Berg Schlossberg Riesling GG", producer="Josef Leitz", region="Rüdesheim, Rheingau, Germany", country="Germany", appellation="Rheingau", varietal="Riesling", wine_type="white", avg_retail_price=75.0, price_tier="premium", aliases=["Leitz Berg Schlossberg GG", "Josef Leitz Rüdesheim Riesling"], description="Josef Leitz has become one of the Rheingau's most exciting producers; the Berg Schlossberg GG is a textbook example of powerful, mineral Rüdesheimer Riesling with great aging potential."),
    WineCatalogEntry(id="kunstler-hochheimer-gg", name="Weingut Künstler Hochheimer Kirchenstück Riesling GG", producer="Weingut Künstler", region="Hochheim, Rheingau, Germany", country="Germany", appellation="Rheingau", varietal="Riesling", wine_type="white", avg_retail_price=65.0, price_tier="premium", aliases=["Künstler Hochheimer Kirchenstück GG", "Kunstler Hochheim Riesling Rheingau"], description="Weingut Künstler in Hochheim produces some of Germany's most powerful and mineral Rieslings; Kirchenstück GG from deep clay soils shows remarkable body and complexity."),
    # Rheinhessen
    WineCatalogEntry(id="keller-riesling-gg-kirchspiel", name="Weingut Keller Dalsheimer Hubacker Riesling GG", producer="Weingut Keller", region="Flörsheim-Dalsheim, Rheinhessen, Germany", country="Germany", appellation="Rheinhessen", varietal="Riesling", wine_type="white", avg_retail_price=90.0, price_tier="premium", aliases=["Keller Hubacker Riesling GG", "Keller Dalsheimer GG Rheinhessen", "Weingut Keller Riesling GG"], description="Weingut Keller is perhaps Germany's most celebrated Riesling producer; the Hubacker GG from Flörsheim-Dalsheim shows extraordinary minerality and aging potential from limestone soils."),
    WineCatalogEntry(id="keller-von-der-fels", name="Weingut Keller Riesling von der Fels", producer="Weingut Keller", region="Flörsheim-Dalsheim, Rheinhessen, Germany", country="Germany", appellation="Rheinhessen", varietal="Riesling", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Keller Von der Fels Riesling", "Weingut Keller Rheinhessen Dry Riesling"], description="Von der Fels is Keller's entry-level dry Riesling; even at this level, the limestone soils of Dalsheim produce a wine of extraordinary mineral precision and food-friendliness."),
    WineCatalogEntry(id="wittmann-kirchspiel-riesling-gg", name="Weingut Wittmann Westhofener Kirchspiel Riesling GG", producer="Weingut Wittmann", region="Westhofen, Rheinhessen, Germany", country="Germany", appellation="Rheinhessen", varietal="Riesling", wine_type="white", avg_retail_price=70.0, price_tier="premium", aliases=["Wittmann Kirchspiel GG", "Philipp Wittmann Westhofen Riesling GG"], description="Weingut Wittmann is a leading biodynamic estate in Rheinhessen; Kirchspiel GG is their most mineral and structured Grosses Gewächs from loam-over-limestone soils."),
    # Franken
    WineCatalogEntry(id="rudolf-furst-spatburgunder-gg", name="Weingut Rudolf Fürst Bürgstadter Centgrafenberg Spätburgunder GG", producer="Weingut Rudolf Fürst", region="Bürgstadt, Franken, Germany", country="Germany", appellation="Franken", varietal="Spätburgunder", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Rudolf Fürst Spätburgunder GG", "Fürst Centgrafenberg Pinot Noir Franken"], description="Rudolf Fürst produces Germany's most acclaimed Spätburgunder (Pinot Noir); the Centgrafenberg GG from red sandstone soils shows extraordinary finesse and Burgundian elegance."),
    WineCatalogEntry(id="horst-sauer-escherndorfer-lump", name="Weingut Horst Sauer Escherndorfer Lump Riesling Spätlese", producer="Weingut Horst Sauer", region="Escherndorf, Franken, Germany", country="Germany", appellation="Franken", varietal="Riesling", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Horst Sauer Escherndorf Lump Riesling", "Sauer Escherndorfer Lump Franken"], description="Horst Sauer is Franken's most exciting producer; the Escherndorfer Lump Spätlese from one of Germany's steepest terraced vineyards is a wine of remarkable concentration and minerality."),
]

# ---------------------------------------------------------------------------
# AUSTRIA – Grüner Veltliner, Blaufränkisch, Steiermark completeness
# ---------------------------------------------------------------------------
AUSTRIA_ADDITIONS = [
    WineCatalogEntry(id="hirsch-heiligenstein-riesling", name="Weingut Hirsch Heiligenstein Riesling 1ÖTW", producer="Weingut Hirsch", region="Kammern, Kamptal, Austria", country="Austria", appellation="Kamptal DAC Reserve", varietal="Riesling", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Hirsch Heiligenstein Riesling GG", "Johannes Hirsch Heiligenstein Kamptal"], description="Weingut Hirsch is one of Kamptal's most dynamic estates; the Heiligenstein Riesling from the volcanic gneiss hilltop shows extraordinary spice, depth, and longevity."),
    WineCatalogEntry(id="nikolaihof-im-weingebirge", name="Nikolaihof Im Weingebirge Riesling Smaragd", producer="Nikolaihof", region="Mautern, Wachau, Austria", country="Austria", appellation="Wachau", varietal="Riesling", wine_type="white", avg_retail_price=65.0, price_tier="premium", aliases=["Nikolaihof Im Weingebirge Smaragd", "Nikolaihof Wachau Riesling Im Weingebirge"], description="Nikolaihof is the Wachau's oldest organic estate; Im Weingebirge Smaragd from very old vines on ancient terraces produces one of Austria's most profound and age-worthy Rieslings."),
    WineCatalogEntry(id="loimer-kamptal-gruner-spiegel", name="Fred Loimer Kamptal Grüner Veltliner Spiegel", producer="Fred Loimer", region="Langenlois, Kamptal, Austria", country="Austria", appellation="Kamptal DAC", varietal="Grüner Veltliner", wine_type="white", avg_retail_price=40.0, price_tier="mid", aliases=["Loimer Spiegel Grüner Veltliner", "Fred Loimer GV Spiegel Kamptal"], description="Fred Loimer is one of Austria's most innovative biodynamic producers; the Spiegel Grüner Veltliner shows the peppery freshness and mineral depth of Kamptal's finest single-vineyard GVs."),
    WineCatalogEntry(id="moric-blaufrankisch-lutzmannsburg", name="Moric Blaufränkisch Lutzmannsburg Alte Reben", producer="Moric", region="Mittelburgenland, Austria", country="Austria", appellation="Mittelburgenland DAC", varietal="Blaufränkisch", wine_type="red", avg_retail_price=65.0, price_tier="premium", aliases=["Moric Blaufrankisch Lutzmannsburg Alte Reben", "Roland Velich Moric Blaufrankisch"], description="Moric's Roland Velich produces some of Austria's greatest Blaufränkisch; the Lutzmannsburg Alte Reben from 50+ year old vines shows extraordinary depth, spice, and aging potential."),
    WineCatalogEntry(id="umathum-saint-laurent", name="Weingut Umathum St. Laurent Vom Stein", producer="Weingut Umathum", region="Frauenkirchen, Burgenland, Austria", country="Austria", appellation="Burgenland", varietal="St. Laurent", wine_type="red", avg_retail_price=40.0, price_tier="mid", aliases=["Umathum St Laurent Vom Stein", "Josef Umathum Saint Laurent Burgenland"], description="Weingut Umathum is one of the pioneers of serious biodynamic winemaking in Austria; their Vom Stein St. Laurent is a benchmark for this unique variety with silky tannins and great depth."),
    WineCatalogEntry(id="tement-sauvignon-blanc-zieregg", name="Weingut Tement Zieregg Sauvignon Blanc Grosse STK Lage", producer="Weingut Tement", region="Berghausen, Südsteiermark, Austria", country="Austria", appellation="Südsteiermark DAC", varietal="Sauvignon Blanc", wine_type="white", avg_retail_price=70.0, price_tier="premium", aliases=["Tement Zieregg Sauvignon Blanc", "Manfred Tement Zieregg Südsteiermark"], description="Tement's Zieregg is one of Austria's most celebrated single-vineyard Sauvignon Blancs; from steep Südsteiermark slopes, it shows a mineral, complex style utterly different from New World examples."),
    WineCatalogEntry(id="polz-weissburgunder-hochgrassnitzberg", name="Weingut Polz Hochgrassnitzberg Weißburgunder Grosse STK Lage", producer="Weingut Polz", region="Spielfeld, Südsteiermark, Austria", country="Austria", appellation="Südsteiermark DAC", varietal="Weißburgunder", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Polz Hochgrassnitzberg Pinot Blanc", "Polz Weissburgunder Styria"], description="Weingut Polz produces one of Austria's most distinctive Pinot Blancs; the Hochgrassnitzberg vineyard on the Slovenian border produces wines of remarkable mineral depth and complexity."),
]

# ---------------------------------------------------------------------------
# SPAIN – Sherry + Galicia depth + more Rioja
# ---------------------------------------------------------------------------
SPAIN_ADDITIONS = [
    # Jerez/Sherry
    WineCatalogEntry(id="lustau-almacenista-manzanilla", name="Emilio Lustau Almacenista Manzanilla de Sanlúcar", producer="Emilio Lustau", region="Jerez de la Frontera, Andalucía, Spain", country="Spain", appellation="Manzanilla-Sanlúcar de Barrameda DO", varietal="Palomino Fino", wine_type="fortified", avg_retail_price=30.0, price_tier="value", aliases=["Lustau Almacenista Manzanilla", "Emilio Lustau Manzanilla Sherry"], description="Emilio Lustau is Jerez's leading single-vineyard Sherry producer; their Almacenista series draws from individual small producers to bottle exceptional character and individuality."),
    WineCatalogEntry(id="lustau-palo-cortado-vors", name="Emilio Lustau Palo Cortado Peninsula VORS", producer="Emilio Lustau", region="Jerez de la Frontera, Andalucía, Spain", country="Spain", appellation="Jerez-Xérès-Sherry DO", varietal="Palomino Fino", wine_type="fortified", avg_retail_price=75.0, price_tier="premium", aliases=["Lustau Palo Cortado VORS", "Lustau Peninsula VORS Sherry"], description="Lustau's VORS Palo Cortado is aged for 30+ years; it achieves extraordinary complexity combining the richness of Oloroso with the delicacy of Amontillado."),
    WineCatalogEntry(id="gonzalez-byass-apostoles-oloroso", name="González Byass Apóstoles Oloroso Muy Viejo VORS", producer="González Byass", region="Jerez de la Frontera, Andalucía, Spain", country="Spain", appellation="Jerez-Xérès-Sherry DO", varietal="Palomino Fino/Pedro Ximénez", wine_type="fortified", avg_retail_price=65.0, price_tier="premium", aliases=["Gonzalez Byass Apostoles VORS", "Apostoles Oloroso Gonzalez Byass"], description="Apóstoles is González Byass's greatest VORS Oloroso; aged for 30+ years with a touch of PX, it shows extraordinary nutty complexity and a rich, lingering finish."),
    WineCatalogEntry(id="hidalgo-la-gitana-manzanilla", name="Hidalgo La Gitana Manzanilla", producer="Hidalgo-La Gitana", region="Sanlúcar de Barrameda, Andalucía, Spain", country="Spain", appellation="Manzanilla-Sanlúcar de Barrameda DO", varietal="Palomino Fino", wine_type="fortified", avg_retail_price=18.0, price_tier="value", aliases=["La Gitana Manzanilla Hidalgo", "Hidalgo Manzanilla Sherry"], description="La Gitana is Spain's most iconic Manzanilla; produced in Sanlúcar de Barrameda with its distinctive sea breeze, it shows the classic salty, almond character of this unique Sherry style."),
    WineCatalogEntry(id="barbadillo-solear-manzanilla", name="Barbadillo Solear Manzanilla en Rama", producer="Barbadillo", region="Sanlúcar de Barrameda, Andalucía, Spain", country="Spain", appellation="Manzanilla-Sanlúcar de Barrameda DO", varietal="Palomino Fino", wine_type="fortified", avg_retail_price=22.0, price_tier="value", aliases=["Barbadillo Solear En Rama Manzanilla", "Barbadillo Sanlúcar Manzanilla"], description="Barbadillo is the largest producer in Sanlúcar; their Solear en Rama is unfiltered Manzanilla bottled from the finest casks, offering exceptional freshness and mineral complexity."),
    WineCatalogEntry(id="equipo-navazos-la-bota-fino", name="Equipo Navazos La Bota de Fino", producer="Equipo Navazos", region="Jerez de la Frontera, Andalucía, Spain", country="Spain", appellation="Jerez-Xérès-Sherry DO", varietal="Palomino Fino", wine_type="fortified", avg_retail_price=35.0, price_tier="value", aliases=["Navazos La Bota de Fino", "Equipo Navazos La Bota Fino Sherry"], description="Equipo Navazos selects exceptional individual casks of Sherry for their La Bota series; each bottling is a unique expression of a specific fino, manzanilla, or aged style."),
    # Galicia depth
    WineCatalogEntry(id="palacio-fefiñanes-albarino", name="Palacio de Fefiñanes Albariño de Fefiñanes III año", producer="Palacio de Fefiñanes", region="Cambados, Rías Baixas, Spain", country="Spain", appellation="Rías Baixas DO", varietal="Albariño", wine_type="white", avg_retail_price=60.0, price_tier="premium", aliases=["Fefiñanes III Año Albariño", "Palacio Fefiñanes Albarino Rias Baixas"], description="Palacio de Fefiñanes produces one of Rías Baixas's most age-worthy Albariños; the III Año bottling is aged for 3 years before release, showing extraordinary complexity and richness."),
    WineCatalogEntry(id="zarate-albarino-el-palomar", name="Zárate Albariño El Palomar Rías Baixas", producer="Zárate", region="Meaño, Rías Baixas, Spain", country="Spain", appellation="Rías Baixas DO", varietal="Albariño", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Zarate El Palomar Albarino", "Zárate Rías Baixas Albariño El Palomar"], description="Zárate is one of Rías Baixas's most artisanal producers; El Palomar from very old vines in the O Rosal subzone shows mineral depth and saline complexity."),
    # More Rioja
    WineCatalogEntry(id="rioja-alta-890-gran-reserva", name="La Rioja Alta Gran Reserva 890", producer="La Rioja Alta", region="Haro, Rioja, Spain", country="Spain", appellation="Rioja DOCa", varietal="Tempranillo/Graciano/Mazuelo", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["La Rioja Alta 890 Gran Reserva", "Rioja Alta Reserva 890 Gran Reserva"], description="La Rioja Alta's 890 is the pinnacle of traditional Rioja winemaking; aged for 10+ years, it embodies the austere, complex style of Rioja at its most profound."),
    WineCatalogEntry(id="marques-murrieta-castillo-ygay", name="Marqués de Murrieta Castillo Ygay Gran Reserva Especial", producer="Marqués de Murrieta", region="Logroño, Rioja, Spain", country="Spain", appellation="Rioja DOCa", varietal="Tempranillo/Mazuelo", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Murrieta Castillo Ygay Gran Reserva Especial", "Marqués de Murrieta Castillo Ygay"], description="Castillo Ygay Gran Reserva Especial is one of Rioja's most iconic bottles; released only in the greatest vintages after years of aging, it represents the pinnacle of the traditional style."),
    WineCatalogEntry(id="artadi-grandes-anadas", name="Bodegas Artadi Grandes Añadas Rioja", producer="Bodegas Artadi", region="Laguardia, Rioja, Spain", country="Spain", appellation="Rioja DOCa", varietal="Tempranillo", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Artadi Grandes Anadas Rioja", "Artadi Viñas de Gain Rioja"], description="Artadi's Grandes Añadas is their prestige single-vineyard cuvée from old vines in Laguardia; one of Rioja's finest expressions of Tempranillo with great structure and aging potential."),
]

# ---------------------------------------------------------------------------
# PORTUGAL – Douro, Port, Alentejo, Dão, Vinho Verde
# ---------------------------------------------------------------------------
PORTUGAL_ADDITIONS = [
    WineCatalogEntry(id="quinta-do-crasto-reserva", name="Quinta do Crasto Reserva Old Vines Douro", producer="Quinta do Crasto", region="Douro Superior, Portugal", country="Portugal", appellation="Douro DOC", varietal="Touriga Nacional/Touriga Franca/Tinta Roriz", wine_type="red", avg_retail_price=45.0, price_tier="mid", aliases=["Crasto Reserva Old Vines", "Quinta Crasto Douro Reserva"], description="Quinta do Crasto is one of the Douro's most reliable and widely distributed quality estates; the Reserva Old Vines shows the power and complexity of Portugal's greatest red wine region."),
    WineCatalogEntry(id="quinta-crasto-touriga-nacional", name="Quinta do Crasto Touriga Nacional Douro", producer="Quinta do Crasto", region="Douro Superior, Portugal", country="Portugal", appellation="Douro DOC", varietal="Touriga Nacional", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Crasto Touriga Nacional", "Quinta do Crasto TN Douro Single Variety"], description="Crasto's single-variety Touriga Nacional is one of the Douro's finest expressions of Portugal's most noble grape; structured, aromatic, and built for long aging."),
    WineCatalogEntry(id="graham-late-bottled-vintage-port", name="W & J Graham's Late Bottled Vintage Port", producer="W & J Graham's", region="Douro, Portugal", country="Portugal", appellation="Porto DO", varietal="Touriga Nacional/Touriga Franca/Tinta Roriz", wine_type="fortified", avg_retail_price=30.0, price_tier="value", aliases=["Graham's LBV Port", "Graham's Late Bottled Vintage", "W J Grahams LBV"], description="Graham's LBV is one of the most widely distributed and consistently excellent Late Bottled Vintage Ports; fruit-forward, rich, and accessible on release or cellarable for a decade."),
    WineCatalogEntry(id="fonseca-vintage-port", name="Fonseca Guimaraens Vintage Port", producer="Fonseca", region="Douro, Portugal", country="Portugal", appellation="Porto DO", varietal="Touriga Nacional/Touriga Franca/Tinta Roriz", wine_type="fortified", avg_retail_price=80.0, price_tier="premium", aliases=["Fonseca Vintage Port", "Fonseca Guimaraens VP"], description="Fonseca is renowned for producing some of the Douro's most elegant and perfumed Vintage Ports; the Fonseca house style emphasizes finesse and floral aromatics over sheer power."),
    WineCatalogEntry(id="taylors-vintage-port", name="Taylor Fladgate Vintage Port", producer="Taylor Fladgate", region="Douro, Portugal", country="Portugal", appellation="Porto DO", varietal="Touriga Nacional/Touriga Franca/Tinta Barroca", wine_type="fortified", avg_retail_price=120.0, price_tier="luxury", aliases=["Taylor Fladgate Vintage Port", "Taylors Port Vintage", "Taylor's Vintage Port"], description="Taylor Fladgate is one of the Port trade's most venerable houses; their Vintage Port is consistently among the Douro's most structured and long-lived, requiring decades to reach its peak."),
    WineCatalogEntry(id="ramos-pinto-duas-quintas-douro", name="Ramos Pinto Duas Quintas Douro Reserva", producer="Ramos Pinto", region="Douro, Portugal", country="Portugal", appellation="Douro DOC", varietal="Touriga Franca/Touriga Nacional", wine_type="red", avg_retail_price=25.0, price_tier="value", aliases=["Ramos Pinto Duas Quintas", "Ramos Pinto Douro Reserva"], description="Ramos Pinto's Duas Quintas is an accessible yet serious Douro red; blending fruit from two great quintas, it demonstrates the elegance and power of Portugal's premier wine region."),
    WineCatalogEntry(id="esporao-reserva-alentejo", name="Herdade do Esporão Reserva Alentejo", producer="Herdade do Esporão", region="Reguengos de Monsaraz, Alentejo, Portugal", country="Portugal", appellation="Alentejo DOC", varietal="Aragonez/Trincadeira/Cabernet Sauvignon", wine_type="red", avg_retail_price=25.0, price_tier="value", aliases=["Esporao Reserva Alentejo Red", "Herdade Esporao Reserva"], description="Herdade do Esporão is the benchmark estate for Alentejo wines; their Reserva red is a consistent and food-friendly ambassador for Portugal's sun-drenched interior wine region."),
    WineCatalogEntry(id="conceito-douro-conceito", name="Conceito Vinhos Douro Tinto Conceito", producer="Conceito Vinhos", region="Douro, Portugal", country="Portugal", appellation="Douro DOC", varietal="Touriga Nacional/Touriga Franca/Tinta Roriz", wine_type="red", avg_retail_price=35.0, price_tier="value", aliases=["Conceito Douro Tinto", "Conceito Vinhos Rita Ferreira Marques"], description="Conceito is one of the Douro's most exciting young estates; Rita Ferreira Marques produces compelling wines that combine native Douro varieties with genuine freshness and precision."),
    WineCatalogEntry(id="luis-pato-bairrada-sercial", name="Luís Pato Baga Vinha Barrosa Bairrada", producer="Luís Pato", region="Bairrada, Portugal", country="Portugal", appellation="Bairrada DOC", varietal="Baga", wine_type="red", avg_retail_price=40.0, price_tier="mid", aliases=["Luis Pato Vinha Barrosa Bairrada", "Luís Pato Baga Bairrada"], description="Luís Pato is the patriarch of Bairrada's modern wine scene; Vinha Barrosa from ancient ungrafted Baga vines produces one of Portugal's most distinctive and age-worthy red wines."),
]

# ---------------------------------------------------------------------------
# ARGENTINA – Expanded Mendoza + Patagonia
# ---------------------------------------------------------------------------
ARGENTINA_ADDITIONS = [
    WineCatalogEntry(id="catena-adrianna-white-bones", name="Catena Zapata Adrianna Vineyard White Bones Chardonnay", producer="Catena Zapata", region="Gualtallary, Mendoza, Argentina", country="Argentina", appellation="Gualtallary", varietal="Chardonnay", wine_type="white", avg_retail_price=200.0, price_tier="luxury", aliases=["Catena Adrianna White Bones Chardonnay", "Bodega Catena Zapata Adrianna Vineyard"], description="Adrianna Vineyard's White Bones is one of the world's highest-altitude Chardonnays; from Gualtallary's calcareous soils at 5,000 feet, it achieves extraordinary mineral depth and complexity."),
    WineCatalogEntry(id="catena-adrianna-malbec", name="Catena Zapata Adrianna Vineyard Malbec", producer="Catena Zapata", region="Gualtallary, Mendoza, Argentina", country="Argentina", appellation="Gualtallary", varietal="Malbec", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["Catena Adrianna Malbec", "Catena Zapata Adrianna Vineyard Fortuna Terrae"], description="Adrianna Vineyard Malbec is the pinnacle of Catena Zapata's single-vineyard program; from the world's highest Malbec vines, it combines extraordinary concentration with vibrant acidity."),
    WineCatalogEntry(id="achaval-ferrer-quimera", name="Achaval Ferrer Quimera Mendoza", producer="Achaval Ferrer", region="Mendoza, Argentina", country="Argentina", appellation="Mendoza", varietal="Malbec/Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=60.0, price_tier="premium", aliases=["Achaval Ferrer Quimera Blend", "Achaval-Ferrer Quimera Mendoza Red"], description="Quimera is Achaval Ferrer's Bordeaux-inspired blend; crafted from the finest parcels across multiple Mendoza sub-regions, it achieves complexity and balance rare in Argentina."),
    WineCatalogEntry(id="achaval-ferrer-finca-bella-vista", name="Achaval Ferrer Finca Bella Vista Malbec", producer="Achaval Ferrer", region="Luján de Cuyo, Mendoza, Argentina", country="Argentina", appellation="Luján de Cuyo", varietal="Malbec", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Achaval Ferrer Bella Vista Malbec", "Achaval-Ferrer Finca Bella Vista Single Vineyard"], description="Finca Bella Vista is Achaval Ferrer's flagship single-vineyard Malbec from old vines in Luján de Cuyo; one of Argentina's most sought-after bottles with extraordinary concentration and aging potential."),
    WineCatalogEntry(id="cheval-des-andes-mendoza", name="Cheval des Andes Mendoza", producer="Cheval des Andes", region="Luján de Cuyo, Mendoza, Argentina", country="Argentina", appellation="Luján de Cuyo", varietal="Malbec/Cabernet Sauvignon/Petit Verdot", wine_type="red", avg_retail_price=160.0, price_tier="luxury", aliases=["Cheval des Andes Argentina", "Terrazas de los Andes Cheval des Andes Mendoza"], description="Cheval des Andes is the joint venture between Cheval Blanc and Terrazas de los Andes; it produces one of South America's most sophisticated and collectible red wines."),
    WineCatalogEntry(id="clos-de-los-siete-mendoza", name="Clos de los Siete Mendoza", producer="Clos de los Siete", region="Vista Flores, Mendoza, Argentina", country="Argentina", appellation="Mendoza", varietal="Malbec/Merlot/Syrah/Cabernet Sauvignon", wine_type="red", avg_retail_price=45.0, price_tier="mid", aliases=["Clos de los Siete Vista Flores", "Michel Rolland Clos Siete Argentina"], description="Clos de los Siete is Michel Rolland's ambitious Mendoza project from seven co-invested estates; one of Argentina's most consistent, complex, and widely appreciated Bordeaux-style blends."),
    WineCatalogEntry(id="zuccardi-jose-zuccardi-malbec", name="Familia Zuccardi José Zuccardi Malbec", producer="Familia Zuccardi", region="Paraje Altamira, Valle de Uco, Argentina", country="Argentina", appellation="Valle de Uco", varietal="Malbec", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Zuccardi José Zuccardi Malbec Valle de Uco", "Familia Zuccardi Jose Malbec"], description="José Zuccardi is the family's tribute wine from their finest high-altitude parcels in Paraje Altamira; one of the world's greatest Malbecs with extraordinary finesse and longevity."),
    WineCatalogEntry(id="clos-apalta-chile", name="Casa Lapostolle Clos Apalta", producer="Casa Lapostolle", region="Colchagua Valley, Chile", country="Chile", appellation="Colchagua Valley", varietal="Carménère/Merlot/Cabernet Sauvignon", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Clos Apalta Colchagua Chile", "Lapostolle Clos Apalta Red Wine"], description="Clos Apalta is Chile's most celebrated wine; from a steep granite amphitheater in Colchagua, this Carménère-led blend achieves extraordinary complexity that rivals the world's finest reds."),
]

# ---------------------------------------------------------------------------
# CHILE – Quality tier expansion
# ---------------------------------------------------------------------------
CHILE_ADDITIONS = [
    WineCatalogEntry(id="montes-alpha-m", name="Montes Alpha M Cabernet Sauvignon", producer="Montes", region="Colchagua Valley, Chile", country="Chile", appellation="Colchagua Valley", varietal="Cabernet Sauvignon/Merlot/Carménère/Cabernet Franc", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Montes Alpha M Red Blend Chile", "Montes Winery Alpha M Colchagua"], description="Montes Alpha M is one of Chile's most prestigious red wines; a Bordeaux-style blend from old vines in Colchagua that demonstrates the potential of Chile's finest terroir."),
    WineCatalogEntry(id="errazuriz-don-maximiano", name="Viña Errázuriz Don Maximiano Founder's Reserve", producer="Viña Errázuriz", region="Aconcagua Valley, Chile", country="Chile", appellation="Aconcagua Valley", varietal="Cabernet Sauvignon/Cabernet Franc/Petit Verdot", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Errazuriz Don Maximiano Founders Reserve", "Errázuriz Don Maximiano Aconcagua"], description="Don Maximiano Founder's Reserve is Errázuriz's flagship wine; a Bordeaux-inspired blend from Chile's original premium wine region showing structure, elegance, and age-worthiness."),
    WineCatalogEntry(id="neyen-de-apalta-carmenere", name="Neyen de Apalta Colchagua", producer="Neyen", region="Apalta, Colchagua, Chile", country="Chile", appellation="Colchagua Valley", varietal="Carménère/Cabernet Sauvignon", wine_type="red", avg_retail_price=75.0, price_tier="premium", aliases=["Neyen Apalta Red Wine Chile", "Neyen de Apalta Carmenere Blend"], description="Neyen sources from ancient Carménère and Cabernet Sauvignon vines around the historic Apalta estate; one of Chile's most textured and complex red wines with excellent aging potential."),
    WineCatalogEntry(id="matetic-corralillo-syrah", name="Matetic Vineyards Corralillo Syrah", producer="Matetic Vineyards", region="San Antonio Valley, Chile", country="Chile", appellation="San Antonio Valley", varietal="Syrah", wine_type="red", avg_retail_price=25.0, price_tier="value", aliases=["Matetic Corralillo Syrah Chile", "Matetic Vineyards San Antonio Syrah"], description="Matetic's Corralillo Syrah from the cool coastal San Antonio Valley is one of Chile's most vibrant and food-friendly reds; organically farmed with genuine freshness and savory character."),
    WineCatalogEntry(id="concha-y-toro-don-melchor-cabernet", name="Concha y Toro Don Melchor Cabernet Sauvignon", producer="Concha y Toro", region="Puente Alto, Maipo Valley, Chile", country="Chile", appellation="Maipo Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Don Melchor Cabernet Sauvignon", "Concha y Toro Don Melchor Maipo"], description="Don Melchor is Chile's iconic benchmark Cabernet from the Maipo Valley; consistently among the country's finest wines with classical structure and impressive aging potential."),
]

# ---------------------------------------------------------------------------
# AUSTRALIA – Clare Valley, Margaret River, McLaren Vale, Barossa depth
# ---------------------------------------------------------------------------
AUSTRALIA_GLOBAL = [
    # Clare Valley
    WineCatalogEntry(id="grosset-polish-hill-riesling", name="Grosset Polish Hill Riesling", producer="Grosset", region="Polish Hill, Clare Valley, South Australia", country="Australia", appellation="Clare Valley", varietal="Riesling", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Grosset Polish Hill Clare Valley", "Jeffrey Grosset Riesling Clare Valley"], description="Grosset's Polish Hill is Australia's greatest dry Riesling; from the shallow slate soils of Polish Hill, it shows extraordinary mineral intensity that ages magnificently for decades."),
    WineCatalogEntry(id="grosset-watervale-riesling", name="Grosset Watervale Riesling", producer="Grosset", region="Watervale, Clare Valley, South Australia", country="Australia", appellation="Clare Valley", varietal="Riesling", wine_type="white", avg_retail_price=40.0, price_tier="mid", aliases=["Grosset Watervale Clare Valley Riesling", "Grosset Riesling Watervale"], description="Grosset Watervale Riesling is from the limestone soils of Watervale; more immediately accessible than Polish Hill, it shows classic Clare Valley lime juice and floral character."),
    WineCatalogEntry(id="jim-barry-the-armagh-shiraz", name="Jim Barry The Armagh Clare Valley Shiraz", producer="Jim Barry Wines", region="Clare Valley, South Australia", country="Australia", appellation="Clare Valley", varietal="Shiraz", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Jim Barry The Armagh Shiraz", "The Armagh Clare Valley Shiraz Jim Barry"], description="The Armagh is Australia's rarest and most sought-after Clare Valley Shiraz; from a single small vineyard, it achieves extraordinary concentration, complexity, and aging potential."),
    WineCatalogEntry(id="kilikanoon-oracle-shiraz", name="Kilikanoon Oracle Shiraz Clare Valley", producer="Kilikanoon", region="Clare Valley, South Australia", country="Australia", appellation="Clare Valley", varietal="Shiraz", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Kilikanoon Oracle Clare Valley Shiraz", "Kilikanoon Winery Oracle Shiraz"], description="Kilikanoon's Oracle is their prestige single-vineyard Shiraz from old vines in the Armagh sub-district; one of Clare Valley's most concentrated and age-worthy expressions of the variety."),
    # Margaret River
    WineCatalogEntry(id="leeuwin-art-series-chardonnay", name="Leeuwin Estate Art Series Chardonnay", producer="Leeuwin Estate", region="Margaret River, Western Australia", country="Australia", appellation="Margaret River", varietal="Chardonnay", wine_type="white", avg_retail_price=80.0, price_tier="premium", aliases=["Leeuwin Art Series Chardonnay Margaret River", "Leeuwin Estate Prelude Chardonnay"], description="Leeuwin Estate's Art Series Chardonnay is one of Australia's greatest whites; from a single vineyard in Margaret River, it rivals the finest Burgundy in its combination of power and finesse."),
    WineCatalogEntry(id="moss-wood-cabernet-sauvignon", name="Moss Wood Cabernet Sauvignon Margaret River", producer="Moss Wood", region="Wilyabrup, Margaret River, Western Australia", country="Australia", appellation="Margaret River", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Moss Wood Margaret River Cabernet", "Moss Wood Wilyabrup Cabernet Sauvignon"], description="Moss Wood is Margaret River's most celebrated Cabernet Sauvignon producer; their estate wine shows the region's classic cassis, graphite, and cedar character with exceptional aging potential."),
    WineCatalogEntry(id="cape-mentelle-cabernet-sauvignon", name="Cape Mentelle Cabernet Sauvignon Margaret River", producer="Cape Mentelle", region="Margaret River, Western Australia", country="Australia", appellation="Margaret River", varietal="Cabernet Sauvignon/Merlot", wine_type="red", avg_retail_price=60.0, price_tier="premium", aliases=["Cape Mentelle Margaret River Cabernet", "Cape Mentelle Winery Cabernet Sauvignon"], description="Cape Mentelle is one of Margaret River's founding and most consistent estates; their Cabernet Sauvignon is a benchmark for the region's classically structured, European-influenced style."),
    WineCatalogEntry(id="xanadu-reserve-cabernet", name="Xanadu Reserve Cabernet Sauvignon Margaret River", producer="Xanadu", region="Margaret River, Western Australia", country="Australia", appellation="Margaret River", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=65.0, price_tier="premium", aliases=["Xanadu Reserve Cabernet Margaret River", "Xanadu Winery Reserve Cab Sauvignon WA"], description="Xanadu Reserve Cabernet is one of Margaret River's most refined and food-friendly expressions; elegant tannins and restrained fruit make it a top choice for sommeliers."),
    # McLaren Vale
    WineCatalogEntry(id="darenberg-dead-arm-shiraz", name="d'Arenberg The Dead Arm Shiraz McLaren Vale", producer="d'Arenberg", region="McLaren Vale, South Australia", country="Australia", appellation="McLaren Vale", varietal="Shiraz", wine_type="red", avg_retail_price=65.0, price_tier="premium", aliases=["d'Arenberg Dead Arm McLaren Vale", "d Arenberg The Dead Arm Shiraz"], description="d'Arenberg's Dead Arm is McLaren Vale's most iconic Shiraz; named after a fungal vine condition, it produces extraordinarily concentrated, age-worthy wines of unusual complexity."),
    WineCatalogEntry(id="rockford-basket-press-shiraz", name="Rockford Basket Press Shiraz Barossa Valley", producer="Rockford", region="Barossa Valley, South Australia", country="Australia", appellation="Barossa Valley", varietal="Shiraz", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Rockford Basket Press Shiraz", "Rocky O'Callaghan Rockford Basket Press"], description="Rockford Basket Press is one of Australia's most traditional and beloved Barossas; Robert O'Callaghan's old-vine Shiraz, basket-pressed and aged in old American oak, is a living museum piece."),
    WineCatalogEntry(id="charlie-melton-nine-popes", name="Charlie Melton Nine Popes Barossa Valley", producer="Charlie Melton", region="Barossa Valley, South Australia", country="Australia", appellation="Barossa Valley", varietal="Grenache/Shiraz/Mourvèdre", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Charlie Melton Nine Popes GSM", "Melton Wines Nine Popes Barossa"], description="Nine Popes is Australia's original Rhône-style blend; Charlie Melton's old-vine Grenache/Shiraz/Mourvèdre from the Barossa Valley shows warmth, spice, and remarkable complexity."),
    # Yarra Valley
    WineCatalogEntry(id="bannockburn-pinot-noir-geelong", name="Bannockburn Vineyards Pinot Noir", producer="Bannockburn Vineyards", region="Geelong, Victoria, Australia", country="Australia", appellation="Geelong", varietal="Pinot Noir", wine_type="red", avg_retail_price=70.0, price_tier="premium", aliases=["Bannockburn Geelong Pinot", "Bannockburn Vineyards SRH Pinot Noir"], description="Bannockburn is one of Australia's most revered Pinot Noir estates; Gary Farr's influence produced wines of extraordinary Burgundian elegance from Geelong's cool-climate basalt soils."),
    WineCatalogEntry(id="mac-forbes-yarra-yering-pinot", name="Mac Forbes Yarra Valley Pinot Noir", producer="Mac Forbes", region="Yarra Valley, Victoria, Australia", country="Australia", appellation="Yarra Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Mac Forbes Pinot Noir Yarra", "Mac Forbes Winery Yarra Valley Pinot"], description="Mac Forbes is one of the Yarra Valley's most thoughtful producers; his single-village Pinot Noirs show remarkable precision and terroir expression from this cool southern Australian region."),
]

# ---------------------------------------------------------------------------
# NEW ZEALAND – Central Otago depth + Hawke's Bay
# ---------------------------------------------------------------------------
NZ_ADDITIONS = [
    WineCatalogEntry(id="rippon-pinot-noir-mature", name="Rippon Mature Vine Pinot Noir Central Otago", producer="Rippon", region="Lake Wanaka, Central Otago, New Zealand", country="New Zealand", appellation="Central Otago", varietal="Pinot Noir", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Rippon Mature Vine Pinot Central Otago", "Rippon Vineyard Pinot Noir Wanaka"], description="Rippon is Central Otago's most spectacular and revered estate; the biodynamic Mature Vine Pinot Noir from Lake Wanaka's schist soils is one of New Zealand's greatest wines."),
    WineCatalogEntry(id="burn-cottage-pinot-noir", name="Burn Cottage Pinot Noir Lowburn Ferry", producer="Burn Cottage", region="Cromwell Basin, Central Otago, New Zealand", country="New Zealand", appellation="Central Otago", varietal="Pinot Noir", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Burn Cottage Lowburn Ferry Pinot", "Burn Cottage Vineyard Central Otago Pinot"], description="Burn Cottage is one of Central Otago's newest and most acclaimed estates; biodynamically farmed Pinot Noir from the Cromwell Basin shows a refined, aromatic style with remarkable mineral depth."),
    WineCatalogEntry(id="greywacke-sauvignon-blanc", name="Greywacke Marlborough Sauvignon Blanc", producer="Greywacke", region="Marlborough, New Zealand", country="New Zealand", appellation="Marlborough", varietal="Sauvignon Blanc", wine_type="white", avg_retail_price=30.0, price_tier="value", aliases=["Greywacke Sauvignon Blanc Marlborough", "Kevin Judd Greywacke SB New Zealand"], description="Greywacke is Kevin Judd's label after his tenure at Cloudy Bay; a more terroir-focused, precise style of Marlborough Sauvignon Blanc that has quickly become the region's quality benchmark."),
    WineCatalogEntry(id="dog-point-sauvignon-blanc", name="Dog Point Vineyard Marlborough Sauvignon Blanc", producer="Dog Point Vineyard", region="Marlborough, New Zealand", country="New Zealand", appellation="Marlborough", varietal="Sauvignon Blanc", wine_type="white", avg_retail_price=30.0, price_tier="value", aliases=["Dog Point Sauvignon Blanc Marlborough", "Dog Point Vineyard NZ SB"], description="Dog Point is founded by former Cloudy Bay viticulturalists; their Sauvignon Blanc shows greater restraint and mineral depth than many Marlborough wines with excellent aging potential."),
    WineCatalogEntry(id="te-mata-coleraine-cabernet", name="Te Mata Coleraine Hawke's Bay", producer="Te Mata Estate", region="Hawke's Bay, New Zealand", country="New Zealand", appellation="Hawke's Bay", varietal="Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Te Mata Coleraine Hawkes Bay Cabernet", "Te Mata Estate Coleraine Red"], description="Te Mata's Coleraine is New Zealand's most celebrated Bordeaux-style red; from the classic Gimblett Gravels of Hawke's Bay, it shows great structure and elegance."),
    WineCatalogEntry(id="villa-maria-reserve-hawkes-bay-cab", name="Villa Maria Reserve Cabernet Sauvignon/Merlot Hawke's Bay", producer="Villa Maria Estate", region="Hawke's Bay, New Zealand", country="New Zealand", appellation="Hawke's Bay", varietal="Cabernet Sauvignon/Merlot", wine_type="red", avg_retail_price=45.0, price_tier="mid", aliases=["Villa Maria Reserve Hawkes Bay Red", "Villa Maria Reserve Cabernet Merlot NZ"], description="Villa Maria Reserve is New Zealand's most widely distributed premium red; consistent quality and reliable Gimblett Gravels character make it a staple on New Zealand restaurant lists."),
]

# ---------------------------------------------------------------------------
# SOUTH AFRICA – Hamilton Russell + Swartland + Stellenbosch depth
# ---------------------------------------------------------------------------
SA_ADDITIONS = [
    WineCatalogEntry(id="hamilton-russell-pinot-noir", name="Hamilton Russell Vineyards Pinot Noir Hemel-en-Aarde", producer="Hamilton Russell Vineyards", region="Hemel-en-Aarde Valley, Western Cape, South Africa", country="South Africa", appellation="Hemel-en-Aarde Valley WO", varietal="Pinot Noir", wine_type="red", avg_retail_price=75.0, price_tier="premium", aliases=["Hamilton Russell Pinot Noir", "Hamilton Russell Hemel en Aarde Valley Pinot"], description="Hamilton Russell Pinot Noir is Africa's most celebrated Pinot Noir; from the cool marine-influenced Hemel-en-Aarde Valley, it shows extraordinary elegance and terroir expression."),
    WineCatalogEntry(id="hamilton-russell-chardonnay", name="Hamilton Russell Vineyards Chardonnay Hemel-en-Aarde", producer="Hamilton Russell Vineyards", region="Hemel-en-Aarde Valley, Western Cape, South Africa", country="South Africa", appellation="Hemel-en-Aarde Valley WO", varietal="Chardonnay", wine_type="white", avg_retail_price=70.0, price_tier="premium", aliases=["Hamilton Russell Chardonnay Hemel-en-Aarde", "HRV Chardonnay South Africa"], description="Hamilton Russell Chardonnay is one of the Southern Hemisphere's most Burgundian whites; the cool Hemel-en-Aarde Valley produces a wine of remarkable mineral precision and complexity."),
    WineCatalogEntry(id="de-trafford-elevation-393", name="De Trafford Elevation 393 Stellenbosch", producer="De Trafford Wines", region="Stellenbosch, South Africa", country="South Africa", appellation="Stellenbosch WO", varietal="Cabernet Sauvignon/Merlot/Shiraz", wine_type="red", avg_retail_price=70.0, price_tier="premium", aliases=["De Trafford Elevation 393 Cab Blend", "De Trafford Wines Elevation Stellenbosch"], description="De Trafford's Elevation 393 is one of Stellenbosch's finest Bordeaux-style blends; from high-altitude mountain vineyards, it shows restrained elegance and exceptional aging potential."),
    WineCatalogEntry(id="porseleinberg-swartland-syrah", name="Porseleinberg Swartland Syrah", producer="Porseleinberg", region="Swartland, South Africa", country="South Africa", appellation="Swartland WO", varietal="Syrah", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Porseleinberg Syrah Swartland", "Boekenhoutskloof Porseleinberg"], description="Porseleinberg is one of the Swartland's most celebrated single-farm bottlings; Syrah from dry-farmed schist vineyards shows the savory, meaty character that defines the region at its best."),
    WineCatalogEntry(id="raats-family-cabernet-franc", name="Raats Family Wines Cabernet Franc Stellenbosch", producer="Raats Family Wines", region="Stellenbosch, South Africa", country="South Africa", appellation="Stellenbosch WO", varietal="Cabernet Franc", wine_type="red", avg_retail_price=45.0, price_tier="mid", aliases=["Raats Cabernet Franc Stellenbosch", "Bruwer Raats Cabernet Franc South Africa"], description="Raats Family Wines is South Africa's champion of Cabernet Franc; from Stellenbosch's granite-clay soils, their Cab Franc shows the leafy, aromatic character that makes this variety irresistible."),
]

# ---------------------------------------------------------------------------
# GREECE – Complete new section
# ---------------------------------------------------------------------------
GREECE = [
    WineCatalogEntry(id="sigalas-assyrtiko-santorini", name="Domaine Sigalas Assyrtiko Santorini", producer="Domaine Sigalas", region="Santorini, Greece", country="Greece", appellation="Santorini PDO", varietal="Assyrtiko", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Sigalas Assyrtiko Santorini PDO", "Paris Sigalas Assyrtiko Greece"], description="Domaine Sigalas is Santorini's most celebrated producer; their Assyrtiko is a benchmark for this extraordinary volcanic island wine with its electric acidity, saline mineral depth, and remarkable aging potential."),
    WineCatalogEntry(id="sigalas-kavalieros", name="Domaine Sigalas Kavalieros Assyrtiko Santorini", producer="Domaine Sigalas", region="Santorini, Greece", country="Greece", appellation="Santorini PDO", varietal="Assyrtiko", wine_type="white", avg_retail_price=120.0, price_tier="luxury", aliases=["Sigalas Kavalieros Santorini", "Sigalas Kavalieros Single Vineyard Assyrtiko"], description="Kavalieros is Sigalas's prestige single-vineyard Assyrtiko from very old basket-trained vines; one of Greece's most profound and collectible white wines."),
    WineCatalogEntry(id="gaia-thalassitis-assyrtiko", name="Gaia Wines Thalassitis Assyrtiko Santorini", producer="Gaia Wines", region="Santorini, Greece", country="Greece", appellation="Santorini PDO", varietal="Assyrtiko", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Gaia Thalassitis Santorini Assyrtiko", "Gaia Wines Santorini White"], description="Gaia Wines is one of Santorini's most innovative producers; Thalassitis showcases the extraordinary minerality and citrus purity of Assyrtiko grown in the volcanic caldera soils."),
    WineCatalogEntry(id="argyros-estate-assyrtiko", name="Estate Argyros Assyrtiko Santorini", producer="Estate Argyros", region="Santorini, Greece", country="Greece", appellation="Santorini PDO", varietal="Assyrtiko", wine_type="white", avg_retail_price=40.0, price_tier="mid", aliases=["Argyros Assyrtiko Santorini", "Estate Argyros Santorini PDO White"], description="Estate Argyros is one of Santorini's largest private wine estates; their Assyrtiko is widely considered the island's most consistent and accessible expression of this iconic variety."),
    WineCatalogEntry(id="kir-yianni-xinomavro", name="Kir-Yianni Naoussa Xinomavro", producer="Kir-Yianni", region="Naoussa, Macedonia, Greece", country="Greece", appellation="Naoussa PDO", varietal="Xinomavro", wine_type="red", avg_retail_price=35.0, price_tier="value", aliases=["Kir-Yianni Naoussa Xinomavro PDO", "Kir Yianni Xinomavro Macedonia Greece"], description="Kir-Yianni is the reference for Naoussa Xinomavro; this indigenous variety produces wines with Barolo-like structure, high acidity, and savory complexity that age magnificently."),
    WineCatalogEntry(id="thimiopoulos-young-vines-xinomavro", name="Thimiopoulos Vineyards Young Vines Xinomavro Naoussa", producer="Thimiopoulos Vineyards", region="Naoussa, Macedonia, Greece", country="Greece", appellation="Naoussa PDO", varietal="Xinomavro", wine_type="red", avg_retail_price=25.0, price_tier="value", aliases=["Thimiopoulos Young Vines Naoussa", "Apostolos Thimiopoulos Xinomavro Young Vines"], description="Apostolos Thimiopoulos is one of Greece's most exciting young winemakers; Young Vines Xinomavro from Naoussa is a vivid, fruit-forward introduction to this remarkable indigenous variety."),
    WineCatalogEntry(id="gaia-agiorgitiko-notios-red", name="Gaia Wines Notios Agiorgitiko Nemea", producer="Gaia Wines", region="Nemea, Peloponnese, Greece", country="Greece", appellation="Nemea PDO", varietal="Agiorgitiko", wine_type="red", avg_retail_price=20.0, price_tier="value", aliases=["Gaia Notios Nemea Red", "Gaia Agiorgitiko Nemea Greece"], description="Gaia's Notios is a brilliant value introduction to Greece's Nemea appellation; Agiorgitiko (St. George) from the high-altitude clay-limestone soils shows plush fruit and Mediterranean warmth."),
    WineCatalogEntry(id="domaine-gerovassiliou-malagousia", name="Domaine Gerovassiliou Malagousia Epanomi", producer="Domaine Gerovassiliou", region="Epanomi, Macedonia, Greece", country="Greece", appellation="Malagousia", varietal="Malagousia", wine_type="white", avg_retail_price=25.0, price_tier="value", aliases=["Gerovassiliou Malagousia", "Vangelis Gerovassiliou Malagousia Greece"], description="Vangelis Gerovassiliou revived the near-extinct Malagousia variety; his Epanomi bottling is a uniquely aromatic white wine that has become one of Greece's most internationally acclaimed whites."),
]

# ---------------------------------------------------------------------------
# HUNGARY – Tokaji classics
# ---------------------------------------------------------------------------
HUNGARY = [
    WineCatalogEntry(id="royal-tokaji-mezes-maly-aszu-5", name="Royal Tokaji Mézesmály Aszú 5 Puttonyos", producer="Royal Tokaji Wine Co.", region="Tokaj, Hungary", country="Hungary", appellation="Tokaj PDO", varietal="Furmint/Hárslevelű", wine_type="dessert", avg_retail_price=80.0, price_tier="premium", aliases=["Royal Tokaji 5 Puttonyos Aszú", "Royal Tokaji Mezes Maly Aszu", "Royal Tokaji 5P"], description="Royal Tokaji's Mézesmály is one of their finest single-vineyard Aszú wines; from ancient clay-loam soils with exceptional botrytis, it shows extraordinary sweetness balanced by vibrant acidity."),
    WineCatalogEntry(id="szepsy-tokaji-aszu-6-puttonyos", name="István Szepsy Tokaji Aszú 6 Puttonyos", producer="István Szepsy", region="Mád, Tokaj, Hungary", country="Hungary", appellation="Tokaj PDO", varietal="Furmint/Hárslevelű/Muscat Blanc", wine_type="dessert", avg_retail_price=200.0, price_tier="luxury", aliases=["Szepsy Aszu 6 Puttonyos Tokaj", "Istvan Szepsy Tokaji 6P"], description="István Szepsy is Hungary's most celebrated winemaker; his 6 Puttonyos Aszú achieves extraordinary concentration of botrytized sweetness balanced by Tokaj's electric acidity."),
    WineCatalogEntry(id="disznoko-tokaji-late-harvest", name="Disznókő Tokaji Late Harvest", producer="Disznókő", region="Tokaj, Hungary", country="Hungary", appellation="Tokaj PDO", varietal="Furmint", wine_type="dessert", avg_retail_price=35.0, price_tier="value", aliases=["Disznoko Late Harvest Tokaj", "Disznókő Furmint Late Harvest"], description="Disznókő is one of Tokaj's largest and most reliable estates; their Late Harvest Furmint is an accessible entry into the world of Tokaji with honey, apricot, and mineral character."),
    WineCatalogEntry(id="szepsy-furmint-dry", name="István Szepsy Tokaji Furmint Dry", producer="István Szepsy", region="Mád, Tokaj, Hungary", country="Hungary", appellation="Tokaj PDO", varietal="Furmint", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Szepsy Dry Furmint Tokaj", "Istvan Szepsy Furmint Sec"], description="Szepsy's dry Furmint is one of the most compelling arguments for Furmint as a great white wine variety; the mineral intensity, acidity, and savory complexity rival the finest white Burgundies."),
    WineCatalogEntry(id="oremus-aszu-5-puttonyos", name="Oremus Tokaji Aszú 5 Puttonyos", producer="Oremus", region="Tolcsva, Tokaj, Hungary", country="Hungary", appellation="Tokaj PDO", varietal="Furmint/Hárslevelű", wine_type="dessert", avg_retail_price=65.0, price_tier="premium", aliases=["Oremus 5 Puttonyos Aszu Tokaj", "Vega Sicilia Oremus Tokaji Aszu"], description="Oremus is the historic Tokaj estate owned by Spain's Vega Sicilia family; their 5 Puttonyos Aszú combines centuries of Hungarian winemaking tradition with modern precision."),
]

# ---------------------------------------------------------------------------
# LEBANON – Château Musar + Massaya
# ---------------------------------------------------------------------------
LEBANON = [
    WineCatalogEntry(id="chateau-musar-rouge", name="Château Musar Rouge Bekaa Valley", producer="Château Musar", region="Bekaa Valley, Lebanon", country="Lebanon", appellation="Bekaa Valley", varietal="Cabernet Sauvignon/Cinsault/Carignan", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Chateau Musar Red Lebanon", "Musar Rouge Bekaa Valley", "Serge Hochar Chateau Musar"], description="Château Musar is Lebanon's most iconic wine; the Serge Hochar-created red blend from old vines in the Bekaa Valley produces wines of extraordinary complexity that age for 30+ years."),
    WineCatalogEntry(id="chateau-musar-blanc", name="Château Musar Blanc Bekaa Valley", producer="Château Musar", region="Bekaa Valley, Lebanon", country="Lebanon", appellation="Bekaa Valley", varietal="Obaideh/Merwah", wine_type="white", avg_retail_price=50.0, price_tier="mid", aliases=["Chateau Musar White Lebanon", "Musar Blanc Bekaa Valley"], description="Château Musar Blanc is made from Lebanon's unique indigenous varieties Obaideh and Merwah; fermented in oak and aged for years before release, it achieves an amber, oxidative complexity."),
    WineCatalogEntry(id="massaya-classic-bekaa", name="Massaya Classic Bekaa Valley", producer="Massaya", region="Bekaa Valley, Lebanon", country="Lebanon", appellation="Bekaa Valley", varietal="Cinsault/Cabernet Sauvignon/Syrah", wine_type="red", avg_retail_price=20.0, price_tier="value", aliases=["Massaya Classic Red Lebanon", "Massaya Bekaa Valley Classic Red"], description="Massaya Classic is one of the most accessible and widely distributed Lebanese wines; a consistent blend showing the warmth and spice of Bekaa Valley Cinsault with Cabernet structure."),
]

# ---------------------------------------------------------------------------
# GEORGIA (Country) – Amber wines + Rkatsiteli
# ---------------------------------------------------------------------------
GEORGIA_COUNTRY = [
    WineCatalogEntry(id="pheasants-tears-rkatsiteli", name="Pheasant's Tears Rkatsiteli Kakheti", producer="Pheasant's Tears", region="Signagi, Kakheti, Georgia", country="Georgia", appellation="Kakheti", varietal="Rkatsiteli", wine_type="orange", avg_retail_price=35.0, price_tier="value", aliases=["Pheasants Tears Rkatsiteli Georgia", "John Wurdeman Pheasant's Tears"], description="Pheasant's Tears is Georgia's most internationally acclaimed producer; their Rkatsiteli fermented and aged in qvevri (clay amphorae) is a benchmark for ancient winemaking techniques."),
    WineCatalogEntry(id="pheasants-tears-mtsvane", name="Pheasant's Tears Mtsvane Kakheti", producer="Pheasant's Tears", region="Signagi, Kakheti, Georgia", country="Georgia", appellation="Kakheti", varietal="Mtsvane", wine_type="orange", avg_retail_price=35.0, price_tier="value", aliases=["Pheasants Tears Mtsvane Georgia", "Pheasant's Tears Green Wine Mtsvane"], description="Pheasant's Tears' Mtsvane is a more aromatic and floral expression of Georgian amber wine; the extended skin contact in qvevri produces a golden wine of extraordinary spice and texture."),
    WineCatalogEntry(id="alaverdi-monastery-rkatsiteli", name="Alaverdi Monastery Amber Wine Rkatsiteli", producer="Alaverdi Monastery", region="Kakheti, Georgia", country="Georgia", appellation="Kakheti", varietal="Rkatsiteli", wine_type="orange", avg_retail_price=40.0, price_tier="mid", aliases=["Alaverdi Monastery Rkatsiteli Kakheti", "Georgian Monastery Wine Rkatsiteli"], description="Alaverdi Monastery produces wine using unbroken 1,500-year traditions; their Rkatsiteli from the historic cathedral cellar is one of the world's most authentic and fascinating amber wines."),
]

# ---------------------------------------------------------------------------
# USA – Sonoma + Santa Barbara completeness
# ---------------------------------------------------------------------------
USA_SONOMA_SANTA_BARBARA = [
    # Sonoma additional
    WineCatalogEntry(id="littorai-mays-canyon-pinot", name="Littorai Wines Mays Canyon Pinot Noir Russian River Valley", producer="Littorai Wines", region="Russian River Valley, Sonoma, California, USA", country="USA", appellation="Russian River Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Littorai Mays Canyon Pinot", "Ted Lemon Littorai Russian River Pinot"], description="Littorai's Ted Lemon produces some of California's most Burgundian Pinot Noirs; Mays Canyon from the cooler western RRV shows remarkable mineral precision and elegance."),
    WineCatalogEntry(id="aubert-uv-vineyard-chardonnay", name="Aubert Wines UV-SL Vineyard Chardonnay", producer="Aubert Wines", region="Sonoma Coast, California, USA", country="USA", appellation="Sonoma Coast", varietal="Chardonnay", wine_type="white", avg_retail_price=130.0, price_tier="luxury", aliases=["Aubert UV Vineyard Chardonnay", "Mark Aubert UV Chardonnay Sonoma Coast"], description="Mark Aubert's UV-SL Vineyard Chardonnay is one of California's most opulent and collected whites; from the extreme Sonoma Coast, it achieves extraordinary richness with coastal freshness."),
    WineCatalogEntry(id="flowers-sea-view-ridge-pinot", name="Flowers Vineyard Sea View Ridge Pinot Noir Sonoma Coast", producer="Flowers Vineyards & Winery", region="Fort Ross-Seaview, Sonoma Coast, California, USA", country="USA", appellation="Fort Ross-Seaview", varietal="Pinot Noir", wine_type="red", avg_retail_price=85.0, price_tier="premium", aliases=["Flowers Sea View Ridge Pinot Noir", "Flowers Vineyards Sonoma Coast Pinot"], description="Flowers is one of the Sonoma Coast's pioneer estates; Sea View Ridge from the extreme coastal zone shows Pinot Noir of remarkable freshness, mineral depth, and savory complexity."),
    WineCatalogEntry(id="patz-hall-chenoweth-pinot", name="Patz & Hall Chenoweth Ranch Pinot Noir Russian River Valley", producer="Patz & Hall", region="Russian River Valley, Sonoma, California, USA", country="USA", appellation="Russian River Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Patz Hall Chenoweth Pinot Noir", "Patz and Hall Russian River Valley Pinot"], description="Patz & Hall is one of Russian River Valley's most acclaimed Pinot Noir producers; Chenoweth Ranch shows the classic bright cherry, spice, and silky texture of this prized sub-region."),
    WineCatalogEntry(id="porter-creek-fiona-hill-pinot", name="Porter Creek Vineyards Fiona Hill Vineyard Pinot Noir", producer="Porter Creek Vineyards", region="Russian River Valley, Sonoma, California, USA", country="USA", appellation="Russian River Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=60.0, price_tier="premium", aliases=["Porter Creek Fiona Hill Pinot", "Porter Creek Winery RRV Pinot Noir"], description="Porter Creek produces biodynamic Pinot Noir from old vines in the Russian River Valley; their single-vineyard wines show genuine terroir character and Burgundian-inspired restraint."),
    WineCatalogEntry(id="rochioli-west-block-pinot", name="J. Rochioli West Block Pinot Noir Russian River Valley", producer="J. Rochioli Vineyard", region="Russian River Valley, Sonoma, California, USA", country="USA", appellation="Russian River Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=300.0, price_tier="luxury", aliases=["Rochioli West Block Pinot Noir", "J Rochioli Russian River Valley West Block"], description="Rochioli's West Block is one of California's most legendary and sought-after Pinot Noirs; from old vines on a prime RRV site, it achieves extraordinary depth and aging potential."),
    # Santa Barbara
    WineCatalogEntry(id="brewer-clifton-sta-rita-pinot", name="Brewer-Clifton Sta. Rita Hills Pinot Noir", producer="Brewer-Clifton", region="Sta. Rita Hills, Santa Barbara, California, USA", country="USA", appellation="Sta. Rita Hills", varietal="Pinot Noir", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Brewer Clifton Pinot Sta Rita Hills", "Brewer-Clifton Santa Barbara Pinot"], description="Brewer-Clifton is one of the Sta. Rita Hills' founding and most acclaimed producers; their wines from chalk-limestone soils show extraordinary mineral depth and aging potential."),
    WineCatalogEntry(id="qupe-bien-nacido-syrah", name="Qupé Bien Nacido Vineyard Syrah Santa Maria Valley", producer="Qupé", region="Santa Maria Valley, Santa Barbara, California, USA", country="USA", appellation="Santa Maria Valley", varietal="Syrah", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Qupe Bien Nacido Syrah", "Bob Lindquist Qupe Santa Maria Syrah"], description="Qupé's Bob Lindquist pioneered Rhône varieties in California; the Bien Nacido Syrah from this legendary Santa Maria vineyard is a benchmark for cool-climate California Syrah."),
    WineCatalogEntry(id="alban-rivas-vineyard-syrah", name="Alban Vineyards Rivas Vineyard Syrah Edna Valley", producer="Alban Vineyards", region="Edna Valley, San Luis Obispo, California, USA", country="USA", appellation="Edna Valley", varietal="Syrah", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Alban Rivas Syrah Edna Valley", "John Alban Rivas Vineyard Syrah"], description="Alban Vineyards was the first estate in California to plant Roussanne; the Rivas Vineyard Syrah from Edna Valley is a powerful, meaty expression of this grape at its California best."),
    WineCatalogEntry(id="foxen-julia-s-vineyard-pinot", name="Foxen Santa Maria Valley Julia's Vineyard Pinot Noir", producer="Foxen", region="Santa Maria Valley, Santa Barbara, California, USA", country="USA", appellation="Santa Maria Valley", varietal="Pinot Noir", wine_type="red", avg_retail_price=55.0, price_tier="mid", aliases=["Foxen Julia's Vineyard Pinot Noir", "Foxen Winery Santa Maria Pinot"], description="Foxen is one of the Santa Maria Valley's founding estates; Julia's Vineyard Pinot Noir shows the cool-climate elegance and bright cherry character that defines this coastal California region."),
]

# ---------------------------------------------------------------------------
# NAPA VALLEY COMPLETENESS – Mid-tier staples + iconic classics
# ---------------------------------------------------------------------------
NAPA_ADDITIONS = [
    # Historic / Iconic
    WineCatalogEntry(id="heitz-marthas-vineyard", name="Heitz Cellar Martha's Vineyard Cabernet Sauvignon", producer="Heitz Cellar", region="St. Helena, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Heitz Martha's Vineyard Cabernet", "Heitz Cellar Marthas Vineyard Napa", "Heitz Marthas Vineyard Cab"], description="Martha's Vineyard is one of Napa's most storied sites; Heitz Cellar's single-vineyard Cabernet is a California icon with decades of history and unmistakable eucalyptus character."),
    WineCatalogEntry(id="heitz-trailside-vineyard", name="Heitz Cellar Trailside Vineyard Cabernet Sauvignon", producer="Heitz Cellar", region="Rutherford, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=100.0, price_tier="premium", aliases=["Heitz Trailside Vineyard Cab", "Heitz Cellar Trailside Napa"], description="Heitz Cellar's Trailside Vineyard is their second iconic single-vineyard Cabernet; from Rutherford's famous benchland soils, it shows classic dusty tannins and earthy depth."),
    WineCatalogEntry(id="inglenook-rubicon", name="Inglenook Rubicon Rutherford", producer="Inglenook", region="Rutherford, Napa Valley, California, USA", country="USA", appellation="Rutherford", varietal="Cabernet Sauvignon/Cabernet Franc/Merlot", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Inglenook Rubicon Napa", "Niebaum-Coppola Rubicon", "Francis Ford Coppola Rubicon Inglenook"], description="Rubicon is Inglenook's flagship wine from one of Napa's most historic estates (formerly Niebaum-Coppola); a Bordeaux-style blend of extraordinary elegance and aging potential."),
    WineCatalogEntry(id="robert-mondavi-reserve-cab", name="Robert Mondavi Winery Cabernet Sauvignon Reserve To Kalon Vineyard", producer="Robert Mondavi Winery", region="Oakville, Napa Valley, California, USA", country="USA", appellation="Oakville", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=180.0, price_tier="luxury", aliases=["Robert Mondavi Reserve Cabernet", "Mondavi To Kalon Reserve Cab", "Robert Mondavi Oakville Reserve"], description="Robert Mondavi's Reserve Cabernet from the legendary To Kalon Vineyard is a California institution; one of the great benchmarks for structured, age-worthy Napa Cabernet."),
    WineCatalogEntry(id="bv-georges-latour", name="Beaulieu Vineyard Georges de Latour Private Reserve Cabernet Sauvignon", producer="Beaulieu Vineyard", region="Rutherford, Napa Valley, California, USA", country="USA", appellation="Rutherford", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["BV Georges de Latour Private Reserve", "Beaulieu Vineyard Private Reserve Cabernet", "BV Private Reserve Rutherford"], description="Georges de Latour Private Reserve is one of California's oldest prestige Cabernets; from Rutherford's famed benchland, it has defined the 'Rutherford Dust' style for generations."),
    WineCatalogEntry(id="beringer-private-reserve", name="Beringer Private Reserve Cabernet Sauvignon", producer="Beringer Vineyards", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Beringer Private Reserve Cab Napa", "Beringer Napa Private Reserve", "Beringer Vineyards Private Reserve"], description="Beringer Private Reserve is Napa's longest-running luxury Cabernet; from Knights Valley and Napa Valley's finest vineyards, it is a consistently opulent and age-worthy wine."),
    WineCatalogEntry(id="stags-leap-cask-23", name="Stag's Leap Wine Cellars CASK 23 Cabernet Sauvignon", producer="Stag's Leap Wine Cellars", region="Stags Leap District, Napa Valley, California, USA", country="USA", appellation="Stags Leap District", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["Stags Leap CASK 23", "Stag's Leap Cask 23 Cab", "CASK 23 Stags Leap District"], description="CASK 23 is Stag's Leap's prestige cuvée from FAY and SLV vineyards; famous for winning the 1976 Paris Tasting, it remains one of California's most storied Cabernets."),
    # Common fine dining staples
    WineCatalogEntry(id="far-niente-cabernet", name="Far Niente Cabernet Sauvignon", producer="Far Niente", region="Oakville, Napa Valley, California, USA", country="USA", appellation="Oakville", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=160.0, price_tier="luxury", aliases=["Far Niente Napa Cabernet", "Far Niente Winery Cab Sauvignon", "Far Niente Oakville Cabernet"], description="Far Niente is one of Napa's most elegant and consistent Cabernets from Oakville; the estate's meticulous farming and winemaking produce a polished, age-worthy wine every vintage."),
    WineCatalogEntry(id="far-niente-chardonnay", name="Far Niente Chardonnay", producer="Far Niente", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Chardonnay", wine_type="white", avg_retail_price=80.0, price_tier="premium", aliases=["Far Niente Napa Chardonnay", "Far Niente Winery Chardonnay"], description="Far Niente's Chardonnay is one of Napa's most food-friendly and consistent whites; full-bodied with rich, creamy texture and good balance."),
    WineCatalogEntry(id="cakebread-cabernet", name="Cakebread Cellars Napa Valley Cabernet Sauvignon", producer="Cakebread Cellars", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=90.0, price_tier="premium", aliases=["Cakebread Cabernet Napa", "Cakebread Cellars Cab", "Cakebread Napa Cab Sauvignon"], description="Cakebread Cellars is one of the most widely distributed Napa Cabernets; accessible, polished, and food-friendly, it is a restaurant staple across the United States."),
    WineCatalogEntry(id="cakebread-chardonnay", name="Cakebread Cellars Napa Valley Chardonnay", producer="Cakebread Cellars", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Chardonnay", wine_type="white", avg_retail_price=65.0, price_tier="premium", aliases=["Cakebread Chardonnay Napa", "Cakebread Cellars Chard"], description="Cakebread's Chardonnay is one of America's most popular restaurant whites; ripe and generous with well-integrated oak and a creamy finish."),
    WineCatalogEntry(id="pahlmeyer-proprietary-red", name="Pahlmeyer Proprietary Red Napa Valley", producer="Pahlmeyer", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Pahlmeyer Napa Proprietary Red", "Pahlmeyer Red Napa Valley", "Jayson Pahlmeyer Proprietary Red"], description="Pahlmeyer Proprietary Red is a Bordeaux-style blend from various Napa hillside vineyards; opulent and powerful, it showcases the ripe, structured style Pahlmeyer pioneered."),
    WineCatalogEntry(id="pahlmeyer-chardonnay", name="Pahlmeyer Napa Valley Chardonnay", producer="Pahlmeyer", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Chardonnay", wine_type="white", avg_retail_price=90.0, price_tier="premium", aliases=["Pahlmeyer Chardonnay Napa", "Pahlmeyer Winery Chardonnay"], description="Pahlmeyer's Chardonnay is one of Napa's richest and most opulent whites; Helen Turley's original winemaking vision established it as a benchmark for the style."),
    # Second-tier cult
    WineCatalogEntry(id="continuum-estate", name="Continuum Estate Napa Valley Proprietary Red", producer="Continuum Estate", region="Pritchard Hill, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon/Cabernet Franc/Petit Verdot", wine_type="red", avg_retail_price=320.0, price_tier="luxury", aliases=["Continuum Napa Valley", "Tim Mondavi Continuum", "Continuum Estate Proprietary Red"], description="Continuum is Tim Mondavi's estate on Pritchard Hill; this powerful Bordeaux blend from high-elevation volcanic soils is one of Napa's most compelling recent collectibles."),
    WineCatalogEntry(id="quintessa-napa", name="Quintessa Napa Valley Red Wine", producer="Quintessa", region="Rutherford, Napa Valley, California, USA", country="USA", appellation="Rutherford", varietal="Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Quintessa Rutherford Napa", "Quintessa Red Blend Napa Valley"], description="Quintessa is a 280-acre biodynamic estate in Rutherford; their flagship blend is one of Napa's most consistently complex and age-worthy reds."),
    WineCatalogEntry(id="corison-kronos-vineyard", name="Corison Kronos Vineyard Cabernet Sauvignon", producer="Corison Winery", region="St. Helena, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Corison Kronos Cab", "Cathy Corison Kronos Vineyard", "Corison Winery Kronos Napa"], description="Corison's Kronos Vineyard is from 50-year-old vines in St. Helena; Cathy Corison's restrained, elegant style produces one of Napa's most Burgundian and age-worthy Cabernets."),
    WineCatalogEntry(id="corison-napa-cabernet", name="Corison Winery Napa Valley Cabernet Sauvignon", producer="Corison Winery", region="St. Helena, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Corison Cabernet Napa", "Cathy Corison Napa Cab", "Corison Winery Napa Cabernet"], description="Corison's Napa Valley Cabernet is a benchmark for restraint and elegance in a region often dominated by power; old vines and minimal intervention produce wines of genuine terroir expression."),
    WineCatalogEntry(id="promontory-napa", name="Promontory Napa Valley Red Wine", producer="Promontory", region="Howell Mountain, Napa Valley, California, USA", country="USA", appellation="Howell Mountain", varietal="Cabernet Sauvignon/Cabernet Franc", wine_type="red", avg_retail_price=450.0, price_tier="ultra-luxury", aliases=["Promontory Howell Mountain Red", "Harlan Promontory Napa", "Promontory Red Wine Napa Valley"], description="Promontory is Bill Harlan's mountainside estate on Howell Mountain; it represents a different expression of volcanic, high-elevation Napa Cabernet than the valley-floor Harlan Estate."),
    # Additional mid-tier staples
    WineCatalogEntry(id="plumpjack-reserve-cab", name="PlumpJack Reserve Cabernet Sauvignon", producer="PlumpJack Winery", region="Oakville, Napa Valley, California, USA", country="USA", appellation="Oakville", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["PlumpJack Reserve Oakville Cab", "Plump Jack Reserve Cabernet Napa", "PlumpJack Winery Reserve Cab"], description="PlumpJack's Reserve Cabernet is one of Oakville's most consistently outstanding wines; made in an elegant style from estate vineyards near Opus One and Harlan Estate."),
    WineCatalogEntry(id="nickel-nickel-quarry", name="Nickel & Nickel Quarry Vineyard Cabernet Sauvignon", producer="Nickel & Nickel", region="Oakville, Napa Valley, California, USA", country="USA", appellation="Oakville", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=95.0, price_tier="premium", aliases=["Nickel and Nickel Quarry Vineyard", "Nickel Nickel Oakville Cabernet", "N&N Quarry Vineyard"], description="Nickel & Nickel specializes in single-vineyard 100% varietal Cabernets from Napa's finest sites; Quarry Vineyard in Oakville is one of their most expressive and consistent bottlings."),
    WineCatalogEntry(id="lewis-cellars-reserve-cab", name="Lewis Cellars Reserve Cabernet Sauvignon", producer="Lewis Cellars", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Lewis Cellars Napa Cab", "Lewis Cellars Reserve Napa Cabernet", "Lewis Reserve Cab Sauvignon"], description="Lewis Cellars Reserve Cabernet is one of Napa's most consistently hedonistic and opulent wines; the combination of rich fruit and structured tannins has made it a restaurant favorite."),
    WineCatalogEntry(id="darioush-signature-cab", name="Darioush Signature Cabernet Sauvignon", producer="Darioush", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Darioush Napa Cabernet", "Darioush Signature Cab Napa", "Darioush Winery Cabernet"], description="Darioush's Signature Cabernet is a richly textured Napa Valley blend with Persian-heritage winemaking influences; consistent, opulent, and a popular restaurant pick."),
    WineCatalogEntry(id="realm-farella-vineyard", name="Realm Cellars Farella Vineyard Cabernet Sauvignon", producer="Realm Cellars", region="Coombsville, Napa Valley, California, USA", country="USA", appellation="Coombsville", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=200.0, price_tier="luxury", aliases=["Realm Farella Vineyard Cab", "Realm Cellars Coombsville Cabernet"], description="Realm Cellars has quickly established itself among Napa's most collectible producers; the Farella Vineyard Cabernet from Coombsville shows the cooler-climate elegance of this appellation."),
    WineCatalogEntry(id="newton-le-puzzle", name="Newton Vineyard Le Puzzle Napa Valley Red", producer="Newton Vineyard", region="Spring Mountain, Napa Valley, California, USA", country="USA", appellation="Spring Mountain District", varietal="Cabernet Sauvignon/Merlot/Cabernet Franc", wine_type="red", avg_retail_price=130.0, price_tier="luxury", aliases=["Newton Le Puzzle Napa", "Newton Vineyard Le Puzzle Red Blend", "Newton Le Puzzle Spring Mountain"], description="Newton Vineyard's Le Puzzle is their flagship unfiltered Bordeaux blend from Spring Mountain; structured and complex with excellent aging potential."),
    WineCatalogEntry(id="schramsberg-blanc-de-blancs", name="Schramsberg Vineyards Blanc de Blancs Brut", producer="Schramsberg Vineyards", region="Calistoga, Napa Valley, California, USA", country="USA", appellation="North Coast", varietal="Chardonnay", wine_type="sparkling", avg_retail_price=42.0, price_tier="mid", aliases=["Schramsberg Blanc de Blancs Napa", "Schramsberg BdB Sparkling", "Schramsberg Vineyards Brut"], description="Schramsberg is California's most celebrated sparkling wine producer; the Blanc de Blancs is the country's most-served domestic sparkling wine at state dinners and fine restaurants."),
    WineCatalogEntry(id="schramsberg-j-schram", name="Schramsberg Vineyards J. Schram Brut", producer="Schramsberg Vineyards", region="Calistoga, Napa Valley, California, USA", country="USA", appellation="North Coast", varietal="Chardonnay/Pinot Noir", wine_type="sparkling", avg_retail_price=120.0, price_tier="luxury", aliases=["Schramsberg J Schram Prestige Cuvée", "J. Schram Brut Napa", "Schramsberg JSchram"], description="J. Schram is Schramsberg's prestige cuvée; aged for up to 7 years on the lees, it achieves extraordinary depth and complexity that rivals the finest Champagnes."),
    WineCatalogEntry(id="forman-vineyard-cabernet", name="Forman Vineyard Cabernet Sauvignon", producer="Forman Vineyard", region="St. Helena, Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Forman Cabernet Napa", "Ric Forman Cabernet Sauvignon", "Forman Vineyard Napa Cab"], description="Ric Forman is a Napa legend who helped build Robert Mondavi and Sterling; his own label produces one of Napa's most structured and age-worthy Cabernets in a classic, restrained style."),
    WineCatalogEntry(id="hundred-acre-kayli-morgan", name="Hundred Acre Kayli Morgan Vineyard Cabernet Sauvignon", producer="Hundred Acre", region="Napa Valley, California, USA", country="USA", appellation="Napa Valley", varietal="Cabernet Sauvignon", wine_type="red", avg_retail_price=500.0, price_tier="ultra-luxury", aliases=["Hundred Acre Kayli Morgan Cab", "Hundred Acre Kayli Morgan Vineyard"], description="Hundred Acre's Kayli Morgan Vineyard is their most mineral and structured single-vineyard expression; alongside Ark Vineyard, it demonstrates Hundred Acre's mastery of extreme viticulture."),
]

# ---------------------------------------------------------------------------
# SECOND WAVE – Vouvray, Alsace prestige, Austrian natural, Spanish depth
# ---------------------------------------------------------------------------
SECOND_WAVE = [
    # VOUVRAY / MONTLOUIS
    WineCatalogEntry(id="huet-vouvray-le-haut-lieu-sec", name="Domaine Huet Vouvray Le Haut-Lieu Sec", producer="Domaine Huet", region="Vouvray, Loire, France", country="France", appellation="Vouvray", varietal="Chenin Blanc", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Huet Le Haut-Lieu Sec", "Huet Vouvray Sec Haut Lieu", "Domaine Huet Chenin Blanc Vouvray"], description="Domaine Huet is Vouvray's greatest estate; Le Haut-Lieu Sec is the driest of their three terroirs, mineral and taut with extraordinary aging potential."),
    WineCatalogEntry(id="huet-vouvray-clos-du-bourg-demi", name="Domaine Huet Vouvray Clos du Bourg Demi-Sec", producer="Domaine Huet", region="Vouvray, Loire, France", country="France", appellation="Vouvray", varietal="Chenin Blanc", wine_type="white", avg_retail_price=65.0, price_tier="premium", aliases=["Huet Clos du Bourg Demi Sec", "Huet Vouvray Demi Sec Clos Bourg", "Domaine Huet Clos du Bourg"], description="Clos du Bourg Demi-Sec shows the extraordinary texture and depth of Huet's biodynamic Chenin Blanc from the domaine's most prized vineyard."),
    WineCatalogEntry(id="huet-vouvray-le-mont-moelleux", name="Domaine Huet Vouvray Le Mont Moelleux", producer="Domaine Huet", region="Vouvray, Loire, France", country="France", appellation="Vouvray", varietal="Chenin Blanc", wine_type="white", avg_retail_price=80.0, price_tier="premium", aliases=["Huet Le Mont Moelleux", "Huet Vouvray Moelleux Le Mont"], description="Huet's Le Mont Moelleux is a benchmark for off-dry Vouvray; made in years with natural botrytis, it achieves extraordinary complexity and can age for decades."),
    WineCatalogEntry(id="francois-chidaine-montlouis", name="François Chidaine Montlouis-sur-Loire Clos Habert", producer="François Chidaine", region="Montlouis-sur-Loire, Loire, France", country="France", appellation="Montlouis-sur-Loire", varietal="Chenin Blanc", wine_type="white", avg_retail_price=45.0, price_tier="mid", aliases=["Chidaine Montlouis Clos Habert", "Francois Chidaine Montlouis", "Chidaine Chenin Blanc Loire"], description="François Chidaine is Vouvray's nearest neighbor Montlouis's greatest producer; his Clos Habert shows Chenin Blanc of mineral precision from biodynamic vines."),
    # ALSACE – Prestige cuvées
    WineCatalogEntry(id="trimbach-frederic-emile", name="Trimbach Riesling Cuvée Frédéric Emile", producer="Trimbach", region="Ribeauvillé, Alsace, France", country="France", appellation="Alsace", varietal="Riesling", wine_type="white", avg_retail_price=75.0, price_tier="premium", aliases=["Trimbach Frederic Emile Riesling", "Cuvée Frédéric Émile Trimbach Alsace"], description="Cuvée Frédéric Emile is Trimbach's prestige Riesling from Grands Crus Osterberg and Geisberg; it shows the structured, austere Trimbach style at its most expressive."),
    WineCatalogEntry(id="weinbach-clos-capucins-riesling", name="Domaine Weinbach Riesling Clos des Capucins", producer="Domaine Weinbach", region="Kaysersberg, Alsace, France", country="France", appellation="Alsace", varietal="Riesling", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Weinbach Clos des Capucins Riesling", "Domaine Weinbach Capucins", "Weinbach Colette Riesling Alsace"], description="Weinbach's Clos des Capucins is their estate Riesling from the walled vineyard surrounding the domaine; it demonstrates the freshness and precision that defines the Alsace style."),
    WineCatalogEntry(id="weinbach-altenbourg-riesling", name="Domaine Weinbach Riesling Altenbourg", producer="Domaine Weinbach", region="Kaysersberg, Alsace, France", country="France", appellation="Alsace Grand Cru", varietal="Riesling", wine_type="white", avg_retail_price=85.0, price_tier="premium", aliases=["Weinbach Altenbourg Riesling", "Domaine Weinbach Altenbourg Grand Cru"], description="Altenbourg is one of Weinbach's most distinguished terroirs; the Riesling shows greater richness and spice than the Capucins, with superb aging potential."),
    WineCatalogEntry(id="zind-humbrecht-rangen-riesling", name="Zind-Humbrecht Riesling Rangen de Thann Grand Cru", producer="Zind-Humbrecht", region="Thann, Alsace, France", country="France", appellation="Alsace Grand Cru Rangen", varietal="Riesling", wine_type="white", avg_retail_price=120.0, price_tier="luxury", aliases=["Zind-Humbrecht Rangen Grand Cru", "Zind Humbrecht Rangen de Thann Riesling"], description="Rangen de Thann Grand Cru is one of Alsace's most extraordinary terroirs; Zind-Humbrecht's Riesling from this volcanic slope achieves stunning power and minerality."),
    WineCatalogEntry(id="deiss-schlossberg", name="Marcel Deiss Schlossberg Grand Cru", producer="Marcel Deiss", region="Bergheim, Alsace, France", country="France", appellation="Alsace Grand Cru Schlossberg", varietal="Riesling", wine_type="white", avg_retail_price=80.0, price_tier="premium", aliases=["Marcel Deiss Schlossberg Grand Cru", "Deiss Schlossberg Alsace GC"], description="Marcel Deiss practices complantation (planting multiple varieties together); Schlossberg Grand Cru is one of their finest site expressions from the Bergheim hills."),
    # SPANISH DEPTH
    WineCatalogEntry(id="lopez-heredia-tondonia-gran-reserva", name="R. López de Heredia Viña Tondonia Rioja Gran Reserva", producer="R. López de Heredia", region="Haro, Rioja, Spain", country="Spain", appellation="Rioja DOCa", varietal="Tempranillo/Garnacha/Mazuelo/Graciano", wine_type="red", avg_retail_price=75.0, price_tier="premium", aliases=["Lopez de Heredia Tondonia Gran Reserva", "Viña Tondonia Rioja Gran Reserva", "CVNE Lopez Heredia"], description="R. López de Heredia is the most traditional Rioja producer; Viña Tondonia Gran Reserva spends 6+ years in barrel and 3+ in bottle before release, achieving extraordinary complexity."),
    WineCatalogEntry(id="lopez-heredia-tondonia-blanco", name="R. López de Heredia Viña Tondonia Rioja Blanco Gran Reserva", producer="R. López de Heredia", region="Haro, Rioja, Spain", country="Spain", appellation="Rioja DOCa", varietal="Viura/Malvasía", wine_type="white", avg_retail_price=85.0, price_tier="premium", aliases=["Lopez Heredia Tondonia Blanco", "Viña Tondonia Blanco Gran Reserva", "Heredia Rioja Blanco"], description="Tondonia Blanco Gran Reserva is one of the world's most unusual and remarkable white wines; aged for 6+ years, it develops extraordinary oxidative complexity while retaining freshness."),
    WineCatalogEntry(id="muga-prado-enea-gran-reserva", name="Bodegas Muga Prado Enea Gran Reserva", producer="Bodegas Muga", region="Haro, Rioja, Spain", country="Spain", appellation="Rioja DOCa", varietal="Tempranillo/Garnacha/Mazuelo/Graciano", wine_type="red", avg_retail_price=80.0, price_tier="premium", aliases=["Muga Prado Enea", "Prado Enea Gran Reserva Rioja", "Bodegas Muga Gran Reserva"], description="Prado Enea is Muga's flagship Gran Reserva; aged in American oak using traditional methods, it shows the classic coconut, vanilla, and tobacco character of old-school Rioja."),
    WineCatalogEntry(id="cvne-imperial-gran-reserva", name="CVNE Imperial Rioja Gran Reserva", producer="CVNE", region="Haro, Rioja, Spain", country="Spain", appellation="Rioja DOCa", varietal="Tempranillo/Mazuelo/Graciano", wine_type="red", avg_retail_price=50.0, price_tier="mid", aliases=["CVNE Imperial Gran Reserva", "Compañia Vinicola Norte España Imperial", "Cune Imperial Gran Reserva"], description="CVNE Imperial Gran Reserva is one of Rioja's most consistent and historic wines; elegantly structured Tempranillo that pairs traditional character with modern freshness."),
    WineCatalogEntry(id="alvaro-palacios-lermita-v2", name="Álvaro Palacios L'Ermita Garnacha Velles Vinyes", producer="Álvaro Palacios", region="Priorat, Catalonia, Spain", country="Spain", appellation="Priorat DOCa", varietal="Garnacha/Cabernet Sauvignon", wine_type="red", avg_retail_price=700.0, price_tier="ultra-luxury", aliases=["Alvaro Palacios L'Ermita", "L'Ermita Priorat Palacios", "Álvaro Palacios Ermita Old Vines", "Alvaro Palacios Ermita Priorat"], description="L'Ermita is Spain's most revered and expensive wine; Álvaro Palacios's old-vine Garnacha from llicorella slate soils achieves extraordinary concentration and depth."),
    # AUSTRIAN NATURAL WINE
    WineCatalogEntry(id="claus-preisinger-pannobile", name="Claus Preisinger Pannobile", producer="Claus Preisinger", region="Gols, Burgenland, Austria", country="Austria", appellation="Burgenland", varietal="Blaufränkisch/Zweigelt/St. Laurent", wine_type="red", avg_retail_price=40.0, price_tier="mid", aliases=["Preisinger Pannobile Red", "Claus Preisinger Burgenland Natural Wine"], description="Claus Preisinger is one of Austria's most acclaimed natural wine producers; his Pannobile is a benchmark for the Gols natural wine scene, with expressive fruit and earthy depth."),
    WineCatalogEntry(id="movia-ribolla", name="Movia Ribolla Gialla Brda", producer="Movia", region="Brda, Slovenia/Italy border", country="Slovenia", appellation="Brda", varietal="Ribolla Gialla", wine_type="orange", avg_retail_price=65.0, price_tier="premium", aliases=["Movia Ribolla Gialla", "Movia Brda Ribolla", "Aleš Kristančič Movia"], description="Movia is one of the original orange wine estates; Aleš Kristančič's extended maceration Ribolla Gialla is a benchmark for the Brda region's distinctive amber wine style."),
    WineCatalogEntry(id="bründlmayer-kamptal-riesling", name="Weingut Bründlmayer Riesling Heiligenstein", producer="Weingut Bründlmayer", region="Kamptal, Austria", country="Austria", appellation="Kamptal DAC Reserve", varietal="Riesling", wine_type="white", avg_retail_price=55.0, price_tier="mid", aliases=["Bründlmayer Heiligenstein Riesling", "Brundlmayer Heiligenstein Kamptal", "Willi Bründlmayer Riesling"], description="Bründlmayer's Heiligenstein Riesling is from one of Austria's most celebrated single vineyards; sandstone soils produce Riesling of extraordinary spice and aging potential."),
    # MORE MOSEL CUVÉES
    WineCatalogEntry(id="jj-prum-wehlener-spatlese", name="Weingut J.J. Prüm Wehlener Sonnenuhr Riesling Spätlese", producer="Weingut J.J. Prüm", region="Wehlen, Mosel, Germany", country="Germany", appellation="Mosel", varietal="Riesling", wine_type="white", avg_retail_price=65.0, price_tier="premium", aliases=["JJ Prum Wehlener Sonnenuhr Spätlese", "Prüm Wehlener Sonnenuhr Spatlese", "J.J. Prüm Wehlener Sonnenuhr"], description="J.J. Prüm is the Mosel's most celebrated family estate; the Wehlener Sonnenuhr Spätlese is a benchmark for the appellation's combination of sweetness, acidity, and mineral depth."),
    WineCatalogEntry(id="jj-prum-wehlener-auslese", name="Weingut J.J. Prüm Wehlener Sonnenuhr Riesling Auslese", producer="Weingut J.J. Prüm", region="Wehlen, Mosel, Germany", country="Germany", appellation="Mosel", varietal="Riesling", wine_type="white", avg_retail_price=120.0, price_tier="luxury", aliases=["JJ Prum Wehlener Auslese", "Prüm Wehlener Sonnenuhr Auslese Gold Capsule", "J.J. Prüm Auslese Mosel"], description="J.J. Prüm's Wehlener Sonnenuhr Auslese is among the Mosel's greatest dessert wines; crystalline and pure with extraordinary balance between sweetness and acidity."),
    WineCatalogEntry(id="egon-muller-kabinett", name="Egon Müller Scharzhofberger Riesling Kabinett", producer="Egon Müller", region="Wiltingen, Saar, Germany", country="Germany", appellation="Mosel", varietal="Riesling", wine_type="white", avg_retail_price=80.0, price_tier="premium", aliases=["Egon Müller Scharzhofberger Kabinett", "Egon Mueller Scharzhofberger Riesling Kabinett"], description="Egon Müller's Scharzhofberger Kabinett is perhaps the world's most elegant light-bodied Riesling; electric acidity and subtle sweetness make it a matchless food wine."),
    # MORE BURGUNDY VILLAGE WINES (for common restaurant listings)
    WineCatalogEntry(id="fourrier-gevrey-vieille-vigne", name="Domaine Fourrier Gevrey-Chambertin Vieille Vigne", producer="Domaine Fourrier", region="Gevrey-Chambertin, Burgundy, France", country="France", appellation="Gevrey-Chambertin", varietal="Pinot Noir", wine_type="red", avg_retail_price=120.0, price_tier="luxury", aliases=["Fourrier Gevrey Chambertin Vieille Vigne", "Jean-Marie Fourrier Gevrey VV"], description="Domaine Fourrier is one of Gevrey-Chambertin's most admired estates; the Vieille Vigne bottling from old vines throughout the village is a classically structured Gevrey of great depth."),
    WineCatalogEntry(id="harmand-geoffroy-gevrey-premier", name="Domaine Harmand-Geoffroy Gevrey-Chambertin Lavaux Saint-Jacques 1er Cru", producer="Domaine Harmand-Geoffroy", region="Gevrey-Chambertin, Burgundy, France", country="France", appellation="Gevrey-Chambertin Premier Cru", varietal="Pinot Noir", wine_type="red", avg_retail_price=150.0, price_tier="luxury", aliases=["Harmand Geoffroy Lavaux Saint Jacques", "Harmand-Geoffroy Gevrey Lavaux"], description="Harmand-Geoffroy is one of Gevrey's most traditional domaines; Lavaux Saint-Jacques is one of the village's greatest Premier Crus, showing power and aromatic complexity."),
    WineCatalogEntry(id="de-vogue-chambolle-musigny", name="Domaine Comte Georges de Vogüé Chambolle-Musigny", producer="Domaine Comte Georges de Vogüé", region="Chambolle-Musigny, Burgundy, France", country="France", appellation="Chambolle-Musigny", varietal="Pinot Noir", wine_type="red", avg_retail_price=250.0, price_tier="luxury", aliases=["De Vogue Chambolle Musigny", "Comte de Vogue Chambolle Village"], description="Comte Georges de Vogüé's village Chambolle-Musigny is the finest entry point to this legendary estate; it shows extraordinary precision and floral delicacy."),
    WineCatalogEntry(id="de-vogue-amoureuses", name="Domaine Comte Georges de Vogüé Chambolle-Musigny Les Amoureuses 1er Cru", producer="Domaine Comte Georges de Vogüé", region="Chambolle-Musigny, Burgundy, France", country="France", appellation="Chambolle-Musigny Premier Cru", varietal="Pinot Noir", wine_type="red", avg_retail_price=800.0, price_tier="ultra-luxury", aliases=["De Vogue Les Amoureuses", "Comte de Vogue Amoureuses Chambolle"], description="Les Amoureuses is widely considered the greatest Premier Cru in Burgundy; de Vogüé's version regularly trades at Grand Cru prices for its ethereal elegance and complexity."),
    # RHÔNE ADDITIONAL (Condrieu + Northern)
    WineCatalogEntry(id="guigal-condrieu-la-doriane", name="E. Guigal Condrieu La Doriane", producer="E. Guigal", region="Condrieu, Rhône, France", country="France", appellation="Condrieu", varietal="Viognier", wine_type="white", avg_retail_price=120.0, price_tier="luxury", aliases=["Guigal La Doriane Condrieu", "E Guigal Condrieu Doriane Viognier"], description="La Doriane is Guigal's single-vineyard Condrieu from the finest parcels on the Côte Blonde; it represents the most opulent expression of Viognier from this storied appellation."),
    WineCatalogEntry(id="chapoutier-crozes-meysonniers", name="M. Chapoutier Crozes-Hermitage Les Meysonniers", producer="M. Chapoutier", region="Crozes-Hermitage, Rhône, France", country="France", appellation="Crozes-Hermitage", varietal="Syrah", wine_type="red", avg_retail_price=35.0, price_tier="value", aliases=["Chapoutier Les Meysonniers Crozes", "M Chapoutier Crozes-Hermitage Meysonniers"], description="Les Meysonniers is one of Chapoutier's most food-friendly Northern Rhône wines; structured Syrah from Crozes-Hermitage at an accessible price point."),
]

# ---------------------------------------------------------------------------
# Assemble full catalog
# ---------------------------------------------------------------------------
WINE_CATALOG: list[WineCatalogEntry] = (
    BORDEAUX_LEFT
    + BORDEAUX_RIGHT
    + BURGUNDY_RED
    + BURGUNDY_WHITE
    + RHONE
    + CHAMPAGNE
    + CALIFORNIA
    + TUSCANY
    + SPAIN
    + AUSTRALIA
    + NEW_ZEALAND
    + GERMANY_AUSTRIA
    + OTHER_FRANCE
    + ENTRY_LEVEL
    + BURGUNDY_CULT
    + CHAMPAGNE_GROWERS
    + BORDEAUX_ADDITIONS
    + ITALY_CULT
    + SPAIN_CULT
    + CALIFORNIA_CULT
    + GERMANY_AUSTRIA_ADDITIONS
    + CHILE
    + SOUTH_AFRICA
    + PORTUGAL
    + AUSTRALIA_ADDITIONS
    + CHAMPAGNE_RM
    + ITALY_CAMPANIA
    + ITALY_SICILY
    + ITALY_CENTRAL
    + ITALY_PIEDMONT
    + ITALY_TUSCANY_ADD
    + LOIRE
    + BEAUJOLAIS
    + JURA
    + LANGUEDOC
    + ALSACE
    + SPAIN_REGIONAL
    + GERMANY_ADD
    + ITALY_VENETO
    + ITALY_FRIULI
    + ITALY_NORTHEAST
    + GERMANY_ADDITIONAL
    + AUSTRIA_ADDITIONS
    + SPAIN_ADDITIONS
    + PORTUGAL_ADDITIONS
    + ARGENTINA_ADDITIONS
    + CHILE_ADDITIONS
    + AUSTRALIA_GLOBAL
    + NZ_ADDITIONS
    + SA_ADDITIONS
    + GREECE
    + HUNGARY
    + LEBANON
    + GEORGIA_COUNTRY
    + USA_SONOMA_SANTA_BARBARA
    + NAPA_ADDITIONS
    + SECOND_WAVE
    + CHABLIS_CLASSICS
    + MACONNAIS
    + BURGUNDY_WHITE_EXTRA
    + BURGUNDY_RED_EXTRA
    + CHAMPAGNE_PRESTIGE
    + RHONE_NORTH
    + RHONE_SOUTH_BANDOL
    + LOIRE_ADDITIONS
    + BORDEAUX_EXTRA
    + CALIFORNIA_NAPA_EXTRA
    + CALIFORNIA_PINOT_SYRAH
    + OREGON_WASHINGTON
    + ITALY_EXTRA
    + NY_FINGER_LAKES
)

# Quick lookup by id
WINE_CATALOG_BY_ID: dict[str, WineCatalogEntry] = {w.id: w for w in WINE_CATALOG}
