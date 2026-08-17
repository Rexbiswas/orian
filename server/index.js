import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import axios from 'axios';
import bodyParser from 'body-parser';
import multer from 'multer';
import FormData from 'form-data';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

app.use(cors());
app.use(bodyParser.json());

// Setup Multer for memory storage (handling webcam frames)
const upload = multer({ storage: multer.memoryStorage() });

const ELEVENLABS_API_KEY = process.env.VITE_ELEVENLABS_API_KEY;

// --- HUMAN SENSES: VISION & EMOTION (Proxy to Python) ---
app.post('/api/sense/analyze', upload.single('frame'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No frame provided' });
    }

    const formData = new FormData();
    formData.append('file', req.file.buffer, {
      filename: 'frame.jpg',
      contentType: 'image/jpeg',
    });

    const response = await axios.post(`${PYTHON_BACKEND_URL}/api/sense/process`, formData, {
      headers: {
        ...formData.getHeaders(),
      },
    });

    res.json(response.data);
  } catch (error) {
    console.error('Sensing Error:', error.message);
    res.status(500).json({ 
      error: 'Intelligence Core Link Failure',
      details: error.response?.data || error.message 
    });
  }
});

// --- VOICE ENGINE (Simplified) ---
app.post('/api/voice/speak', async (req, res) => {
  const { text, voiceId, settings } = req.body;
  
  try {
    const response = await axios({
      method: 'post',
      url: `https://api.elevenlabs.io/v1/text-to-speech/${voiceId || 'D38z5RcWu1voky8WS1ja'}`,
      data: {
        text,
        model_id: 'eleven_flash_v2',
        voice_settings: settings || { stability: 0.5, similarity_boost: 0.75 },
      },
      headers: {
        'xi-api-key': ELEVENLABS_API_KEY,
        'Content-Type': 'application/json',
      },
      responseType: 'arraybuffer',
    });

    res.set('Content-Type', 'audio/mpeg');
    res.send(response.data);
  } catch (error) {
    const errDetail = Buffer.isBuffer(error.response?.data) 
      ? error.response.data.toString('utf-8') 
      : (error.response?.data || error.message);
    console.error('ElevenLabs Error:', errDetail);
    res.status(error.response?.status || 500).json({ error: 'Failed to generate voice', details: errDetail });
  }
});

// --- SYSTEM COMMANDS (Direct Execution) ---
// 1. Open VS Code
app.post('/api/commands/open-code', (req, res) => {
  try {
    // Use 'code' if 'code-insiders' is not found
    const { exec } = require('child_process');
    exec('code-insiders .', (error, stdout, stderr) => {
      if (error && error.code !== 127) {
        console.error(`Code Open Error: ${error.message}`);
        return res.status(500).json({ error: 'Failed to open IDE', details: error.message });
      }
      res.json({ success: true, message: 'Code opened' });
    });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// 2. Close IDE
app.post('/api/commands/close-code', (req, res) => {
  try {
    const { exec } = require('child_process');
    // Kill process by name
    exec('taskkill /F /IM "code-insiders.exe" /T', (error, stdout, stderr) => {
      if (error) {
         exec('taskkill /F /IM "Code.exe" /T', (error2, stdout2, stderr2) => {
             if (error2 && error2.code !== 128) {
                return res.status(500).json({ error: 'Failed to close IDE', details: error2.message });
             }
             res.json({ success: true, message: 'IDE closed' });
         });
         return;
      }
      res.json({ success: true, message: 'IDE closed' });
    });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// 3. Restart AI Core
app.post('/api/commands/restart-core', (req, res) => {
  try {
    const { exec } = require('child_process');
    exec('python main.py', { cwd: '../backend' }, (error, stdout, stderr) => {
      if (error) {
        return res.status(500).json({ error: 'Failed to restart', details: error.message });
      }
      res.json({ success: true, message: 'Core restarting...' });
    });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// 4.Shutdown AI
app.post('/api/commands/shutdown', (req, res) => {
  try {
    const { exec } = require('child_process');
    // Use native shutdown command
    exec('shutdown /s /t 1', (error, stdout, stderr) => {
      if (error) {
        return res.status(500).json({ error: 'Failed to shutdown', details: error.message });
      }
      res.json({ success: true, message: 'Shutting down...' });
    });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

app.listen(PORT, () => {
  console.log(`OrionAI Server running on port ${PORT}`);
});
