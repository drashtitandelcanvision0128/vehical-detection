
import cv2

def list_cameras():
    print("Checking for available cameras...")
    index = 0
    available_cameras = []
    while index < 5:  # Check first 5 indices
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"Index {index}: AVAILABLE")
            available_cameras.append(index)
            cap.release()
        else:
            print(f"Index {index}: NOT AVAILABLE")
        index += 1
    
    if available_cameras:
        print(f"\nFound {len(available_cameras)} camera(s) at indices: {available_cameras}")
        print(f"Please use index {available_cameras[0]} for your default camera.")
    else:
        print("\nNo cameras found! Make sure your webcam is connected.")

if __name__ == "__main__":
    list_cameras()
