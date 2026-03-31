import os
from typing import List, Dict, Any, Optional

import asyncio
import time
from dotenv import load_dotenv
from zhipuai import ZhipuAI
from zhipuai.core._errors import APIReachLimitError


load_dotenv()


class ZhipuLLMClient:
    """
    基于官方 `zhipuai` SDK 的 LLM 封装。
    使用同步 SDK，通过 `asyncio.to_thread` 以兼容异步接口。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4.6v-flash",
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("缺少 ZHIPUAI_API_KEY，请在 .env 中配置。")

        self.model = model
        self.timeout = timeout
        self.client = ZhipuAI(api_key=self.api_key)

    async def acompletion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        调用聊天补全接口，返回生成文本。
        """

        def _call_sync() -> str:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if extra_params:
                kwargs.update(extra_params)

            # 模型“当前访问量过大”时，简单重试几次
            max_retries = 3
            delay = 2.0
            for attempt in range(max_retries):
                try:
                    resp = self.client.chat.completions.create(**kwargs)
                    # SDK 一般会抛出异常处理 4xx/5xx，这里只做结果解析
                    try:
                        return resp.choices[0].message.content
                    except Exception as exc:  # noqa: BLE001
                        raise RuntimeError(f"调用智谱接口返回格式异常: {resp}") from exc
                except APIReachLimitError as e:
                    if attempt == max_retries - 1:
                        raise
                    print(
                        f"Zhipu APIReachLimitError: {e}, {delay}s 后重试第 {attempt + 1} 次"
                    )
                    time.sleep(delay)
                    delay *= 2

        return await asyncio.to_thread(_call_sync)

