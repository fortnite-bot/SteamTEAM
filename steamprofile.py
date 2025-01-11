import os
import time
import pyautogui
import pyperclip
import asyncio
import keyboard 
import ctypes
a = ''   
def steamid():

    async def wait_for_keypress_or_steam():
        start_time = time.time()
        keypress_task = asyncio.create_task(listen_for_keypress('q'))
        
        while time.time() - start_time < 45:  # Wait for up to 45 seconds
            if keypress_task.done():
                return True
            await asyncio.sleep(1)

        return True

    async def listen_for_keypress(key):
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def on_press(event):
            if event.name == key:
                loop.call_soon_threadsafe(future.set_result, True)

        listener = keyboard.on_press(on_press)
        try:
            result = await future
        except asyncio.CancelledError:
            result = None
        finally:
            keyboard.unhook(listener)
        return result

    def perform_clicks():
        ctypes.windll.user32.BlockInput(True)
        global a
        # Maximize the Steam window
        pyautogui.hotkey('win', 'up')
        time.sleep(0.1)
        # Click at position X: 575, Y: 59
        pyautogui.click(575, 59)

        # Wait for 2 seconds
        time.sleep(2)

        # Click at position X: 259, Y: 98
        pyautogui.click(259, 98)

        # Retrieve the clipboard content
        clipboard_content = pyperclip.paste()
        a = clipboard_content.split('/')[4:5][0]
        pyautogui.hotkey('win', 'down')
        pyautogui.hotkey('win', 'down')
        ctypes.windll.user32.BlockInput(False)

        # Split the clipboard content and print the value
        return a

    async def main():
        if await wait_for_keypress_or_steam():
            perform_clicks()

    # Start the async function in an event loop
    asyncio.run(main())
    return int(a)

