# OmnitrackAI Project Scope

## Project Overview
OmnitrackAI is a foundational tracking engine that leverages real-time computer vision to monitor and analyze human movements. Using state-of-the-art machine learning models provided by MediaPipe and DeepFace, the system is designed to provide high-performance tracking of the face, head orientation, hands, and facial attributes.

## Scope of Work
The current scope of the project encompasses:
- **Real-Time Video Processing**: Capturing video frames via the user's browser, transmitting them over WebSockets to a backend server, and returning annotated data.
- **Face and Head Tracking**: 
  - Detection of human faces in the video stream.
  - Estimation of head pose (Pitch, Yaw, Roll) using facial landmarks and a PnP solver.
  - Real-time smoothing of tracking data to reduce jitter.
- **Hand Tracking and Gesture Recognition**:
  - Detection of up to two hands simultaneously.
  - Classification of handedness (Left/Right).
  - Recognition of predefined gestures (e.g., Closed Fist, Open Palm, Victory, Thumb Up/Down).
- **Attribute Analysis (DeepFace)**:
  - Asynchronous inference of age, gender, and emotional state using DeepFace models.
- **Dashboard Interface**:
  - A premium, futuristic HUD (Heads-Up Display) styled user interface.
  - Real-time rendering of telemetry, FPS, subject attributes, and spatial bounding boxes.

## Out of Scope
- Persisting tracking data to a database.
- Multi-camera synchronized tracking across different devices.
- Custom model training (the project relies on pre-trained MediaPipe/DeepFace models).

## Tracking Validation
The system's tracking functionality (Hands, Eyes, Face Movement) has been validated:
- **Face Movement**: Pitch/Yaw/Roll are successfully extracted via MediaPipe landmarks and a PnP solver in `face_detector.py`.
- **Eyes**: Eye corner landmarks (indices 33, 263) are actively used in the PnP solver for head pose estimation.
- **Hands**: Handedness, gestures, and joint points are parsed via MediaPipe's GestureRecognizer and relayed in real-time.
