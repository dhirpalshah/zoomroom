import os
import time
import psutil
from pynput.keyboard import Listener, Key
from threading import Thread

zoom_open = False
lock_thread = None
listener_thread = None

def enable_do_not_disturb():
    try:
        os.system("defaults -currentHost write ~/Library/Preferences/ByHost/com.apple.notificationcenterui doNotDisturb -boolean true")
        os.system("killall NotificationCenter")
        print("Do Not Disturb enabled.")
    except Exception as e:
        print(f"Failed to enable Do Not Disturb: {e}")

def disable_do_not_disturb():
    try:
        os.system("defaults -currentHost write ~/Library/Preferences/ByHost/com.apple.notificationcenterui doNotDisturb -boolean false")
        os.system("killall NotificationCenter")
        print("Do Not Disturb disabled.")
    except Exception as e:
        print(f"Failed to disable Do Not Disturb: {e}")

def is_zoom_running():
    global zoom_open
    zoom_open = any(process.info['name'].lower() == "zoom.us" for process in psutil.process_iter(['name']))
    return zoom_open

def focus_zoom():
    if zoom_open:
        os.system("open -a zoom.us")
        print("Zoom window refocused.")
        time.sleep(0.1)

def is_zoom_focused():
    focused_app = os.popen("osascript -e 'tell application \"System Events\" to get name of first process whose frontmost is true'").read().strip().lower()
    print(f"Currently focused app: {focused_app}")  # Debugging output
    return "zoom.us" in focused_app

def is_zoom_in_meeting():
    try:
        window_count = os.popen("osascript -e 'tell application \"System Events\" to count windows of process \"zoom.us\"'").read().strip()
        if window_count and int(window_count) > 0:
            window_title = os.popen("osascript -e 'tell application \"System Events\" to get title of first window of process \"zoom.us\"'").read().lower().strip()
            print(f"Zoom window title: {window_title}")  # Debugging output
            if window_title == 'missing value' or window_title == '':
                return True
            else:
                return False
        else:
            print("No Zoom meeting window found.")
            return False
    except Exception as e:
        print(f"Error checking Zoom meeting window: {e}")
        return False

def lock_focus():
    while zoom_open:
        if is_zoom_in_meeting() and not is_zoom_focused():
            focus_zoom()
        time.sleep(0.3)  # Increased frequency

def keyboard_listener():
    def on_press(key):
        if key == Key.esc:
            print("Screen sharing triggered, unlocking focus temporarily.")
            time.sleep(10)
        elif zoom_open and is_zoom_in_meeting() and not is_zoom_focused():
            focus_zoom()
    
    with Listener(on_press=on_press) as listener:
        listener.join()

def monitor_zoom():
    global zoom_open, lock_thread, listener_thread

    print("Monitoring for Zoom...")

    while True:
        if is_zoom_running():
            if zoom_open and (lock_thread is None or not lock_thread.is_alive()):
                print("Zoom detected. Enabling Do Not Disturb and locking focus.")
                enable_do_not_disturb()
                
                lock_thread = Thread(target=lock_focus, daemon=True)
                lock_thread.start()
                
                listener_thread = Thread(target=keyboard_listener, daemon=True)
                listener_thread.start()
                
            while is_zoom_running():
                time.sleep(1)
                
            print("Zoom closed. Disabling Do Not Disturb.")
            disable_do_not_disturb()
            zoom_open = False
        
        time.sleep(1)

if __name__ == "__main__":
    monitor_zoom()
