import os
import sqlite3
import time
import threading
from .video_downloader import VideoDownloader
from .transcriber import Transcriber
from .translator import Translator
from config import Config

class VideoProcessor:
    def __init__(self, progress_queue=None):
        self.progress_queue = progress_queue
        self.downloader = VideoDownloader()
        self.transcriber = Transcriber()
        self.translator = Translator()
    
    def send_progress(self, status, step, message, **extra):
        if self.progress_queue:
            data = {'status': status, 'step': step, 'message': message}
            data.update(extra)
            self.progress_queue.put(data)
    
    def process(self, url):
        self.send_progress('processing', 'download', '正在下载视频音频...')
        
        video_id = self.downloader.extract_video_id(url)
        output_dir = os.path.join(Config.VIDEOS_DIR, video_id)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            info = self.downloader.download(url, video_id)
            self.send_progress('processing', 'download', f'下载完成: {info["title"]}')
        except Exception as e:
            msg = str(e)
            if 'HTTP Error 412' in msg or 'Precondition Failed' in msg:
                msg = (
                    f'{msg}\n\n'
                    '提示：B 站触发风控（HTTP 412）。通常是 Cookie 未生效/过期或请求头不被接受导致。\n'
                    '解决思路：\n'
                    '1) 重新从浏览器导出并替换 cookies.txt（Netscape 格式，需包含 SESSDATA 等）；\n'
                    '2) 更换网络环境或关闭代理/VPN，稍后重试；\n'
                    '3) 降低频率，避免短时间多次导入。'
                )
            self.send_progress('error', 'download', f'下载失败: {msg}')
            raise
        
        audio_path = info.get('audio_path') or os.path.join(output_dir, 'audio.mp3')
        transcript_txt = os.path.join(output_dir, 'transcript.txt')
        transcript_srt = os.path.join(output_dir, 'transcript.srt')
        
        self.send_progress('processing', 'transcribe', '正在转录英文文本（可能需要几分钟）...')
        
        try:
            def run_transcribe():
                last_reported = {'segments': 0}

                def on_progress(segment_count):
                    if segment_count > last_reported['segments']:
                        last_reported['segments'] = segment_count
                        self.send_progress('processing', 'transcribe', f'正在转录英文文本...（已处理 {segment_count} 段）')

                def on_status(event, payload):
                    if event == 'loading_model' and payload:
                        self.send_progress(
                            'processing',
                            'transcribe',
                            f'正在加载 Whisper 模型: {payload.get("model_size")}（device={payload.get("device")}, compute={payload.get("compute_type")}）',
                        )
                    elif event == 'model_ready':
                        self.send_progress('processing', 'transcribe', 'Whisper 模型加载完成，开始转录...')
                    elif event == 'audio_prepared' and payload:
                        self.send_progress('processing', 'transcribe', '音频预处理完成，开始转录...')

                return self.transcriber.transcribe(
                    audio_path,
                    output_dir,
                    progress_callback=on_progress,
                    status_callback=on_status,
                )

            stop_event = threading.Event()
            start_time = time.time()

            def heartbeat():
                while not stop_event.wait(10):
                    elapsed = int(time.time() - start_time)
                    self.send_progress('processing', 'transcribe', f'正在转录英文文本...（已进行 {elapsed}s）')

            hb_thread = threading.Thread(target=heartbeat, daemon=True)
            hb_thread.start()
            try:
                run_transcribe()
            finally:
                stop_event.set()
            self.send_progress('processing', 'transcribe', '转录完成')
        except Exception as e:
            self.send_progress('error', 'transcribe', f'转录失败: {str(e)}')
            raise
        
        self.send_progress('processing', 'translate', '正在翻译成双语...')
        
        try:
            def on_translate_progress(current, total):
                self.send_progress('processing', 'translate', f'正在翻译成双语...（{current}/{total}）')

            self.translator.translate_and_correct(transcript_txt, transcript_srt, output_dir, progress_callback=on_translate_progress)
            self.send_progress('processing', 'translate', '翻译完成')
        except Exception as e:
            self.send_progress('error', 'translate', f'翻译失败: {str(e)}')
            raise
        
        sentence_count = self._count_sentences(os.path.join(output_dir, 'bilingual.txt'))
        
        self._save_to_db(video_id, info, sentence_count)
        
        self.send_progress('completed', 'done', '处理完成', video_id=video_id, title=info['title'], sentence_count=sentence_count)
        
        return {
            'video_id': video_id,
            'title': info['title'],
            'sentence_count': sentence_count
        }
    
    def _count_sentences(self, bilingual_path):
        with open(bilingual_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
        return len(lines) // 2
    
    def _save_to_db(self, video_id, info, sentence_count):
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO videos (id, title, url, duration, sentence_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (video_id, info['title'], info['url'], info.get('duration', 0), sentence_count))
        conn.commit()
        conn.close()
