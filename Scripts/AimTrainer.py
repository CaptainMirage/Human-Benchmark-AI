import mss
import numpy as np
import win32api, win32con
import time

class AimTrainer:
    def __init__(self, step_size: int = 69, target_color: str = "#95c3e8") -> None:
        self.step_size = step_size
        self.target_color = target_color
        self.target_rgb = self.hex_to_rgb(target_color)
        self.coords = []  # List of (x, y) coordinates for corners
        self.sct = mss.mss()
        self.scan_area = None  # Will store (x1, y1, x2, y2)

    def hex_to_rgb(self, hex_color: str) -> tuple:
        """
        Convert hex color to RGB tuple.
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def collect_coordinates(self) -> list:
        """
        Collect two corner coordinates using mouse position upon 'C' key press.
        """
        print("Please position your mouse over 2 corner positions and press 'C' to register each coordinate.")
        print("These will define the rectangular scanning area.")
        prev_key_state = 0
        while len(self.coords) < 2:
            curr_key_state = win32api.GetKeyState(0x43)  # 'C' key

            # Detect press (transition from not pressed to pressed)
            if curr_key_state < 0 and prev_key_state >= 0:
                # Get current mouse position
                x, y = win32api.GetCursorPos()
                self.coords.append((x, y))
                print(f"Corner {len(self.coords)} registered: ({x}, {y})")
                time.sleep(0.2)  # debounce delay
            prev_key_state = curr_key_state
            time.sleep(0.01)  # Small sleep to reduce CPU usage
            
        # Define scan area from the two corners
        x1, y1 = self.coords[0]
        x2, y2 = self.coords[1]
        self.scan_area = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        print(f"Scan area defined: ({self.scan_area[0]}, {self.scan_area[1]}) to ({self.scan_area[2]}, {self.scan_area[3]})")
        return self.coords

    def is_pixel_target_color(self, x: int, y: int, tolerance: int = 10) -> bool:
        """
        Check if the pixel at (x, y) matches the target color within tolerance.
        """
        region = {'top': y, 'left': x, 'width': 1, 'height': 1}
        screenshot = self.sct.grab(region)
        img = np.array(screenshot)
        b, g, r = img[0, 0, 0], img[0, 0, 1], img[0, 0, 2]
        
        # Check if the pixel matches target color within tolerance
        target_r, target_g, target_b = self.target_rgb
        return (abs(r - target_r) <= tolerance and 
                abs(g - target_g) <= tolerance and 
                abs(b - target_b) <= tolerance)

    def click_at(self, x: int, y: int) -> None:
        """
        Simulate a mouse click at the specified (x, y) position.
        """
        old_x, old_y = win32api.GetCursorPos()  # Save current position
        win32api.SetCursorPos((x, y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.02)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        win32api.SetCursorPos((old_x, old_y))  # Move mouse back to original position
        print(f"Target found and clicked at ({x}, {y})")

    def scan_and_click(self) -> None:
        """
        Scan the defined area in a grid pattern and click target colors as found.
        """
        if not self.scan_area:
            print("No scan area defined!")
            return

        x1, y1, x2, y2 = self.scan_area
        targets_found = 0
        
        # Scan in a grid pattern with step_size intervals
        for y in range(y1, y2, self.step_size):
            for x in range(x1, x2, self.step_size):
                if self.is_pixel_target_color(x, y):
                    self.click_at(x, y)
                    targets_found += 1
                    time.sleep(0.1)  # Brief delay between clicks
        
        if targets_found == 0:
            print("No targets found in current scan")
        else:
            print(f"Scan complete - found and clicked {targets_found} targets")

    def monitor_and_click(self, interval: float = 0.1) -> None:
        """
        Continuously monitor the scan area and click targets as they appear.
        """
        print(f"Monitoring scan area for color {self.target_color} (RGB: {self.target_rgb})")
        print(f"Scanning every {self.step_size} pixels")
        print("Press Ctrl+C to exit.")
        
        try:
            while True:
                self.scan_and_click()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")

def get_user_input() -> tuple:
    """
    Get user preferences for step size and target color.
    """
    # Get step size
    step_input = input("Enter step size for scanning (default 69): ").strip()
    step_size = 69
    if step_input:
        try:
            step_size = int(step_input)
            if step_size <= 0:
                print("Invalid step size, using default (69)")
                step_size = 69
        except ValueError:
            print("Invalid step size, using default (69)")
    
    # Get target color
    color_input = input("Enter target color in hex (default #95c3e8): ").strip()
    target_color = "#95c3e8"
    if color_input:
        # Basic validation for hex color
        if color_input.startswith('#') and len(color_input) == 7:
            try:
                int(color_input[1:], 16)  # Try to parse as hex
                target_color = color_input
            except ValueError:
                print("Invalid hex color, using default (#95c3e8)")
        else:
            print("Invalid hex color format, using default (#95c3e8)")
    
    return step_size, target_color

def main() -> None:
    print("===== Aim Trainer Color Clicker =====")
    print("This tool scans a rectangular area for a specific color and clicks targets as found.")
    print("1. Configure step size and target color")
    print("2. Register 2 corner coordinates to define scan area")
    print("3. Continuous monitoring and clicking begins")
    print("4. Press Ctrl+C to exit")
    print("=====================================")
    
    step_size, target_color = get_user_input()
    print(f"Using step size: {step_size}, target color: {target_color}")
    
    trainer = AimTrainer(step_size=step_size, target_color=target_color)
    
    input("Press Enter to begin coordinate registration...")
    trainer.collect_coordinates()
    
    print(f"\nStarting continuous monitoring and clicking.")
    print(f"Scanning for color {target_color} every {step_size} pixels in the defined area.")
    trainer.monitor_and_click(interval=0.05)

if __name__ == "__main__":
    main()