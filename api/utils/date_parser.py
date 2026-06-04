# api/date_utils.py

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

def extract_month(text):
    text = text.lower()

    for month, value in MONTHS.items():
        if month in text:
            return value

    return None