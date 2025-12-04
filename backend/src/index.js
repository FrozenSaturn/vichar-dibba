const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.get('/', (req, res) => {
    res.send('IdeaBrowser Core API is running 🚀');
});

// The Core Analysis Endpoint
app.post('/api/analyze', (req, res) => {
    const { idea, industry, city } = req.body;

    if (!idea || !industry || !city) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    console.log(`🧠 Analyzing: "${idea}" in ${industry}, ${city}...`);

    // Define path to Python script
    // Note: adjusting path to go UP to root, then DOWN to ml-engine
    const scriptPath = path.join(__dirname, '../../ml-engine/src/predict.py');
    const pythonPath = path.join(__dirname, '../../ml-engine/.venv/bin/python');

    // Spawn Python Process
    const pythonProcess = spawn(pythonPath, [scriptPath, idea, industry, city]);

    let dataString = '';

    // Listen for data from Python
    pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
    });

    // Handle Errors
    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });

    // When Python script finishes
    pythonProcess.on('close', (code) => {
        try {
            const result = JSON.parse(dataString);
            res.json(result);
        } catch (error) {
            console.error("Failed to parse Python response:", dataString);
            res.status(500).json({ error: 'Analysis failed', raw: dataString });
        }
    });
});

// Start Server
app.listen(PORT, () => {
    console.log(`✅ Server running on http://localhost:${PORT}`);
});