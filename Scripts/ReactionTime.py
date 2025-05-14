import pyautogui
import time
import mss
import mouse  # pip install mouse

def react_to_color_changes(x, y):
    with mss.mss() as sct:
        region = {'top': y, 'left': x, 'width': 1, 'height': 1}
        print(f"Monitoring position set to ({x}, {y}).")
        times = []
        click_fn = pyautogui.click  # Cache for speed
        grab = sct.grab             # Cache the grab method
        
        first_test = True
        # Main loop: first cycle waits for a click; later cycles start automatically
        while True:
            if first_test:
                print("Click once to start checking for color change...")
                mouse.wait(button='left')
                first_test = False
            else:
                time.sleep(0.2)  # Automatic delay for subsequent cycles

            initial_color = grab(region).pixel(0, 0)
            print(f"Initial color: {initial_color}. Monitoring for change...")
            
            # Inner loop: busy-wait checking for color change with minimal overhead
            while True:
                start = time.perf_counter()
                current_color = grab(region).pixel(0, 0)
                if current_color != initial_color:
                    rt = (time.perf_counter() - start) * 1000  # Reaction time in ms
                    click_fn(x, y)
                    times.append(rt)
                    print(f"Color changed! RT: {rt:.2f}ms")
                    
                    time.sleep(1)  # Wait a second after first click
                    click_fn(x, y)
                    print("Second click done, restarting test...")
                    break