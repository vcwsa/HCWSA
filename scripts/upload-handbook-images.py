#!/usr/bin/env python3
"""Upload handbook assets to ImgBB and retain resumable, non-secret metadata."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md"
MANIFEST = MD / "image-uploads.json"
INSTRUCTIONS = Path('/config/workspace/VCWSA-posts/Upload Images.md')


def save(data):
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    key = os.environ.get('IMGBB_API_KEY')
    if not key:
        match = re.search(r'IMGBB_API_KEY=([^\s`]+)', INSTRUCTIONS.read_text())
        if not match:
            sys.exit('No ImgBB API key available.')
        key = match.group(1)
    assert re.fullmatch(r'[A-Za-z0-9_-]+', key), 'Unexpected API key format'
    mapping = json.loads((MD / 'assets-map.json').read_text())
    body = (MD / 'index.md').read_text()
    data = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {
        'provider': 'ImgBB', 'category': '新生手册',
        'album_status': 'pending_manual_assignment',
        'album_note': 'ImgBB 公开 API 不支持相册归类；名称使用新生手册前缀，需在后台归类。',
        'images': []}
    previous = {entry['local_path']: entry for entry in data['images']}
    if not previous:
        headings = {}
        for line in body.splitlines():
            heading = re.match(r'^(#{2,4}) (.+)', line)
            if heading:
                level = len(heading[1])
                headings = {k:v for k,v in headings.items() if k < level}
                headings[level] = heading[2]
            img = re.match(r'!\[([^\]]*)\]\((assets/[^)]+)\)', line)
            if not img:
                continue
            alt, local = img.groups()
            original = mapping[local]
            title = f'新生手册-2023-{len(data["images"])+1:02d}-{alt}'
            title = re.sub(r'[/\\\r\n]', '-', title)
            data['images'].append({
                'local_path': local, 'source_path': original,
                'title': title, 'alt': alt,
                'section': ' / '.join(headings.values()) if 'Bilder/' not in original else '封面与封底',
                'source_edition': '2023', 'category': '新生手册',
                'sha256': hashlib.sha256((MD / local).read_bytes()).hexdigest(),
                'bytes': (MD / local).stat().st_size, 'status': 'pending'})
        # Figure captions follow each single image or group of images.
        pending = []
        by_path = {e['local_path']:e for e in data['images']}
        for line in body.splitlines():
            if line.startswith('<a id="figure-') or line.startswith('#'):
                pending = []
            img = re.match(r'!\[[^\]]*\]\((assets/[^)]+)\)', line)
            if img:
                pending.append(by_path[img[1]])
            if line.startswith('图：'):
                for entry in pending:
                    entry['caption_markdown'] = line[2:]
                pending = []
        assert len(data['images']) == len(mapping) == 46
        save(data)
    for number, entry in enumerate(data['images'], 1):
        local = MD / entry['local_path']
        assert hashlib.sha256(local.read_bytes()).hexdigest() == entry['sha256']
        if entry['status'] == 'uploaded':
            continue
        if entry['status'] == 'failed' and '--skip-failed' in sys.argv:
            continue
        # Credentials travel over stdin, never command arguments or logs.
        result = subprocess.run([
            'curl', '--http1.1', '--silent', '--show-error', '--fail-with-body',
            '--connect-timeout', '20', '--max-time', '180',
            '--config', '-', 'https://api.imgbb.com/1/upload',
            '--form', f'image=@{local}', '--form-string', f'name={entry["title"]}'
        ], input=f'form-string = "key={key}"\n', text=True, capture_output=True)
        if result.returncode:
            entry['status'] = 'failed'
            save(data)
            print(f'Upload {number} failed (curl exit {result.returncode}): '
                  + result.stderr.replace(key, '[REDACTED]').strip(), flush=True)
            continue
        response = json.loads(result.stdout)
        if not response.get('success'):
            sys.exit(f'Upload {number} rejected by ImgBB; stopped.')
        remote = response['data']
        assert remote['url'].startswith('https://i.ibb.co/')
        entry.update({
            'status': 'uploaded', 'id': remote['id'], 'url': remote['url'],
            'viewer_url': remote['url_viewer'], 'remote_title': remote['title'],
            'width': int(remote['width']), 'height': int(remote['height']),
            'remote_bytes': int(remote['size']),
            'uploaded_at': datetime.now(timezone.utc).isoformat()})
        # Omit delete_url: it grants deletion authority and must not be committed.
        save(data)
        print(f'Uploaded {number}/{len(data["images"])}: {entry["title"]}', flush=True)
    if any(entry['status'] != 'uploaded' for entry in data['images']):
        sys.exit('Some images remain failed; successful uploads saved, Markdown unchanged.')
    for entry in data['images']:
        body = body.replace('](' + entry['local_path'] + ')', '](' + entry['url'] + ')')
    assert not re.search(r'!\[[^\]]*\]\(assets/', body)
    (MD / 'index.md').write_text(body)
    print('All 46 images uploaded; Markdown links updated.')


if __name__ == '__main__':
    main()
