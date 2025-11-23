import tinytuya
import time
import json
import threading
import queue
from PIL import ImageColor
from pathlib import Path

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
    while True:
        time.sleep(60)
        q.put(heartbeat_keyword)

def worker(q, lamp):
    last_color = None
    last_time = None
    last_immunity = None

    while True:
        i = q.get()

        if i == heartbeat_keyword:
            lamp.heartbeat()
            print('heartbeat')
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

def main():
    config = get_config()
    lamp = get_lamp(config)

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

main()

# #3752ff (55, 82, 255) - nice blue
# #9fff56 (159, 255, 86) - anki green
# #162180 (22, 33, 128) - radioactive blue
# #ff9b42 - sandy

# lamp.turn_off()
# lamp.turn_on()
# print(tinytuya.BulbDevice.hexvalue_to_rgb('005e029403e8'))
# time.sleep(1)
