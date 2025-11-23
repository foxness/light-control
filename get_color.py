import tinytuya
import time
import json
from PIL import ImageColor

def get_config():
    config = {}
    with open('config/devices.json', 'r') as file:
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
    # print(f'lamp status: {lamp_status}')

    return lamp

def set_color(lamp, hex):
    (r, g, b) = ImageColor.getcolor(hex, "RGB")
    lamp.set_colour(r, g, b, nowait=True)

def rgb2hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def get_color(lamp):
    lamp.status()
    return rgb2hex(*lamp.colour_rgb())

def main():
    config = get_config()
    lamp = get_lamp(config)
    print(rgb2hex(*lamp.colour_rgb()))

main()