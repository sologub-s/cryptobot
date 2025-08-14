INSERT INTO `cron_jobs` (`id`, `created_at`, `updated_at`, `execution_interval_seconds`, `last_executed_at`, `name`) VALUES
(13,	1753670530845,	1755135062896,	14400,	1755135052173,	'notify-working'),
(14,	1753670530979,	1755139442868,	180,	1755139431853,	'check-balance-from-binance'),
(15,	1754192534801,	1755139443118,	60,	1755139431853,	'do-orders-updating-routine'),
(16,	1754533241286,	1755139382337,	300,	1755139371544,	'update-trades-for-partially-filled-orders');