"""
文件名: config.py
描述: 统一管理应用配置与环境变量读取，并提供数据目录初始化能力。
作用: 为本地运行与桌面壳模式提供可配置的存储路径与服务参数。
"""

import os
from dotenv import load_dotenv

"""
优先从桌面模式指定路径加载密钥文件，其次使用项目根目录的本地配置。
"""
ENV_FILE_PATH = os.environ.get('APP_ENV_PATH')

"""
根据文件是否存在选择加载路径，兼容桌面模式与本地开发模式。
"""
if ENV_FILE_PATH and os.path.exists(ENV_FILE_PATH):
    load_dotenv(ENV_FILE_PATH)
else:
    load_dotenv(os.path.join(os.path.dirname(__file__), 'ARK_API_KEY.env'))

class Config:
    """
    应用全局配置集合，支持环境变量覆盖，适配桌面壳运行路径。
    """

    """
    Web 安全与服务端 API 配置，支持环境变量注入。
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    ARK_API_KEY = os.environ.get('ARK_API_KEY')
    ARK_ENDPOINT_ID = os.environ.get('ARK_ENDPOINT_ID')
    ARK_BASE_URL = os.environ.get('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
    ARK_MODEL = 'doubao-seed-2-0-mini'
    ARK_REASONING_EFFORT = 'low'
    ARK_MAX_TOKENS = int(os.environ.get('ARK_MAX_TOKENS', '8192'))

    """
    桌面模式下允许指定 Cookie 与数据目录，避免写入只读资源目录。
    """
    APP_DATA_DIR = os.environ.get('APP_DATA_DIR')
    COOKIES_PATH = os.environ.get(
        'APP_COOKIES_PATH',
        os.path.join(os.path.dirname(__file__), 'cookies.txt'),
    )

    """
    B 站下载请求相关请求头配置。
    """
    BILIBILI_REFERER = os.environ.get('BILIBILI_REFERER', 'https://www.bilibili.com/')
    BILIBILI_ORIGIN = os.environ.get('BILIBILI_ORIGIN', 'https://www.bilibili.com')
    BILIBILI_USER_AGENT = os.environ.get(
        'BILIBILI_USER_AGENT',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    )

    """
    Whisper 转录相关可调参数。
    """
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

    """
    翻译拆分策略，控制每次请求的 SRT 分块数量。
    """
    TRANSLATE_SRT_BLOCKS_PER_CHUNK = int(os.environ.get('TRANSLATE_SRT_BLOCKS_PER_CHUNK', '20'))

    """
    数据存储路径，支持桌面壳传入自定义目录。
    """
    DATA_DIR = APP_DATA_DIR or os.path.join(os.path.dirname(__file__), 'data')
    VIDEOS_DIR = os.path.join(DATA_DIR, 'videos')
    DATABASE_PATH = os.path.join(DATA_DIR, 'app.db')

    """
    初始化本地数据目录，确保数据库与视频目录可写。
    """
    @staticmethod
    def init_app():
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.VIDEOS_DIR, exist_ok=True)
