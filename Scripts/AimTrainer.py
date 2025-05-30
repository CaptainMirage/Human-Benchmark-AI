import mss
import numpy as np
import win32api, win32con
import time
from typing import Optional
import math

class AimTrainer:
    def __init__(self, step_size: Optional[int] = None, target_size: int = 160, target_color: str = "#95c3e8") -> None:
        self.target_size = target_size
        # Auto-calculate step size if not provided - use target_size/3 for guaranteed coverage
        self.step_size = step_size if step_size is not None else max(target_size // 3, 15)
        self.target_color = target_color
        self.target_rgb = self.hex_to_rgb(target_color)
        self.coords = []  # List of (x, y) coordinates for corners
        self.sct = mss.mss()
        self.scan_area = None  # Will store (x1, y1, x2, y2)
        
        # Fast duplicate prevention - track recent clicks
        self.recent_clicks = []  # List of (x, y, timestamp)
        self.click_distance_threshold = target_size * 0.8  # 80% of target size
        self.click_memory_duration = 0.1  # Keep clicks in memory for 100ms

    def hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def collect_coordinates(self) -> list:
        """Collect two corner coordinates using mouse position upon 'C' key press."""
        print("Please position your mouse over 2 corner positions and press 'C' to register each coordinate.")
        print("These will define the rectangular scanning area.")
        prev_key_state = 0
        while len(self.coords) < 2:
            curr_key_state = win32api.GetKeyState(0x43)  # 'C' key

            # Detect press (transition from not pressed to pressed)
            if curr_key_state < 0 and prev_key_state >= 0:
                x, y = win32api.GetCursorPos()
                self.coords.append((x, y))
                print(f"Corner {len(self.coords)} registered: ({x}, {y})")
                time.sleep(0.2)  # debounce delay
            prev_key_state = curr_key_state
            time.sleep(0.01)
            
        # Define scan area from the two corners
        x1, y1 = self.coords[0]
        x2, y2 = self.coords[1]
        self.scan_area = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        print(f"Scan area defined: ({self.scan_area[0]}, {self.scan_area[1]}) to ({self.scan_area[2]}, {self.scan_area[3]})")
        print(f"Using step size: {self.step_size} pixels (auto-calculated from target size: {self.target_size})")
        return self.coords

    def is_too_close_to_recent_click(self, x: int, y: int) -> bool:
        """Check if coordinates are too close to a recent click to avoid duplicates."""
        current_time = time.time()
        
        # Clean old clicks (older than click_memory_duration)
        self.recent_clicks = [(cx, cy, ct) for cx, cy, ct in self.recent_clicks 
                             if current_time - ct < self.click_memory_duration]
        
        # Check distance to recent clicks
        for cx, cy, _ in self.recent_clicks:
            distance = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if distance < self.click_distance_threshold:
                return True
        return False

    def click_at(self, x: int, y: int) -> None:
        """Simulate a mouse click at the specified (x, y) position with no delays."""
        # Check if too close to recent click
        if self.is_too_close_to_recent_click(x, y):
            return
            
        old_x, old_y = win32api.GetCursorPos()  # Save current position
        win32api.SetCursorPos((x, y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        
        # Add to recent clicks
        self.recent_clicks.append((x, y, time.time()))
        print(f"Target found and clicked at ({x}, {y})")

    def capture_scan_area(self) -> Optional[np.ndarray]:
        """Capture the entire scan area as a single screenshot for faster processing."""
        if not self.scan_area:
            return None
            
        x1, y1, x2, y2 = self.scan_area
        region = {'top': y1, 'left': x1, 'width': x2 - x1, 'height': y2 - y1}
        screenshot = self.sct.grab(region)
        return np.array(screenshot)

    def scan_and_click(self) -> None:
        """Scan the defined area for target colors and click found targets instantly."""
        if not self.scan_area:
            print("No scan area defined!")
            return

        # Capture entire area once
        img = self.capture_scan_area()
        if img is None:
            return
            
        x1, y1, x2, y2 = self.scan_area
        targets_found = 0
        target_r, target_g, target_b = self.target_rgb
        tolerance = 10
        
        # Check all scan points in the captured image
        for y in range(y1, y2, self.step_size):
            for x in range(x1, x2, self.step_size):
                # Convert absolute coordinates to relative coordinates in the image
                rel_x = x - x1
                rel_y = y - y1
                
                # Check bounds
                if rel_y < img.shape[0] and rel_x < img.shape[1]:
                    b, g, r = img[rel_y, rel_x, 0], img[rel_y, rel_x, 1], img[rel_y, rel_x, 2]
                    
                    # Check if pixel matches target color
                    if (abs(r - target_r) <= tolerance and 
                        abs(g - target_g) <= tolerance and 
                        abs(b - target_b) <= tolerance):
                        self.click_at(x, y)
                        targets_found += 1

    def monitor_and_click(self, interval: float = 0) -> None:
        """Continuously monitor the scan area and click targets as they appear."""
        print(f"Monitoring scan area for color {self.target_color} (RGB: {self.target_rgb})")
        print(f"Target size: {self.target_size}px, Step size: {self.step_size}px")
        print(f"Duplicate prevention distance: {self.click_distance_threshold:.1f}px")
        print("Press Ctrl+C to exit.")
        
        try:
            while True:
                self.scan_and_click()
                # time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")

def get_user_input() -> tuple:
    """Get user preferences for target size, step size and target color."""
    # Get target size
    target_input = input("Enter target size in pixels (default 160): ").strip()
    target_size = 160
    if target_input:
        try:
            target_size = int(target_input)
            if target_size <= 0:
                print("Invalid target size, using default (160)")
                target_size = 160
        except ValueError:
            print("Invalid target size, using default (160)")
    
    # Get step size (optional)
    step_input = input(f"Enter step size for scanning (default auto-calculated from target size = {target_size//3}): ").strip()
    step_size = None  # Will auto-calculate
    if step_input:
        try:
            step_size = int(step_input)
            if step_size <= 0:
                print("Invalid step size, will auto-calculate")
                step_size = None
        except ValueError:
            print("Invalid step size, will auto-calculate")
    
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
    
    return target_size, step_size, target_color

def main() -> None:
    print("===== Aim Trainer Clicker =====")
    print("This tool scans a rectangular area for a specific color and clicks targets as found.")
    print("Features:")
    print("- Auto-calculated step size based on target size for guaranteed coverage")
    print("- Optimized for maximum speed with minimal delays")
    print("===============================================")
    
    target_size, step_size, target_color = get_user_input()
    print(f"Using target size: {target_size}px, target color: {target_color}")
    if step_size:
        print(f"Using custom step size: {step_size}px")
    else:
        print(f"Auto-calculating step size: {target_size//3}px")
    
    trainer = AimTrainer(step_size=step_size, target_size=target_size, target_color=target_color)
    
    input("Press Enter to begin coordinate registration...")
    trainer.collect_coordinates()
    
    print(f"\nStarting continuous monitoring and clicking.")
    trainer.monitor_and_click(interval=0)

if __name__ == "__main__":
    # TODO - add a way to stop the program instead of reloading the website to not let the program see lmao
    main()