"""思想家蒸馏服务测试：切分边界 + map/reduce 编排（LLM 打桩，不真实调用）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import thinker_distiller as td


def test_split_respects_segment_size():
    para = "内容" * 100  # 200 字/段
    text = "\n".join([para] * 400)  # 约 8 万字
    segments = td.ThinkerDistiller.split_text(text)
    assert len(segments) >= 3
    assert all(len(s) <= td.SEGMENT_CHARS + 1 for s in segments)
    # 内容无丢失（按非换行字符数对比）
    assert sum(len(s.replace("\n", "")) for s in segments) == len(text.replace("\n", ""))


def test_split_hard_slices_giant_paragraph():
    text = "字" * (td.SEGMENT_CHARS * 2 + 100)  # 无换行的超长段
    segments = td.ThinkerDistiller.split_text(text)
    assert len(segments) == 3
    assert sum(len(s) for s in segments) == len(text)


class _StubLLMClient:
    """记录调用的打桩客户端"""
    calls = []

    def __init__(self, **kwargs):
        pass

    def chat(self, messages, temperature=0.7, max_tokens=4096):
        content = messages[0]["content"]
        _StubLLMClient.calls.append(content)
        if "思想家人设卡" in content:
            return "## 身份定位\n测试人设卡"
        return "要点摘要"


def test_distill_orchestrates_map_reduce(monkeypatch):
    monkeypatch.setattr(td, "LLMClient", _StubLLMClient)
    _StubLLMClient.calls = []

    distiller = td.ThinkerDistiller()
    text = "\n".join(["观点" * 100] * 400)  # 约 8 万字 -> 多段
    card = distiller.distill(text, "测试书.pdf")

    assert card.startswith("## 身份定位")
    n_segments = len(td.ThinkerDistiller.split_text(text))
    # map 每段一次 + reduce 一次
    assert len(_StubLLMClient.calls) == n_segments + 1
