import win32api, win32con
import time
import pyperclip  # For clipboard operations
from typing import List, Tuple
import win32clipboard

class MouseController:
    def __init__(self, num_coords: int = 1, typing_delay: float = 0.01) -> None:
        self.num_coords = num_coords
        self.coords: List[Tuple[int, int]] = []  # List of (x, y) coordinates
        self.typing_delay = typing_delay  # Delay between keystrokes

    def wait_for_page_switch(self, seconds: int = 5) -> None:
        """
        Prompt the user to switch to the target page and wait for the specified number of seconds.
        """
        print(f"\nPlease switch to the page where you want to run the script...")
        print(f"Waiting {seconds} seconds...")
        
        for i in range(seconds, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
        print("Starting!")

    def open_browser_console(self) -> None:
        """
        Open the browser console using Ctrl+Shift+K.
        """
        print("Opening browser console with Ctrl+Shift+K...")
        
        # Virtual key codes
        CTRL_KEY = 0x11
        SHIFT_KEY = 0x10
        K_KEY = 0x4B
        
        # Press Ctrl+Shift+K
        win32api.keybd_event(CTRL_KEY, 0, 0, 0)  # Ctrl down
        win32api.keybd_event(SHIFT_KEY, 0, 0, 0)  # Shift down
        time.sleep(0.05)
        win32api.keybd_event(K_KEY, 0, 0, 0)  # K down
        time.sleep(0.05)
        win32api.keybd_event(K_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # K up
        win32api.keybd_event(SHIFT_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # Shift up
        win32api.keybd_event(CTRL_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl up
        
        time.sleep(0.3)  # Wait for console to open

    def paste_text_fast(self, text: str) -> None:
        """
        Ultra-fast paste using direct clipboard manipulation.
        """
        # Save original clipboard content
        try:
            win32clipboard.OpenClipboard()
            original_clipboard = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except:
            original_clipboard = ""
        
        # Set new text to clipboard
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"Clipboard error: {e}")
            return
        
        time.sleep(0.01)  # Minimal delay
        
        # Ultra-fast Ctrl+V
        CTRL_KEY = 0x11
        V_KEY = 0x56
        
        win32api.keybd_event(CTRL_KEY, 0, 0, 0)  # Ctrl down
        win32api.keybd_event(V_KEY, 0, 0, 0)  # V down
        win32api.keybd_event(V_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # V up
        win32api.keybd_event(CTRL_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl up
        
        time.sleep(0.01)
        
        # Restore original clipboard content
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            if original_clipboard:
                win32clipboard.SetClipboardText(original_clipboard, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except:
            pass

    def paste_text(self, text: str) -> None:
        """
        Paste the provided text at the current cursor position.
        """
        # Save original clipboard content
        original_clipboard = pyperclip.paste()
        
        # Copy new text to clipboard
        pyperclip.copy(text)
        time.sleep(0.05)
        
        # Paste using Ctrl+V
        self.press_ctrl_v()
        time.sleep(0.05)
        
        # Restore original clipboard content
        pyperclip.copy(original_clipboard)

    def press_enter(self) -> None:
        """
        Simulate pressing the Enter key.
        """
        ENTER_KEY = 0x0D
        win32api.keybd_event(ENTER_KEY, 0, 0, 0)  # Enter down
        time.sleep(0.02)
        win32api.keybd_event(ENTER_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # Enter up
        print("Pressed Enter")
        time.sleep(0.05)

    def press_ctrl_v(self) -> None:
        """
        Simulate pressing Ctrl+V key combination.
        """
        # Virtual key codes: VK_CONTROL (0x11), 'V' (0x56)
        CTRL_KEY = 0x11
        V_KEY = 0x56
        
        # Press Ctrl key
        win32api.keybd_event(CTRL_KEY, 0, 0, 0)  # Ctrl down
        
        # Press V key while holding Ctrl
        win32api.keybd_event(V_KEY, 0, 0, 0)  # V down
        time.sleep(0.02)
        win32api.keybd_event(V_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # V up
        
        # Release Ctrl key
        win32api.keybd_event(CTRL_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl up
        
        print("Pressed Ctrl+V")

    def inject_typing_script(self) -> None:
        """
        Inject JavaScript to enable typing by overriding stopImmediatePropagation.
        """
        # Script to override stopImmediatePropagation to allow typing
        enable_typing_comment = "// This script allows the user to type again by overriding stopImmediatePropagation"
        enable_typing_code = """(function() {
  const originalStopImmediatePropagation = Event.prototype.stopImmediatePropagation;
  Event.prototype.stopImmediatePropagation = function() {
    // Override to do nothing
  };
})();"""
        
        # Open console
        self.open_browser_console()
        
        # TODO - make the paste thing more efficient maybe even make it just output it somehow?
        # Paste and run typing script
        print("\nRunning script to enable typing...")
        self.paste_text(enable_typing_comment)
        self.press_enter()
        self.paste_text(enable_typing_code)
        self.press_enter()
        time.sleep(0.2)
        
        # Close console with f12 key
        F12_KEY = 0x7B
        win32api.keybd_event(F12_KEY, 0, 0, 0)  # f12 down
        time.sleep(0.02)
        win32api.keybd_event(F12_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # f12 up
        print("Closed console with f12 key")
        time.sleep(0.3)

    def run_console_scripts(self) -> None:
        """
        Run initial scripts in the browser console to enable text selection and copying.
        this can technically work for other websites (specially the selection code), but i only tested it on human benchmark
        """
        # Script 1: Enable text selection
        enable_selection_comment = "// This script enables text selection on all elements of the page"
        enable_selection_code = """if (typeof style === 'undefined') {
  let style = document.createElement('style');
  style.innerHTML = `* { -webkit-user-select: text !important; -moz-user-select: text !important; -ms-user-select: text !important; user-select: text !important; }`;
  document.head.appendChild(style);
}"""
        
        # Script 2: Enable copy functionality
        enable_copy_comment = "// This script enables Ctrl+C and other clipboard operations on the page"
        enable_copy_code = """(function() {
  const allowCopy = (e) => {
    e.stopImmediatePropagation();
    return true;
  };

  ['copy', 'cut', 'paste', 'keydown', 'keypress', 'keyup'].forEach((evt) => {
    document.addEventListener(evt, allowCopy, true);
  });
})();"""
        
        # Open console
        self.open_browser_console()
        
        # Paste and run first script
        print("\nRunning script to enable text selection...")
        self.paste_text(enable_selection_comment)
        self.press_enter()
        self.paste_text(enable_selection_code)
        self.press_enter()
        time.sleep(0.2)
        
        # Paste and run second script
        print("\nRunning script to enable copy functionality...")
        self.paste_text(enable_copy_comment)
        self.press_enter()
        self.paste_text(enable_copy_code)
        self.press_enter()
        time.sleep(0.2)
        
        # Close console with f12 key
        F12_KEY = 0x7B
        win32api.keybd_event(F12_KEY, 0, 0, 0)  # f12 down
        time.sleep(0.02)
        win32api.keybd_event(F12_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # f12 up
        print("Closed console with f12 key")
        time.sleep(0.3)

    def collect_coordinates(self) -> List[Tuple[int, int]]:
        """
        Collect a single coordinate using direct mouse click.
        Prompts the user to click at the desired position.
        """
        print("Please click on the location where you want to perform the triple-click.")
        
        prev_click_state = 0
        while len(self.coords) < 1:
            # Check left mouse button state (1 for left mouse button)
            curr_click_state = win32api.GetKeyState(0x01)
            
            # Detect click (transition from not pressed to pressed)
            if curr_click_state < 0 and prev_click_state >= 0:
                # Get current mouse position
                x, y = win32api.GetCursorPos()
                self.coords.append((x, y))
                print(f"Coordinate registered: ({x}, {y})")
                time.sleep(0.2)  # debounce delay
            
            prev_click_state = curr_click_state
            time.sleep(0.01)  # Small sleep to reduce CPU usage
            
        print("Coordinate registered!")
        return self.coords

    def click_at(self, x: int, y: int) -> None:
        """
        Simulate a mouse click at the specified (x, y) position.
        """
        win32api.SetCursorPos((x, y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.02)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        print(f"Clicked at ({x}, {y})")

    def press_ctrl_c(self) -> None:
        """
        Simulate pressing Ctrl+C key combination.
        """
        # Virtual key codes: VK_CONTROL (0x11), 'C' (0x43)
        CTRL_KEY = 0x11
        C_KEY = 0x43
        
        # Press Ctrl key
        win32api.keybd_event(CTRL_KEY, 0, 0, 0)  # Ctrl down
        
        # Press C key while holding Ctrl
        win32api.keybd_event(C_KEY, 0, 0, 0)  # C down
        time.sleep(0.02)
        win32api.keybd_event(C_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # C up
        
        # Release Ctrl key
        win32api.keybd_event(CTRL_KEY, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl up
        
        print("Pressed Ctrl+C")

    def triple_click_at(self, x: int, y: int) -> None:
        """
        Perform a triple-click at the specified coordinates.
        """
        win32api.SetCursorPos((x, y))
        for _ in range(3):
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            time.sleep(0.02)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            time.sleep(0.05)  # Delay between clicks
        print(f"Triple-clicked at ({x}, {y})")

    def get_char_vk_and_shift(self, char: str) -> Tuple[int, bool]:
        """
        Get virtual key code and shift requirement for a character.
        Returns (virtual_key_code, needs_shift)
        """
        # Special character mappings
        special_chars = {
            ' ': (0x20, False),  # Space
            '!': (0x31, True),   # Shift + 1
            '"': (0xDE, True),   # Shift + ' (quote)
            '#': (0x33, True),   # Shift + 3
            '$': (0x34, True),   # Shift + 4
            '%': (0x35, True),   # Shift + 5
            '&': (0x37, True),   # Shift + 7
            "'": (0xDE, False),  # Apostrophe
            '(': (0x39, True),   # Shift + 9
            ')': (0x30, True),   # Shift + 0
            '*': (0x38, True),   # Shift + 8
            '+': (0xBB, True),   # Shift + =
            ',': (0xBC, False),  # Comma
            '-': (0xBD, False),  # Minus
            '.': (0xBE, False),  # Period
            '/': (0xBF, False),  # Forward slash
            ':': (0xBA, True),   # Shift + ;
            ';': (0xBA, False),  # Semicolon
            '<': (0xBC, True),   # Shift + ,
            '=': (0xBB, False),  # Equals
            '>': (0xBE, True),   # Shift + .
            '?': (0xBF, True),   # Shift + /
            '@': (0x32, True),   # Shift + 2
            '[': (0xDB, False),  # Left bracket
            '\\': (0xDC, False), # Backslash
            ']': (0xDD, False),  # Right bracket
            '^': (0x36, True),   # Shift + 6
            '_': (0xBD, True),   # Shift + -
            '`': (0xC0, False),  # Backtick
            '{': (0xDB, True),   # Shift + [
            '|': (0xDC, True),   # Shift + \
            '}': (0xDD, True),   # Shift + ]
            '~': (0xC0, True),   # Shift + `
        }
        
        if char in special_chars:
            return special_chars[char]
        elif char.isdigit():
            # Numbers 0-9
            return (0x30 + int(char), False)
        elif char.isalpha():
            # Letters A-Z
            vk_code = ord(char.upper())
            needs_shift = char.isupper()
            return (vk_code, needs_shift)
        else:
            # Fallback for unknown characters
            return (ord(char.upper()), char.isupper())

    def type_char_robust(self, char: str) -> bool:
        """
        Type a single character with robust error handling.
        Returns True if successful, False otherwise.
        """
        try:
            vk_code, needs_shift = self.get_char_vk_and_shift(char)
            
            if needs_shift:
                win32api.keybd_event(0x10, 0, 0, 0)  # Shift down
            
            # Press the key
            win32api.keybd_event(vk_code, 0, 0, 0)  # Key down
            if self.typing_delay > 0:
                time.sleep(max(0.001, self.typing_delay * 0.5))  # Reduced internal delay
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)  # Key up
            
            if needs_shift:
                win32api.keybd_event(0x10, 0, win32con.KEYEVENTF_KEYUP, 0)  # Shift up
            
            return True
        except Exception as e:
            print(f"Error typing character '{char}': {e}")
            return False

    def type_text_ultra_fast(self, text: str) -> None:
        """
        Ultra-fast typing using clipboard paste method.
        """
        print(f"Ultra-fast typing using clipboard method...")
        self.paste_text_fast(text)
        print("Finished ultra-fast typing!")

    def type_text(self, text: str) -> None:
        """
        Type out text character by character with error handling.
        """
        print(f"Typing text with {self.typing_delay}s delay between keystrokes...")
        
        failed_chars = []
        for i, char in enumerate(text):
            success = self.type_char_robust(char)
            if not success:
                failed_chars.append((i, char))
            
            if self.typing_delay > 0:
                time.sleep(self.typing_delay)
        
        if failed_chars:
            print(f"Warning: Failed to type {len(failed_chars)} characters: {failed_chars}")
        
        print("Finished typing!")

    def execute_action_sequence(self) -> None:
        """
        Executes the defined sequence of actions:
        1. Triple-click at the registered coordinate
        2. Press Ctrl+C (copy operation)
        3. Print the copied text
        4. Click at the same coordinate
        5. Wait 0.3 seconds
        6. Type out the copied text (ultra-fast or robust based on delay)
        """
        if len(self.coords) < 1:
            print("Error: Need coordinate to perform actions.")
            return
        
        # Get the coordinate
        x, y = self.coords[0]
        
        # 1. Triple-click at the coordinate
        print("\nPerforming triple-click operation...")
        self.triple_click_at(x, y)
        
        # 2. Press Ctrl+C to copy the selected content
        print("\nPressing Ctrl+C to copy selection...")
        self.press_ctrl_c()
        
        # Small delay to ensure clipboard is updated
        time.sleep(0.05)
        
        # 3. Inject typing script after copying
        print("\nInjecting typing enabler script...")
        self.inject_typing_script()
        
        # 4. Get and print the copied text
        copied_text = pyperclip.paste()
        print(f"\nCopied text: '{copied_text}'")
        print(f"Text length: {len(copied_text)} characters")
        
        # 5. Click at the same coordinate to position cursor
        print(f"\nClicking at ({x}, {y}) to position cursor...")
        self.click_at(x, y)
        
        # 6. Wait before typing
        print("Waiting 0.3 seconds before typing...")
        time.sleep(0.3)
        
        # 7. Type out the copied text
        if copied_text:
            if self.typing_delay == 0:
                # Ultra-fast mode: use clipboard paste
                # self.type_text_ultra_fast(copied_text)
                print("⚠️ ULTRA-FAST TYPING CURRENTLY UNDER CONSTRUCTION DUMBASS ⚠️")
            else:
                # Regular mode: use robust character-by-character typing
                self.type_text(copied_text)
        else:
            print("No text to type (clipboard empty)")
        
        print("\nAction sequence completed! Program ending.")


def main() -> None:
    # Ask user for typing delay
    print("===== Enhanced Text Selection and Auto-Type Tool =====")
    print("Enter typing delay between keystrokes (in seconds):")
    print("- 0 = Ultra-fast (clipboard paste method) ⚠️ CURRENTLY UNDER CONSTRUCTION ⚠️")
    print("- 0.001 = Extremely fast")
    print("- 0.005 = Very fast")
    print("- 0.01 = Fast")
    print("- 0.05 = Medium")
    
    try:
        typing_delay = float(input("Delay (default 0): ") or "0")
        if typing_delay < 0:
            typing_delay = 0
    except ValueError:
        typing_delay = 0
        print("Invalid input, using ultra-fast mode (0s delay)")
    
    controller = MouseController(num_coords=1, typing_delay=typing_delay)
    
    if typing_delay == 0:
        # print(f"\nUsing ULTRA-FAST mode (clipboard paste)")
        print("⚠️ I SAID ITS CURRENTLY UNDER CONSTRUCTION DUMBASS ⚠️")
    else:
        print(f"\nUsing typing mode with {typing_delay}s delay")
    
    print("This script will:")
    print("1. Enable text selection and copying on any webpage")
    print("2. Triple-click at your selected position to select text")
    print("3. Copy the selected text to clipboard")
    print("4. Print the copied text (just for lookie looks)")
    print("5. Click at the same position and type out the text (and hopefully not fuck up)")
    print("6. End the program")
    print("=========================================")
    input("Press Enter to begin...")
    
    # Wait for user to switch to the target page
    controller.wait_for_page_switch(5)
    
    # Run initial scripts to enable text selection and copying
    controller.run_console_scripts()
    
    print("\nNow please click on the text you want to select and copy.")
    controller.collect_coordinates()
    
    print("\nStarting action sequence in 3 seconds...")
    print("Keep your mouse still during the process")
    time.sleep(3)
    
    controller.execute_action_sequence()


if __name__ == "__main__":
    main()
