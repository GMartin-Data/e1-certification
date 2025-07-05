"""
Column mappings for Collibra Excel exports.
Maps Excel column names to database field names.
"""

# Community mappings (minimal - most processing is custom)
COMS_MAPPING = {"Community": "nom", "Description": "description"}

# Domain mappings
DOMS_MAPPING = {
    "Domain Id": "id",
    "Asset Type": "asset_type",  # Used for filtering
    "Domain": "nom",
    "Community": "communaute",  # Used to get FK
}

# Table mappings
TABS_MAPPING = {
    "Asset Id": "id",
    "Name": "nom",
    "Description (No Formatting)": "description",
    "CreatedOn": "date_creation",
    "LastModifiedOn": "date_derniere_modification",
    "Domain Id": "domaine_id",
}

# Column mappings
COLS_MAPPING = {
    "Asset Id": "id",
    "Name": "nom",
    "Description (No Formatting)": "description",
    "CreatedOn": "date_creation",
    "LastModifiedOn": "date_derniere_modification",
    "Technical Data Type": "data_type",
    "[Column] is part of [Table] > Asset Id": "data_table_id",
}

# File name patterns to entity mapping
FILE_PATTERNS = {
    "communities": "communautes",
    "communautes": "communautes",
    "domaines": "domaines",
    "domains": "domaines",
    "tables": "data_tables",
    "columns": "data_colonnes",
    "colonnes": "data_colonnes",
}
