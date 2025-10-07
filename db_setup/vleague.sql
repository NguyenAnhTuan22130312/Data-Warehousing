-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Oct 07, 2025 at 06:13 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `vleague`
--

-- --------------------------------------------------------

--
-- Table structure for table `etl_log`
--

CREATE TABLE `etl_log` (
  `log_id` int(11) NOT NULL,
  `process_name` varchar(50) NOT NULL,
  `data_date` date NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT NULL,
  `status` varchar(10) NOT NULL,
  `records_processed` int(11) DEFAULT 0,
  `error_message` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RAW_MATCH_RESULT_STAGING`
--

CREATE TABLE `RAW_MATCH_RESULT_STAGING` (
  `match_id` varchar(50) NOT NULL,
  `date_time` datetime DEFAULT NULL,
  `round_id` int(11) DEFAULT NULL,
  `round_name` varchar(50) DEFAULT NULL,
  `home_team` varchar(100) DEFAULT NULL,
  `away_team` varchar(100) DEFAULT NULL,
  `ft_home_goals` int(11) DEFAULT NULL,
  `ft_away_goals` int(11) DEFAULT NULL,
  `status_name` varchar(50) DEFAULT NULL,
  `home_yellow` int(11) DEFAULT NULL,
  `home_red` int(11) DEFAULT NULL,
  `extract_date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `staging_vleague_raw`
--

CREATE TABLE `staging_vleague_raw` (
  `raw_id` int(11) NOT NULL,
  `match_id` varchar(50) NOT NULL,
  `raw_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`raw_data`)),
  `extract_time` timestamp NOT NULL DEFAULT current_timestamp(),
  `source_file` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `vleague_cleansed`
--

CREATE TABLE `vleague_cleansed` (
  `match_id` varchar(50) NOT NULL,
  `date_time` datetime NOT NULL,
  `round_id` int(11) DEFAULT NULL,
  `round_name` varchar(100) DEFAULT NULL,
  `round_alias` varchar(100) DEFAULT NULL,
  `home_team` varchar(100) DEFAULT NULL,
  `away_team` varchar(100) DEFAULT NULL,
  `ht_home_goals` int(11) DEFAULT NULL,
  `ht_away_goals` int(11) DEFAULT NULL,
  `ft_home_goals` int(11) DEFAULT NULL,
  `ft_away_goals` int(11) DEFAULT NULL,
  `status_id` int(11) DEFAULT NULL,
  `status_name` varchar(50) DEFAULT NULL,
  `home_yellow` int(11) DEFAULT NULL,
  `home_red` int(11) DEFAULT NULL,
  `away_yellow` int(11) DEFAULT NULL,
  `away_red` int(11) DEFAULT NULL,
  `last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `etl_log`
--
ALTER TABLE `etl_log`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `idx_log_data_date` (`data_date`);

--
-- Indexes for table `RAW_MATCH_RESULT_STAGING`
--
ALTER TABLE `RAW_MATCH_RESULT_STAGING`
  ADD PRIMARY KEY (`match_id`,`extract_date`);

--
-- Indexes for table `staging_vleague_raw`
--
ALTER TABLE `staging_vleague_raw`
  ADD PRIMARY KEY (`raw_id`),
  ADD KEY `idx_staging_match_id` (`match_id`);

--
-- Indexes for table `vleague_cleansed`
--
ALTER TABLE `vleague_cleansed`
  ADD PRIMARY KEY (`match_id`),
  ADD KEY `idx_cleansed_datetime` (`date_time`),
  ADD KEY `idx_cleansed_round` (`round_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `etl_log`
--
ALTER TABLE `etl_log`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `staging_vleague_raw`
--
ALTER TABLE `staging_vleague_raw`
  MODIFY `raw_id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
