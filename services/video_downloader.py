import os
import re
import json
import yt_dlp
from config import Config

class VideoDownloader:
    def __init__(self):
        self.cookies_path = Config.COOKIES_PATH
        self.output_dir = Config.VIDEOS_DIR
    
    def extract_video_id(self, url):
        match = re.search(r'BV\w+', url)
        if match:
            return match.group(0)
        match = re.search(r'av(\d+)', url)
        if match:
            return f"av{match.group(1)}"
        raise ValueError("无法从链接中提取视频ID")
    
    def download(self, url, video_id):
        output_dir = os.path.join(self.output_dir, video_id)
        os.makedirs(output_dir, exist_ok=True)
        
        info_path = os.path.join(output_dir, 'info.json')
        
        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                info_data = json.load(f)
            audio_path = info_data.get('audio_path')
            if audio_path and os.path.exists(audio_path):
                return info_data
            legacy_audio_path = os.path.join(output_dir, 'audio.mp3')
            if os.path.exists(legacy_audio_path):
                info_data['audio_path'] = legacy_audio_path
                with open(info_path, 'w', encoding='utf-8') as f:
                    json.dump(info_data, f, ensure_ascii=False, indent=2)
                return info_data
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, 'audio.%(ext)s'),
            'http_headers': {
                'User-Agent': Config.BILIBILI_USER_AGENT,
                'Referer': Config.BILIBILI_REFERER,
                'Origin': Config.BILIBILI_ORIGIN,
            },
            'writesubtitles': False,
            'writeautomaticsub': False,
            'quiet': True,
            'no_warnings': True,
        }

        if self.cookies_path and os.path.exists(self.cookies_path) and os.path.getsize(self.cookies_path) > 0:
            ydl_opts['cookiefile'] = self.cookies_path
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = None
            requested = info.get('requested_downloads') if isinstance(info, dict) else None
            if requested and isinstance(requested, list) and requested:
                audio_path = requested[0].get('filepath') or requested[0].get('_filename')
            if not audio_path:
                try:
                    audio_path = ydl.prepare_filename(info)
                except Exception:
                    audio_path = None
            if not audio_path or not os.path.exists(audio_path):
                candidates = [
                    os.path.join(output_dir, name)
                    for name in os.listdir(output_dir)
                    if name.startswith('audio.')
                ]
                candidates = [p for p in candidates if os.path.isfile(p)]
                audio_path = max(candidates, key=os.path.getmtime) if candidates else None
            
            info_data = {
                'id': video_id,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'description': info.get('description', ''),
                'url': url,
                'audio_path': audio_path,
            }
            
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, ensure_ascii=False, indent=2)
            
            return info_data
