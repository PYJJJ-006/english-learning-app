import os
from volcenginesdkarkruntime import Ark
from config import Config

class Translator:
    def __init__(self):
        self.client = Ark(api_key=Config.ARK_API_KEY, base_url=Config.ARK_BASE_URL)
        self.model = Config.ARK_ENDPOINT_ID
    
    def translate_and_correct(self, transcript_txt, transcript_srt, output_dir, progress_callback=None):
        bilingual_txt_path = os.path.join(output_dir, 'bilingual.txt')
        bilingual_srt_path = os.path.join(output_dir, 'bilingual.srt')
        
        if os.path.exists(bilingual_txt_path) and os.path.exists(bilingual_srt_path):
            try:
                with open(transcript_txt, 'r', encoding='utf-8') as f:
                    transcript_lines = [l for l in f.read().splitlines() if l.strip()]
                with open(bilingual_txt_path, 'r', encoding='utf-8') as f:
                    bilingual_lines = f.read().splitlines()
                pairs = 0
                i = 0
                while i < len(bilingual_lines) - 1:
                    if bilingual_lines[i].strip() and bilingual_lines[i + 1].strip():
                        pairs += 1
                        i += 2
                    else:
                        i += 1
                if transcript_lines and pairs >= int(len(transcript_lines) * 0.9):
                    with open(bilingual_txt_path, 'r', encoding='utf-8') as f:
                        return f.read()
            except Exception:
                pass
        
        with open(transcript_txt, 'r', encoding='utf-8') as f:
            txt_content = f.read()
        
        with open(transcript_srt, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        blocks = self._split_srt_blocks(srt_content)
        if not blocks:
            raise ValueError('SRT 解析失败')

        chunk_size = Config.TRANSLATE_SRT_BLOCKS_PER_CHUNK
        total_chunks = (len(blocks) + chunk_size - 1) // chunk_size
        all_txt_parts = []
        all_srt_parts = []

        for chunk_index in range(total_chunks):
            start = chunk_index * chunk_size
            end = min(len(blocks), start + chunk_size)
            chunk_blocks = blocks[start:end]
            chunk_srt = "\n\n".join(chunk_blocks).strip()
            prompt = f"""你是一个专业的英语翻译助手。请把下面这段英文字幕翻译成中文，并严格保持格式。

要求：
1) 不要遗漏任何条目，不要合并或拆分条目。
2) 保持原有序号与时间轴不变。
3) 每条字幕保持英文原文不变，在其下一行添加中文翻译。
4) 输出必须包含两个部分：先输出 \"## TXT内容\"，再输出 \"## SRT内容\"。

## TXT内容格式
每条英文一行，下一行是中文翻译，两行一组；组与组之间空一行。

## SRT内容格式
保持原有 SRT 时间轴与序号，每条英文下面一行添加中文。

以下是需要处理的 SRT 片段：
{chunk_srt}
"""

            if progress_callback:
                progress_callback(chunk_index + 1, total_chunks)

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的英语翻译助手，擅长将英文内容翻译成中文，并进行文本校正。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=Config.ARK_MAX_TOKENS,
                extra_headers={
                    "X-Reasoning-Effort": Config.ARK_REASONING_EFFORT
                }
            )

            response_content = completion.choices[0].message.content
            txt_part, srt_part = self._parse_response(response_content)
            all_txt_parts.append(txt_part.strip())
            all_srt_parts.append(srt_part.strip())

        merged_txt = "\n\n".join([p for p in all_txt_parts if p]).strip() + "\n"
        merged_srt = "\n\n".join([p for p in all_srt_parts if p]).strip() + "\n"

        with open(bilingual_txt_path, 'w', encoding='utf-8') as f:
            f.write(merged_txt)

        with open(bilingual_srt_path, 'w', encoding='utf-8') as f:
            f.write(merged_srt)

        return merged_txt
    
    def _parse_response(self, response):
        if not response:
            return "", ""
        parts = response.split("## SRT内容", 1)
        txt_part = parts[0]
        txt_part = txt_part.replace("## TXT内容", "").strip()
        srt_part = parts[1].strip() if len(parts) > 1 else ""
        return txt_part, srt_part

    def _split_srt_blocks(self, srt_content):
        raw_blocks = [b.strip() for b in srt_content.strip().split("\n\n") if b.strip()]
        blocks = []
        for b in raw_blocks:
            lines = [l.rstrip() for l in b.splitlines() if l.strip()]
            if len(lines) < 3:
                continue
            if "-->" not in lines[1]:
                continue
            blocks.append("\n".join(lines))
        return blocks
