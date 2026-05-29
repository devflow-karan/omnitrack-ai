from pydantic import BaseModel
from typing import Optional, List

class BoundingBox(BaseModel):
    x: int
    y: int
    w: int
    h: int

class Orientation(BaseModel):
    pitch: float
    yaw: float
    roll: float

class DeepFaceAttributes(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    emotion: Optional[str] = None

class FaceData(BaseModel):
    face_id: int
    bbox: BoundingBox
    orientation: Orientation
    deep_attributes: DeepFaceAttributes
    is_deep_stale: bool = True

class Point3D(BaseModel):
    x: float
    y: float
    z: float

class HandData(BaseModel):
    handedness: str
    gesture: str
    landmarks: List[Point3D]

class FrameResponse(BaseModel):
    faces: List[FaceData]
    hands: List[HandData]
    two_hand_gesture: Optional[str] = None
    audio_event: Optional[str] = None
    fps: float
    timestamp: float
