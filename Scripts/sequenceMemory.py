import mss
import numpy as np
import win32api, win32con
import time
from collections import deque

class PixelChecker:
    def __init__(self, num_coords=9):
        self.num_coords = num_coords
        self.coords = []
        self.sct = mss.mss()
        # Queue to store coordinates that have turned white
        self.white_sequence = deque()
        self.last_white_detection = 0
        
    def collect_coordinates(self):
        """Collect coordinates using mouse position and 'C' key press
        This avoids any mouse clicks during registration"""
        print(f"Please position your mouse over {self.num_coords} different locations and press 'C' key to register each coordinate.")
        
        # Track state of 'C' key (virtual key code 0x43)
        prev_key_state = 0
        while len(self.coords) < self.num_coords:
            # Check if 'C' key is pressed
            curr_key_state = win32api.GetKeyState(0x43)
            
            # Detect press (transition from not pressed to pressed)
            if curr_key_state < 0 and prev_key_state >= 0:
                # Get current mouse position without clicking
                x, y = win32api.GetCursorPos()
                self.coords.append((x, y))
                print(f"Coordinate {len(self.coords)} registered: ({x}, {y})")
                
                # Add a small delay to avoid multiple detections
                time.sleep(0.2)
            
            prev_key_state = curr_key_state
            time.sleep(0.01)  # Small sleep to reduce CPU usage
            
        print("All coordinates registered!")
        return self.coords
        
    def is_pixel_white(self, x, y, threshold=240):
        """Check if a pixel at (x,y) is white using mss"""
        region = {'top': y, 'left': x, 'width': 1, 'height': 1}
        screenshot = self.sct.grab(region) # Capture the screen region
        img = np.array(screenshot)
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
    
    def click_at(self, x, y):
        """Simulate mouse click at specific coordinates"""
        old_x, old_y = win32api.GetCursorPos() # Store the current mouse position
        win32api.SetCursorPos((x, y)) # Move mouse to the target position
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.05) # Short delay
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        win32api.SetCursorPos((old_x, old_y)) # make Optional: move mouse back to original position
        print(f"Clicked at ({x}, {y})")
    
    def execute_white_sequence(self):
        """Click all coordinates in the white sequence in order"""
        print(f"Executing sequence of {len(self.white_sequence)} clicks...")
        
        sequence_copy = list(self.white_sequence) # Make a copy of the queue to preserve original sequence
        
        # Click each coordinate in order
        for i, coord_index in enumerate(sequence_copy):
            x, y = self.coords[coord_index]
            print(f"Clicking sequence step {i+1}: Coord {coord_index+1} at ({x}, {y})")
            self.click_at(x, y)
            # time.sleep(0.2)  # Short delay between clicks
        
        # Clear the sequence after execution
        self.white_sequence.clear()
        print("Sequence executed and cleared")
    
    def monitor_coordinates(self, interval=0.1, timeout=3.0):
        """Continuously monitor the coordinates for changes to white
        and click them in order if timeout is reached without new white pixels"""
        print(f"Monitoring coordinates. Will click sequence if no new white pixels for {timeout} seconds.")
        print("Press Ctrl+C to exit.")
        
        previous_states = [False] * len(self.coords) # Keep track of previous state for each coordinate
        
        try:
            while True:
                any_new_white = False
                
                for i, (x, y) in enumerate(self.coords):
                    is_white_now = self.is_pixel_white(x, y)
                    
                    if not previous_states[i] and is_white_now:
                        print(f"Coord {i+1} is now white")
                        self.white_sequence.append(i)
                        self.last_white_detection = time.time()
                        any_new_white = True
                    
                    previous_states[i] = is_white_now # Update the previous state
                
                if (not any_new_white and 
                    self.white_sequence and # checks if there are any white coordinates
                    time.time() - self.last_white_detection > timeout):
                    self.execute_white_sequence()
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            
def main():
    # Create pixel checker instance
    checker = PixelChecker()
    
    print("===== Sequence Memory AI =====")
    print("This tool will remember which coordinates turn white and then click them in order.")
    print("1. Register 9 coordinates to monitor (mouse over + 'C' key)")
    print("2. The program monitors these spots for white pixels")
    print("3. After 3 seconds with no new white pixels, clicks will be performed in sequence")
    print("4. Press Ctrl+C to exit")
    print("====================================")
    
    input("Press Enter to begin coordinate registration...")
    
    checker.collect_coordinates()
    
    # Initial check
    print("\nChecking coordinates:")
    checker.check_all_coordinates()
    
    # Start monitoring mode
    print("\nStarting monitoring mode with automatic sequence execution.")
    print("If no new white pixels are detected for 3 seconds, the recorded sequence will be clicked in order.")
    
    checker.monitor_coordinates(interval=0.1, timeout=3.0)
    
if __name__ == "__main__":
    main()