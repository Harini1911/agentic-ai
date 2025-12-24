# 🎯 Access Your Live AI Assistant from Your Laptop

## ✅ Best Solution: SSH Port Forwarding (No sudo required!)

Since the firewall is blocking direct access and you don't have sudo, use SSH port forwarding to tunnel the connection.

## 📱 On Your Laptop

### Step 1: Open SSH Tunnel

Open a terminal on your laptop and run:

```bash
ssh -L 8000:localhost:8000 harini@121.242.232.220
```

**What this does:**
- Forwards port 8000 from the remote server to your laptop
- You can now access the server as if it's running locally
- No firewall changes needed!

### Step 2: Open Browser

While keeping the SSH connection open, open your browser and go to:

```
http://localhost:8000
```

### Step 3: Use the App

1. **Click "Connect"**
2. **Allow microphone access** when prompted
3. **Start speaking!**

Your laptop's microphone and speakers will be used! 🎙️

## 🔄 Alternative: Clone to Laptop (Recommended)

If SSH forwarding doesn't work well, clone the repo to your laptop:

```bash
# On your laptop
git clone <your-repo-url>
cd live-api

# Create .env file with your API keys
# (copy from remote server)
cat > .env << EOF
GOOGLE_API_KEY=your_key_here
LAMINAR_PROJECT_API_KEY=your_laminar_key_here
SERVER_HOST=localhost
SERVER_PORT=8000
GEMINI_MODEL=gemini-2.5-flash-native-audio-preview-12-2025
EOF

# Install dependencies
uv sync

# Run the server locally
uv run python3 server/server.py

# Open http://localhost:8000 in browser
```

This way everything runs on your laptop with full audio support!

## 🐍 Python CLI Demos (Best Audio Experience)

For the best experience, use the Python CLI demos directly:

```bash
# On your laptop (after cloning)
uv run python3 examples/basic_audio_demo.py
```

This gives you direct audio interaction without browser limitations!
