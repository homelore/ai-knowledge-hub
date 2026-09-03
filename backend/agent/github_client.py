"""GitHub API 客户端封装 — 仓库搜索与 Release 拉取，内置限流控制与指数退避重试。

使用 httpx 同步客户端，自动管理请求头、速率限制和错误重试。
未配置 token 时以未认证身份请求（限额 60 次/小时），但会输出警告。
"""

import time
import logging
from typing import Optional

import httpx

from config import (
    GITHUB_TOKEN,
    GITHUB_API_BASE,
    GITHUB_API_VERSION,
    MIN_STARS,
)

logger = logging.getLogger("ai-hub.github")

# 指数退避重试配置
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [2, 4, 8]  # 三次重试的等待时间（秒）


class GitHubClient:
    """GitHub REST API 同步客户端。

    内置能力：
    - 请求头管理（Authorization / Accept / X-GitHub-Api-Version）
    - 限流控制（检查 X-RateLimit-Remaining，不足时休眠至 reset 时间）
    - 指数退避重试（网络错误 / 429 / 5xx / 限额 403，最多 3 次）
    """

    def __init__(self, token: Optional[str] = None):
        """初始化客户端。

        Args:
            token: GitHub Personal Access Token，为 None 时从 config 读取；
                   若仍为空则以未认证身份请求（限额 60/h）。
        """
        self.token = token if token is not None else GITHUB_TOKEN
        self.base_url = GITHUB_API_BASE

        # 构造请求头
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        else:
            logger.warning(
                "未配置 GITHUB_TOKEN，将以未认证身份请求 GitHub API（限额 60 次/小时）"
            )

        # 创建复用连接的同步客户端
        self._client = httpx.Client(headers=self.headers, timeout=30.0)

    # ── 内部方法 ──────────────────────────────────────────

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        """检查响应头中的限流信息，剩余配额不足时休眠等待至重置时间。

        GitHub 在每次响应中返回 X-RateLimit-Remaining 和 X-RateLimit-Reset。
        当剩余次数 <= 1 时，下一次请求很可能触发限流，提前休眠。
        """
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_ts = response.headers.get("X-RateLimit-Reset")

        if remaining is None or reset_ts is None:
            return

        remaining_int = int(remaining)
        if remaining_int <= 1:
            wait_seconds = int(reset_ts) - int(time.time())
            if wait_seconds > 0:
                logger.warning(
                    f"GitHub API 配额不足（剩余 {remaining_int}），"
                    f"休眠 {wait_seconds}s 等待至重置时间..."
                )
                time.sleep(wait_seconds + 1)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """发送 HTTP 请求，内置指数退避重试。

        重试条件：网络错误（httpx.RequestError）、429（Too Many Requests）、
        5xx（服务器错误）、403 且限额耗尽（X-RateLimit-Remaining=0）。
        其他 4xx 错误不重试，直接抛出。

        Args:
            method: HTTP 方法（GET / POST 等）
            path: API 路径（如 /search/repositories），会自动拼接 base_url
            **kwargs: 透传给 httpx.Client.request 的额外参数（如 params）

        Returns:
            httpx.Response 成功响应

        Raises:
            httpx.HTTPStatusError: 重试耗尽后仍返回错误状态码
            httpx.RequestError: 重试耗尽后仍发生网络错误
        """
        url = path if path.startswith("http") else f"{self.base_url}{path}"

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self._client.request(method, url, **kwargs)
                status = response.status_code

                # 限流检查：从当前响应头读取剩余配额，不足则休眠（为下次请求做准备）
                self._handle_rate_limit(response)

                # 判断是否可重试
                is_rate_limited_403 = (
                    status == 403
                    and response.headers.get("X-RateLimit-Remaining") == "0"
                )
                should_retry = (
                    status == 429
                    or status >= 500
                    or is_rate_limited_403
                )

                if should_retry:
                    if attempt < MAX_RETRIES:
                        # 优先使用 Retry-After 头（429 时 GitHub 会返回），否则指数退避
                        retry_after = response.headers.get("Retry-After")
                        wait = int(retry_after) if retry_after else RETRY_BACKOFF_SECONDS[attempt]
                        logger.warning(
                            f"请求 {url} 返回 {status}，"
                            f"第 {attempt + 1}/{MAX_RETRIES} 次重试（等待 {wait}s）"
                        )
                        time.sleep(wait)
                        continue
                    # 重试次数用尽，抛出异常
                    response.raise_for_status()

                # 其他 4xx 错误 → 不重试，直接抛出
                if status >= 400:
                    response.raise_for_status()

                return response

            except httpx.RequestError as exc:
                # 网络层错误（连接超时、DNS 失败等）→ 重试
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_SECONDS[attempt]
                    logger.warning(
                        f"请求 {url} 网络异常: {exc}，"
                        f"第 {attempt + 1}/{MAX_RETRIES} 次重试（等待 {wait}s）"
                    )
                    time.sleep(wait)
                    continue
                raise

        # 理论上不会到达（循环内总会 return 或 raise）
        raise RuntimeError(f"请求 {url} 重试 {MAX_RETRIES} 次后仍失败")

    # ── 公开方法 ──────────────────────────────────────────

    def search_repositories(
        self,
        topic: str,
        sort: str = "stars",
        per_page: int = 30,
        max_results: int = 30,
    ) -> list[dict]:
        """搜索指定 topic 的仓库，按 star 数降序排列。

        构造查询参数：
            q=topic:{topic} stars:>{MIN_STARS}&sort={sort}&order=desc&per_page={per_page}

        自动分页直到收集 max_results 条或无更多结果。

        Args:
            topic: GitHub topic 关键词（如 "llm"）
            sort: 排序字段，默认 "stars"
            per_page: 每页数量（GitHub 上限 100）
            max_results: 最多收集的仓库数

        Returns:
            仓库原始 JSON items 列表（最多 max_results 条）
        """
        all_items: list[dict] = []
        page = 1

        while len(all_items) < max_results:
            params = {
                "q": f"topic:{topic} stars:>{MIN_STARS}",
                "sort": sort,
                "order": "desc",
                "per_page": min(per_page, 100),
                "page": page,
            }
            response = self._request("GET", "/search/repositories", params=params)
            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            all_items.extend(items)

            # 不足一页说明已到最后一页
            if len(items) < per_page:
                break

            page += 1

        return all_items[:max_results]

    def get_releases(
        self,
        owner: str,
        repo: str,
        per_page: int = 5,
    ) -> list[dict]:
        """获取指定仓库的 Release 列表。

        调用 GET /repos/{owner}/{repo}/releases，返回最新的若干条 Release。

        Args:
            owner: 仓库所有者（如 "langchain-ai"）
            repo: 仓库名（如 "langchain"）
            per_page: 最多拉取的 Release 数量

        Returns:
            Release 原始 JSON 列表（最新在前）
        """
        params = {"per_page": min(per_page, 100)}
        response = self._request(
            "GET", f"/repos/{owner}/{repo}/releases", params=params
        )
        return response.json()

    # ── 资源清理 ──────────────────────────────────────────

    def close(self) -> None:
        """关闭底层 HTTP 客户端，释放连接池资源。"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
