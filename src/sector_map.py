"""
Sector Mapping — Stock → Sector ETF relationships
Used by hot_stock_ranker.py to compute sector tailwind scores.
"""

# Sector ETFs to scan
SECTOR_ETFS = {
    "XLK": "Technology",
    "SMH": "Semiconductors",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLC": "Communication",
    "XLP": "Consumer Staples",
    "XLY": "Consumer Discretionary",
    "IBB": "Biotech",
    "ARKK": "Innovation",
    "XLRE": "Real Estate",
}

# Stock → Primary sector ETF(s)
# First entry is primary, rest are secondary/confirming
STOCK_SECTOR_MAP = {
    # Tech / AI
    "NVDA": ["SMH", "XLK"],
    "AMD": ["SMH", "XLK"],
    "INTC": ["SMH", "XLK"],
    "AVGO": ["SMH", "XLK"],
    "QCOM": ["SMH", "XLK"],
    "MU": ["SMH", "XLK"],
    "ARM": ["SMH", "XLK"],
    # Quantum / Emerging Tech
    "IONQ": ["XLK"],
    "RKLB": ["XLK"],
    # Nuclear / Energy
    "SMR": ["XLU", "XLE"],
    "OKLO": ["XLU", "XLE"],
    "EOSE": ["XLU", "XLE"],
    "TLN": ["XLU", "XLE"],
    "VST": ["XLU", "XLE"],
    "CEG": ["XLU", "XLE"],
    # EV / Consumer
    "TSLA": ["XLY", "ARKK"],
    "RIVN": ["XLY", "ARKK"],
    "LCID": ["XLY", "ARKK"],
    # Canadian Energy
    "CNQ.TO": ["XLE"],
    "CVE.TO": ["XLE"],
    "SU.TO": ["XLE"],
    "XEG.TO": ["XLE"],
    # Materials / Mining
    "PAAS.TO": ["XLB"],
    "TECK": ["XLB"],
    "TECK.TO": ["XLB"],
    "WPM": ["XLB"],
    "FNV": ["XLB"],
    # Biotech
    "MRNA": ["IBB", "XLV"],
    "BNTX": ["IBB", "XLV"],
    "CRSP": ["IBB", "XLV"],
    # Financials
    "JPM": ["XLF"],
    "GS": ["XLF"],
    "MS": ["XLF"],
    # Healthcare
    "UNH": ["XLV"],
    "LLY": ["XLV"],
    # Industrials
    "GE": ["XLI"],
    "CAT": ["XLI"],
    # Utilities
    "NEE": ["XLU"],
    "DUK": ["XLU"],
    # Crypto-adjacent
    "COIN": ["XLK", "XLF"],
    "MSTR": ["XLK"],
    # Commodities
    "GOLD": ["XLB"],
    "NEM": ["XLB"],
    "FCX": ["XLB"],
}


def get_sector_etfs(stock_symbol: str) -> list:
    """Return list of sector ETF symbols for a given stock."""
    return STOCK_SECTOR_MAP.get(stock_symbol.upper(), [])


def get_sector_name(etf_symbol: str) -> str:
    """Return human-readable sector name for an ETF symbol."""
    return SECTOR_ETFS.get(etf_symbol.upper(), etf_symbol)


def get_all_tracked_stocks() -> list:
    """Return all stocks that have sector mappings."""
    return sorted(STOCK_SECTOR_MAP.keys())
