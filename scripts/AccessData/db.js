const mysql = require('mysql2/promise');
const fs = require('fs');
const ini = require('ini');
const path = require('path');

// Đọc config
const configFile = path.join(__dirname, '../../config/config.ini');
const config = ini.parse(fs.readFileSync(configFile, 'utf-8'));

// Lấy config cho Player_Performance_Mart
const dbConfig = config.databasePlayer_Performance_Mart;

async function getConnection() {
    const conn = await mysql.createConnection({
        host: dbConfig.host,
        user: dbConfig.user,
        password: dbConfig.password,
        database: dbConfig.database,
        port: Number(dbConfig.port || 3306)
    });
    return conn;
}

module.exports = { getConnection };
