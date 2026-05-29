# OmnitrackAI Tracking Engine

A modular, real-time computer vision system using Python, MediaPipe, and FastAPI to track face landmarks, head movement (pitch/yaw/roll), and hand gestures. Results are streamed back in real-time over WebSockets to a premium HTML5/CSS/JS dashboard UI.

## Features

- **Face & Movement Tracking**: Tracks face meshes and computes head orientation (Pitch, Yaw, Roll) using a PnP solver.
- **Hand & Gesture Tracking**: Detects hands, handedness, and classifies gestures (Fist, Open Palm, Peace, Thumbs Up, etc.).
- **Real-Time WebSocket Pipeline**: Processes webcam frames via WebSockets, allowing the application to run smoothly in remote/dockerized environments.

## Prerequisites

- Python 3.9+
- [Docker](https://docs.docker.com/get-docker/) (Optional, for containerized running)
- Webcam (Required for tracking)

## How to Run

### Method 1: Local Setup

1. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the FastAPI server:
   ```bash
   python -m app.main
   ```

4. Open your browser and navigate to `http://localhost:8000`. Make sure to allow camera permissions.

### Method 2: Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t omnitrackai-tracker .
   ```

2. Run the Docker container:
   ```bash
   docker run -p 8000:8000 omnitrackai-tracker
   ```

3. Navigate to `http://localhost:8000` in your browser.

## Documentation

For more detailed information regarding the project's scope and verified tracking features, see the [docs/project_scope.md](docs/project_scope.md) folder.
