import mss
import numpy as np
import win32api, win32con
import time
from collections import deque

class CubeGridCounter:
    def __init__(self) -> None:
        self.coords = []  # List of 2 corner coordinates
        self.sct = mss.mss()
        self.target_color = (0x2b, 0x87, 0xd1)  # RGB values for #2b87d1
        self.tolerance = 0  # Color matching tolerance
        self.screenshot = None  # Store the single screenshot
        self.grid_size = 0  # Store calculated grid size
        self.cube_centers = []  # Store calculated cube centers
        self.previous_grid_size = 0  # Cache for grid size comparison
        
        # White detection variables
        self.white_cubes = deque()  # Queue of cube indices that are white
        self.last_white_detection = 0.0
        self.last_clicked_pattern = set()  # Store the last pattern of white cubes that were clicked

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

    def take_single_screenshot(self) -> None:
        """
        Take a single screenshot of the defined region and store it for analysis.
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
        
        print(f"Taking screenshot of region: {region}")
        screenshot = self.sct.grab(region)
        self.screenshot = np.array(screenshot)
        self.screenshot_offset = (min_x, min_y)  # Store offset for coordinate conversion
        print("Screenshot captured successfully!")

    def is_target_color(self, r: int, g: int, b: int) -> bool:
        """
        Check if the RGB values match the target color within tolerance.
        """
        target_r, target_g, target_b = self.target_color
        return (abs(int(r) - target_r) <= self.tolerance and 
                abs(int(g) - target_g) <= self.tolerance and 
                abs(int(b) - target_b) <= self.tolerance)

    def get_pixel_color_from_screenshot(self, x: int, y: int) -> tuple:
        """
        Get the RGB color of the pixel at (x, y) from the stored screenshot.
        x, y are global screen coordinates.
        """
        if self.screenshot is None:
            raise ValueError("No screenshot available. Call take_single_screenshot() first.")
        
        # Convert global coordinates to screenshot local coordinates
        local_x = x - self.screenshot_offset[0]
        local_y = y - self.screenshot_offset[1]
        
        # Check bounds
        if (local_x < 0 or local_x >= self.screenshot.shape[1] or 
            local_y < 0 or local_y >= self.screenshot.shape[0]):
            raise IndexError(f"Coordinates ({x}, {y}) -> ({local_x}, {local_y}) out of screenshot bounds")
        
        # Extract RGB values (screenshot is in BGRA format)
        b, g, r = self.screenshot[local_y, local_x, 0], self.screenshot[local_y, local_x, 1], self.screenshot[local_y, local_x, 2]
        return (r, g, b)

    def get_pixel_color(self, x: int, y: int) -> tuple:
        """
        Get the RGB color of the pixel at (x, y).
        This method is kept for compatibility but now uses the single screenshot.
        """
        return self.get_pixel_color_from_screenshot(x, y)

    def is_pixel_white(self, x: int, y: int, threshold: int = 240) -> bool:
        """
        Check if the pixel at (x, y) is approximately white.
        Uses real-time screenshot for white detection.
        """
        region = {'top': y, 'left': x, 'width': 1, 'height': 1}
        screenshot = self.sct.grab(region)
        img = np.array(screenshot)
        b, g, r = img[0, 0, 0], img[0, 0, 1], img[0, 0, 2]
        
        # Check if the pixel is approximately white
        return all(channel >= threshold for channel in (r, g, b))

    def verify_cube_center(self, x: int, y: int) -> bool:
        """
        Verify if the calculated center pixel is actually on a cube (not gap).
        Returns True if pixel is NOT the gap color (i.e., is on a cube).
        
        Usage: Can be used to validate calculated centers before clicking:
        - In calculate_cube_centers(): filter out invalid centers
        - In click_all_cubes(): skip invalid centers
        - As a debug tool to check calculation accuracy
        """
        try:
            r, g, b = self.get_pixel_color_from_screenshot(x, y)
            return not self.is_target_color(r, g, b)  # True if NOT gap color
        except (ValueError, IndexError):
            return False  # Consider out-of-bounds as invalid

    def calculate_scan_line(self) -> tuple:
        """
        Calculate the vertical scan line position and boundaries.
        Returns (x_position, y_start, y_end)
        """
        x1, y1 = self.coords[0]
        x2, y2 = self.coords[1]
        
        # Ensure we have proper min/max values
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Calculate dimensions
        width = max_x - min_x
        height = max_y - min_y
        
        # 5% offset to the right from left edge
        x_position = min_x + int(width * 0.05)
        
        # Reduce height by ~10% on each side to avoid edge artifacts
        height_reduction = int(height * 0.1)
        y_start = min_y + height_reduction
        y_end = max_y - height_reduction
        
        print(f"Scan line: x={x_position}, y_start={y_start}, y_end={y_end}")
        return x_position, y_start, y_end

    def count_gaps(self) -> int:
        """
        Count the number of gaps (target color regions) in the vertical scan line.
        Uses the single screenshot for all pixel color checks.
        """
        # Take a single screenshot before analysis
        self.take_single_screenshot()
        
        x_pos, y_start, y_end = self.calculate_scan_line()
        gap_count = 0
        in_gap = False
        
        print(f"Scanning from y={y_start} to y={y_end} at x={x_pos}")
        
        for y in range(y_start, y_end + 1):
            r, g, b = self.get_pixel_color_from_screenshot(x_pos, y)
            is_target = self.is_target_color(r, g, b)
            
            if is_target and not in_gap:
                # Found start of a new gap
                gap_count += 1
                in_gap = True
                print(f"Gap {gap_count} starts at y={y}")
            elif not is_target and in_gap:
                # Found end of current gap
                in_gap = False
                print(f"Gap {gap_count} ends at y={y-1}")
        
        return gap_count

    def calculate_cube_grid(self, gaps: int) -> tuple:
        """
        Calculate the cube grid dimensions and total count based on gaps.
        Returns (grid_dimension, total_cubes)
        """
        grid_dimension = gaps + 1
        total_cubes = grid_dimension * grid_dimension
        return grid_dimension, total_cubes

    def calculate_cube_centers(self) -> list:
        """
        Calculate the center coordinates of all cubes using relative positioning.
        Returns list of (x, y) tuples representing cube centers.
        """
        if self.grid_size == 0:
            raise ValueError("Grid size not calculated. Run analyze_grid() first.")
        
        x1, y1 = self.coords[0]
        x2, y2 = self.coords[1]
        
        # Ensure we have proper min/max values
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Calculate total dimensions
        total_width = max_x - min_x
        total_height = max_y - min_y
        
        # Calculate cell size (cube + gap space)
        cell_width = total_width / self.grid_size
        cell_height = total_height / self.grid_size
        
        centers = []
        print(f"Calculating centers for {self.grid_size}x{self.grid_size} grid")
        print(f"Cell dimensions: {cell_width:.1f} x {cell_height:.1f}")
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                # Calculate center of each cell
                center_x = min_x + (col * cell_width) + (cell_width / 2)
                center_y = min_y + (row * cell_height) + (cell_height / 2)
                
                center_coord = (int(center_x), int(center_y))
                centers.append(center_coord)
        
        print(f"Calculated {len(centers)} cube centers")
        self.cube_centers = centers
        return centers

    def click_white_cubes(self) -> None:
        """
        Click on all cube centers that were detected as white, then clear the white list.
        Only clicks if the pattern is different from the last clicked pattern.
        """
        if not self.white_cubes:
            print("No white cubes to click")
            return
        
        # Convert current white cubes to a set for comparison
        current_pattern = set(self.white_cubes)
        
        # Check if this pattern is the same as the last clicked pattern
        if current_pattern == self.last_clicked_pattern:
            print(f"Same pattern detected ({len(current_pattern)} cubes) - skipping click to avoid duplicates")
            self.white_cubes.clear()
            return
        
        white_positions = []
        for cube_index in self.white_cubes:
            if cube_index < len(self.cube_centers):
                white_positions.append(self.cube_centers[cube_index])
        
        if not white_positions:
            print("No valid white cube positions found")
            self.white_cubes.clear()
            return
        
        print(f"Clicking {len(white_positions)} white cubes (new pattern)...")
        start_time = time.time()
        
        for i, (x, y) in enumerate(white_positions):
            # Move cursor and click
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        print(f"Clicked {len(white_positions)} white cubes in {elapsed_ms:.1f}ms ({elapsed_ms/len(white_positions):.1f}ms per cube)")
        
        # Store this pattern as the last clicked pattern
        self.last_clicked_pattern = current_pattern.copy()
        
        # Clear the white cubes list after clicking
        self.white_cubes.clear()
        print("White cube list cleared")

    def click_all_cubes(self) -> None:
        """
        Click on all calculated cube centers rapidly.
        Waits 1 second before starting, then clicks without delays.
        """
        if not self.cube_centers:
            raise ValueError("No cube centers calculated. Run calculate_cube_centers() first.")
        
        print(f"\nWaiting 1 second before clicking {len(self.cube_centers)} cubes...")
        time.sleep(1.0)
        
        print("Starting rapid clicking...")
        start_time = time.time()
        
        for i, (x, y) in enumerate(self.cube_centers):
            # Move cursor and click
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        print(f"Clicked all cubes in {elapsed_ms:.1f}ms ({elapsed_ms/len(self.cube_centers):.1f}ms per cube)")

    def analyze_grid(self) -> bool:
        """
        Perform the complete analysis: count gaps and calculate cube grid.
        Returns True if analysis was successful, False otherwise.
        """
        print("\n=== Starting Grid Analysis ===")
        
        # Count gaps (this will take the screenshot internally)
        gap_count = self.count_gaps()
        print(f"\nTotal gaps detected: {gap_count}")
        
        # Calculate cube grid
        if gap_count > 0:
            new_grid_size, total_cubes = self.calculate_cube_grid(gap_count)
            
            # Check if grid size actually changed
            if new_grid_size != self.grid_size:
                print(f"Grid size changed: {self.grid_size}x{self.grid_size} -> {new_grid_size}x{new_grid_size}")
                self.grid_size = new_grid_size
                # Reset the last clicked pattern when grid changes
                self.last_clicked_pattern = set()
                # Force recalculation of cube centers
                self.calculate_cube_centers()
                return True
            else:
                print(f"Grid size unchanged: {self.grid_size}x{self.grid_size}")
                return False
            
        else:
            print("No gaps detected - unable to determine grid size")
            print("This might indicate a single row/column or detection issue")
            return False

    def monitor_white_cubes_batch(self, batch_interval: float = 0.05, timeout: float = 3.0) -> int:
        """
        Monitor all cube centers for white pixels in batches for better performance.
        Returns the number of white cubes detected.
        """
        if not self.cube_centers:
            return 0
        
        white_count = 0
        last_detection_time = time.time()
        
        print(f"Starting batch monitoring of {len(self.cube_centers)} cubes...")
        
        while time.time() - last_detection_time < timeout:
            batch_start = time.time()
            new_whites_this_batch = 0
            
            # Check all cubes in this batch
            for i, (x, y) in enumerate(self.cube_centers):
                try:
                    if self.is_pixel_white(x, y):
                        if i not in self.white_cubes:  # Only add if not already in queue
                            self.white_cubes.append(i)
                            print(f"Cube {i+1} at ({x}, {y}) is now white")
                            new_whites_this_batch += 1
                            white_count += 1
                except Exception as e:
                    # Skip problematic coordinates
                    continue
            
            # If we found new white cubes, reset the timeout
            if new_whites_this_batch > 0:
                last_detection_time = time.time()
            
            # Sleep for the remaining batch interval
            elapsed = time.time() - batch_start
            sleep_time = max(0, batch_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        return white_count

    def run_white_detection_mode(self) -> None:
        """
        Run the complete white detection sequence with grid re-analysis after each click batch.
        """
        print("Starting white detection mode with grid re-analysis after each click batch...")
        
        try:
            # Initial grid analysis
            self.analyze_grid()
            
            if not self.cube_centers:
                print("No valid cube centers found initially - exiting...")
                return
            
            while True:
                # Monitor for white cubes with faster detection
                white_count = self.monitor_white_cubes_batch(
                    batch_interval=0.05,  # Check all cubes every 50ms
                    timeout=2.0  # Wait 2 seconds after last white detection
                )
                
                # Click any detected white cubes
                if self.white_cubes:
                    self.click_white_cubes()
                    
                    # Re-analyze grid after clicking white cubes
                    print("Re-analyzing grid after clicking white cubes...")
                    grid_changed = self.analyze_grid()
                    
                    if grid_changed:
                        print("Grid layout changed - using new cube positions")
                    elif not self.cube_centers:
                        print("No valid cube centers found - retrying...")
                        time.sleep(1.0)
                        continue
                
                # Short pause before next detection cycle
                time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nWhite detection mode stopped.")

    def run_full_sequence(self) -> None:
        """
        Run the complete sequence: analyze grid and click all cubes.
        """
        self.analyze_grid()
        
        if self.cube_centers:
            self.click_all_cubes()
        else:
            print("No valid cube centers found - skipping clicking phase")

def main() -> None:
    counter = CubeGridCounter()
    print("===== Enhanced Cube Grid Counter =====")
    print("This tool detects cube grids and monitors for white flashes.")
    print("")
    print("Setup Process:")
    print("1. Register 2 opposite corners of the cube area (mouse over + 'C' key)")
    print("2. Automatic white detection mode will start")
    print("=====================================")
    
    counter.collect_coordinates()
    print(f"\nRegistered area: {counter.coords[0]} to {counter.coords[1]}")
    print("\nStarting white detection mode automatically...")
    
    counter.run_white_detection_mode()
    
    print("Program complete!")

if __name__ == "__main__":
    main()