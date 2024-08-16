import cv2
import numpy as np
import mediapipe as mp
import screen_brightness_control as sbc
from math import hypot
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

def get_left_right_landmarks(frame, processed, draw, mpHands): 
    left_landmark_list = None
    right_landmark_list = None

    if processed.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(processed.multi_hand_landmarks):
            hand_label = processed.multi_handedness[idx].classification[0].label
            landmark_list = []

            for lm in hand_landmarks.landmark:
                h, w, c = frame.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                landmark_list.append((cx, cy))

            if hand_label == "Right":
                right_landmark_list = landmark_list
            elif hand_label == "Left":
                left_landmark_list = landmark_list

            draw.draw_landmarks(frame, hand_landmarks, mpHands.HAND_CONNECTIONS)

    return left_landmark_list, right_landmark_list

def get_distance(frame, landmark_list):
    x1, y1 = landmark_list[4]
    x2, y2 = landmark_list[8]
    return hypot(x2 - x1, y2 - y1)

def main():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volRange = volume.GetVolumeRange()
    minVol, maxVol, _ = volRange

    mpHands = mp.solutions.hands
    hands = mpHands.Hands(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.75,
        min_tracking_confidence=0.75,
        max_num_hands=2)

    draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = hands.process(frameRGB)

            left_landmark_list, right_landmark_list = get_left_right_landmarks(frame, processed, draw, mpHands)

            # Change brightness using left hand (In video it would appear as right hand as we are mirroring the frame)
            if left_landmark_list:
                left_distance = get_distance(frame, left_landmark_list)
                b_level = np.interp(left_distance, [20, 250], [0, 100])
                sbc.set_brightness(int(b_level))

            # Change volume using right hand (In video it would appear as left hand as we are mirroring the frame)
            if right_landmark_list:
                right_distance = get_distance(frame, right_landmark_list)
                vol = np.interp(right_distance, [20, 250], [minVol, maxVol])
                volume.SetMasterVolumeLevel(vol, None)

            cv2.imshow('Image', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
