from typing import Literal

INTENT_KEYWORDS = {
    "profit_analysis": ["profit", "margin", "revenue", "loss", "earning"],
    "sales_analysis": ["sales", "trend", "growth", "demand", "orders"],
    "inventory_analysis": ["inventory", "stock", "stockout", "restock", "stock status"],
    "top_products": ["top", "best sellers", "sku", "product performance"],
    "dead_stock": ["dead stock", "stale", "no sales", "slow moving", "dead inventory"],
    "pricing_recommendation": ["price", "pricing", "discount", "markup", "sell price"],
    "rto_analysis": ["rto", "return to origin", "return rate", "reverse logistics"],
    "settlement_analysis": ["settlement", "reconciliation", "mismatch", "payout", "payable"],
    "marketplace_growth": ["growth", "meesho", "amazon", "flipkart", "ajio", "myntra"],
}

DEFAULT_INTENT: Literal["sales_analysis"] = "sales_analysis"


class IntentClassifier:
    @staticmethod
    def classify(message: str) -> str:
        text = message.strip().lower()

        for intent, keywords in INTENT_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return intent

        return DEFAULT_INTENT
