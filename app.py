"""
文件名: app.py
描述: Flask 应用路由与 API，支撑练习流程与数据管理。
作用: 提供页面渲染、句子接口与导入处理入口。
"""
import os
import json
import sqlite3
import threading
import uuid
from datetime import datetime
from queue import Queue, Empty
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, stream_with_context
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app()

progress_queues = {}

def init_db():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            duration INTEGER,
            sentence_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    videos = c.execute('SELECT * FROM videos ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('index.html', videos=videos)

@app.route('/import')
def import_page():
    return render_template('import.html')

@app.route('/paste')
def paste_page():
    return render_template('paste.html')

@app.route('/api/import', methods=['POST'])
def start_import():
    if os.environ.get('VERCEL') == '1':
        return jsonify({'error': '云端暂不支持直接导入B站视频，请先在本地导入后再在手机端练习，或使用“粘贴材料”功能'}), 503

    data = request.get_json()
    video_url = data.get('url', '').strip()
    
    if not video_url:
        return jsonify({'error': '请输入视频链接'}), 400
    
    if 'bilibili.com/video/' not in video_url:
        return jsonify({'error': '请输入有效的B站视频链接'}), 400
    
    import re
    match = re.search(r'BV\w+', video_url)
    if match:
        video_id = match.group(0)
    else:
        match = re.search(r'av(\d+)', video_url)
        if match:
            video_id = f"av{match.group(1)}"
        else:
            return jsonify({'error': '无法从链接中提取视频ID'}), 400

    if video_id in progress_queues:
        return jsonify({'video_id': video_id, 'message': '该视频正在处理中，请稍候...'}), 202

    progress_queues[video_id] = Queue()
    
    def process_in_background():
        from services.video_processor import VideoProcessor
        processor = VideoProcessor(progress_queues[video_id])
        try:
            processor.process(video_url)
        except Exception as e:
            progress_queues[video_id].put({'status': 'error', 'message': str(e)})
    
    thread = threading.Thread(target=process_in_background)
    thread.start()
    
    return jsonify({'video_id': video_id})

@app.route('/api/paste', methods=['POST'])
def create_from_paste():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()

    if not content:
        return jsonify({'error': '请输入中英文双语内容'}), 400

    pairs = parse_pasted_bilingual(content)
    if not pairs:
        return jsonify({'error': '未识别到任何句子对，请按“英文一行+中文下一行”（可空行分隔）或“英文\\t中文”格式粘贴'}), 400

    if not title:
        title = f'自定义材料 {datetime.now().strftime("%Y-%m-%d %H:%M")}'

    video_id = f'manual_{uuid.uuid4().hex[:12]}'
    output_dir = os.path.join(app.config['VIDEOS_DIR'], video_id)
    os.makedirs(output_dir, exist_ok=True)

    bilingual_path = os.path.join(output_dir, 'bilingual.txt')
    with open(bilingual_path, 'w', encoding='utf-8') as f:
        for english, chinese in pairs:
            f.write(f'{english}\n{chinese}\n\n')

    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO videos (id, title, url, duration, sentence_count)
        VALUES (?, ?, ?, ?, ?)
    ''', (video_id, title, 'manual://paste', 0, len(pairs)))
    conn.commit()
    conn.close()

    return jsonify({'video_id': video_id, 'sentence_count': len(pairs), 'title': title})

@app.route('/api/progress/<video_id>')
def progress_stream(video_id):
    def generate():
        queue = progress_queues.get(video_id)
        if not queue:
            yield f"data: {json.dumps({'status': 'error', 'message': '无效的视频ID'})}\n\n"
            return
        
        while True:
            try:
                data = queue.get(timeout=15)
                yield f"data: {json.dumps(data)}\n\n"
                
                if data.get('status') in ['completed', 'error']:
                    if video_id in progress_queues:
                        del progress_queues[video_id]
                    break
            except Empty:
                yield ": keepalive\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/practice/<video_id>')
def practice(video_id):
    video_dir = os.path.join(app.config['VIDEOS_DIR'], video_id)
    if not os.path.exists(video_dir):
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    video = c.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()
    conn.close()
    
    if not video:
        return redirect(url_for('index'))
    
    bilingual_path = os.path.join(video_dir, 'bilingual.txt')
    with open(bilingual_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sentences = parse_bilingual(content)
    
    return render_template('practice.html', video=video, sentences=sentences)

@app.route('/mobile/reading/<video_id>')
# 渲染移动端阅读模式页面壳，数据由前端异步获取
def mobile_reading(video_id):
    video_dir = os.path.join(app.config['VIDEOS_DIR'], video_id)
    if not os.path.exists(video_dir):
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    video = c.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()
    conn.close()
    
    if not video:
        return redirect(url_for('index'))
    
    return render_template('mobile_reading.html', video=video)

def parse_bilingual(content):
    lines = content.strip().split('\n')
    sentences = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line and i + 1 < len(lines):
            english = line
            chinese = lines[i + 1].strip()
            if chinese:
                sentences.append({
                    'english': english,
                    'chinese': chinese
                })
            i += 2
        else:
            i += 1
    return sentences

def parse_pasted_bilingual(content):
    raw_lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    lines = [l.strip() for l in raw_lines]

    pairs = []
    pending_english = None

    for line in lines:
        if not line:
            continue

        if '\t' in line:
            left, right = line.split('\t', 1)
            left = left.strip()
            right = right.strip()
            if left and right:
                pairs.append((left, right))
                pending_english = None
            continue

        if pending_english is None:
            pending_english = line
        else:
            pairs.append((pending_english, line))
            pending_english = None

    return pairs

@app.route('/api/videos/<video_id>/sentences')
def get_sentences(video_id):
    bilingual_path = os.path.join(app.config['VIDEOS_DIR'], video_id, 'bilingual.txt')
    if not os.path.exists(bilingual_path):
        return jsonify({'error': 'Video not found'}), 404
    
    with open(bilingual_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sentences = parse_bilingual(content)
    return jsonify({'sentences': sentences})

@app.route('/delete/<video_id>', methods=['POST'])
def delete_video(video_id):
    import shutil
    video_dir = os.path.join(app.config['VIDEOS_DIR'], video_id)
    if os.path.exists(video_dir):
        shutil.rmtree(video_dir)
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    c = conn.cursor()
    c.execute('DELETE FROM videos WHERE id = ?', (video_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
