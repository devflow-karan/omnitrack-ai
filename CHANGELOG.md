# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
