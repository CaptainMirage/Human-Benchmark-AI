import win32api, win32con
import time
from typing import List, Tuple

class MouseController:
    def __init__(self, num_coords: int = 2) -> None:
        self.num_coords = num_coords
        self.coords: List[Tuple[int, int]] = []  # List of (x, y) coordinates

    def collect_coordinates(self) -> List[Tuple[int, int]]:
        """
        Collect coordinates using direct mouse clicks.
        Prompts the user to click at the required number of positions.
        """
        print(f"Please click on {self.num_coords} different locations to register your coordinates.")
        
        prev_click_state = 0
        while len(self.coords) < self.num_coords:
            # Check left mouse button state (1 for left mouse button)
            curr_click_state = win32api.GetKeyState(0x01)
            
            # Detect click (transition from not pressed to pressed)
            if curr_click_state < 0 and prev_click_state >= 0:
                # Get current mouse position
                x, y = win32api.GetCursorPos()
                self.coords.append((x, y))
                print(f"Coordinate {len(self.coords)} registered: ({x}, {y})")
                time.sleep(0.2)  # debounce delay
            
            prev_click_state = curr_click_state
            time.sleep(0.01)  # Small sleep to reduce CPU usage
            
        print("All coordinates registered!")
        return self.coords

    def click_at(self, x: int, y: int) -> None:
        """
        Simulate a mouse click at the specified (x, y) position.
        """
        win32api.SetCursorPos((x, y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        print(f"Clicked at ({x}, {y})")

    def right_click_at(self, x: int, y: int) -> None:
        """
        Simulate a right mouse click at the specified (x, y) position.
        """
        win32api.SetCursorPos((x, y))
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
        print(f"Right-clicked at ({x}, {y})")

    def press_key(self, key_code: int) -> None:
        """
        Simulate a keyboard key press.
        """
        win32api.keybd_event(key_code, 0, 0, 0)  # Key down
        time.sleep(0.05)
        win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)  # Key up
        print(f"Pressed key with code {key_code}")

    def drag_between_points(self, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        """
        Click and hold at starting coordinates, drag to ending coordinates, then release.
        """
        # Move to starting position
        win32api.SetCursorPos((start_x, start_y))
        
        # Click and hold
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, start_x, start_y, 0, 0)
        print(f"Mouse down at ({start_x}, {start_y})")
        
        # Small delay before drag
        time.sleep(0.2)
        
        # Move to end position (this creates the drag effect)
        win32api.SetCursorPos((end_x, end_y))
        print(f"Dragged to ({end_x}, {end_y})")
        
        # Small delay before release
        time.sleep(0.2)
        
        # Release mouse button
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, end_x, end_y, 0, 0)
        print("Mouse up - drag complete")

    def execute_action_sequence(self) -> None:
        """
        Executes the defined sequence of actions:
        1. Click and drag from first to second coordinate
        2. Right click in the middle of the coordinates
        3. Press the 'C' key
        """
        if len(self.coords) < 2:
            print("Error: Need at least two coordinates to perform actions.")
            return
        
        # Get the two coordinates
        start_x, start_y = self.coords[0]
        end_x, end_y = self.coords[1]
        
        # 1. Click and drag from first to second coordinate
        print("\nPerforming click and drag operation...")
        self.drag_between_points(start_x, start_y, end_x, end_y)
        
        # 2. Calculate the middle point and right click there
        middle_x = (start_x + end_x) // 2
        middle_y = (start_y + end_y) // 2
        print(f"\nRight-clicking at middle point ({middle_x}, {middle_y})...")
        self.right_click_at(middle_x, middle_y)
        
        # 3. Press the 'C' key (virtual key code 0x43)
        print("\nPressing the 'C' key...")
        self.press_key(0x43)
        
        print("\nAction sequence completed!")


def main() -> None:
    controller = MouseController(num_coords=2)
    
    print("===== Mouse Action Sequence Tool =====")
    print("This tool will:")
    print("1. Let you select 2 coordinates by clicking")
    print("2. Click and drag from the first coordinate to the second")
    print("3. Right-click at the middle point between coordinates")
    print("4. Press the 'C' key")
    print("====================================")
    input("Press Enter to begin coordinate registration...")
    
    controller.collect_coordinates()
    
    print("\nStarting action sequence in 3 seconds...")
    print("Keep your mouse still")
    time.sleep(3)
    
    controller.execute_action_sequence()


if __name__ == "__main__":
    main()