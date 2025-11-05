/*
 Navicat Premium Dump SQL

 Source Server         : localhost
 Source Server Type    : MariaDB
 Source Server Version : 100432 (10.4.32-MariaDB)
 Source Host           : localhost:3306
 Source Schema         : controlmanagementdb

 Target Server Type    : MariaDB
 Target Server Version : 100432 (10.4.32-MariaDB)
 File Encoding         : 65001

 Date: 30/10/2025 23:12:09
*/

create database Performance_Staging;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for configuration
-- ----------------------------
DROP TABLE IF EXISTS `configuration`;
CREATE TABLE `configuration`  (
  `Config_ID` int(11) NOT NULL AUTO_INCREMENT,
  `Config_Key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `Config_Value` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `Config_Type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `Description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `Environment` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'PROD',
  `Is_Active` tinyint(1) NULL DEFAULT 1,
  `Created_At` datetime NULL DEFAULT current_timestamp(),
  `Updated_At` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`Config_ID`) USING BTREE,
  UNIQUE INDEX `uq_config`(`Config_Key`, `Environment`) USING BTREE,
  INDEX `idx_active`(`Is_Active`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'Cấu hình hệ thống ETL' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of configuration
-- ----------------------------
INSERT INTO `configuration` VALUES (1, 'DATA_DATE', '2025-10-30', 'ETL', 'Ngày dữ liệu được load', 'PROD', 1, '2025-10-30 18:10:42', '2025-10-30 18:10:46');

-- ----------------------------
-- Table structure for datasource
-- ----------------------------
DROP TABLE IF EXISTS `datasource`;
CREATE TABLE `datasource`  (
  `Source_ID` int(11) NOT NULL AUTO_INCREMENT,
  `Source_Name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `Source_Type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'API',
  `Base_URL` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `Endpoint` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `HTTP_Method` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'GET',
  `Auth_Type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'API_KEY',
  `API_Key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `Params` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL CHECK (json_valid(`Params`)),
  `Description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `Is_Active` tinyint(1) NULL DEFAULT 1,
  `Created_At` datetime NULL DEFAULT current_timestamp(),
  `Updated_At` datetime NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`Source_ID`) USING BTREE,
  UNIQUE INDEX `Source_Name`(`Source_Name`) USING BTREE,
  INDEX `idx_active`(`Is_Active`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'Thông tin nguồn dữ liệu (API)' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of datasource
-- ----------------------------
INSERT INTO `datasource` VALUES (1, 'PLAYER_API', 'API', 'https://api.fstats.ai', '/fbs/api/public/league/top5-player-by-everything', 'GET', 'API_KEY', NULL, '{\"leagueId\": 28, \"limit\": 10}', 'Nguồn dữ liệu cầu thủ', 1, '2025-10-30 18:12:45', '2025-10-30 20:22:49');
INSERT INTO `datasource` VALUES (2, 'OVERVIEW_PLAYER_API', 'API', 'https://api.fstats.ai', '/fbs/api/public/player/overview', 'GET', 'API_KEY', NULL, '{\"leagueId\": 28, \"playerId\": null}', 'Nguồn dữ liệu thông tin chi tiết cầu thủ', 1, '2025-10-30 18:12:52', '2025-10-30 18:15:40');
INSERT INTO `datasource` VALUES (3, 'PERFORMANCE_PLAYER_APY', 'API', 'https://api.fstats.ai', '/fbs/api/public/player/performance', 'GET', 'API_KEY', NULL, '{\"leagueId\": 28, \"playerId\": null}', 'Nguồn dữ liệu chỉ số hiệu suất cá nhân', 1, '2025-10-30 18:16:30', '2025-10-30 18:17:19');

-- ----------------------------
-- Table structure for log_history
-- ----------------------------
DROP TABLE IF EXISTS `log_history`;
CREATE TABLE `log_history`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `job_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Tên job ETL (extract, transform, load)',
  `source_id` int(11) NULL DEFAULT NULL COMMENT 'Nguồn dữ liệu (FK -> DataSource.Source_ID)',
  `start_time` datetime NOT NULL COMMENT 'Thời gian bắt đầu chạy',
  `end_time` datetime NULL DEFAULT NULL COMMENT 'Thời gian kết thúc chạy',
  `duration_seconds` int(11) GENERATED ALWAYS AS (timestampdiff(SECOND,`start_time`,`end_time`)) PERSISTENT COMMENT 'Thời gian chạy (giây)',
  `status` enum('SUCCESS','FAILED','RUNNING') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Trạng thái job',
  `records_processed` int(11) NULL DEFAULT 0 COMMENT 'Số bản ghi đã xử lý',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Thông báo lỗi (nếu có)',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp() COMMENT 'Thời điểm tạo log',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE CURRENT_TIMESTAMP COMMENT 'Thời điểm cập nhật log',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `source_id`(`source_id`) USING BTREE,
  CONSTRAINT `log_history_ibfk_1` FOREIGN KEY (`source_id`) REFERENCES `datasource` (`Source_ID`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'Lịch sử chạy ETL' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of log_history
-- ----------------------------
INSERT INTO `log_history` VALUES (1, 'extract_player_stats', 1, '2025-10-30 18:36:08', '2025-10-30 18:38:08', DEFAULT, 'SUCCESS', 75, NULL, '2025-10-30 18:38:08', '2025-10-30 18:38:08');
INSERT INTO `log_history` VALUES (2, 'ETL_Player_Data', NULL, '2025-10-30 19:30:15', '2025-10-30 19:30:15', DEFAULT, 'FAILED', 0, 'Extract.py trả về mã lỗi khác 0 (có thể lỗi trong quá trình lấy dữ liệu).', '2025-10-30 19:30:15', '2025-10-30 19:30:15');
INSERT INTO `log_history` VALUES (4, 'ETL_Player_Data', NULL, '2025-10-30 20:23:47', '2025-10-30 20:23:47', DEFAULT, 'FAILED', 0, 'Extract.py trả về mã lỗi khác 0 (có thể lỗi trong quá trình lấy dữ liệu).', '2025-10-30 20:23:47', '2025-10-30 20:23:47');
INSERT INTO `log_history` VALUES (5, 'ETL_Player_Data', NULL, '2025-10-30 20:25:38', NULL, DEFAULT, 'RUNNING', 0, NULL, '2025-10-30 20:25:38', '2025-10-30 20:25:38');
INSERT INTO `log_history` VALUES (6, 'ETL_Player_Data', NULL, '2025-10-30 20:34:58', '2025-10-30 20:36:51', DEFAULT, 'SUCCESS', 0, NULL, '2025-10-30 20:34:58', '2025-10-30 20:36:51');
INSERT INTO `log_history` VALUES (7, 'ETL_Player_Data', NULL, '2025-10-30 20:51:46', '2025-10-30 20:54:00', DEFAULT, 'SUCCESS', 0, NULL, '2025-10-30 20:51:46', '2025-10-30 20:54:00');
INSERT INTO `log_history` VALUES (8, 'extract_player_stats', 1, '2025-10-30 20:52:00', '2025-10-30 20:54:00', DEFAULT, 'SUCCESS', 150, NULL, '2025-10-30 20:54:00', '2025-10-30 20:54:00');
INSERT INTO `log_history` VALUES (9, 'ETL_Player_Data', NULL, '2025-10-30 23:01:15', '2025-10-30 23:01:16', DEFAULT, 'SUCCESS', 0, NULL, '2025-10-30 23:01:15', '2025-10-30 23:01:16');
INSERT INTO `log_history` VALUES (10, 'ETL_Player_Data', NULL, '2025-10-30 23:02:15', '2025-10-30 23:02:16', DEFAULT, 'SUCCESS', 0, NULL, '2025-10-30 23:02:15', '2025-10-30 23:02:16');
INSERT INTO `log_history` VALUES (11, 'ETL_Player_Data', NULL, '2025-10-30 23:04:01', '2025-10-30 23:04:02', DEFAULT, 'SUCCESS', 0, NULL, '2025-10-30 23:04:01', '2025-10-30 23:04:02');
INSERT INTO `log_history` VALUES (12, 'ETL_Player_Data', NULL, '2025-10-30 23:06:36', '2025-10-30 23:06:37', DEFAULT, 'SUCCESS', 0, NULL, '2025-10-30 23:06:36', '2025-10-30 23:06:37');
INSERT INTO `log_history` VALUES (13, 'ETL_Player_Data', NULL, '2025-10-30 23:08:01', '2025-10-30 23:09:47', DEFAULT, 'SUCCESS', 0, NULL, '2025-10-30 23:08:01', '2025-10-30 23:09:47');
INSERT INTO `log_history` VALUES (14, 'extract_player_stats', 1, '2025-10-30 23:07:47', '2025-10-30 23:09:47', DEFAULT, 'SUCCESS', 150, NULL, '2025-10-30 23:09:47', '2025-10-30 23:09:47');

SET FOREIGN_KEY_CHECKS = 1;
