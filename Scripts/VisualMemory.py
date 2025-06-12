import mss
import numpy as np
import win32api, win32con
import time
from collections import deque

class CubeGridCounter:
    def __init__(self) -> None:
        self.coords = []  # List of 2 corner coordinates
        self.sct = mss.mss()
        self.target_color = (0x2b, 0x87, 0xd1)  # RGB values for #2b87d1 (gap color)
        self.default_cube_color = (0x25, 0x73, 0xc1)  # RGB values for #2573c1 (default cube)
        self.clicked_cube_color = (0x15, 0x43, 0x68)  # RGB values for #154368 (clicked/wrong cube)
        self.tolerance = 5  # Increased tolerance for color matching
        self.grid_size = 0  # Store calculated grid size
        self.cube_centers = []  # Store calculated cube centers
        
        # White detection variables
        self.white_cubes = set()  # Use set to avoid duplicates
        self.last_clicked_pattern = set()  # Store the last pattern of white cubes that were clicked
        self.consecutive_same_grids = 0  # Track consecutive same grid detections

    def collect_coordinates(self) -> list:
        """
        Collect 2 corner coordinates using mouse position upon 'C' key press.
        """
        print("Please position your mouse over 2 opposite corners of the cube area and press 'C' to register each coordinate.")
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
            
        print("Both corners registered!")
        return self.coords

    def take_screenshot(self) -> np.ndarray:
        """
        Take a fresh screenshot of the defined region.
        Returns the screenshot as numpy array.
        """
        x1, y1 = self.coords[0]
        x2, y2 = self.coords[1]
        
        # Ensure we have proper min/max values
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Define the region to capture
        region = {
            'top': min_y,
            'left': min_x,
            'width': max_x - min_x,
            'height': max_y - min_y
        }
        
        screenshot = self.sct.grab(region)
        screenshot_array = np.array(screenshot)
        self.screenshot_offset = (min_x, min_y)  # Store offset for coordinate conversion
        return screenshot_array

    def is_color_match(self, r: int, g: int, b: int, target_color: tuple) -> bool:
        """
        Check if RGB values match target color within tolerance.
        """
        target_r, target_g, target_b = target_color
        return (abs(int(r) - target_r) <= self.tolerance and 
                abs(int(g) - target_g) <= self.tolerance and 
                abs(int(b) - target_b) <= self.tolerance)

    def get_pixel_color_from_screenshot(self, screenshot: np.ndarray, x: int, y: int) -> tuple:
        """
        Get the RGB color of pixel at global coordinates (x, y) from screenshot.
        """
        # Convert global coordinates to screenshot local coordinates
        local_x = x - self.screenshot_offset[0]
        local_y = y - self.screenshot_offset[1]
        
        # Check bounds
        if (local_x < 0 or local_x >= screenshot.shape[1] or 
            local_y < 0 or local_y >= screenshot.shape[0]):
            raise IndexError(f"Coordinates ({x}, {y}) -> ({local_x}, {local_y}) out of screenshot bounds")
        
        # Extract RGB values (screenshot is in BGRA format)
        b, g, r = screenshot[local_y, local_x, 0], screenshot[local_y, local_x, 1], screenshot[local_y, local_x, 2]
        return (r, g, b)

    def is_pixel_white(self, x: int, y: int, threshold: int = 240) -> bool:
        """
        Check if pixel at (x, y) is white using fresh screenshot.
        """
        try:
            region = {'top': y, 'left': x, 'width': 1, 'height': 1}
            screenshot = self.sct.grab(region)
            img = np.array(screenshot)
            b, g, r = img[0, 0, 0], img[0, 0, 1], img[0, 0, 2]
            return all(channel >= threshold for channel in (r, g, b))
        except:
            return False

    def is_cube_clickable(self, x: int, y: int) -> bool:
        """
        Check if cube at position is safe to click (not already clicked/wrong).
        Returns False if cube is the clicked color (#154368).
        """
        try:
            region = {'top': y, 'left': x, 'width': 1, 'height': 1}
            screenshot = self.sct.grab(region)
            img = np.array(screenshot)
            b, g, r = img[0, 0, 0], img[0, 0, 1], img[0, 0, 2]
            
            # Check if it's the clicked/wrong cube color
            return not self.is_color_match(r, g, b, self.clicked_cube_color)
        except:
            return False

    def calculate_scan_line(self) -> tuple:
        """
        Calculate the vertical scan line position and boundaries.
        """
        x1, y1 = self.coords[0]
        x2, y2 = self.coords[1]
        
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # 5% offset to the right from left edge
        x_position = min_x + int(width * 0.05)
        
        # Reduce height by ~10% on each side to avoid edge artifacts
        height_reduction = int(height * 0.1)
        y_start = min_y + height_reduction
        y_end = max_y - height_reduction
        
        return x_position, y_start, y_end

    def detect_grid_size(self) -> int:
        """
        Detect current grid size by counting gaps.
        Returns grid size (gaps + 1) or 0 if detection failed.
        """
        screenshot = self.take_screenshot()
        x_pos, y_start, y_end = self.calculate_scan_line()
        
        gap_count = 0
        in_gap = False
        
        for y in range(y_start, y_end + 1):
            try:
                r, g, b = self.get_pixel_color_from_screenshot(screenshot, x_pos, y)
                is_gap = self.is_color_match(r, g, b, self.target_color)
                
                if is_gap and not in_gap:
                    gap_count += 1
                    in_gap = True
                elif not is_gap and in_gap:
                    in_gap = False
            except:
                continue
        
        return gap_count + 1 if gap_count > 0 else 0

    def force_grid_update(self) -> bool:
        """
        Force detection of current grid size and update cube centers.
        Returns True if grid was updated, False otherwise.
        """
        new_grid_size = self.detect_grid_size()
        
        if new_grid_size > 0 and new_grid_size != self.grid_size:
            print(f"Grid size changed: {self.grid_size}x{self.grid_size} -> {new_grid_size}x{new_grid_size}")
            self.grid_size = new_grid_size
            self.calculate_cube_centers()
            self.last_clicked_pattern = set()  # Reset clicked pattern
            self.consecutive_same_grids = 0
            return True
        elif new_grid_size == self.grid_size:
            self.consecutive_same_grids += 1
        
        return False

    def calculate_cube_centers(self) -> list:
        """
        Calculate center coordinates of all cubes in current grid.
        """
        if self.grid_size == 0:
            return []
        
        x1, y1 = self.coords[0]
        x2, y2 = self.coords[1]
        
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        total_width = max_x - min_x
        total_height = max_y - min_y
        
        cell_width = total_width / self.grid_size
        cell_height = total_height / self.grid_size
        
        centers = []
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                center_x = min_x + (col * cell_width) + (cell_width / 2)
                center_y = min_y + (row * cell_height) + (cell_height / 2)
                centers.append((int(center_x), int(center_y)))
        
        self.cube_centers = centers
        print(f"Updated cube centers for {self.grid_size}x{self.grid_size} grid ({len(centers)} cubes)")
        return centers

    def scan_for_white_cubes(self) -> set:
        """
        Scan all cube centers for white pixels.
        Returns set of cube indices that are white.
        """
        white_indices = set()
        
        if not self.cube_centers:
            return white_indices
        
        for i, (x, y) in enumerate(self.cube_centers):
            if self.is_pixel_white(x, y) and self.is_cube_clickable(x, y):
                white_indices.add(i)
        
        return white_indices

    def click_white_cubes(self) -> bool:
        """
        Click all currently detected white cubes.
        Returns True if any cubes were clicked.
        """
        if not self.white_cubes:
            return False
        
        # Convert to pattern for comparison
        current_pattern = set(self.white_cubes)
        
        # Skip if same pattern as last clicked
        if current_pattern == self.last_clicked_pattern:
            print(f"Same pattern detected ({len(current_pattern)} cubes) - skipping")
            return False
        
        # Validate all cubes are still clickable before clicking any
        valid_cubes = []
        for cube_index in self.white_cubes:
            if cube_index < len(self.cube_centers):
                x, y = self.cube_centers[cube_index]
                if self.is_cube_clickable(x, y):
                    valid_cubes.append((cube_index, x, y))
        
        if not valid_cubes:
            print("No valid white cubes to click")
            return False
        
        print(f"Clicking {len(valid_cubes)} white cubes...")
        
        # Click all valid cubes rapidly
        for cube_index, x, y in valid_cubes:
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        
        # Store clicked pattern
        self.last_clicked_pattern = current_pattern.copy()
        print(f"Successfully clicked {len(valid_cubes)} cubes")
        return True

    def run_detection_loop(self) -> None:
        """
        Main detection loop with improved grid change detection.
        """
        print("Starting white cube detection with improved grid tracking...")
        
        # Initial grid detection
        if not self.force_grid_update():
            print("Failed to detect initial grid - retrying...")
            time.sleep(1.0)
            if not self.force_grid_update():
                print("Could not detect grid - exiting")
                return
        
        no_whites_count = 0
        
        try:
            while True:
                # Check for grid changes more frequently
                if no_whites_count % 10 == 0:  # Every 10 cycles when no whites found
                    self.force_grid_update()
                
                # Scan for white cubes
                self.white_cubes = self.scan_for_white_cubes()
                
                if self.white_cubes:
                    print(f"Found {len(self.white_cubes)} white cubes: {sorted(self.white_cubes)}")
                    
                    # Small delay to ensure cubes are stable
                    time.sleep(0.05)
                    
                    # Re-verify white cubes before clicking
                    verified_whites = self.scan_for_white_cubes()
                    self.white_cubes = verified_whites
                    
                    time.sleep(2)

                    if self.white_cubes:
                        clicked = self.click_white_cubes()
                        if clicked:
                            # Force grid check after successful click
                            time.sleep(0.1)
                            self.force_grid_update()
                            no_whites_count = 0
                    
                    self.white_cubes.clear()
                else:
                    no_whites_count += 1
                
                # Short sleep to prevent excessive CPU usage
                time.sleep(0.02)  # 50 FPS checking
                
        except KeyboardInterrupt:
            print("\nDetection stopped by user.")

def main() -> None:
    counter = CubeGridCounter()
    print("===== Fixed Cube Grid Counter =====")
    print("Improvements:")
    print("- Better grid change detection")
    print("- Validation before clicking")
    print("- Avoided clicking wrong cubes")
    print("- Removed unused functions")
    print("=====================================")
    
    counter.collect_coordinates()
    print(f"\nRegistered area: {counter.coords[0]} to {counter.coords[1]}")
    print("\nStarting improved detection mode...")
    
    counter.run_detection_loop()
    print("Program complete!")

if __name__ == "__main__":
    main()
    # TODO = make the timings right, the system seesm to work