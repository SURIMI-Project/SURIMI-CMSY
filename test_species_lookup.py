from server.species_lookup import species_lookup_instance

def test_existing_code():
    print("🔎 Checking known species...")
    name = species_lookup_instance.get_or_add_common_name("PIL")
    print(f"✅ Common name for 'PIL': {name}")

def test_unknown_code():
    print("➕ Adding new unknown species...")
    new_code = "XXX"
    name = species_lookup_instance.get_or_add_common_name(new_code)
    print(f"✅ Placeholder for '{new_code}': {name}")

if __name__ == "__main__":
    test_existing_code()
    test_unknown_code()
