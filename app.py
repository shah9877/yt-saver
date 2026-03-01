from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import threading

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = tempfile.mkdtemp()

def get_ydl_opts(format_type='video', quality='best', output_path=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': output_path or os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    }
    
    if format_type == 'audio':
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        if quality == 'best':
            opts['format'] = 'bestvideo+bestaudio/best'
        elif quality == '1080':
            opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
        elif quality == '720':
            opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
        elif quality == '480':
            opts['format'] = 'bestvideo[height<=480]+bestaudio/best'
        elif quality == '360':
            opts['format'] = 'bestvideo[height<=360]+bestaudio/best'
        else:
            opts['format'] = 'best'
        
        opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
    
    return opts

@app.route('/')
def index():
    with open('index.html', 'r') as f:
        return f.read()

@app.route('/info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Playlist check
            if info.get('_type') == 'playlist':
                entries = []
                for entry in (info.get('entries') or [])[:50]:
                    if entry:
                        entries.append({
                            'id': entry.get('id'),
                            'title': entry.get('title'),
                            'duration': entry.get('duration'),
                            'thumbnail': entry.get('thumbnail'),
                            'url': entry.get('webpage_url', url),
                        })
                return jsonify({
                    'type': 'playlist',
                    'title': info.get('title'),
                    'count': len(entries),
                    'entries': entries
                })
            
            # Single video
            formats = []
            seen = set()
            for f in (info.get('formats') or []):
                h = f.get('height')
                ext = f.get('ext')
                if h and ext == 'mp4' and h not in seen:
                    seen.add(h)
                    formats.append({'quality': h, 'ext': ext})
            
            formats = sorted(formats, key=lambda x: x['quality'], reverse=True)
            
            return jsonify({
                'type': 'video',
                'title': info.get('title'),
                'duration': info.get('duration'),
                'thumbnail': info.get('thumbnail'),
                'uploader': info.get('uploader'),
                'view_count': info.get('view_count'),
                'formats': formats,
                'url': url
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '')
    format_type = data.get('format', 'video')  # video or audio
    quality = data.get('quality', 'best')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        output_template = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
        opts = get_ydl_opts(format_type, quality, output_template)
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')
            
            # Find downloaded file
            for f in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, f)
                if format_type == 'audio' and f.endswith('.mp3'):
                    return send_file(filepath, as_attachment=True, download_name=f)
                elif format_type == 'video' and f.endswith('.mp4'):
                    return send_file(filepath, as_attachment=True, download_name=f)
            
            return jsonify({'error': 'File not found after download'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
