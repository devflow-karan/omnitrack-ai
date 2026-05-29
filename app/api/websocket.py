import time
import base64
import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from app.services.face_detector import AdvancedFaceDetector
from app.services.audio_detector import YAMNetAudioClassifier
from app.models.schemas import FrameResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/process")
async def websocket_process(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected for custom frames processing.")

    detector = AdvancedFaceDetector()
    audio_classifier = YAMNetAudioClassifier()
    frame_count = 0
    start_time = time.time()

    try:
        while True:
            # 1. Receive JSON containing base64 image
            data = await websocket.receive_json()
            image_data = data.get("image")
            
            if not image_data:
                continue

            # 2. Decode base64 image
            try:
                if "base64," in image_data:
                    image_data = image_data.split("base64,")[1]
                
                img_bytes = base64.b64decode(image_data)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue
            except Exception as e:
                logger.error(f"Error decoding image: {e}")
                continue

            # 3. Process frame with AdvancedFaceDetector
            faces, hands, two_hand_gesture = detector.process_frame(frame)
            
            # Calculate FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time if elapsed_time > 0 else 0

            # Reset FPS counter every 30 frames
            if frame_count > 30:
                frame_count = 0
                start_time = time.time()

            audio_event = None
            audio_data = data.get("audio")
            if audio_data:
                try:
                    audio_bytes = base64.b64decode(audio_data)
                    float_array = np.frombuffer(audio_bytes, dtype=np.float32)
                    audio_event = audio_classifier.process(float_array)
                except Exception as e:
                    logger.error(f"Error decoding audio: {e}")

            # 4. Construct response using Pydantic models
            response = FrameResponse(
                faces=faces,
                hands=hands,
                two_hand_gesture=two_hand_gesture,
                audio_event=audio_event,
                fps=fps,
                timestamp=time.time()
            )

            # 5. Send results back to client
            await websocket.send_json(response.model_dump())

    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        detector.close()
        audio_classifier.close()
