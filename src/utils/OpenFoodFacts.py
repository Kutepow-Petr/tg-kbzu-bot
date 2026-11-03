import requests
from Product import Product

class OpenFoodFacts:
    URL = "https://world.openfoodfacts.org/cgi/search.pl"

    def __init__(self):
        self.PARAMS = {
            'search_terms': "",
            'search_simple': 1,
            'action': 'process',
            'json': 1,
            'page_size': 20,
            'cc': 'ru',
            'lc': 'ru',
            'nutrient_0': 'proteins',
            'nutrient_modifier_0': '>',
            'nutrient_value_0': '0',
            'nutrient_1': 'fat',
            'nutrient_modifier_1': '>',
            'nutrient_value_1': '0',
            'nutrient_2': 'carbohydrates',
            'nutrient_modifier_2': '>',
            'nutrient_value_2': '0',
            'sort_by': 'unique_scans_n',
            'fields': 'product_name,product_name_ru,brands,energy-kcal_100g,proteins_100g,fat_100g,carbohydrates_100g'
        }

    def search(self, product_name: str) -> list:
        params = self.PARAMS.copy()
        params['search_terms'] = product_name

        headers = {
            "User-Agent": "tg-kbzu-bot/1.0 (contact@mymail.com)"
        }

        try:
            response = requests.get(
                self.URL,
                params=params,
                headers=headers,
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            return []

        valid_products = []
        for product in data.get('products', []):
            try:
                parsed_product = self._parse_product(product)
                if parsed_product:
                    valid_products.append(parsed_product)
            except Exception as e:
                print(f"Ошибка парсинга продукта: {e}")
                continue

        return valid_products

    def _parse_product(self, product_data: dict) -> Product:
        name = product_data.get('product_name_ru') or product_data.get('product_name', '')
        name = name.strip()
        if not name or len(name) < 2:
            return None

        brand = product_data.get('brands', '').strip()
        if brand and brand.lower() not in name.lower():
            name += f" ({brand})"

        # Теперь читаем напрямую с верхнего уровня
        proteins = round(product_data.get('proteins_100g', 0) or 0, 1)
        fats = round(product_data.get('fat_100g', 0) or 0, 1)
        carbs = round(product_data.get('carbohydrates_100g', 0) or 0, 1)

        # Отсеиваем явно битые данные
        if (proteins > 100 or fats > 100 or carbs > 100) or (proteins <= 0 and fats <= 0 and carbs <= 0):
            return None

        calories = round(product_data.get('energy-kcal_100g', 0) or 0, 1)
        return Product(
            name=name,
            calories=calories,
            proteins=proteins,
            fats=fats,
            carbs=carbs
        )