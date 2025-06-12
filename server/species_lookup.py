import csv
from pathlib import Path

try:
    base_dir = Path(__file__).resolve().parent.parent
    species_csv_path = base_dir / "R_files" / "Common_names" / "asfis.csv"

    _species_map = {}

    if species_csv_path.exists():
        with species_csv_path.open(mode='r', encoding='latin-1', newline='') as f:
            reader = csv.DictReader(f)
            print(f"[DEBUG] Detected headers: {reader.fieldnames}")
            for row in reader:
                code = (row.get("alpha_code") or row.get("\ufeffalpha_code") or "").strip().upper()
                common = (row.get("common_name") or "").strip()
                if code and common:
                    _species_map[code] = common
        print(f"[INFO] Species CSV loaded with {len(_species_map)} entries.")
    else:
        print(f"[WARNING] Species CSV not found at: {species_csv_path}")

except Exception as e:
    print(f"[ERROR] Could not load species data: {e}")
    _species_map = {}

def get_common_name(alpha_code: str) -> str:
    code = alpha_code.strip().upper()
    return _species_map.get(code, f"Unknown Species - {code}")

if __name__ == "__main__":
    test_codes = ["PIL", "XYZ", "BBK", "sal", " abc "]
    for code in test_codes:
        print(f"{code} → {get_common_name(code)}")
