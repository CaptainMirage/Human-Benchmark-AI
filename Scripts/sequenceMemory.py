import mss
import numpy as np
import win32api, win32con
import time
import sys

class PixelChecker:
    def __init__(self, num_coords=9):
        self.num_coords = num_coords
        self.coords = []
        self.sct = mss.mss()
        
    def collect_coordinates(self):
        """Collect coordinates using mouse clicks with win32api"""
        print(f"Please click on {self.num_coords} different locations to register coordinates...")
        print("Press left mouse button to register a coordinate.")
        
        # Track state of left mouse button
        prev_state = 0
        
        while len(self.coords) < self.num_coords:
            # Check if left mouse button is pressed
            curr_state = win32api.GetKeyState(0x01)  # 0x01 is the virtual key code for left mouse button
            
            # Detect press (transition from not pressed to pressed)
            if curr_state < 0 and prev_state >= 0:
                # Get current mouse position
                x, y = win32api.GetCursorPos()
                self.coords.append((x, y))
                print(f"Coordinate {len(self.coords)} registered: ({x}, {y})")
                
                # Add a small delay to avoid multiple detections for the same click
                time.sleep(0.2)
            
            prev_state = curr_state
            time.sleep(0.01)  # Small sleep to reduce CPU usage
            
        print("All coordinates registered!")
        return self.coords
        
    def is_pixel_white(self, x, y, threshold=240):
        """Check if a pixel at (x,y) is white using mss"""
        # Define a small region around the pixel
        region = {'top': y, 'left': x, 'width': 1, 'height': 1}
        
        # Capture the screen region
        screenshot = self.sct.grab(region)
        
        # Convert to numpy array for easier processing
        img = np.array(screenshot)
        
        # Get RGB values (mss returns BGRA)
        b, g, r = img[0, 0, 0], img[0, 0, 1], img[0, 0, 2]
        
        # Check if the pixel is approximately white
        return all(channel >= threshold for channel in (r, g, b))
    
    def check_all_coordinates(self):
        """Check all stored coordinates for white pixels and only report white ones"""
        any_white = False
        for i, (x, y) in enumerate(self.coords, 1):
            if self.is_pixel_white(x, y):
                print(f"Coord {i} is white")
                any_white = True
        
        if not any_white:
            print("No white coordinates detected")
        return any_white
    
    def monitor_coordinates(self, interval=0.1):
        """Continuously monitor the coordinates for changes to white"""
        print("Monitoring coordinates. Press Ctrl+C to exit.")
        
        # Keep track of previous state for each coordinate
        # False = not white, True = white
        previous_states = [False] * len(self.coords)
        
        try:
            while True:
                for i, (x, y) in enumerate(self.coords):
                    is_white_now = self.is_pixel_white(x, y)
                    
                    # If it wasn't white before but is white now, notify
                    if not previous_states[i] and is_white_now:
                        print(f"Coord {i+1} is now white")
                    
                    # Update the previous state
                    previous_states[i] = is_white_now
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            
def main():
    # Create pixel checker instance
    checker = PixelChecker()
    
    # Collect coordinates
    checker.collect_coordinates()
    
    # Initial check
    print("\nChecking coordinates:")
    checker.check_all_coordinates()
    
    # Ask if user wants to monitor continuously
    monitor = input("\nDo you want to continue monitoring all the coordinates? (y/n): ").lower()
    if monitor == 'y':
        checker.monitor_coordinates()
    
if __name__ == "__main__":
    main()