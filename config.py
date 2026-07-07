from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = PROJECT_ROOT / "agribusiness_tracker.db"
LATEST_CSV_PATH = DATA_DIR / "latest_events.csv"
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"

DATA_DIR.mkdir(exist_ok=True)

EXPECTED_COLUMNS = [
    "event_id",
    "announcement_date",
    "event_date",
    "year",
    "company_tier",
    "company",
    "event_group",
    "event_type",
    "evidence_text",
    "commodity_group",
    "commodity_subcategory",
    "asset_name",
    "asset_type",
    "value_chain",
    "value_chain_link",
    "region",
    "country",
    "counterparty",
    "deal_value",
    "deal_currency",
    "deal_status",
    "source_url",
    "source_title",
    "source_type",
    "confidence_score",
    "needs_review",
    "created_at",
    "updated_at",
]

CRITICAL_COLUMNS = [
    "event_id",
    "year",
    "company",
    "company_tier",
    "event_type",
    "commodity_group",
    "commodity_subcategory",
    "value_chain",
    "value_chain_link",
    "region",
    "country",
    "source_url",
    "evidence_text",
]

# event_id is special: the app can generate it when the column is absent or blank.
CRITICAL_COLUMNS_AFTER_EVENT_ID_GENERATION = [c for c in CRITICAL_COLUMNS if c != "event_id"]

DATE_COLUMNS = ["announcement_date", "event_date", "created_at", "updated_at"]

UNKNOWN_IF_BLANK_FIELDS = [
    "company_tier",
    "event_group",
    "event_type",
    "commodity_group",
    "commodity_subcategory",
    "value_chain",
    "value_chain_link",
    "region",
    "country",
    "deal_status",
    "source_type",
]

MULTIVALUE_FIELDS = [
    "commodity_group",
    "commodity_subcategory",
    "value_chain",
    "value_chain_link",
    "region",
    "country",
    "counterparty",
]

ANALYSIS_LENSES = ["Players", "Commodity Group"]

PLAYER_ORDER = [
    "ADM",
    "Bunge",
    "Cargill",
    "COFCO International",
    "LDC",
    "Viterra",
    "Olam Group",
    "Wilmar",
    "CHS",
    "Seaboard",
    "Amaggi",
    "ACA",
    "AGD",
    "Molinos Agro",
    "Ameropa",
    "Raízen",
    "São Martinho",
    "Copersucar",
    "Atvos",
    "BP Bioenergy",
    "Tereos",
    "Usina Coruripe",
    "Zilor",
    "ECOM",
    "NKG",
    "Volcafe",
    "Sucafina",
    "Sucden",
]

TABLE_COLUMNS = [
    "event_date",
    "company",
    "event_group",
    "event_type",
    "commodity_group",
    "commodity_subcategory",
    "value_chain",
    "value_chain_link",
    "country",
    "asset_name",
    "counterparty",
    "deal_value",
    "deal_currency",
    "deal_status",
    "source_title",
    "source_url",
    "needs_review",
]

DETAIL_COLUMNS = [
    "event_id",
    "announcement_date",
    "event_date",
    "year",
    "company_tier",
    "company",
    "event_group",
    "event_type",
    "commodity_group",
    "commodity_subcategory",
    "asset_name",
    "asset_type",
    "value_chain",
    "value_chain_link",
    "region",
    "country",
    "counterparty",
    "deal_value",
    "deal_currency",
    "deal_status",
    "source_title",
    "source_type",
    "source_url",
    "confidence_score",
    "needs_review",
    "created_at",
    "updated_at",
    "evidence_text",
]

ADVANCED_FILTER_FIELDS = [
    "company_tier",
    "company",
    "event_group",
    "event_type",
    "commodity_group",
    "commodity_subcategory",
    "value_chain",
    "value_chain_link",
    "region",
    "country",
    "deal_status",
    "source_type",
    "needs_review",
    "has_deal_value",
]

VALUE_CHAIN_LINK_ORDER = [
    "Farming",
    "Origination",
    "Inland Logistics",
    "Trading",
    "Ports",
    "Ocean Freight",
    "Processing",
    "Commodity Distribution",
    "Food & Food Ingredients",
    "Feed & Animal Nutrition",
    "Proteins",
    "Meat / Poultry / Dairy",
    "Pharmaceutical / Health",
    "Energy Distribution",
    "R&D / Innovation",
    "Others",
    "Corporate / Multi-Chain",
]

