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

    def is_target_color(self, r: int, g: int, b: int) -> bool:
        """
        Check if the RGB values match the target color within tolerance.
        """
        target_r, target_g, target_b = self.target_color
        return (abs(r - target_r) <= self.tolerance and 
                abs(g - target_g) <= self.tolerance and 
                abs(b - target_b) <= self.tolerance)

    def get_pixel_color(self, x: int, y: int) -> tuple:
        """
        Get the RGB color of the pixel at (x, y).
        """
        region = {'top': y, 'left': x, 'width': 1, 'height': 1}
        screenshot = self.sct.grab(region)
        img = np.array(screenshot)
        b, g, r = img[0, 0, 0], img[0, 0, 1], img[0, 0, 2]
        return (r, g, b)

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
        """
        x_pos, y_start, y_end = self.calculate_scan_line()
        gap_count = 0
        in_gap = False
        
        print(f"Scanning from y={y_start} to y={y_end} at x={x_pos}")
        
        for y in range(y_start, y_end + 1):
            r, g, b = self.get_pixel_color(x_pos, y)
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

    def analyze_grid(self) -> None:
        """
        Perform the complete analysis: count gaps and calculate cube grid.
        """
        print("\n=== Starting Grid Analysis ===")
        
        # Count gaps
        gap_count = self.count_gaps()
        print(f"\nTotal gaps detected: {gap_count}")
        
        # Calculate cube grid
        if gap_count > 0:
            grid_size, total_cubes = self.calculate_cube_grid(gap_count)
            print(f"Grid dimensions: {grid_size}x{grid_size}")
            print(f"Total cubes in grid: {total_cubes}")
        else:
            print("No gaps detected - unable to determine grid size")
            print("This might indicate a single row/column or detection issue")

def main() -> None:
    counter = CubeGridCounter()
    print("===== Cube Grid Counter =====")
    print("This tool counts cube grids by detecting gaps between them.")
    print("1. Register 2 opposite corners of the cube area (mouse over + 'C' key)")
    print("2. The program scans a vertical line to detect gaps")
    print("3. Calculates total cubes based on gap count: (gaps + 1)²")
    print("4. Gap color: #2b87d1")
    print("================================")
    input("Press Enter to begin coordinate registration...")
    
    counter.collect_coordinates()
    
    print(f"\nRegistered area: {counter.coords[0]} to {counter.coords[1]}")
    
    input("\nPress Enter to start grid analysis...")
    counter.analyze_grid()
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()