"""
AI 供应商抽象层

统一接口调用不同 AI 视觉模型（Claude Vision、OpenAI GPT-4V、自定义端点）。
通过数据库配置动态切换供应商，无需重启服务。
"""
import base64
import json
from abc import ABC, abstractmethod
from pathlib import Path

import httpx


CONTENT_ANALYSIS_PROMPT = """你是专业照片内容分析师。分析图片内容，返回结构化标签 JSON：

{
  "scene": ["<场景标签>"],
  "people": {"count": <人数>, "tags": ["<人物描述>"]},
  "setting": ["<环境标签>"],
  "composition": ["<构图标签>"]
}

标签词表（优先使用，可补充）：
- scene: 风景, 人像, 建筑, 美食, 动物, 静物, 运动, 街拍, 活动, 花卉, 夜景, 交通
- people: count=整数, 描述: 成人, 儿童, 群体, 正面, 侧面, 背影
- setting: 室内, 户外, 街道, 自然, 海边, 山地, 城市, 公园, 餐厅, 工作室
- composition: 特写, 全身, 半身, 大头, 俯拍, 仰拍, 平视, 对称, 三分法, 留白, 前景虚化

规则：每维度 1-3 个标签，仅返回 JSON，不要包含其他文字。"""


class AIProvider(ABC):
    @abstractmethod
    async def analyze_image(self, image_path: str) -> dict:
        pass

    @abstractmethod
    async def test_connection(self) -> str:
        pass


def _load_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def _parse_ai_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model or "claude-sonnet-4-20250514"

    async def analyze_image(self, image_path: str) -> dict:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        image_data = _load_image_base64(image_path)

        ext = Path(image_path).suffix.lower()
        media_type = "image/jpeg"
        if ext == ".png":
            media_type = "image/png"
        elif ext == ".webp":
            media_type = "image/webp"

        message = await client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": CONTENT_ANALYSIS_PROMPT},
                ],
            }],
        )
        return _parse_ai_response(message.content[0].text)

    async def test_connection(self) -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        message = await client.messages.create(
            model=self.model,
            max_tokens=50,
            messages=[{"role": "user", "content": "回复OK"}],
        )
        return f"连接成功，模型: {self.model}"


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str, base_url: str = ""):
        self.api_key = api_key
        self.model = model or "gpt-4o"
        self.base_url = base_url or "https://api.openai.com/v1"

    async def analyze_image(self, image_path: str) -> dict:
        image_data = _load_image_base64(image_path)
        ext = Path(image_path).suffix.lower()
        media_type = "image/jpeg"
        if ext == ".png":
            media_type = "image/png"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
                            {"type": "text", "text": CONTENT_ANALYSIS_PROMPT},
                        ],
                    }],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return _parse_ai_response(data["choices"][0]["message"]["content"])

    async def test_connection(self) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "max_tokens": 50,
                    "messages": [{"role": "user", "content": "回复OK"}],
                },
            )
            resp.raise_for_status()
            return f"连接成功，模型: {self.model}"


class CustomProvider(AIProvider):
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    async def analyze_image(self, image_path: str) -> dict:
        image_data = _load_image_base64(image_path)
        ext = Path(image_path).suffix.lower()
        media_type = "image/jpeg"
        if ext == ".png":
            media_type = "image/png"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
                            {"type": "text", "text": CONTENT_ANALYSIS_PROMPT},
                        ],
                    }],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return _parse_ai_response(data["choices"][0]["message"]["content"])

    async def test_connection(self) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "max_tokens": 50,
                    "messages": [{"role": "user", "content": "回复OK"}],
                },
            )
            resp.raise_for_status()
            return f"连接成功，端点: {self.base_url}"


def get_ai_provider(settings: dict[str, str]) -> AIProvider:
    provider = settings.get("ai_provider", "claude")
    api_key = settings.get("ai_api_key", "")
    model = settings.get("ai_model_name", "")
    base_url = settings.get("ai_base_url", "")

    if not api_key:
        raise ValueError("未配置 API Key")

    if provider == "claude":
        return ClaudeProvider(api_key, model)
    elif provider == "openai":
        return OpenAIProvider(api_key, model, base_url)
    elif provider == "deepseek":
        return OpenAIProvider(api_key, model or "deepseek-chat", base_url or "https://api.deepseek.com/v1")
    elif provider == "custom":
        if not base_url:
            raise ValueError("自定义供应商需要配置接口地址")
        return CustomProvider(api_key, model, base_url)
    else:
        raise ValueError(f"不支持的供应商: {provider}")
