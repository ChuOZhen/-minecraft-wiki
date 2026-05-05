#!/usr/bin/env python3
"""Download missing images for specific items from Minecraft Wiki."""
import json, os, subprocess, time, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, 'docs', 'data', 'data.json')
IMAGES_DIR = os.path.join(SCRIPT_DIR, 'docs', 'images')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find items without images
imgs = set(f.lower() for f in os.listdir(IMAGES_DIR))
missing = [i for i in data['items'] if f'{i["id"]}.png' not in imgs]

print(f'Missing images: {len(missing)}')

# Known wiki image URLs (Invicon format for inventory items)
URL_PATTERNS = {
    '_sword': '{id}_JE2_BE2.png',
    '_pickaxe': '{id}_JE3_BE2.png',
    '_hoe': '{id}_JE3_BE2.png',
    '_axe': '{id}_JE3_BE2.png',
    '_shovel': '{id}_JE2_BE2.png',
}

success = 0
failed = []

for item in missing:
    iid = item['id']
    dest = os.path.join(IMAGES_DIR, f'{iid}.png')

    # Try Invicon format first (best for inventory icons)
    invicon_url = f'https://minecraft.wiki/images/Invicon_{iid.replace("/","_")}.png'
    # Try direct format
    direct_url = f'https://minecraft.wiki/Special:FilePath/{iid.replace("_"," ").title().replace(" ","_")}.png'

    for url in [invicon_url, direct_url]:
        result = subprocess.run([
            'curl', '-s', '-o', dest, '-w', '%{http_code}',
            '-L', '--max-time', '15',
            url
        ], capture_output=True, text=True, timeout=25)

        http = result.stdout.strip()
        if http == '200' and os.path.exists(dest) and os.path.getsize(dest) > 200:
            with open(dest, 'rb') as f:
                h = f.read(4)
            if h[:4] == b'\x89PNG' or h[:3] == b'\xff\xd8\xff':
                success += 1
                print(f'  OK: {iid} ({url.split("/")[-1][:40]})')
                break
            else:
                os.remove(dest)
        elif os.path.exists(dest):
            os.remove(dest)
        time.sleep(0.3)
    else:
        failed.append(iid)
        print(f'  FAIL: {iid}')

print(f'\nDownloaded: {success}/{len(missing)}')
print(f'Failed: {len(failed)}')
if failed:
    print('Failed items:')
    for f in failed:
        print(f'  - {f}')
