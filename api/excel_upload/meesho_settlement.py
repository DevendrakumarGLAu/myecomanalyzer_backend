class MeeshoSettlementPlatform:

    def detect_columns(self, columns):

        col_map = {c.lower(): c for c in columns}

        def find(name):
            for k, v in col_map.items():
                if name in k:
                    return v
            return None

        return {
            "sub_order_id": find("sub order"),
            "transaction_id": find("transaction"),
            "payment_date": find("payment date"),
            "final_settlement_amount": find("final settlement"),

            "total_sale_amount": find("total sale amount"),
            "total_return_amount": find("return amount"),

            "live_status": find("live order status"),

            "claims": find("claims"),
            "compensation": find("compensation"),
            "recovery": find("recovery"),

            "fixed_fee": find("fixed fee"),
            "warehousing_fee": find("warehousing"),
            "return_premium": find("return premium (incl gst)"),
            "return_premium_return": find("return premium (incl gst) of return"),

            "gst_percent": find("product gst"),
        }