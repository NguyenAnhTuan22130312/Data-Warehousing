/*
 Navicat Premium Dump SQL

 Source Server         : localhost
 Source Server Type    : MariaDB
 Source Server Version : 100432 (10.4.32-MariaDB)
 Source Host           : localhost:3306
 Source Schema         : warehousedb

 Target Server Type    : MariaDB
 Target Server Version : 100432 (10.4.32-MariaDB)
 File Encoding         : 65001

 Date: 03/11/2025 00:59:16
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for dim_date
-- ----------------------------
DROP TABLE IF EXISTS `dim_date`;
CREATE TABLE `dim_date`  (
  `date_key` char(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `api_date` date NOT NULL,
  `full_date` date NULL DEFAULT NULL,
  `year` smallint(6) NULL DEFAULT NULL,
  `quarter` tinyint(4) NULL DEFAULT NULL,
  `month` tinyint(4) NULL DEFAULT NULL,
  `day` tinyint(4) NULL DEFAULT NULL,
  `day_of_week` tinyint(4) NULL DEFAULT NULL,
  `day_name` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `month_name` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `is_weekend` tinyint(1) NULL DEFAULT NULL,
  `load_batch` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`date_key`) USING BTREE,
  UNIQUE INDEX `uq_api_date`(`api_date`) USING BTREE,
  INDEX `idx_load_batch`(`load_batch`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of dim_date
-- ----------------------------

-- ----------------------------
-- Table structure for dim_player
-- ----------------------------
DROP TABLE IF EXISTS `dim_player`;
CREATE TABLE `dim_player`  (
  `player_key` int(11) NOT NULL AUTO_INCREMENT,
  `player_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `player_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `team_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `team_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `nationality` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `position` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `age` int(11) NULL DEFAULT NULL,
  `height_cm` decimal(6, 2) NULL DEFAULT NULL,
  `weight_kg` decimal(6, 2) NULL DEFAULT NULL,
  `dominant_foot` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `is_current` tinyint(1) NULL DEFAULT 1,
  `effective_from` datetime NULL DEFAULT current_timestamp(),
  `effective_to` datetime NULL DEFAULT NULL,
  `load_batch` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`player_key`) USING BTREE,
  UNIQUE INDEX `uq_player_id`(`player_id`) USING BTREE,
  INDEX `idx_team_id`(`team_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of dim_player
-- ----------------------------

-- ----------------------------
-- Table structure for fact_performance
-- ----------------------------
DROP TABLE IF EXISTS `fact_performance`;
CREATE TABLE `fact_performance`  (
  `fact_key` int(11) NOT NULL AUTO_INCREMENT,
  `player_key` int(11) NOT NULL,
  `date_key` char(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `metric_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `metric_value` decimal(10, 2) NULL DEFAULT NULL,
  `duelWon` int(11) NULL DEFAULT NULL,
  `passSuccess` decimal(6, 2) NULL DEFAULT NULL,
  `assist` int(11) NULL DEFAULT NULL,
  `shotOnTarget` int(11) NULL DEFAULT NULL,
  `rating` decimal(6, 2) NULL DEFAULT NULL,
  `source_id` int(11) NULL DEFAULT NULL,
  `load_batch` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`fact_key`) USING BTREE,
  INDEX `idx_player_key`(`player_key`) USING BTREE,
  INDEX `idx_date_key`(`date_key`) USING BTREE,
  INDEX `idx_metric_type`(`metric_type`) USING BTREE,
  CONSTRAINT `fk_fact_date` FOREIGN KEY (`date_key`) REFERENCES `dim_date` (`date_key`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_fact_player` FOREIGN KEY (`player_key`) REFERENCES `dim_player` (`player_key`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of fact_performance
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
