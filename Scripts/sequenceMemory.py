<<<<<<< HEAD
import mss
import numpy as np
import win32api, win32con
import time

class CubeGridCounter:
    def __init__(self) -> None:
        self.coords = []  # List of 2 corner coordinates
        self.sct = mss.mss()
        self.target_color = (0x2b, 0x87, 0xd1)  # RGB values for #2b87d1
        self.tolerance = 0  # Color matching tolerance
        self.screenshot = None  # Store the single screenshot
        self.grid_size = 0  # Store calculated grid size
        self.cube_centers = []  # Store calculated cube centers

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
                
                # Optional: Uncomment to verify each center (but trusting the math as requested)
                # is_valid = self.verify_cube_center(center_coord[0], center_coord[1])
                # print(f"Cube [{row}][{col}]: {center_coord} - Valid: {is_valid}")
        
        print(f"Calculated {len(centers)} cube centers")
        self.cube_centers = centers
        return centers

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
            # Optional: Uncomment to verify before clicking (but trusting math as requested)
            # if not self.verify_cube_center(x, y):
            #     print(f"Skipping invalid center at ({x}, {y})")
            #     continue
            
            # Move cursor and click
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        print(f"Clicked all cubes in {elapsed_ms:.1f}ms ({elapsed_ms/len(self.cube_centers):.1f}ms per cube)")

    def analyze_grid(self) -> None:
        """
        Perform the complete analysis: count gaps and calculate cube grid.
        """
        print("\n=== Starting Grid Analysis ===")
        
        # Count gaps (this will take the screenshot internally)
        gap_count = self.count_gaps()
        print(f"\nTotal gaps detected: {gap_count}")
        
        # Calculate cube grid
        if gap_count > 0:
            grid_size, total_cubes = self.calculate_cube_grid(gap_count)
            self.grid_size = grid_size  # Store for later use
            print(f"Grid dimensions: {grid_size}x{grid_size}")
            print(f"Total cubes in grid: {total_cubes}")
            
            # Calculate cube centers
            self.calculate_cube_centers()
            
        else:
            print("No gaps detected - unable to determine grid size")
            print("This might indicate a single row/column or detection issue")

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
    print("===== Cube Grid Counter =====")
    print("This tool counts cube grids by detecting gaps between them.")
    print("1. Register 2 opposite corners of the cube area (mouse over + 'C' key)")
    print("2. The program takes a single screenshot of the area")
    print("3. Scans a vertical line to detect gaps using the screenshot")
    print("4. Calculates total cubes based on gap count: (gaps + 1)²")
    print("5. Calculates cube centers using relative positioning")
    print("6. Clicks all cube centers rapidly")
    print("Gap color: #2b87d1")
    print("===============================")
    input("Press Enter to begin coordinate registration...")
    
    counter.collect_coordinates()
    
    print(f"\nRegistered area: {counter.coords[0]} to {counter.coords[1]}")
    
    # Run complete sequence
    counter.run_full_sequence()
    
    print("\nSequence complete!")

if __name__ == "__main__":
    main()
=======
dsdfsdf
>>>>>>> c8031803b5e7aa9dc95bdcddf1e5ce3983dfb8be
