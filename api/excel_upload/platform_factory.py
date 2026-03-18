# payments/platforms/platform_factory.py





from api.excel_upload.meesho_settlement import MeeshoSettlementPlatform


class SettlementPlatformFactory:

    @staticmethod
    def get_platform(platform_code):

        platform_code = platform_code.lower()

        if platform_code == "meesho":
            return MeeshoSettlementPlatform()

        # future platforms
        if platform_code == "amazon":
            pass

        if platform_code == "flipkart":
            pass

        raise Exception(f"Unsupported platform {platform_code}")