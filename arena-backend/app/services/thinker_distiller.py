"""
思想家蒸馏服务

整本书级别的思想家资料 -> 思想家人设卡。
分段总结（map，可并行）-> 汇总人设卡（reduce），用便宜模型跑批量阅读，
让本体/图谱生成读几千字的人设卡而不是几十万字的原书。
"""

import concurrent.futures
from typing import List

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient

logger = get_logger('mirofish.thinker_distiller')

# 单段长度（字符）。中文约 1.5 token/字，24000 字远低于任何模型的上下文上限
SEGMENT_CHARS = 24000

# 超长资料的分段上限（约 96 万字），超出部分截断并记录日志
MAX_SEGMENTS = 40

MAP_PROMPT = """以下是《{filename}》的第 {index}/{total} 部分。
请提取本部分中体现作者思想的内容，用要点列表输出，600 字以内：
- 核心观点与论断
- 关键概念、术语及其含义
- 体现作者论证风格 / 语言特征的要点
- 涉及的立场判断（对行业、技术、社会等）

原文：
{segment}"""

REDUCE_PROMPT = """以下是《{filename}》全书的分段要点。请汇总成一张「思想家人设卡」，
供多智能体辩论系统为该思想家建立辩论人设。忠于原文，不虚构。总长 2000-3000 字。

结构：
## 身份定位
## 核心观点（8-15 条）
## 论证风格与语言特征
## 标志性概念
## 对常见议题的立场倾向（经济 / 技术 / 社会 / 行业等）

分段要点：
{summaries}"""


class ThinkerDistiller:
    """把书籍级思想家资料蒸馏为人设卡"""

    def __init__(self):
        self.model = Config.LLM_DISTILL_MODEL_NAME or Config.LLM_MODEL_NAME
        self.client = LLMClient(model=self.model)

    @staticmethod
    def split_text(text: str) -> List[str]:
        """按段落边界切分，单段不超过 SEGMENT_CHARS"""
        segments = []
        current = []
        current_len = 0

        for para in text.split('\n'):
            # 单个超长段落（无换行的原始文本）硬切
            while len(para) > SEGMENT_CHARS:
                if current:
                    segments.append('\n'.join(current))
                    current, current_len = [], 0
                segments.append(para[:SEGMENT_CHARS])
                para = para[SEGMENT_CHARS:]

            if current_len + len(para) > SEGMENT_CHARS and current:
                segments.append('\n'.join(current))
                current, current_len = [], 0

            current.append(para)
            current_len += len(para) + 1

        if current and any(p.strip() for p in current):
            segments.append('\n'.join(current))

        return segments

    def _summarize_segment(self, segment: str, index: int, total: int, filename: str) -> str:
        prompt = MAP_PROMPT.format(
            filename=filename, index=index, total=total, segment=segment
        )
        return self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

    def distill(self, text: str, filename: str) -> str:
        """整本书 -> 人设卡。任何一步失败都抛出异常，由调用方决定回退策略。"""
        segments = self.split_text(text)

        if len(segments) > MAX_SEGMENTS:
            logger.warning(
                "思想家资料过长，截断分段: %s（%d 段 -> %d 段）",
                filename, len(segments), MAX_SEGMENTS
            )
            segments = segments[:MAX_SEGMENTS]

        total = len(segments)
        logger.info(
            "开始蒸馏思想家资料: %s（%d 字，%d 段，模型 %s）",
            filename, len(text), total, self.model
        )

        # map：分段并行总结
        summaries: List[str] = [""] * total
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = {
                pool.submit(self._summarize_segment, seg, i + 1, total, filename): i
                for i, seg in enumerate(segments)
            }
            for future in concurrent.futures.as_completed(futures):
                i = futures[future]
                summaries[i] = future.result()
                logger.info("分段总结完成 %d/%d: %s", i + 1, total, filename)

        # reduce：汇总人设卡
        joined = "\n\n".join(
            f"--- 第 {i + 1} 部分要点 ---\n{s}" for i, s in enumerate(summaries)
        )
        card = self.client.chat(
            messages=[{"role": "user", "content": REDUCE_PROMPT.format(filename=filename, summaries=joined)}],
            temperature=0.4,
            max_tokens=8192,
        )
        logger.info("人设卡生成完成: %s（%d 字）", filename, len(card))
        return card
