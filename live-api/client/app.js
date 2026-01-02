/**
 * Gemini Live AI Assistant - Main Application
 * 
 * Handles WebSocket communication, audio streaming, and UI updates.
 */

class LiveAIAssistant {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.audioContext = null;
        this.mediaStream = null;
        this.audioWorklet = null;

        // Metrics
        this.turnCount = 0;
        this.toolCallsCount = 0;
        this.sessionStartTime = null;

        // UI elements
        this.elements = {
            micButton: document.getElementById('micButton'),
            micLabel: document.getElementById('micLabel'),
            statusDot: document.getElementById('statusDot'),
            statusText: document.getElementById('statusText'),
            transcriptContainer: document.getElementById('transcriptContainer'),
            toolsPanel: document.getElementById('toolsPanel'),
            resetBtn: document.getElementById('resetBtn'),
            metricsBtn: document.getElementById('metricsBtn'),
            metricsModal: document.getElementById('metricsModal'),
            closeMetrics: document.getElementById('closeMetrics'),
            waveformCanvas: document.getElementById('waveformCanvas')
        };

        // Waveform visualization
        this.waveformCtx = this.elements.waveformCanvas.getContext('2d');
        this.waveformData = new Array(100).fill(0);

        this.init();
    }

    init() {
        // Enable mic button
        this.elements.micButton.disabled = false;

        // Event listeners
        this.elements.micButton.addEventListener('click', () => this.toggleConnection());
        this.elements.resetBtn.addEventListener('click', () => this.resetSession());
        this.elements.metricsBtn.addEventListener('click', () => this.showMetrics());
        this.elements.closeMetrics.addEventListener('click', () => this.hideMetrics());

        // Start waveform animation
        this.animateWaveform();
    }

    async toggleConnection() {
        if (this.isConnected) {
            await this.disconnect();
        } else {
            await this.connect();
        }
    }

    async connect() {
        try {
            this.updateStatus('connecting', 'Connecting...');
            this.elements.micLabel.textContent = 'Connecting...';

            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });

            // Connect to WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/live`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => this.onWebSocketOpen();
            this.ws.onmessage = (event) => this.onWebSocketMessage(event);
            this.ws.onerror = (error) => this.onWebSocketError(error);
            this.ws.onclose = () => this.onWebSocketClose();

        } catch (error) {
            console.error('Connection error:', error);
            this.addTranscript('system', `Error: ${error.message}`);
            this.updateStatus('disconnected', 'Connection failed');
            this.elements.micLabel.textContent = 'Click to Connect';
        }
    }

    async disconnect() {
        if (this.ws) {
            this.ws.close();
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
        }

        this.isConnected = false;
        this.updateStatus('disconnected', 'Disconnected');
        this.elements.micLabel.textContent = 'Click to Connect';
        this.elements.micButton.classList.remove('active');
        this.elements.resetBtn.disabled = true;
    }

    onWebSocketOpen() {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.sessionStartTime = Date.now();
        this.updateStatus('connected', 'Connected - Speak now!');
        this.elements.micLabel.textContent = 'Listening...';
        this.elements.micButton.classList.add('active');
        this.elements.resetBtn.disabled = false;

        // Start audio capture
        this.startAudioCapture();

        // Clear transcript placeholder
        this.elements.transcriptContainer.innerHTML = '';
    }

    onWebSocketMessage(event) {
        try {
            // Parse JSON if it's a string
            let message;
            if (typeof event.data === 'string') {
                try {
                    message = JSON.parse(event.data);
                } catch (e) {
                    console.error('Failed to parse message as JSON:', event.data);
                    return;
                }
            } else {
                message = event.data;
            }

            console.log('Received:', message.type);

            switch (message.type) {
                case 'connected':
                    console.log('Session connected:', message.session_id);
                    break;

                case 'audio':
                    this.playAudio(message.data);
                    break;

                case 'text':
                    this.addTranscript('assistant', message.text);
                    break;

                case 'tool_call_start':
                    this.handleToolCallStart(message.tools);
                    break;

                case 'tool_result':
                    this.handleToolResult(message.tool, message.result);
                    break;

                case 'interrupted':
                    console.log('Interrupted by user');
                    break;

                case 'turn_complete':
                    this.turnCount = message.turn_number;
                    break;

                case 'state_change':
                    console.log('State changed:', message.state);
                    break;

                case 'error':
                    console.error('Server error:', message.error);
                    this.addTranscript('system', `Error: ${message.error}`);
                    break;
            }
        } catch (error) {
            console.error('Error handling message:', error);
        }
    }

    onWebSocketError(error) {
        console.error('WebSocket error:', error);
        this.addTranscript('system', 'Connection error occurred');
    }

    onWebSocketClose() {
        console.log('WebSocket closed');
        this.disconnect();
    }

    startAudioCapture() {
        const source = this.audioContext.createMediaStreamSource(this.mediaStream);
        const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = (e) => {
            if (!this.isConnected || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
                return;
            }

            const inputData = e.inputBuffer.getChannelData(0);

            // Update waveform
            const rms = Math.sqrt(inputData.reduce((sum, val) => sum + val * val, 0) / inputData.length);
            this.waveformData.push(rms * 100);
            this.waveformData.shift();

            // Convert to 16-bit PCM
            const pcmData = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                const s = Math.max(-1, Math.min(1, inputData[i]));
                pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }

            // Send to server as hex string
            const hexString = Array.from(new Uint8Array(pcmData.buffer))
                .map(b => b.toString(16).padStart(2, '0'))
                .join('');

            this.ws.send(JSON.stringify({
                type: 'audio',
                data: hexString
            }));
        };

        source.connect(processor);
        processor.connect(this.audioContext.destination);
    }

    async playAudio(hexData) {
        try {
            // Convert hex string to bytes
            const bytes = new Uint8Array(hexData.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
            const int16Array = new Int16Array(bytes.buffer);

            // Convert to float32
            const float32Array = new Float32Array(int16Array.length);
            for (let i = 0; i < int16Array.length; i++) {
                float32Array[i] = int16Array[i] / (int16Array[i] < 0 ? 0x8000 : 0x7FFF);
            }

            // Create audio buffer
            const audioBuffer = this.audioContext.createBuffer(1, float32Array.length, 24000);
            audioBuffer.getChannelData(0).set(float32Array);

            // Play audio
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start();

        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }

    handleToolCallStart(tools) {
        tools.forEach(tool => {
            this.toolCallsCount++;

            const toolCard = document.createElement('div');
            toolCard.className = 'tool-card';
            toolCard.id = `tool-${tool.name}-${Date.now()}`;

            const icon = this.getToolIcon(tool.name);

            toolCard.innerHTML = `
                <div class="tool-header">
                    <span class="tool-icon">${icon}</span>
                    <span class="tool-name">${tool.name}</span>
                    <span class="tool-status executing">Executing...</span>
                </div>
                <div class="tool-args">
                    <code>${JSON.stringify(tool.args, null, 2)}</code>
                </div>
            `;

            this.elements.toolsPanel.appendChild(toolCard);
        });
    }

    handleToolResult(toolName, result) {
        // Find the most recent tool card for this tool
        const toolCards = Array.from(document.querySelectorAll('.tool-card'));
        const toolCard = toolCards.reverse().find(card =>
            card.querySelector('.tool-name').textContent === toolName
        );

        if (toolCard) {
            const status = toolCard.querySelector('.tool-status');
            status.textContent = 'Completed';
            status.className = 'tool-status completed';

            const resultDiv = document.createElement('div');
            resultDiv.className = 'tool-result';
            resultDiv.textContent = JSON.stringify(result, null, 2);
            toolCard.appendChild(resultDiv);
        }
    }

    getToolIcon(toolName) {
        const icons = {
            'get_weather': '🌤️',
            'get_forecast': '📅',
            'get_current_time': '🕐',
            'get_time_difference': '⏰',
            'google_search': '🔍'
        };
        return icons[toolName] || '🔧';
    }

    addTranscript(role, text) {
        const message = document.createElement('div');
        message.className = `transcript-message ${role}`;
        message.textContent = text;
        this.elements.transcriptContainer.appendChild(message);
        this.elements.transcriptContainer.scrollTop = this.elements.transcriptContainer.scrollHeight;
    }

    async resetSession() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'reset' }));
            this.elements.transcriptContainer.innerHTML = '';
            this.elements.toolsPanel.innerHTML = '';
            this.turnCount = 0;
            this.toolCallsCount = 0;
            this.sessionStartTime = Date.now();
        }
    }

    updateStatus(status, text) {
        this.elements.statusDot.className = `status-dot ${status}`;
        this.elements.statusText.textContent = text;
    }

    showMetrics() {
        const duration = this.sessionStartTime
            ? Math.floor((Date.now() - this.sessionStartTime) / 1000)
            : 0;

        document.getElementById('turnCount').textContent = this.turnCount;
        document.getElementById('toolCallsCount').textContent = this.toolCallsCount;
        document.getElementById('sessionDuration').textContent = `${duration}s`;
        document.getElementById('sessionState').textContent =
            this.isConnected ? 'Connected' : 'Disconnected';

        this.elements.metricsModal.classList.add('active');
    }

    hideMetrics() {
        this.elements.metricsModal.classList.remove('active');
    }

    animateWaveform() {
        const canvas = this.elements.waveformCanvas;
        const ctx = this.waveformCtx;
        const width = canvas.width;
        const height = canvas.height;

        const draw = () => {
            ctx.clearRect(0, 0, width, height);

            // Draw waveform
            ctx.beginPath();
            ctx.strokeStyle = this.isConnected ? '#00d4ff' : '#667eea';
            ctx.lineWidth = 2;

            const barWidth = width / this.waveformData.length;

            this.waveformData.forEach((value, i) => {
                const x = i * barWidth;
                const barHeight = (value / 100) * (height / 2);
                const y = height / 2;

                ctx.fillStyle = this.isConnected
                    ? `rgba(0, 212, 255, ${0.3 + value / 200})`
                    : `rgba(102, 126, 234, ${0.3 + value / 200})`;

                ctx.fillRect(x, y - barHeight / 2, barWidth - 2, barHeight);
            });

            requestAnimationFrame(draw);
        };

        draw();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new LiveAIAssistant();
});
