class BalanceMapper:
    # Asset constants
    ASSET_UNKNOWN = 0
    ASSET_USDT = 1
    ASSET_ETH = 2

    asset_mapping: dict[str, int] = {
        'USDT': 1,
        'ETH': 2,
    }

    @classmethod
    def map_asset(cls, asset: str) -> int:
        if not asset:
            return cls.ASSET_UNKNOWN
        asset = asset.upper()
        if asset == "USDT":
            return cls.ASSET_USDT
        if asset == "ETH":
            return cls.ASSET_ETH
        return cls.ASSET_UNKNOWN

    @classmethod
    def get_assets(cls):
        return cls.asset_mapping
