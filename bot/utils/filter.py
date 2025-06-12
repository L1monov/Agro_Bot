
import re

STOP_WORDS = {
    "упаковка", "упаковке", "упакованная", "упакованный", "упаковки", "окара", "кормовая добавка", "комбикорм",
    "замороженные", "замороженный", "замороженная", "крупы", "крупа", "полуфабрикат","полуфабрикаты", "быстрозамороженные",
    "сушенные", "чипсы", "набор", "вакумная упаковка", "в вакуумной упаковке", "смесь", "коктель", "ассорти",
    "в пакеты из полиэтиленовой пленки", "пленка полиэтиленовая", "консервы", "концентрат", "фрукты", "ягоды",
    "собак", "манка", "товарный знак", "товарным знаком", "агрохимикат", "легион", "наш урожай", "365 дней",
    "то, что надо!", "красная цена", "первым делом", "сушеные", "ассортименте", "свежезамороженные",
    "быстрозамороженная", "жареные", "жареный", "жареная", "жареное", "паста", "пасты", "орехи", "ореховые",
    "ореховая", "кулинарные", "кулинария", "кулинарное", "кулинарная", "каша", "абрикосы", "абрикос", "вок",
    "завтрак", "персик", "персики", "миндаль", "фундук", "кешью", "макадамия", "грецкий орех", "сельдерей",
    "кинза", "петрушка", "укроп", "арахис", "очищеннные", "неочищенные", "клубника", "микс", "миксы", "арбуз", "арбузы", "микрозелень"
}

STRICT_PRODUCT_KEYWORDS = {
    "пшеница", "соя", "рожь", "чечевица", "тритикале", "рапс", "ячмень", "свекла", "овес",
    "лен", "лён", "подсолнечник", "сорго", "рис", "вика", "гречиха", "люпин", "пшено",
    "горчица", "просо", "рыжик", "кукуруза", "лук", "картофель", "морковь", "горох",
    "фасоль", "нут", "мука", "масло", "масла", "сахар", "крахмал", "шрот", "жмых",
    "жом", "отруби", "дрожжи"
}

STOP_COMPANIES_ALWAYS = [
    "донская экспортная компания",
    "грейн гейтс",
    "торгово-финансовая компания пром экспорт",
    "рус трейдинг",
    "грейн филд",
    "топ грейн",
    "грейн фермер",
    "интрофорус",
    "русьальфатрейд",
    "грейн",
    "гранд-трейд",
    "вкусвилл",
    "орантес",
    "арвиай",
    "астон",
    "морем",
    "черкизово"
]

RESTRICTED_COMPANIES = {
    "астон": {"масло", "жмых", "шрот"},
    "юг руси": {"масло", "жмых", "шрот"},
    "содружество": {"масло", "жмых", "шрот"},
    "эфко": {"масло", "жмых", "шрот"},
}

def contains_stop_words(text: str, allow_krahmal=False, allow_maslo=False) -> bool:
    text = (text or "").lower()

    if not allow_krahmal and "крахмал" in text and not re.search(r"\bкрахмал\b", text):
        return True
    if not allow_maslo and re.search(r"\bмасло\b", text):
        return True

    pattern = re.compile(
        r"\b(?:" + "|".join(map(re.escape, STOP_WORDS)) + r")\b",
        flags=re.IGNORECASE
    )

    return bool(pattern.search(text))


def match_product_keywords(selected_keywords: list[str], product_name: str, product_designation: str) -> bool:
    combined_text = f"{product_name} {product_designation}".lower()
    for keyword in selected_keywords:
        keyword = keyword.lower()
        if keyword in STRICT_PRODUCT_KEYWORDS:
            if re.search(rf"\b{re.escape(keyword)}\b", combined_text):
                return True
        else:
            if keyword in combined_text:
                return True
    return False


def should_skip_company(company_name: str, product_name: str, product_designation: str) -> bool:
    """
    Возвращает True, если по названию компании нужно пропустить эту декларацию:
    - Если компания в STOP_COMPANIES_ALWAYS — всегда пропускаем.
    - Если компания в RESTRICTED_COMPANIES — пропускаем, если продукт не в разрешённом списке.
    """
    cn = (company_name or "").lower()
    combined = f"{product_name or ''} {product_designation or ''}".lower()

    # полностью стоп
    for stop in STOP_COMPANIES_ALWAYS:
        if stop in cn:
            return True

    # частичный стоп: только масло/жмых/шрот
    for comp, allowed in RESTRICTED_COMPANIES.items():
        if comp in cn:
            # если ни одно из разрешённых слов не встретилось в названии или обозначении — пропускаем
            if not any(w in combined for w in allowed):
                return True

    return False


async def filter_sellers(announcements: list[dict]) -> dict:
    from collections import defaultdict

    # Вложенный defaultdict: для каждой компании — словарь адресов, и для каждого адреса — список предложений
    grouped = defaultdict(lambda: defaultdict(list))

    for item in announcements:
        company = item.get('name_company', '').strip()
        address = item.get('company_address', '').strip() or '—'
        specs = item.get('specs', '').strip()
        price = item.get('price', '').strip()

        # Добавляем запись под конкретный адрес
        grouped[company][address].append({
            'specs': specs,
            'price': price
        })

    # Приводим вложенные defaultdict к обычным dict
    result = {
        company: dict(addresses)
        for company, addresses in grouped.items()
    }
    return result