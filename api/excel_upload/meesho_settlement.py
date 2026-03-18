# payments/platforms/meesho_settlement.py

from .base_platform import BaseSettlementPlatform


class MeeshoSettlementPlatform(BaseSettlementPlatform):

    COLUMN_MAP = {
        "sub_order_id": [
            "Sub Order No"
        ],
        "transaction_id": [
            "Transaction ID"
        ],
        "payment_date": [
            "Payment Date"
        ],
        "final_settlement_amount": [
            "Final Settlement Amount"
        ],
        "total_sale_amount": [
            "Total Sale Amount (Incl. Shipping & GST)"
        ],
        "total_return_amount": [
            "Total Sale Return Amount (Incl. Shipping & GST)"
        ],
        "fixed_fee": [
            "Fixed Fee (Incl. GST)"
        ],
        "warehousing_fee": [
            "Warehousing fee (inc Gst)"
        ],
        "return_premium": [
            "Return premium (incl GST)"
        ],
        "return_premium_return": [
            "Return premium (incl GST) of Return"
        ],
        "gst_percent": [
            "Product GST %"
        ]
    }