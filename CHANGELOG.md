# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-05-29

### Added
- Integrated **YAMNet Audio Classification** via Google MediaPipe. The system now records microphone audio through the browser, converts it to a 16kHz raw PCM Float32 stream, and transmits it over WebSocket alongside the video frame.
- Added a `YAMNetAudioClassifier` on the Python backend that buffers audio and triggers detection events specifically for 50+ classes of Animals and Birds (e.g. Dog bark, Cat meow, Bird chirp, Roar).
- Added a **Jarvis Text-to-Speech (TTS)** module to the frontend using the Web Speech API. When the AI detects an animal/bird sound, it will synthesize speech and announce: *"Sir, I have detected the sound of a [Bird/Dog/etc]"* using a deep UK English voice.
- Added an `AUDIO SCANNERS` block to the HUD Telemetry dashboard to visualize when the system detects a target sound.

## [1.1.5] - 2026-05-29

### Fixed
- Fixed an issue where DeepFace telemetrics (Age, Emotion, Gender) were failing to lock onto live faces but worked fine for static images. This was caused by the recent WebRTC alignment fix trying to stream massive 1080p/4K raw frames over the WebSocket, which plummeted the FPS and caused the Centroid Tracker to lose track of the face ID between frames due to large pixel distances. 
- Implemented a smart cap on the WebRTC canvas resolution (max 800px width) while maintaining intrinsic aspect ratios, bringing FPS back up.
- Increased the tracking algorithm's `MAX_DISTANCE_THRESHOLD` in `config.py` from 150 to 300 to better handle rapid head movements.

## [1.1.4] - 2026-05-29

### Fixed
- Fixed critical WebRTC canvas alignment bug where the drawing path would not follow the finger perfectly due to camera aspect ratio stretching. The canvas now dynamically syncs to the intrinsic video resolution.
- Fixed an issue where single-point strokes (dots) would be invisible.

## [1.1.3] - 2026-05-29

### Changed
- UI Redesign: Removed the floating `TRK_ID` and telemetry text blocks that were drawing directly next to faces on the canvas.
- Face telemetry (ID, Age, Gender, Emotion, Rotation) is now dynamically listed in the `TELEMETRY` sidebar panel, making the main camera feed much cleaner.

## [1.1.2] - 2026-05-29

### Added
- Added `TWO-HAND SHAPE` field to the sidebar dashboard for continuous monitoring of joined hand shapes.

## [1.1.1] - 2026-05-29

### Fixed
- Improved Air Drawing logic to support multiple separate drawing strokes. Drawing now appropriately stops when the user lowers their finger and starts a new stroke when raised again, instead of connecting all points with a single continuous line.

## [1.1.0] - 2026-05-29

### Added
- **Air Drawing**: Hold up an index finger (`POINTING_UP`) to draw neon pink paths on the screen. Open your hand (`OPEN_PALM`) to erase the canvas.
- **Two-Hand Shape Recognition**: Geometrically tracks and identifies shapes (like Hearts, Triangles, and Rectangles/Cameras) formed by joining two hands.
- Hid the distracting full-hand skeleton wireframe to give the UI a cleaner HUD look.

## [1.0.2] - 2026-05-29

### Fixed
- Fixed issue where MediaPipe misclassified a fist as `Thumb_Up` by calculating explicit thumb extension distances.
- Added 3D landmark based fallback to override DeepFace's neutral emotion when the subject is clearly smiling.
- Moved emotion emoji from floating over the subject's head to the 'Gestures & Emotion' dashboard panel on the right side.

## [1.0.1] - 2026-05-29

### Fixed
- Added robust heuristic fallback for `Closed_Fist` gesture recognition to properly detect back-hand fists, which the default MediaPipe model frequently misses.

## [1.0.0] - 2026-05-29

### Added
- Rebranded tracking engine to OmnitrackAI.
- Added comprehensive `.gitignore` for Python environments.
- Implemented robust face, head pose (pitch/yaw/roll), and hand gesture tracking.
- Created premium HUD WebSocket dashboard for real-time telemetry.
- Created `docs/project_scope.md` to define project scope and track validated features.

### Fixed
- Fixed bug causing emotion emojis to hide off-screen when a tracked face is near the top edge.
- Fixed UI dashboard layout to split L-Hand and R-Hand tracking stats into a dedicated panel on the right side.
- Bound hand wrist gesture tags to the bottom canvas edge to prevent off-screen hiding.
