import csv
from pathlib import Path
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

__all__ = ["get_common_name"]  # Exported functions

# Path to the species CSV
_species_data_file = Path(__file__).parent.parent.resolve() / "R_files" / "Common_names" / "asfis.csv"

# alpha_code → {"common_name": ..., "scient_name": ...}
_common_name_map = {}

# Load the CSV on module import
try:
    if _species_data_file.exists():
        with _species_data_file.open(mode='r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = (row.get("alpha_code") or "").strip().upper()
                common = (row.get("common_name") or "").strip()
                scient = (row.get("scient_name") or "").strip()
                if code and common:
                    _common_name_map[code] = {
                        "common_name": common,
                        "scient_name": scient
                    }
        logger.info(f"✅ Loaded {_species_data_file} with {len(_common_name_map)} entries.")
    else:
        logger.warning(f"⚠️ Species file not found: {_species_data_file}")
except Exception as e:
    logger.error(f"❌ Failed to load species file: {e}")

def get_common_name(alpha_code: str) -> str:
    """
    Returns the common name for the given alpha code.
    If it's not found, adds a placeholder entry and persists it.

    Args:
        alpha_code: The 3-letter species code (e.g. "PIL").

    Returns:
        Common name string (or placeholder).
    """
    sanitized = alpha_code.strip().upper()

    if sanitized in _common_name_map:
        return _common_name_map[sanitized]["common_name"]

    # Create fallback
    fallback_common = f"UNKNOWN_SPECIES_{sanitized}"
    fallback_scient = f"UNKNOWN_SCIENT_NAME_{sanitized}"
    _common_name_map[sanitized] = {
        "common_name": fallback_common,
        "scient_name": fallback_scient
    }
    logger.info(f"➕ Added placeholder for {sanitized}: {fallback_common}")
    _save()
    return fallback_common

def _save():
    """Writes the current _common_name_map to the CSV file."""
    try:
        _species_data_file.parent.mkdir(parents=True, exist_ok=True)
        with _species_data_file.open(mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["alpha_code", "scient_name", "common_name"])
            for code in sorted(_common_name_map):
                entry = _common_name_map[code]
                writer.writerow([code, entry["scient_name"], entry["common_name"]])
        logger.info(f"💾 Species data saved to {_species_data_file}")
    except Exception as e:
        logger.error(f"❌ Failed to save species file: {e}")
