def get_mock_asset_balance() -> dict[str, dict[str, str]]:
    return  {
        'USDT': {
            'asset': 'USDT',
            'free': '0.38976000',
            'locked': '0.00000000',
        },
        'ETH': {
            'asset': 'ETH',
            'free': '0.00007340',
            'locked': '0.01850000',
        },
        'BTC': {
            'asset': 'BTC',
            'free': '0.00000000',
            'locked': '0.00000000',
        },
    }