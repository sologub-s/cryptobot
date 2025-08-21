def get_mock_asset_transfers() -> dict[str, dict[str, int]]:
    return {
        'CMFUTURE_MAIN': {'total': 0},
        'FUNDING_MAIN': {'total': 0},
        'MAIN_CMFUTURE': {'total': 0},
        'MAIN_FUNDING': {'total': 0},
        'MAIN_MARGIN': {'total': 0},
        'MAIN_MINING': {'total': 0},
        'MAIN_UMFUTURE': {'total': 0},
        'MARGIN_MAIN': {'total': 0},
        'MINING_MAIN': {'total': 0},
        'UMFUTURE_MAIN': {'total': 0},
    }