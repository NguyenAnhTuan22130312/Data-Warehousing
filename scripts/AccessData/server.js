const express = require('express');
const cors = require('cors');
const { getConnection } = require('./db');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

// API lấy Top Players (top_player_ranking_mart)
app.get('/api/top_players', async (req, res) => {
    try {
        const conn = await getConnection();
        const [rows] = await conn.execute(`
            SELECT player_name AS name, team_name AS team, metric_type AS metric, 
                   metric_value AS value, rating, api_date, month_name
            FROM top_player_ranking_mart
            ORDER BY metric_value DESC
            LIMIT 10
        `);
        await conn.end();
        res.json(rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Không thể lấy dữ liệu Top Players' });
    }
});

// API lấy tất cả Player Performance (player_performance_agg_mart)
app.get('/api/player_performance', async (req, res) => {
    try {
        const conn = await getConnection();
        const [rows] = await conn.execute(`
            SELECT player_name AS name, team_name AS team, position, 
                   height_cm AS height, weight_kg AS weight,
                   metric_type AS metric, metric_value AS value, rating,
                   CASE WHEN rating>0 THEN 'Active' ELSE 'Inactive' END AS status
            FROM player_performance_agg_mart
            LIMIT 500
        `);
        await conn.end();
        res.json(rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Không thể lấy dữ liệu Player Performance' });
    }
});

// Khởi chạy server
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
