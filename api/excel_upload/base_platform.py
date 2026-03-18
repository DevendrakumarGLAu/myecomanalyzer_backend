# api/excel_upload/base_platform.py

class BaseSettlementPlatform:

    COLUMN_MAP = {}

    def detect_columns(self, df_columns):
        detected = {}
        normalized = [c.strip().lower() for c in df_columns]

        for field, possibilities in self.COLUMN_MAP.items():
            detected[field] = None

            for col in possibilities:
                if col.lower() in normalized:
                    detected[field] = df_columns[normalized.index(col.lower())]
                    break

        return detected