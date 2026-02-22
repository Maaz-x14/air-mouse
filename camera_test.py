import cv2

def test_camera(index=0):
    print(f"Testing camera index {index}...")
    cap = cv2.VideoCapture(index)
    
    if not cap.isOpened():
        print(f"[FAIL] Could not open camera at index {index}")
        return False
    
    ret, frame = cap.read()
    if not ret or frame is None:
        print(f"[FAIL] Camera opened but failed to read frame")
        cap.release()
        return False
    
    print(f"[PASS] Camera works! Frame shape: {frame.shape}")
    print(f"       FPS: {cap.get(cv2.CAP_PROP_FPS)}")
    print(f"       Width: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}")
    print(f"       Height: {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
    cap.release()
    return True

# Try indices 0 through 3
for i in range(4):
    if test_camera(i):
        print(f"\n✅ Use CAMERA_INDEX = {i} in config.py")
        break
else:
    print("\n❌ No working camera found. Check connections and permissions.")
