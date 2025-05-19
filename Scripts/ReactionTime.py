from time import sleep, perf_counter_ns
import mss
import win32api, win32con  # Much faster than pyautogui for clicking

def click(x, y):
    """Simulates a left mouse click at the given (x, y) position."""
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

def wait_for_left_click(prompt: str):
    """Waits for the user to left-click, displaying the given prompt."""
    print(prompt)
    # Ensure the left mouse button is released
    while win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
        sleep(0.01)
    # Wait for a left click to occur
    while not (win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000):
        sleep(0.01)

def react_to_color_changes(x, y):
    """Monitors a single screen pixel for a color change then clicks at (x, y)."""
    with mss.mss() as sct:
        # Define a minimal capture region for performance
        region = {'top': y, 'left': x, 'width': 1, 'height': 1}
        print(f"Monitoring position set to ({x}, {y}).")
        times = []
        
        # Pre-allocate variables outside loops
        start_time = 0
        first_test = True

        while True:
            if first_test:
                # Wait for the initial left click from the user to start monitoring
                wait_for_left_click("Left click to start monitoring...")
                first_test = False
                sleep(0.2)  # Delay to avoid immediate re-triggering

            # Capture the initial screenshot and color without timing overhead
            sct_img = sct.grab(region)
            initial_color = sct_img.pixel(0, 0)
            print(f"Initial color: {initial_color}. Monitoring for change...")

            # Busy-loop for minimal latency color checking
            while True:
                start_time = perf_counter_ns()
                sct_img = sct.grab(region)
                current_color = sct_img.pixel(0, 0)
                
                if current_color != initial_color:
                    rt = (perf_counter_ns() - start_time) / 1000000  # Reaction time in ms
                    click(x, y)
                    times.append(rt)
                    print(f"Color changed! RT: {rt:.3f}ms")
                    
                    sleep(0.5)
                    click(x, y)
                    print("Second click done, restarting test...")
                    sleep(0.2)  # Small delay before restarting
                    break

if __name__ == '__main__':
    print("===== Reaction Time Test =====")
    print("This tool monitors a specific screen pixel and clicks when a color change is detected.")
    print("1. Position your mouse over the reaction test area.")
    print("2. After the countdown, your position will be captured.")
    print("3. Then, left click to begin monitoring.")
    print("4. Press Ctrl+C at any time to exit.")
    print("================================")
    input("Press Enter to start...")
    
    # alt+tab switching option (default: false)
    alttab: bool = False
    if alttab:
        win32api.keybd_event(0x12, 0, 0, 0)  # Alt key down
        win32api.keybd_event(0x09, 0, 0, 0)  # Tab key down
        win32api.keybd_event(0x09, 0, win32con.KEYEVENTF_KEYUP, 0)  # Tab key up
        win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt key up

    print("Capturing your position in 3 seconds...")
    sleep(3)
    pos = win32api.GetCursorPos()
    print(f"Position captured: {pos}")
    
    try:
        # Start monitoring using the captured mouse position
        react_to_color_changes(pos[0], pos[1])
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")