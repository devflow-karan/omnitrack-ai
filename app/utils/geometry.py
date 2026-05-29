import numpy as np
import cv2
from typing import Tuple, List, Optional

def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """
    Calculate the angle at vertex b given three points: a, b, c.
    Points can be 2D or 3D numpy arrays.
    Returns angle in degrees.
    """
    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    angle = np.arccos(cosine_angle)

    return float(np.degrees(angle))

def estimate_head_pose(
    landmarks_2d: np.ndarray, 
    img_size: Tuple[int, int]
) -> Tuple[float, float, float, np.ndarray, np.ndarray]:
    """
    Estimates head pose (pitch, yaw, roll) using Perspective-n-Point (PnP) solver.
    :param landmarks_2d: 2D coordinates of facial landmarks in image space.
                         Expected shape: (6, 2) corresponding to:
                         0: Nose tip (Index 1)
                         1: Chin (Index 152)
                         2: Left eye outer corner (Index 263)
                         3: Right eye outer corner (Index 33)
                         4: Left mouth corner (Index 291)
                         5: Right mouth corner (Index 61)
    :param img_size: (width, height) of the image.
    :return: (pitch, yaw, roll, rvec, tvec) where:
             pitch, yaw, roll are Euler angles in degrees
             rvec is the rotation vector
             tvec is the translation vector
    """
    # 3D model points of standard human face.
    model_points = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye outer corner
        (225.0, 170.0, -135.0),      # Right eye outer corner
        (-150.0, -150.0, -125.0),    # Left mouth corner
        (150.0, -150.0, -125.0)      # Right mouth corner
    ], dtype=np.float64)

    # Camera internals configuration
    focal_length = img_size[0]
    center = (img_size[0] / 2, img_size[1] / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1)) # Assuming no lens distortion

    # Solve PnP
    success, rvec, tvec = cv2.solvePnP(
        model_points, 
        landmarks_2d, 
        camera_matrix, 
        dist_coeffs, 
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return 0.0, 0.0, 0.0, np.zeros((3, 1)), np.zeros((3, 1))

    # Calculate Euler angles from rotation matrix
    rmat, _ = cv2.Rodrigues(rvec)
    
    # Projection matrix
    proj_matrix = np.hstack((rmat, tvec))
    # Decompose projection matrix to find Euler angles
    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)
    
    pitch = float(euler_angles[0, 0])
    yaw = float(euler_angles[1, 0])
    roll = float(euler_angles[2, 0])

    # Adjust signs / scales depending on coordination mapping
    # Pitch: looking up/down, Yaw: looking left/right, Roll: tilting head left/right
    # Let's adjust representation
    pitch = pitch * 180.0 # scale factor adjustments if needed
    # Standard mapping for simple visualization:
    # We can also compute directly from rotation matrix:
    sy = np.sqrt(rmat[0, 0]**2 + rmat[1, 0]**2)
    singular = sy < 1e-6

    if not singular:
        x = np.arctan2(rmat[2, 1], rmat[2, 2])
        y = np.arctan2(-rmat[2, 0], sy)
        z = np.arctan2(rmat[1, 0], rmat[0, 0])
    else:
        x = np.arctan2(-rmat[1, 2], rmat[1, 1])
        y = np.arctan2(-rmat[2, 0], sy)
        z = 0

    # Convert to degrees
    pitch = float(np.degrees(x))
    yaw = float(np.degrees(y))
    roll = float(np.degrees(z))

    return pitch, yaw, roll, rvec, tvec

def calculate_ear(eye_landmarks: List[Tuple[float, float]]) -> float:
    """
    Calculate Eye Aspect Ratio (EAR) to detect blinking.
    Expected order: 6 landmarks outlining the eye
    [p1, p2, p3, p4, p5, p6]
    where p1-p4 is horizontal axis, p2-p6 and p3-p5 are vertical axes.
    EAR = (|p2 - p6| + |p3 - p5|) / (2 * |p1 - p4|)
    """
    p = [np.array(pt) for pt in eye_landmarks]
    
    # Vertical distances
    dist1 = np.linalg.norm(p[1] - p[5])
    dist2 = np.linalg.norm(p[2] - p[4])
    
    # Horizontal distance
    dist3 = np.linalg.norm(p[0] - p[3])
    
    ear = (dist1 + dist2) / (2.0 * dist3 + 1e-6)
    return float(ear)

def calculate_mar(lip_landmarks: List[Tuple[float, float]]) -> float:
    """
    Calculate Mouth Aspect Ratio (MAR) to detect mouth open/closed.
    Expected landmarks: 
    - Upper inner lip center, Lower inner lip center (vertical)
    - Left inner lip corner, Right inner lip corner (horizontal)
    MAR = |vertical| / |horizontal|
    """
    p = [np.array(pt) for pt in lip_landmarks]
    
    # Vertical distance
    dist_v = np.linalg.norm(p[0] - p[1])
    
    # Horizontal distance
    dist_h = np.linalg.norm(p[2] - p[3])
    
    mar = dist_v / (dist_h + 1e-6)
    return float(mar)