VALUE_CHAIN_LINK_DISPLAY_LABELS = {
    "Commodity Distribution": "Distribution / Sales",
    "Energy Distribution": "Energy",
}

VALUE_CHAIN_LINK_TO_CHAIN = {
    "Farming": "Upstream",
    "Origination": "Upstream",
    "Inland Logistics": "Upstream",
    "Trading": "Upstream",
    "Ports": "Upstream",
    "Ocean Freight": "Upstream",
    "Processing": "Upstream",
    "Commodity Distribution": "Downstream",
    "Food & Food Ingredients": "Downstream",
    "Feed & Animal Nutrition": "Downstream",
    "Proteins": "Downstream",
    "Meat / Poultry / Dairy": "Downstream",
    "Pharmaceutical / Health": "Downstream",
    "Energy Distribution": "Downstream",
    "R&D / Innovation": "Downstream",
    "Others": "Downstream",
    "Corporate / Multi-Chain": "Corporate / Multi-Chain",
}

EVENT_GROUP_ORDER = [
    "Growth Investment",
    "Equity / Deal Activity",
    "Partnership",
    "Capital Market / Financing",
    "Portfolio Reduction",
    "Restructuring / Distress",
]

EVENT_TYPE_ORDER = [
    "Greenfield Investment",
    "Capacity Expansion",
    "Business Expansion",
    "Market Entry",
    "Concession / Long-term Lease",
    "M&A",
    "Joint Venture",
    "Minority Investment",
    "Strategic Partnership",
    "Financing / Capital Raising",
    "IPO / Spin-off / Listing",
    "Divestiture / Asset Sale",
    "Business Exit",
    "Plant Closure",
    "Restructuring",
    "Layoff",
    "Bankruptcy",
]

EVENT_TYPE_TO_GROUP = {
    "Greenfield Investment": "Growth Investment",
    "Capacity Expansion": "Growth Investment",
    "Business Expansion": "Growth Investment",
    "Market Entry": "Growth Investment",
    "Concession / Long-term Lease": "Growth Investment",
    "M&A": "Equity / Deal Activity",
    "Joint Venture": "Equity / Deal Activity",
    "Minority Investment": "Equity / Deal Activity",
    "Strategic Partnership": "Partnership",
    "Financing / Capital Raising": "Capital Market / Financing",
    "IPO / Spin-off / Listing": "Capital Market / Financing",
    "Divestiture / Asset Sale": "Portfolio Reduction",
    "Business Exit": "Portfolio Reduction",
    "Plant Closure": "Portfolio Reduction",
    "Restructuring": "Restructuring / Distress",
    "Layoff": "Restructuring / Distress",
    "Bankruptcy": "Restructuring / Distress",
}

COMMODITY_GROUP_ORDER = [
    "Grains & Oilseeds",
    "Sugar & Ethanol",
    "Coffee",
    "Cotton",
    "Specialty Crops",
    "Fertilizers & Crop Inputs",
    "Renewable Fuels & Bioenergy",
    "Multi-commodity / Corporate",
    "Others",
    "Unknown",
]

EVENT_GROUP_COLORS = {
    "Growth Investment": "#2563EB",
    "Equity / Deal Activity": "#0891B2",
    "Partnership": "#059669",
    "Capital Market / Financing": "#0D9488",
    "Portfolio Reduction": "#F97316",
    "Restructuring / Distress": "#DC2626",
    "Unknown": "#64748B",
    "Others": "#94A3B8",
}

COMMODITY_GROUP_COLORS = {
    "Grains & Oilseeds": "#2563EB",
    "Sugar & Ethanol": "#16A34A",
    "Coffee": "#92400E",
    "Cotton": "#64748B",
    "Specialty Crops": "#7C3AED",
    "Fertilizers & Crop Inputs": "#CA8A04",
    "Renewable Fuels & Bioenergy": "#059669",
    "Multi-commodity / Corporate": "#475569",
    "Others": "#94A3B8",
    "Unknown": "#CBD5E1",
}

VALUE_CHAIN_COLORS = {
    "Upstream": "#0891B2",
    "Downstream": "#7C3AED",
    "Corporate / Multi-Chain": "#64748B",
    "Unknown": "#CBD5E1",
}
