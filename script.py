import os
import time
import psutil
from pynput.keyboard import Listener, Key
from threading import Thread

zoom_open = False

def enable_do_not_disturb():
    """Enable Do Not Disturb on macOS."""
    try:
        os.system("defaults -currentHost write ~/Library/Preferences/ByHost/com.apple.notificationcenterui doNotDisturb -boolean true")
        os.system("killall NotificationCenter")
        print("Do Not Disturb enabled.")
    except Exception as e:
        print(f"Failed to enable Do Not Disturb: {e}")

def disable_do_not_disturb():
    """Disable Do Not Disturb on macOS."""
    try:
        os.system("defaults -currentHost write ~/Library/Preferences/ByHost/com.apple.notificationcenterui doNotDisturb -boolean false")
        os.system("killall NotificationCenter")
        print("Do Not Disturb disabled.")
    except Exception as e:
        print(f"Failed to disable Do Not Disturb: {e}")

def is_zoom_running():
    """Check if Zoom is running and update zoom_open state."""
    global zoom_open
    zoom_open = any(process.info['name'].lower() == "zoom.us" for process in psutil.process_iter(['name']))
    return zoom_open

def focus_zoom():
    """Bring Zoom to the foreground on macOS only if it is running."""
    if zoom_open:
        os.system("open -a zoom.us")
        print("Zoom window refocused.")
        time.sleep(0.1)

def is_zoom_focused():
    """Check if Zoom is the frontmost application on macOS."""
    focused_app = os.popen("osascript -e 'tell application \"System Events\" to get name of first process whose frontmost is true'").read().lower()
    print(f"Currently focused app: {focused_app.strip()}")  # Debugging output
    return "zoom" in focused_app

def is_zoom_in_meeting():
    """Check if Zoom is in a meeting by looking for meeting keywords in the window title."""
    window_title = os.popen("osascript -e 'tell application \"System Events\" to get title of first window of process \"zoom.us\"'").read().lower()
    print(f"Zoom window title: {window_title.strip()}")  # Debugging output
    return "meeting" in window_title or "id" in window_title

def lock_focus():
    """Continuously refocus on Zoom if the user tries to switch windows."""
    while zoom_open:
        if not is_zoom_focused():
            focus_zoom()
        time.sleep(0.5)

def keyboard_listener():
    """Listen for specific keys to temporarily disable focus lock for screen sharing."""
    def on_press(key):
        if key == Key.esc:  # Modify this to match your screen share shortcut
            # Temporarily unlock focus
            print("Screen sharing triggered, unlocking focus temporarily.")
            time.sleep(10)  # Allows 10 seconds for screen sharing setup before relocking
        elif zoom_open and not is_zoom_focused():
            focus_zoom()

    with Listener(on_press=on_press) as listener:
        listener.join()

def monitor_zoom():
    """Monitor Zoom status and apply focus lock and DND only when Zoom is active."""
    global zoom_open

    print("Monitoring for Zoom...")

    while True:
        # Check if Zoom is running
        if is_zoom_running():
            if zoom_open and is_zoom_in_meeting():
                print("Zoom detected. Enabling Do Not Disturb and locking focus.")
                enable_do_not_disturb()
                
                # Start the lock focus thread and keyboard listener
                lock_thread = Thread(target=lock_focus)
                lock_thread.start()
                listener_thread = Thread(target=keyboard_listener)
                listener_thread.start()
                
            # Keep checking until Zoom is no longer running
            while is_zoom_running():
                time.sleep(1)
                
            # If Zoom closes, disable Do Not Disturb
            print("Zoom closed. Disabling Do Not Disturb.")
            disable_do_not_disturb()
            zoom_open = False
        
        time.sleep(1)

if __name__ == "__main__":
    monitor_zoom()
