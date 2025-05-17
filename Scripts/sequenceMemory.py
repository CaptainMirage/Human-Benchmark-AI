import mss
import numpy as np
import win32api, win32con
import time
import sys
from collections import deque

class PixelChecker:
    def __init__(self, num_coords=9):
        self.num_coords = num_coords
        self.coords = []
        self.sct = mss.mss()
        # Queue to store coordinates that have turned white
        self.white_sequence = deque()
        # Last time a white pixel was detected
        self.last_white_detection = 0
        
    def collect_coordinates(self):
        """Collect coordinates using mouse hover and keyboard trigger (Space) with win32api
        This method doesn't perform actual clicks to avoid triggering actions"""
        print(f"Please hover your mouse over {self.num_coords} different locations and press SPACE to register each coordinate.")
        print("NO clicks will be performed during registration.")
        
        # Track state of space bar
        prev_space_state = 0
        
        while len(self.coords) < self.num_coords:
            # Check if space bar is pressed
            curr_space_state = win32api.GetKeyState(0x20)  # 0x20 is the virtual key code for space bar
            
            # Detect press (transition from not pressed to pressed)
            if curr_space_state < 0 and prev_space_state >= 0:
                # Get current mouse position without clicking
                x, y = win32api.GetCursorPos()
                self.coords.append((x, y))
                print(f"Coordinate {len(self.coords)} registered: ({x}, {y})")
                
                # Add a small delay to avoid multiple detections
                time.sleep(0.2)
            
            prev_space_state = curr_space_state
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
    
    def click_at(self, x, y):
        """Simulate mouse click at specific coordinates"""
        # Store the current mouse position
        old_x, old_y = win32api.GetCursorPos()
        
        # Move mouse to the target position
        win32api.SetCursorPos((x, y))
        
        # Perform the click
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.05)  # Short delay
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        
        # Optional: move mouse back to original position
        win32api.SetCursorPos((old_x, old_y))
        
        print(f"Clicked at ({x}, {y})")
    
    def execute_white_sequence(self):
        """Click all coordinates in the white sequence in order"""
        print(f"Executing sequence of {len(self.white_sequence)} clicks...")
        
        # Make a copy of the queue to preserve original sequence
        sequence_copy = list(self.white_sequence)
        
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
        
        # Keep track of previous state for each coordinate
        # False = not white, True = white
        previous_states = [False] * len(self.coords)
        
        try:
            while True:
                any_new_white = False
                
                for i, (x, y) in enumerate(self.coords):
                    is_white_now = self.is_pixel_white(x, y)
                    
                    # If it wasn't white before but is white now, notify and add to sequence
                    if not previous_states[i] and is_white_now:
                        print(f"Coord {i+1} is now white")
                        self.white_sequence.append(i)
                        self.last_white_detection = time.time()
                        any_new_white = True
                    
                    # Update the previous state
                    previous_states[i] = is_white_now
                
                # Check if we should execute the sequence
                if (not any_new_white and 
                    len(self.white_sequence) > 0 and 
                    time.time() - self.last_white_detection > timeout):
                    self.execute_white_sequence()
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            
def main():
    # Create pixel checker instance
    checker = PixelChecker()
    
    # Show instructions
    print("===== Sequence Memory Clicker =====")
    print("This tool will remember which coordinates turn white and then click them in order.")
    print("INSTRUCTIONS:")
    print("1. First, you'll register 9 coordinates to monitor")
    print("2. HOVER your mouse over each point and press SPACE (this won't perform any clicks)")
    print("3. The program will monitor these spots for white pixels")
    print("4. When spots turn white, they'll be recorded in sequence")
    print("5. If no new white pixels appear for 3 seconds, it will automatically click") 
    print("   all recorded white spots in the order they appeared")
    print("6. Press Ctrl+C at any time to exit")
    print("====================================")
    
    input("Press Enter to begin coordinate registration...")
    
    # Collect coordinates
    checker.collect_coordinates()
    
    # Initial check
    print("\nChecking coordinates:")
    checker.check_all_coordinates()
    
    # Start monitoring mode
    print("\nStarting monitoring mode with automatic sequence execution.")
    print("When pixels turn white, they'll be recorded in sequence.")
    print("If no new white pixels are detected for 3 seconds, the recorded sequence will be clicked in order.")
    
    checker.monitor_coordinates(interval=0.1, timeout=3.0)
    
if __name__ == "__main__":
    main()