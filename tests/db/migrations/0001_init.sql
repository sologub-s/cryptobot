#SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

SET NAMES utf8mb4;

CREATE TABLE `balances` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `created_at` bigint(20) NOT NULL,
  `updated_at` bigint(20) DEFAULT NULL,
  `checked_at` bigint(20) NOT NULL,
  `asset` tinyint(3) unsigned NOT NULL,
  `free` decimal(18,8) unsigned NOT NULL,
  `locked` decimal(18,8) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `cron_jobs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `created_at` bigint(20) unsigned NOT NULL,
  `updated_at` bigint(20) unsigned DEFAULT NULL,
  `execution_interval_seconds` bigint(20) unsigned NOT NULL DEFAULT 0,
  `last_executed_at` bigint(20) unsigned DEFAULT NULL,
  `name` char(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `orders` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `binance_order_id` bigint(20) unsigned NOT NULL,
  `client_order_id` char(40) DEFAULT NULL,
  `binance_order_type` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `created_at` bigint(20) unsigned NOT NULL,
  `updated_at` bigint(20) unsigned DEFAULT NULL,
  `binance_created_at` bigint(20) unsigned DEFAULT NULL,
  `binance_updated_at` bigint(20) unsigned DEFAULT NULL,
  `symbol` bigint(20) unsigned NOT NULL DEFAULT 0,
  `side` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `order_price` decimal(18,8) unsigned NOT NULL,
  `delta_up` decimal(18,2) unsigned DEFAULT NULL,
  `delta_down` decimal(18,2) unsigned DEFAULT NULL,
  `original_quantity` decimal(18,8) unsigned NOT NULL,
  `executed_quantity` decimal(18,8) unsigned NOT NULL,
  `cummulative_quote_quantity` decimal(18,8) unsigned NOT NULL,
  `status` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `created_by_bot` tinyint(1) unsigned NOT NULL DEFAULT 0,
  `trades_checked` tinyint(1) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `binance_order_id` (`binance_order_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `orders_filling_history` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` bigint(20) unsigned NOT NULL,
  `updated_at` bigint(20) unsigned DEFAULT NULL,
  `logged_at` bigint(20) unsigned DEFAULT NULL,
  `order_id` bigint(20) NOT NULL,
  `status` tinyint(3) unsigned DEFAULT 0,
  `original_quantity` decimal(18,8) NOT NULL,
  `executed_quantity` decimal(18,8) NOT NULL,
  `cummulative_quote_quantity` decimal(18,8) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `order_trades` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `created_at` bigint(20) unsigned NOT NULL,
  `updated_at` bigint(20) unsigned DEFAULT NULL,
  `binance_id` bigint(20) unsigned NOT NULL,
  `order_id` bigint(20) unsigned NOT NULL,
  `binance_order_id` bigint(20) unsigned NOT NULL,
  `symbol` bigint(20) unsigned NOT NULL DEFAULT 0,
  `order_list_id` bigint(20) NOT NULL DEFAULT -1,
  `price` decimal(18,8) unsigned NOT NULL,
  `quantity` decimal(18,8) unsigned NOT NULL,
  `quote_quantity` decimal(18,8) unsigned NOT NULL,
  `commission` decimal(18,8) unsigned NOT NULL,
  `commission_asset_char` char(10) NOT NULL,
  `binance_time` bigint(20) unsigned NOT NULL,
  `is_buyer` tinyint(1) unsigned NOT NULL,
  `is_maker` tinyint(1) unsigned NOT NULL,
  `is_best_match` tinyint(1) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `binance_id` (`binance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `settings` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` bigint(20) NOT NULL,
  `updated_at` bigint(20) DEFAULT NULL,
  `the_key` char(40) NOT NULL,
  `the_value` longtext NOT NULL,
  `the_type` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `the_key` (`the_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
