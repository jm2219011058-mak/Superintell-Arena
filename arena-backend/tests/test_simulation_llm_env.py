"""回归测试：sk-ant key 未显式配置 base_url 时，模拟脚本必须把
camel 的 OpenAI 客户端指向 Anthropic 的 OpenAI 兼容端点。

背景：camel/OASIS 只用 OpenAI 协议发请求。修复前 base_url 为空会打到
api.openai.com，Anthropic key 全部 401，模拟十轮 0 动作（sim_698b4fb5fb53）。
"""

import importlib.util
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

COMPAT_URL = "https://api.anthropic.com/v1"


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_anthropic_key_defaults_to_compat_endpoint(monkeypatch):
    mod = _load_script("run_parallel_simulation")

    monkeypatch.setenv("LLM_API_KEY", "sk-ant-test-key")
    monkeypatch.setenv("LLM_MODEL_NAME", "claude-sonnet-5")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_BOOST_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE_URL", raising=False)

    mod.create_model({}, use_boost=False)

    assert os.environ.get("OPENAI_API_BASE_URL") == COMPAT_URL


def test_explicit_base_url_is_respected(monkeypatch):
    mod = _load_script("run_parallel_simulation")

    monkeypatch.setenv("LLM_API_KEY", "sk-ant-test-key")
    monkeypatch.setenv("LLM_MODEL_NAME", "claude-sonnet-5")
    monkeypatch.setenv("LLM_BASE_URL", "http://my-proxy.local/v1")
    monkeypatch.delenv("LLM_BOOST_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE_URL", raising=False)

    mod.create_model({}, use_boost=False)

    assert os.environ.get("OPENAI_API_BASE_URL") == "http://my-proxy.local/v1"


def test_non_anthropic_key_keeps_default(monkeypatch):
    mod = _load_script("run_parallel_simulation")

    monkeypatch.setenv("LLM_API_KEY", "sk-openai-style-key")
    monkeypatch.setenv("LLM_MODEL_NAME", "gpt-4o-mini")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_BOOST_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE_URL", raising=False)

    mod.create_model({}, use_boost=False)

    assert os.environ.get("OPENAI_API_BASE_URL") is None
