import tinytuya
import time
import json
import threading
import queue
from PIL import ImageColor
from pathlib import Path

import numpy as np
import colour

immunity_keyword = 'immunity'
heartbeat_keyword = 'heartbeat'

def get_config():
    config = {}
    path = Path(__file__).parent / 'config/devices.json'
    with open(path, 'r') as file:
        data = json.load(file)
        device = data[0]

        config['dev_id'] = device['id']
        config['address'] = device['ip']
        config['local_key'] = device['key']
        config['version'] = device['version']

    return config

def get_lamp(config):
    lamp = tinytuya.BulbDevice(
        dev_id=config['dev_id'],
        address=config['address'], # Or set to 'Auto' to auto-discover IP address
        local_key=config['local_key'],
        version=config['version']
    )

    lamp.set_socketPersistent(True)
    lamp_status = lamp.status()
    print(f'lamp status: {lamp_status}')

    return lamp

def set_color(lamp, hex):
    (r, g, b) = ImageColor.getcolor(hex, "RGB")
    lamp.set_colour(r, g, b, nowait=True)

def rgb2hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def get_color(lamp):
    lamp.status()
    return rgb2hex(*lamp.colour_rgb())

def heartbeat(q):
    heartbeat_count = 0
    while True:
        time.sleep(60)
        q.put(heartbeat_keyword)
        print(f'heartbeat {heartbeat_count}')
        heartbeat_count += 1

def worker(q, lamp):
    last_color = None
    last_time = None
    last_immunity = None

    while True:
        i = q.get()

        if i == heartbeat_keyword:
            lamp.heartbeat()
            q.task_done()
            continue
        elif i == 'get':
            print(get_color(lamp))
            q.task_done()
            continue

        i = i.split(' ')
        if len(i) > 2:
            print('Invalid format')
            q.task_done()
            continue

        color = i[0]
        immunity = i[1] if len(i) == 2 else None

        if len(color) != 7:
            print('Invalid hex')
            q.task_done()
            continue

        if immunity != None:
            if not immunity.startswith(immunity_keyword):
                print('Invalid immunity format')
                q.task_done()
                continue

            immunity = float(immunity[len(immunity_keyword):])

        if color == last_color:
            print('Same color, ignoring')
            q.task_done()
            continue

        current_time = time.time()
        if last_immunity != None and last_time != None:
            difference = current_time - last_time
            if difference < last_immunity:
                time_left = last_immunity - difference
                print(f"Can't pierce immunity, need to wait {time_left:.3}s")
                q.task_done()
                continue

        set_color(lamp, color)
        print(f'set color to {color}')
        # q.put(color)

        last_color = color
        last_immunity = immunity
        last_time = current_time

        q.task_done()

def daemon(lamp):
    q = queue.Queue()
    workerThread = threading.Thread(target=worker, args=[q, lamp], daemon=True)
    workerThread.start()

    heartbeatThread = threading.Thread(target=heartbeat, args=[q], daemon=True)
    heartbeatThread.start()

    while True:
        item = input()
        if item == 'q':
            print('Quitting...')
            break

        q.put(item)

    q.join()
    print('All work completed')

def shift_hue_oklab(rgb_8bit, degrees):
    # Normalize 0-255 -> 0-1
    rgb = rgb_8bit.astype(float) / 255.0

    # Pipeline: sRGB (Display) -> sRGB (Linear) -> XYZ -> Oklab
    # In 0.4.x, we can use the explicit model paths to be safe

    # Linearize (EOTF)
    rgb_linear = colour.cctf_decoding(rgb)

    # Linear RGB -> XYZ
    xyz = colour.sRGB_to_XYZ(rgb_linear)

    # XYZ -> Oklab
    # Note: If this fails, your version is definitely not 0.4.x
    oklab = colour.XYZ_to_Oklab(xyz)

    # Oklab -> Oklch (Polar) to shift Hue
    # We use the specific definition from the models module if top-level is missing
    try:
        oklch = colour.Oklab_to_Oklch(oklab)
    except AttributeError:
        # Fallback for slightly older 0.3.x versions
        oklch = colour.models.Oklab_to_Oklch(oklab)

    # Shift Hue (Index 2 is h)
    oklch[2] = (oklch[2] + degrees) % 360

    # Back down the ladder
    try:
        oklab_shifted = colour.Oklch_to_Oklab(oklch)
    except AttributeError:
        oklab_shifted = colour.models.Oklch_to_Oklab(oklch)

    xyz_shifted = colour.Oklab_to_XYZ(oklab_shifted)
    rgb_linear_shifted = colour.XYZ_to_sRGB(xyz_shifted)

    # Encode (OETF)
    rgb_display = colour.cctf_encoding(rgb_linear_shifted)

    # Clip and Integers
    return (np.clip(rgb_display, 0, 1) * 255).astype(int)

def shift_hue_oklch(rgb_8bit: np.ndarray, degrees: float) -> np.ndarray:
    
    # ... (Forward Pipeline: sRGB -> Oklch) ...
    rgb_input = np.atleast_2d(rgb_8bit) 
    rgb_normalized = rgb_input.astype(float) / 255.0
    rgb_linear = colour.cctf_decoding(rgb_normalized)
    xyz = colour.sRGB_to_XYZ(rgb_linear)
    oklab = colour.XYZ_to_Oklab(xyz)
    oklch = colour.Oklab_to_Oklch(oklab)

    # 1. Apply Hue Shift
    oklch[..., 2] = (oklch[..., 2] + degrees) % 360

    # 2. Hard clamp Chroma (C) to avoid instability near primaries
    # This is a defensive move against unstable matrices.
    # The max Chroma for a given Lightness/Hue in Oklab is complex, but 0.4 is a safe, high value.
    oklch[..., 1] = np.clip(oklch[..., 1], None, 0.4) 

    # 3. Backward Pipeline (Explicit, Stable Conversions)
    oklab_shifted = colour.Oklch_to_Oklab(oklch)
    xyz_shifted = colour.Oklab_to_XYZ(oklab_shifted)
    
    # 4. FINAL CLIP in XYZ space (This prevents the numerical instability from propagating)
    # Tristimulus values must be non-negative.
    xyz_clipped = np.clip(xyz_shifted, 0.0, None)
    
    # 5. Conversion to sRGB (The Final Gauntlet)
    rgb_linear_shifted = colour.XYZ_to_sRGB(xyz_clipped)
    rgb_display_shifted = colour.cctf_encoding(rgb_linear_shifted)
    
    # 6. Quantize and return
    return (np.clip(rgb_display_shifted, 0, 1) * 255).astype(np.uint8).squeeze()

def rainbow(lamp):
    # color = [55, 82, 255]
    color = np.array([143, 172, 255])
    duration = 240
    for i in range(duration + 1):
        shift = i * (360 / duration)
        new_color = shift_hue_oklch(color, shift)
        r, g, b = new_color.tolist()
        lamp.set_colour(r, g, b, nowait=True)
        print(f'color: {new_color}, shift: {shift}')
        time.sleep(0.5)

def main():
    config = get_config()
    lamp = get_lamp(config)

    # rainbow(lamp)
    daemon(lamp)

main()

# #3752ff (55, 82, 255) - nice blue
# #9fff56 (159, 255, 86) - anki green
# #162180 (22, 33, 128) - radioactive blue
# #ff9b42 - sandy

# lamp.turn_off()
# lamp.turn_on()
# print(tinytuya.BulbDevice.hexvalue_to_rgb('005e029403e8'))
# time.sleep(1)
