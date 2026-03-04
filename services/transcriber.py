import os
import shutil
import subprocess
from faster_whisper import WhisperModel
from config import Config

class Transcriber:
    def __init__(self, model_size=None, device=None, compute_type=None, cpu_threads=None, num_workers=None):
        model_size = model_size or Config.WHISPER_MODEL_SIZE
        if model_size in ('tiny', 'base', 'small', 'medium'):
            model_size = f'{model_size}.en'
        device = device or Config.WHISPER_DEVICE
        compute_type = compute_type or Config.WHISPER_COMPUTE_TYPE
        cpu_threads = Config.WHISPER_CPU_THREADS if cpu_threads is None else cpu_threads
        num_workers = Config.WHISPER_NUM_WORKERS if num_workers is None else num_workers
        self._model_args = {
            'model_size': model_size,
            'device': device,
            'compute_type': compute_type,
            'cpu_threads': cpu_threads,
            'num_workers': num_workers,
        }
        self._model = None

    def _get_model(self):
        if self._model is None:
            self._model = WhisperModel(
                self._model_args['model_size'],
                device=self._model_args['device'],
                compute_type=self._model_args['compute_type'],
                cpu_threads=self._model_args['cpu_threads'],
                num_workers=self._model_args['num_workers'],
            )
        return self._model

    def _maybe_convert_to_wav16k(self, audio_path, output_dir):
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            return audio_path, None
        _, ext = os.path.splitext(audio_path)
        ext = ext.lower()
        if ext == '.wav':
            return audio_path, None
        wav_path = os.path.join(output_dir, 'audio_16k.wav')
        cmd = [
            ffmpeg,
            '-y',
            '-i',
            audio_path,
            '-vn',
            '-ac',
            '1',
            '-ar',
            '16000',
            wav_path,
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return wav_path, wav_path
    
    def transcribe(self, audio_path, output_dir, progress_callback=None, status_callback=None):
        txt_path = os.path.join(output_dir, 'transcript.txt')
        srt_path = os.path.join(output_dir, 'transcript.srt')
        
        if os.path.exists(txt_path) and os.path.exists(srt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        if status_callback:
            status_callback(
                'loading_model',
                {
                    'model_size': self._model_args['model_size'],
                    'device': self._model_args['device'],
                    'compute_type': self._model_args['compute_type'],
                },
            )
        model = self._get_model()
        if status_callback:
            status_callback('model_ready', None)

        prepared_audio_path, temp_path = self._maybe_convert_to_wav16k(audio_path, output_dir)
        if status_callback and prepared_audio_path != audio_path:
            status_callback('audio_prepared', {'path': prepared_audio_path})
        try:
            segments, info = model.transcribe(
                prepared_audio_path,
                language='en',
                task='transcribe',
                beam_size=Config.WHISPER_BEAM_SIZE,
                best_of=Config.WHISPER_BEST_OF,
                temperature=Config.WHISPER_TEMPERATURE,
                condition_on_previous_text=Config.WHISPER_CONDITION_ON_PREVIOUS_TEXT,
                vad_filter=Config.WHISPER_VAD_FILTER,
                vad_parameters={'min_silence_duration_ms': Config.WHISPER_MIN_SILENCE_DURATION_MS},
                chunk_length=Config.WHISPER_CHUNK_LENGTH,
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        
        transcript_lines = []
        srt_lines = []
        
        for i, segment in enumerate(segments, 1):
            start_time = segment.start
            end_time = segment.end
            text = segment.text.strip()
            
            transcript_lines.append(text)
            
            srt_lines.append(f"{i}")
            srt_lines.append(f"{self._format_time(start_time)} --> {self._format_time(end_time)}")
            srt_lines.append(text)
            srt_lines.append("")

            if progress_callback and (i % 20 == 0):
                progress_callback(i)
        
        transcript_text = "\n".join(transcript_lines)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(srt_lines))
        
        return transcript_text
    
    def _format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
