import os
import time
import threading
import tkinter as tk

import cv2  # OpenCV
import mediapipe as mp  # Hand detection
import pyautogui as p  # Keyboard operations


# -----------------------------
# Hand detector utility
# -----------------------------
class HandDetector:
    def __init__(
        self,
        mode: bool = False,
        max_hands: int = 2,
        detection_con: float = 0.5,
        track_con: float = 0.5,
    ):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.results = None

    def find_hands(self, img, draw: bool = True):
        """Run hand detection and optionally draw landmarks."""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(
                        img,
                        hand_lms,
                        self.mp_hands.HAND_CONNECTIONS,
                    )
        return img

    def find_position(self, img, hand_no: int = 0, draw: bool = False):
        """Return list of [id, x, y] landmark positions for a given hand."""
        lm_list = []
        if self.results and self.results.multi_hand_landmarks:
            if hand_no >= len(self.results.multi_hand_landmarks):
                return lm_list
            my_hand = self.results.multi_hand_landmarks[hand_no]
            h, w, _ = img.shape
            for lm_id, lm in enumerate(my_hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append([lm_id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 6, (255, 0, 255), cv2.FILLED)
        return lm_list


# -----------------------------
# Gesture detection loop
# -----------------------------
def detection_loop():
    w_cam, h_cam = 640, 480
    tip_ids = [4, 8, 12, 16, 20]  # Thumb + fingertips

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w_cam)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h_cam)

    if not cap.isOpened():
        print("Error: Cannot open webcam.")
        return

    detector = HandDetector(detection_con=0.75)
    p_time = 0.0

    while True:
        success, img = cap.read()
        if not success:
            print("Warning: Failed to read frame from webcam.")
            break

        img = detector.find_hands(img)
        lm_list = detector.find_position(img, draw=False)

        result = ""
        if lm_list:
            fingers = []

            # Thumb: compare x (since thumb bends sideways)
            if lm_list[tip_ids[0]][1] > lm_list[tip_ids[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

            # Other 4 fingers: compare y of fingertip with pip joint
            for i in range(1, 5):
                if lm_list[tip_ids[i]][2] < lm_list[tip_ids[i] - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)

            total_fingers = fingers.count(1)

            # Map gestures to keys/actions (kept consistent with your original)
            if total_fingers == 1:
                p.press("space")
                result = "forward"
            elif total_fingers == 2:
                p.press("left")
                result = "backward"
            elif total_fingers == 3:
                p.press("right")
                result = "volume up"
            elif total_fingers == 4:
                p.press("up")
                result = "volume down"
            elif total_fingers == 5:
                p.press("down")
                result = "volume down"

        # FPS (optional)
        c_time = time.time()
        fps = 0.0 if c_time == p_time else 1.0 / (c_time - p_time)
        p_time = c_time

        if result:
            cv2.putText(
                img,
                result,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2,
                cv2.LINE_AA,
            )
        cv2.putText(
            img,
            f"FPS: {fps:.1f}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.imshow("Hand Gesture Detection", img)
        # Press 'q' in the video window to quit the detection loop
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# -----------------------------
# Tkinter UI
# -----------------------------
def start_detection_thread():
    # Run detection in a background thread so the UI stays responsive
    t = threading.Thread(target=detection_loop, daemon=True)
    t.start()


def build_ui():
    window = tk.Tk()
    window.title("Hand Gesture Detection")
    window.geometry("500x380")
    window.configure(background="snow")

    title = tk.Label(
        window,
        text="Hand Gesture Detection",
        font=("Times", 20, "bold"),
        bg="snow",
    )
    title.pack(pady=30)

    detect_btn = tk.Button(
        window,
        text="Detect",
        command=start_detection_thread,
        fg="black",
        bg="deep pink",
        width=12,
        height=1,
        activebackground="red",
        font=("Times", 15, "bold"),
    )
    detect_btn.pack(pady=20)

    note = tk.Label(
        window,
        text="Tip: Click Detect, then press 'q' in the video window to stop.",
        font=("Times", 10),
        bg="snow",
    )
    note.pack(pady=10)

    window.mainloop()


if __name__ == "__main__":
    # Optional: Prevent PyAutoGUI from failing if failsafe is triggered
    p.FAILSAFE = True
    build_ui()
