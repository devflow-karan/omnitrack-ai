from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import logging
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.websocket import router as ws_router
from app.services.inference import deep_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting OmnitrackAI Server...")
    deep_worker.start()
    yield
    # Shutdown
    logger.info("Shutting down OmnitrackAI Server...")
    deep_worker.stop()

app = FastAPI(title="OmnitrackAI Server", version="1.1.4", lifespan=lifespan)

# Include Routers
app.include_router(ws_router)

# Futuristic HUD UI
@app.get("/")
async def get():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OMNITRACK.SYS</title>
        <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #00f3ff;
                --primary-glow: rgba(0, 243, 255, 0.4);
                --bg-color: #030a16;
                --glass-bg: rgba(3, 10, 22, 0.6);
                --glass-border: rgba(0, 243, 255, 0.2);
                --danger: #ff003c;
            }

            * { box-sizing: border-box; font-family: 'Share Tech Mono', monospace; margin: 0; padding: 0; }

            body {
                background-color: var(--bg-color);
                color: var(--primary);
                min-height: 100vh;
                margin: 0;
                overflow: hidden;
            }

            /* Fullscreen Video Background */
            .video-container {
                position: fixed;
                top: 0; left: 0;
                width: 100vw;
                height: 100vh;
                background: #000;
                z-index: 1;
            }

            video, canvas {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                object-fit: cover; /* Fill screen without stretching */
            }

            video { transform: scaleX(-1); } /* Mirror video */
            canvas { pointer-events: none; } /* Canvas is NOT mirrored so text is readable */

            /* HUD Overlay Layer */
            .hud-layer {
                position: relative;
                z-index: 10;
                width: 100%;
                height: 100vh;
                pointer-events: none;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                padding: 2rem;
            }

            header {
                text-align: center;
                text-shadow: 0 4px 30px var(--primary-glow);
            }

            h1 { 
                font-weight: 400; 
                letter-spacing: 4px; 
                text-transform: uppercase; 
                font-size: 2.5rem;
                text-shadow: 0 0 10px var(--primary);
                margin-top: 1rem;
            }

            .dashboard {
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                width: 100%;
            }

            .stats-panel {
                background: var(--glass-bg);
                backdrop-filter: blur(8px);
                border: 1px solid var(--glass-border);
                border-radius: 8px;
                padding: 1.5rem;
                width: 320px;
                display: flex;
                flex-direction: column;
                gap: 1rem;
                box-shadow: inset 0 0 20px rgba(0, 243, 255, 0.05);
                pointer-events: auto; /* Allow interaction with panel if needed */
            }

            .stats-panel h3 {
                border-bottom: 1px solid var(--glass-border);
                padding-bottom: 0.5rem;
                color: #fff;
                font-weight: 400;
                letter-spacing: 2px;
                text-transform: uppercase;
                text-shadow: 0 0 5px #fff;
            }

            .stat-box {
                background: rgba(0, 243, 255, 0.05);
                border-left: 3px solid var(--primary);
                padding: 1rem;
                transition: transform 0.2s, background 0.2s;
                position: relative;
                overflow: hidden;
            }
            .stat-box:hover { 
                transform: translateX(5px); 
                background: rgba(0, 243, 255, 0.1);
            }
            
            .stat-box p { margin-bottom: 0.5rem; font-size: 0.8rem; color: #88c0d0; text-transform: uppercase; letter-spacing: 1px; }
            .stat-box span { font-size: 1.5rem; font-weight: bold; color: var(--primary); text-shadow: 0 0 8px var(--primary-glow); }

            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(255, 0, 60, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(255, 0, 60, 0); }
                100% { box-shadow: 0 0 0 0 rgba(255, 0, 60, 0); }
            }

            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                background: var(--danger);
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 1.5s infinite;
            }

        </style>
    </head>
    <body>
        <div class="video-container">
            <video id="video" width="640" height="480" autoplay playsinline></video>
            <canvas id="overlay" width="640" height="480"></canvas>
        </div>

        <div class="hud-layer">
            <header>
                <h1>SYS.OMNITRACK.AI // <span style="color:#fff;">HUD</span></h1>
            </header>

            <div class="dashboard">
                <div class="stats-panel">
                    <h3><div class="status-indicator"></div> TELEMETRY</h3>
                    <div class="stat-box">
                        <p>SYSTEM FPS</p>
                        <span id="ui-fps">--</span>
                    </div>
                    <div class="stat-box">
                        <p>SUBJECTS DETECTED</p>
                        <span id="ui-faces">0</span>
                    </div>
                    <div class="stat-box" id="ui-subjects-list-box" style="padding: 0; background: transparent; border: none; box-shadow: none;">
                        <p style="margin-bottom: 8px;">SUBJECT DETAILS</p>
                        <div id="ui-subjects-list" style="display: flex; flex-direction: column; gap: 8px;">
                            <!-- Injected via JS -->
                        </div>
                    </div>
                </div>
                <div class="stats-panel">
                    <h3>GESTURES & EMOTION</h3>
                    <div class="stat-box" id="ui-emotion-box">
                        <p>EMOTION</p>
                        <span id="ui-emotion">😐 NEUTRAL</span>
                    </div>
                    <div class="stat-box" id="ui-left-box">
                        <p>L-HAND GESTURE</p>
                        <span id="ui-left-hand">NONE</span>
                    </div>
                    <div class="stat-box" id="ui-right-box">
                        <p>R-HAND GESTURE</p>
                        <span id="ui-right-hand">NONE</span>
                    </div>
                    <div class="stat-box" id="ui-shape-box">
                        <p>TWO-HAND SHAPE</p>
                        <span id="ui-two-hand-shape">NONE</span>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('overlay');
            const ctx = canvas.getContext('2d');
            
            const uiFps = document.getElementById('ui-fps');
            const uiFaces = document.getElementById('ui-faces');
            const uiLeftHand = document.getElementById('ui-left-hand');
            const uiRightHand = document.getElementById('ui-right-hand');
            const uiTwoHandShape = document.getElementById('ui-two-hand-shape');
            const uiEmotion = document.getElementById('ui-emotion');
            const uiSubjectsList = document.getElementById('ui-subjects-list');

            let ws;
            let drawingPaths = [];
            let currentStrokes = { 'Left': [], 'Right': [] };
            const hiddenCanvas = document.createElement('canvas');
            hiddenCanvas.width = 640;
            hiddenCanvas.height = 480;
            const hiddenCtx = hiddenCanvas.getContext('2d');

            navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
                .then(stream => { video.srcObject = stream; })
                .catch(err => console.error("Camera access denied:", err));

            function connectWebSocket() {
                const ws_url = window.location.protocol === 'https:' ? 'wss' : 'ws';
                ws = new WebSocket(`${ws_url}://${window.location.host}/ws/process`);
                
                ws.onopen = () => { console.log("WebSocket connected"); sendFrame(); };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    drawOverlay(data);
                    requestAnimationFrame(sendFrame);
                };
                
                ws.onclose = () => { setTimeout(connectWebSocket, 1000); };
            }

            function sendFrame() {
                if (ws.readyState !== WebSocket.OPEN) return;
                
                // Ensure canvases match the actual camera resolution to fix alignment/tracking offset
                if (video.videoWidth && video.videoHeight) {
                    if (hiddenCanvas.width !== video.videoWidth) {
                        hiddenCanvas.width = video.videoWidth;
                        hiddenCanvas.height = video.videoHeight;
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                    }
                }
                
                hiddenCtx.drawImage(video, 0, 0, hiddenCanvas.width, hiddenCanvas.height);
                const base64Data = hiddenCanvas.toDataURL('image/jpeg', 0.6);
                ws.send(JSON.stringify({ image: base64Data }));
            }

            // Emotion to Emoji Mapping
            const EMOJI_MAP = {
                'happy': '😀',
                'sad': '😢',
                'angry': '😠',
                'surprise': '😲',
                'neutral': '😐',
                'fear': '😨',
                'disgust': '🤢'
            };

            // Hand Skeleton Connections
            const HAND_CONNECTIONS = [
                [0, 1], [1, 2], [2, 3], [3, 4], // Thumb
                [0, 5], [5, 6], [6, 7], [7, 8], // Index
                [5, 9], [9, 10], [10, 11], [11, 12], // Middle
                [9, 13], [13, 14], [14, 15], [15, 16], // Ring
                [13, 17], [0, 17], [17, 18], [18, 19], [19, 20] // Pinky
            ];
            const FINGER_TIPS = { 4: 'Thumb', 8: 'Index', 12: 'Middle', 16: 'Ring', 20: 'Pinky' };
            const GESTURE_MAP = {
                'None': 'NONE',
                'Closed_Fist': 'FIST ✊',
                'Open_Palm': 'PALM 🖐️',
                'Pointing_Up': 'POINT UP ☝️',
                'Thumb_Down': 'THUMB DOWN 👎',
                'Thumb_Up': 'THUMB UP 👍',
                'Victory': 'PEACE ✌️',
                'ILoveYou': 'ROCK ON 🤘'
            };

            // Draw HUD target corners
            function drawTargetCorners(ctx, x, y, w, h, size=15) {
                ctx.beginPath();
                // Top Left
                ctx.moveTo(x, y + size); ctx.lineTo(x, y); ctx.lineTo(x + size, y);
                // Top Right
                ctx.moveTo(x + w - size, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + size);
                // Bottom Left
                ctx.moveTo(x, y + h - size); ctx.lineTo(x, y + h); ctx.lineTo(x + size, y + h);
                // Bottom Right
                ctx.moveTo(x + w - size, y + h); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w, y + h - size);
                ctx.stroke();
            }

            function drawOverlay(data) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Update Sidebar
                uiFps.textContent = data.fps.toFixed(1);
                uiFaces.textContent = data.faces ? data.faces.length : 0;
                uiSubjectsList.innerHTML = '';

                // Draw Faces
                if (data.faces && data.faces.length > 0) {
                    data.faces.forEach(face => {
                        const b = face.bbox;
                        const d = face.deep_attributes;
                        
                        // Flip X coordinate for mirrored video alignment
                        const flippedX = canvas.width - b.x - b.w;
                        
                        // HUD Target Box
                        ctx.strokeStyle = face.is_deep_stale ? '#ff003c' : '#00f3ff';
                        ctx.lineWidth = 2;
                        
                        // Draw corners instead of full rect for HUD feel
                        drawTargetCorners(ctx, flippedX, b.y, b.w, b.h, 20);
                        
                        // Add face details to sidebar list instead of floating on canvas
                        const isStaleColor = face.is_deep_stale ? '#ff003c' : '#00f3ff';
                        const staleEmoColor = face.is_deep_stale ? '#ff003c' : '#fff';
                        
                        const faceHtml = `
                            <div style="background: rgba(0, 243, 255, 0.05); padding: 10px; border-left: 3px solid ${isStaleColor}; font-size: 0.8rem; line-height: 1.4;">
                                <div style="color: #00f3ff; margin-bottom: 4px; font-weight: bold; font-size: 0.9rem;">TRK_ID: ${face.face_id}</div>
                                <div style="color: #fff;">AGE: ${d.age || '--'}</div>
                                <div style="color: #fff;">GEN: ${(d.gender || '--').toUpperCase()}</div>
                                <div style="color: ${staleEmoColor};">EMO: ${(d.emotion || 'SCANNING').toUpperCase()}</div>
                                <div style="color: rgba(255,255,255,0.5);">ROT_X: ${face.orientation.pitch.toFixed(1)}°</div>
                            </div>
                        `;
                        uiSubjectsList.innerHTML += faceHtml;
                    });
                } else {
                    uiSubjectsList.innerHTML = '<div style="color: rgba(255,255,255,0.5); font-size: 0.8rem; font-style: italic;">NO SUBJECTS IN VIEW</div>';
                }
                
                let leftGesture = "NONE";
                let rightGesture = "NONE";
                let activeDrawingHands = { 'Left': false, 'Right': false };

                // Draw Hands
                if (data.hands) {
                    data.hands.forEach(hand => {
                        const displayGesture = GESTURE_MAP[hand.gesture] || hand.gesture.toUpperCase();
                        if (hand.handedness === "Left") {
                            leftGesture = displayGesture;
                        } else if (hand.handedness === "Right") {
                            rightGesture = displayGesture;
                        }
                        
                        const w = canvas.width;
                        const h = canvas.height;

                        // --- Air Drawing Logic ---
                        if (hand.gesture === 'Pointing_Up') {
                            activeDrawingHands[hand.handedness] = true;
                            const indexTip = hand.landmarks[8];
                            currentStrokes[hand.handedness].push({ x: w - (indexTip.x * w), y: indexTip.y * h });
                        } else if (hand.gesture === 'Open_Palm') {
                            drawingPaths = []; // Erase the board
                            currentStrokes = { 'Left': [], 'Right': [] };
                        }

                        // Draw Gesture & Handedness Tag near the wrist
                        const wrist = hand.landmarks[0];
                        const wristX = w - (wrist.x * w);
                        const wristY = wrist.y * h;
                        
                        const displayGestureForHand = GESTURE_MAP[hand.gesture] || hand.gesture.toUpperCase();

                        // Keep tag on-screen if hand goes too low
                        const tagY = Math.min(wristY + 20, h - 50);

                        ctx.fillStyle = 'rgba(3, 10, 22, 0.8)';
                        ctx.beginPath();
                        ctx.rect(wristX - 60, tagY, 120, 45);
                        ctx.fill();
                        ctx.strokeStyle = '#00f3ff';
                        ctx.stroke();
                        
                        ctx.fillStyle = '#fff';
                        ctx.font = '12px "Share Tech Mono"';
                        ctx.textAlign = 'center';
                        ctx.fillText(`SYS.${hand.handedness.toUpperCase()}`, wristX, tagY + 15);
                        ctx.fillStyle = '#00f3ff';
                        ctx.fillText(`[${displayGestureForHand}]`, wristX, tagY + 30);
                    });
                }
                
                // End strokes for hands that are no longer pointing up
                ['Left', 'Right'].forEach(hnd => {
                    if (!activeDrawingHands[hnd] && currentStrokes[hnd].length > 0) {
                        drawingPaths.push(currentStrokes[hnd]);
                        currentStrokes[hnd] = [];
                    }
                });
                
                // --- Render Air Drawing Path ---
                const allStrokes = [...drawingPaths];
                if (currentStrokes['Left'].length > 0) allStrokes.push(currentStrokes['Left']);
                if (currentStrokes['Right'].length > 0) allStrokes.push(currentStrokes['Right']);

                if (allStrokes.length > 0) {
                    ctx.beginPath();
                    ctx.strokeStyle = '#ff00ff'; // Neon pink/purple for drawing
                    ctx.lineWidth = 4;
                    ctx.lineCap = 'round';
                    ctx.lineJoin = 'round';
                    ctx.shadowBlur = 15;
                    ctx.shadowColor = '#ff00ff';
                    
                    allStrokes.forEach(stroke => {
                        if (stroke.length === 1) {
                            // Draw a dot if stroke is only 1 point
                            ctx.moveTo(stroke[0].x, stroke[0].y);
                            ctx.lineTo(stroke[0].x + 0.1, stroke[0].y);
                        } else if (stroke.length > 1) {
                            ctx.moveTo(stroke[0].x, stroke[0].y);
                            for (let i = 1; i < stroke.length; i++) {
                                ctx.lineTo(stroke[i].x, stroke[i].y);
                            }
                        }
                    });
                    
                    ctx.stroke();
                    ctx.shadowBlur = 0; // reset
                }
                
                // --- Render Two-Hand Shape Guess ---
                if (data.two_hand_gesture) {
                    uiTwoHandShape.textContent = data.two_hand_gesture.toUpperCase();
                    
                    ctx.fillStyle = '#00f3ff';
                    ctx.font = 'bold 40px "Share Tech Mono"';
                    ctx.textAlign = 'center';
                    ctx.shadowBlur = 20;
                    ctx.shadowColor = '#00f3ff';
                    ctx.fillText(`[ SHAPE DETECTED: ${data.two_hand_gesture} ]`, canvas.width / 2, 80);
                    ctx.shadowBlur = 0;
                } else {
                    uiTwoHandShape.textContent = "NONE";
                }
                
                uiLeftHand.textContent = leftGesture;
                uiRightHand.textContent = rightGesture;
            }

            video.addEventListener('playing', () => { connectWebSocket(); });
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
