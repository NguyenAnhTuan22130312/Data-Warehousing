/*
 Navicat Premium Dump SQL

 Source Server         : localhost
 Source Server Type    : MariaDB
 Source Server Version : 100432 (10.4.32-MariaDB)
 Source Host           : localhost:3306
 Source Schema         : player_performance_mart

 Target Server Type    : MariaDB
 Target Server Version : 100432 (10.4.32-MariaDB)
 File Encoding         : 65001

 Date: 03/11/2025 01:25:28
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for player_performance_agg_mart
-- ----------------------------
DROP TABLE IF EXISTS `player_performance_agg_mart`;
CREATE TABLE `player_performance_agg_mart`  (
  `player_key` int(11) NOT NULL,
  `player_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `player_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `team_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `team_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `nationality` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `position` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `age` int(11) NULL DEFAULT NULL,
  `height_cm` decimal(6, 2) NULL DEFAULT NULL,
  `weight_kg` decimal(6, 2) NULL DEFAULT NULL,
  `dominant_foot` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `date_key` char(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `api_date` date NOT NULL,
  `year` smallint(6) NOT NULL,
  `quarter` tinyint(4) NOT NULL,
  `month` tinyint(4) NOT NULL,
  `month_name` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `metric_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `metric_value` decimal(10, 2) NULL DEFAULT NULL,
  `duelWon` int(11) NULL DEFAULT NULL,
  `passSuccess` decimal(6, 2) NULL DEFAULT NULL,
  `assist` int(11) NULL DEFAULT NULL,
  `shotOnTarget` int(11) NULL DEFAULT NULL,
  `rating` decimal(6, 2) NULL DEFAULT NULL,
  `goals` decimal(10, 2) NULL DEFAULT NULL,
  `total_duels` int(11) NULL DEFAULT NULL,
  `pass_accuracy_pct` decimal(5, 2) NULL DEFAULT NULL,
  `load_batch` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`player_key`, `date_key`, `metric_type`) USING BTREE,
  INDEX `idx_player_name`(`player_name`) USING BTREE,
  INDEX `idx_team_name`(`team_name`) USING BTREE,
  INDEX `idx_date`(`api_date`) USING BTREE,
  INDEX `idx_metric`(`metric_type`) USING BTREE,
  INDEX `idx_rating`(`rating`) USING BTREE,
  INDEX `idx_goals`(`goals`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of player_performance_agg_mart
-- ----------------------------

-- ----------------------------
-- Table structure for top_player_ranking_mart
-- ----------------------------
DROP TABLE IF EXISTS `top_player_ranking_mart`;
CREATE TABLE `top_player_ranking_mart`  (
  `ranking` int(11) NOT NULL AUTO_INCREMENT,
  `player_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `team_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `metric_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `metric_value` decimal(10, 2) NULL DEFAULT NULL,
  `rating` decimal(6, 2) NULL DEFAULT NULL,
  `api_date` date NULL DEFAULT NULL,
  `month_name` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `load_batch` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`ranking`) USING BTREE,
  INDEX `idx_metric`(`metric_value`) USING BTREE,
  INDEX `idx_rating`(`rating`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of top_player_ranking_mart
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
