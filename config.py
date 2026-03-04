import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), 'ARK_API_KEY.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    ARK_API_KEY = os.environ.get('ARK_API_KEY')
    ARK_ENDPOINT_ID = os.environ.get('ARK_ENDPOINT_ID')
    ARK_BASE_URL = os.environ.get('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
    
    ARK_MODEL = 'doubao-seed-2-0-mini'
    ARK_REASONING_EFFORT = 'low'
    ARK_MAX_TOKENS = int(os.environ.get('ARK_MAX_TOKENS', '8192'))
    
    COOKIES_PATH = os.path.join(os.path.dirname(__file__), 'cookies.txt')

    BILIBILI_REFERER = os.environ.get('BILIBILI_REFERER', 'https://www.bilibili.com/')
    BILIBILI_ORIGIN = os.environ.get('BILIBILI_ORIGIN', 'https://www.bilibili.com')
    BILIBILI_USER_AGENT = os.environ.get(
        'BILIBILI_USER_AGENT',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    )

    WHISPER_MODEL_SIZE = os.environ.get('WHISPER_MODEL_SIZE', 'tiny')
    WHISPER_DEVICE = os.environ.get('WHISPER_DEVICE', 'auto')
    WHISPER_COMPUTE_TYPE = os.environ.get('WHISPER_COMPUTE_TYPE', 'auto')
    WHISPER_CPU_THREADS = int(os.environ.get('WHISPER_CPU_THREADS', '0'))
    WHISPER_NUM_WORKERS = int(os.environ.get('WHISPER_NUM_WORKERS', '1'))
    WHISPER_BEAM_SIZE = int(os.environ.get('WHISPER_BEAM_SIZE', '1'))
    WHISPER_BEST_OF = int(os.environ.get('WHISPER_BEST_OF', '1'))
    WHISPER_TEMPERATURE = float(os.environ.get('WHISPER_TEMPERATURE', '0.0'))
    WHISPER_CONDITION_ON_PREVIOUS_TEXT = os.environ.get('WHISPER_CONDITION_ON_PREVIOUS_TEXT', 'false').lower() in ('1', 'true', 'yes', 'y', 'on')
    WHISPER_VAD_FILTER = os.environ.get('WHISPER_VAD_FILTER', 'true').lower() in ('1', 'true', 'yes', 'y', 'on')
    WHISPER_MIN_SILENCE_DURATION_MS = int(os.environ.get('WHISPER_MIN_SILENCE_DURATION_MS', '500'))
    WHISPER_CHUNK_LENGTH = int(os.environ.get('WHISPER_CHUNK_LENGTH', '30'))

    TRANSLATE_SRT_BLOCKS_PER_CHUNK = int(os.environ.get('TRANSLATE_SRT_BLOCKS_PER_CHUNK', '20'))
    
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    VIDEOS_DIR = os.path.join(DATA_DIR, 'videos')
    DATABASE_PATH = os.path.join(DATA_DIR, 'app.db')
    
    @staticmethod
    def init_app():
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.VIDEOS_DIR, exist_ok=True)
