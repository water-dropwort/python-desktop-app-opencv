import websockets
import cv2
import base64
import asyncio
import threading
from os.path import expanduser

frontalface = cv2.CascadeClassifier(expanduser("~") + "/opencv/opencv/data/haarcascades/haarcascade_frontalface_default.xml")
exit_event = threading.Event()

latest_image = None
latest_image_lock = threading.Lock()

async def stream_image_handler(websocket, state, lock):
    while not exit_event.is_set():
        async with lock:
            running = state["running"]
        if running:
            img = None
            with latest_image_lock:
                img = latest_image
            if img is None:
                print("img is none")
                continue
            _, buffer = cv2.imencode('.jpg', img)
            decimg = base64.b64encode(buffer).decode("utf-8")
            await websocket.send(decimg)
        await asyncio.sleep(1/100)

async def receive_command_handler(websocket, state, lock):
    async for message in websocket:
        async with lock:
            state["running"] = (message == "start")

async def handler(websocket):
    print("handler: client connected(", threading.current_thread())
    state = {"running": True}
    lock = asyncio.Lock()
    stream_image_task = asyncio.create_task(stream_image_handler(websocket, state, lock))
    receive_command_task = asyncio.create_task(receive_command_handler(websocket, state, lock))
    _, pending = await asyncio.wait(
        [stream_image_task, receive_command_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

def detect_face(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lists = frontalface.detectMultiScale(gray, minSize=(100,100))
    if(len(lists)):
        for (x,y,w,h) in lists:
            cv2.rectangle(img, (x,y), (x+w, y+h), (0,0,200), thickness=2)
    return img

def capture_thread_task():
    print("capture_thread_task: start(", threading.current_thread())
    global latest_image
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("capture_thread_task: failed to open the video capture")
        return

    while not exit_event.is_set():
        ret, img = cap.read()
        if not ret:
            print("capture_thread_task: failed to read")
            break

        img2 = detect_face(img)
        with latest_image_lock:
            latest_image = img2
    cap.release()
    print("capture_thread_task: completed")
    exit_event.set()

async def main():
    async with websockets.serve(handler, "", 8080):
        await asyncio.Future()

if __name__ == "__main__":
    capture_thread = threading.Thread(target=capture_thread_task)
    try:
        capture_thread.start()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("__main__: KeyboardInterrupt")
    except Exception as e:
        print("__main__:", e)
    finally:
        print("__main__: finally")
        exit_event.set()
        capture_thread.join()
