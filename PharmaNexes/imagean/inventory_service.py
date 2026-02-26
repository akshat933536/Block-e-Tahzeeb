import csv
import difflib
import re

CSV_FILE = "medicines.csv"


def load_inventory():
    inventory = []

    try:
        with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Use the CSV headers that exist
                name = row.get("name", "").strip().lower()
                if not name:
                    continue  # skip empty rows

                # Use review % as a placeholder for price/availability
                # Excellent + Average + Poor = 100%, just for reference
                price = "N/A"  # No price in CSV
                is_discontinued = "false"  # assume available

                inventory.append({
                    "name": name,
                    "price": price,
                    "is_discontinued": is_discontinued
                })

    except FileNotFoundError:
        print("Inventory CSV file not found")

    return inventory


def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9/ ]', '', text)  # remove special characters
    for word in ["tablet", "tab", "injection", "syrup", "suspension", "cream"]:
        text = text.replace(word, "")
    text = text.strip()
    return text


def check_inventory(medicines):
    inventory = load_inventory()
    inventory_names = [item["name"] for item in inventory]

    result = []

    for med in medicines:
        original_name = med.get("medicine_name", "")
        normalized_input = normalize(original_name)

        # Try best match
        best_match = difflib.get_close_matches(
            normalized_input,
            [normalize(name) for name in inventory_names],
            n=1,
            cutoff=0.6
        )

        if best_match:
            for item in inventory:
                if normalize(item["name"]) == best_match[0]:
                    result.append({
                        "original_name": original_name,
                        "corrected_name": item["name"],
                        "price": item["price"],
                        "available": item["is_discontinued"].lower() == "false",
                        "present": True,
                        "alternatives": []
                    })
                    break
        else:
            # Suggest alternatives (top 3 similar medicines)
            alternative_matches = difflib.get_close_matches(
                normalized_input,
                [normalize(name) for name in inventory_names],
                n=3,
                cutoff=0.3
            )

            alternatives = []
            for match in alternative_matches:
                for item in inventory:
                    if normalize(item["name"]) == match:
                        alternatives.append(item["name"])

            result.append({
                "original_name": original_name,
                "corrected_name": None,
                "price": None,
                "available": False,
                "present": False,
                "alternatives": alternatives
            })

    return result