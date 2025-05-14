from time import sleep, perf_counter_ns
import mss
import numpy as np
import win32api, win32con  # Much faster than pyautogui for clicking

def click(x, y):
    # Direct Windows API call is much faster than pyautogui
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

def react_to_color_changes(x, y):
    with mss.mss() as sct:
        # Minimize region size for faster capture
        region = {'top': y, 'left': x, 'width': 1, 'height': 1}
        print(f"Monitoring position set to ({x}, {y}).")
        times = []
        
        # Pre-allocate variables outside loops
        start_time = 0
        first_test = True

        while True:
            if first_test:
                # Wait for any prior left mouse clicks to be released.
                while win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                    sleep(0.01)
                
                print("left click to start monitoring...")
                # waits for the user to left click to continue
                while True:
                    if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                        break
                first_test = False
                sleep(0.2)  # Small delay to avoid immediate re-triggering
            
            # Get initial screenshot without timing impact
            sct_img = sct.grab(region)
            initial_color = sct_img.pixel(0, 0)
            print(f"Initial color: {initial_color}. Monitoring for change...")
            
            # Use busy loop for minimal latency
            while True:
                start_time = perf_counter_ns()
                sct_img = sct.grab(region)
                current_color = sct_img.pixel(0, 0)
                
                if current_color != initial_color:
                    rt = (perf_counter_ns() - start_time) / 1000000  # ms
                    click(x, y)
                    times.append(rt)
                    print(f"Color changed! RT: {rt:.3f}ms")
                    
                    sleep(0.5)
                    click(x, y)
                    print("Second click done, restarting test...")
                    sleep(0.2)  # Small delay to avoid immediate re-triggering
                    break
    
if __name__ == '__main__':
    # # switches the window to the next window with alt + tab
    alttab: bool = False
    if alttab:
        win32api.keybd_event(0x12, 0, 0, 0)  # Alt key down
        win32api.keybd_event(0x09, 0, 0, 0)  # Tab key down
        win32api.keybd_event(0x09, 0, win32con.KEYEVENTF_KEYUP, 0)  # Tab key up
        win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt key up

    print("Position your mouse over the reaction test area in 3 seconds")
    sleep(3)
    pos = win32api.GetCursorPos()
    print(f"Position captured: {pos}")
    
    try:
        # calls react_to_color_changes that inputs the pos which is a tuple[int, int]
        react_to_color_changes(pos[0], pos[1])
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")