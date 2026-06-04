from typing import Literal

INTENT_KEYWORDS = {
    "dispatch_analysis": [ "dispatch","dispatched", "shipped","shipment", "pending dispatch"],
    "profit_analysis": ["profit", "margin", "revenue", "loss", "earning"],
    "sales_analysis": ["sales", "revenue", "sales growth", "sales trend", "sales performance"],
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
        text = message.lower()

        # High priority intents

        if any(word in text for word in [
            "dispatch",
            "dispatched",
            "shipment",
            "shipped"
        ]):
            return "dispatch_analysis"

        for intent, keywords in INTENT_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return intent

        return DEFAULT_INTENT
