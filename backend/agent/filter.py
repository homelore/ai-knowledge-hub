"""数据转换与筛选 — 将 GitHub API 返回的原始 JSON 映射为内部字段，并做去重/过滤/分类。

所有函数均为纯函数，不依赖数据库或网络，便于单元测试。
"""

import datetime
from typing import Optional

from config import MIN_STARS


def _parse_github_datetime(dt_str: Optional[str]) -> Optional[datetime.datetime]:
    """解析 GitHub API 返回的 ISO 8601 时间字符串为 naive UTC datetime。

    GitHub 返回格式如 "2026-08-23T10:30:00Z"，Z 表示 UTC。
    转换为 naive datetime 以与数据库中的 utcnow() 保持一致。

    Args:
        dt_str: ISO 8601 时间字符串，可能为 None

    Returns:
        naive UTC datetime，输入为 None 或解析失败时返回 None
    """
    if not dt_str:
        return None
    try:
        # Python 3.11+ 的 fromisoformat 直接支持 "Z"，此处做兼容处理
        normalized = dt_str.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(normalized)
        # 去除时区信息，统一存储为 naive UTC（与 datetime.utcnow() 一致）
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        return None


def map_repo(raw_repo: dict) -> dict:
    """将 GitHub API 返回的仓库 JSON 映射为内部字段字典。

    字段映射关系：
        id              → github_id
        full_name       → full_name
        name            → name
        description     → description
        html_url        → url
        stargazers_count→ stars
        forks_count     → forks
        language        → language
        license.name    → license
        updated_at      → github_updated_at

    Args:
        raw_repo: GitHub API /search/repositories 返回的单个仓库 JSON

    Returns:
        内部字段字典，包含 9 个字段
    """
    license_info = raw_repo.get("license")
    license_name = license_info.get("name") if license_info else None

    return {
        "github_id": raw_repo.get("id"),
        "full_name": raw_repo.get("full_name"),
        "name": raw_repo.get("name"),
        "description": raw_repo.get("description"),
        "url": raw_repo.get("html_url"),
        "stars": raw_repo.get("stargazers_count", 0) or 0,
        "forks": raw_repo.get("forks_count", 0) or 0,
        "language": raw_repo.get("language"),
        "license": license_name,
        "github_updated_at": _parse_github_datetime(raw_repo.get("updated_at")),
    }


def map_release(raw_release: dict) -> dict:
    """将 GitHub API 返回的 Release JSON 映射为内部字段字典。

    字段映射关系：
        tag_name    → tag_name
        name        → release_name
        body        → body
        html_url    → url
        prerelease  → is_prerelease
        published_at→ published_at

    Args:
        raw_release: GitHub API /repos/{owner}/{repo}/releases 返回的单个 Release JSON

    Returns:
        内部字段字典，包含 6 个字段
    """
    return {
        "tag_name": raw_release.get("tag_name"),
        "release_name": raw_release.get("name"),
        "body": raw_release.get("body"),
        "url": raw_release.get("html_url"),
        "is_prerelease": raw_release.get("prerelease", False),
        "published_at": _parse_github_datetime(raw_release.get("published_at")),
    }


def dedup_repos(repos: list[dict]) -> list[dict]:
    """按 github_id 去重，保留首次出现的记录。

    同时兼容已映射格式（github_id 键）和 GitHub 原始格式（id 键）。

    Args:
        repos: 仓库字段字典列表（map_repo 后或原始 JSON）

    Returns:
        去重后的列表，顺序保持首次出现时的顺序
    """
    seen: set[int] = set()
    result: list[dict] = []

    for repo in repos:
        # 优先取映射后的 github_id，回退到原始 id
        gid = repo.get("github_id") or repo.get("id")
        if gid is None:
            # 无 ID 的记录直接保留（不应出现在正常流程中）
            result.append(repo)
            continue
        if gid not in seen:
            seen.add(gid)
            result.append(repo)

    return result


def filter_by_stars(repos: list[dict], min_stars: int = MIN_STARS) -> list[dict]:
    """过滤掉 star 数低于阈值的仓库。

    Args:
        repos: 仓库字段字典列表（需含 stars 键）
        min_stars: 最低 star 阈值，默认从 config.MIN_STARS 读取

    Returns:
        stars >= min_stars 的仓库列表
    """
    return [r for r in repos if (r.get("stars") or 0) >= min_stars]


def classify_topics(raw_topics: list[str], predefined_topics: list[dict]) -> list[str]:
    """将 GitHub 仓库自带的 topics 列表映射到预定义主题 name 列表。

    取交集：对预定义主题逐个检查其 name 是否出现在仓库的 raw_topics 中。
    返回顺序遵循 predefined_topics 的定义顺序（便于一致展示）。

    Args:
        raw_topics: GitHub repo 的 topics 列表（如 ["llm", "python", "transformer"]）
        predefined_topics: 预定义主题列表（config.FETCH_TOPICS 格式，含 name 键）

    Returns:
        匹配到的预定义主题 name 列表（如 ["llm", "transformer"]）
    """
    raw_set = set(raw_topics or [])
    return [t["name"] for t in predefined_topics if t["name"] in raw_set]


def calculate_weekly_gain(
    current_stars: int,
    previous_stars: Optional[int],
) -> int:
    """计算周 Star 增长量。

    首次拉取时 previous_stars 为 None，此时 gain = current_stars（视为从 0 增长）。
    非首次时 gain = current_stars - previous_stars（可能为负数，表示本周掉星）。

    Args:
        current_stars: 本次拉取到的 star 数
        previous_stars: 上次拉取记录的 star 数，None 表示首次拉取

    Returns:
        周 Star 增长量
    """
    if previous_stars is None:
        return current_stars
    return current_stars - previous_stars


def get_week_label() -> str:
    """返回当前 ISO 周标识，格式如 "2026-W34"。

    使用 datetime.date.isocalendar() 获取 ISO 周年和周数。
    ISO 周以周一为起始，跨年时按 ISO 8601 标准归属到正确的年份。

    Returns:
        ISO 周标识字符串
    """
    today = datetime.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"
