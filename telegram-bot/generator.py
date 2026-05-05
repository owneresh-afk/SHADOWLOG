import random
import time
from data.bins import COUNTRY_BANKS, GENERIC_BINS, CARD_BRANDS

def luhn_checksum(card_number: str) -> bool:
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return total % 10 == 0

def luhn_complete(partial: str) -> str:
    partial = partial + '0'
    digits = [int(d) for d in partial]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    check = (10 - (total % 10)) % 10
    return partial[:-1] + str(check)

def generate_card_number(bin_prefix: str, brand: str = None) -> str:
    if brand == "AMEX":
        length = 15
    elif brand == "UNIONPAY":
        length = 16
    else:
        length = 16
    
    remaining = length - len(bin_prefix) - 1
    partial = bin_prefix + ''.join([str(random.randint(0, 9)) for _ in range(remaining)])
    return luhn_complete(partial)

def generate_expiry() -> tuple:
    year = random.randint(2025, 2030)
    month = random.randint(1, 12)
    return f"{month:02d}", str(year)

def generate_cvv(brand: str = "VISA") -> str:
    if brand == "AMEX":
        return str(random.randint(1000, 9999))
    return str(random.randint(100, 999))

def get_bins_for_criteria(countries: list, banks: list, brands: list, card_types: list, card_categories: list) -> list:
    bins_pool = []
    
    for country_code in countries:
        country_data = COUNTRY_BANKS.get(country_code)
        if not country_data:
            continue
        
        bank_list = banks if banks else list(country_data["banks"].keys())
        
        for bank_name in bank_list:
            bank_data = country_data["banks"].get(bank_name)
            if not bank_data:
                continue
            
            for brand in brands:
                brand_data = bank_data["bins"].get(brand)
                if not brand_data:
                    continue
                
                for category in card_categories:
                    cat_key = category.lower()
                    cat_data = brand_data.get(cat_key, {})
                    if not cat_data:
                        continue
                    
                    for card_type in card_types:
                        type_bins = cat_data.get(card_type, [])
                        for b in type_bins:
                            bins_pool.append({
                                "bin": b,
                                "brand": brand,
                                "country": country_code,
                                "bank": bank_name,
                                "type": card_type,
                                "category": category
                            })
    
    if not bins_pool:
        for brand in brands:
            generic = GENERIC_BINS.get(brand, {})
            for category in card_categories:
                cat_key = category.lower()
                for b in generic.get(cat_key, []):
                    bins_pool.append({
                        "bin": b,
                        "brand": brand,
                        "country": countries[0] if countries else "US",
                        "bank": "Generic",
                        "type": card_types[0] if card_types else "CLASSIC",
                        "category": category
                    })
    
    return bins_pool

def generate_cards(
    countries: list,
    banks: list,
    brands: list,
    card_types: list,
    card_categories: list,
    quantity: int
) -> list:
    bins_pool = get_bins_for_criteria(countries, banks, brands, card_types, card_categories)
    
    if not bins_pool:
        for brand in brands:
            generic = GENERIC_BINS.get(brand, {})
            for cat in card_categories:
                for b in generic.get(cat.lower(), []):
                    bins_pool.append({"bin": b, "brand": brand, "country": "US", "bank": "Generic", "type": "CLASSIC", "category": cat})
    
    if not bins_pool:
        bins_pool = [{"bin": "411111", "brand": "VISA", "country": "US", "bank": "Generic", "type": "CLASSIC", "category": "CREDIT"}]
    
    cards = []
    for _ in range(quantity):
        bin_info = random.choice(bins_pool)
        number = generate_card_number(bin_info["bin"], bin_info["brand"])
        month, year = generate_expiry()
        cvv = generate_cvv(bin_info["brand"])
        cards.append({
            "number": number,
            "month": month,
            "year": year,
            "cvv": cvv,
            "brand": bin_info["brand"],
            "bank": bin_info["bank"],
            "type": bin_info["type"],
            "category": bin_info["category"],
            "country": bin_info["country"]
        })
    
    return cards

def format_card(card: dict) -> str:
    return f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
