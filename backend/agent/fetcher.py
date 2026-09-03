"""拉取主流程 — 编排 GitHub 客户端与数据筛选，UPSERT 到数据库。

入口函数 fetch_weekly_trending() 依次完成：
  a) 创建 FetchLog 记录
  b) 遍历主题拉取仓库
  c) 字段映射、去重、star 筛选
  d) 对 Top 50 仓库拉取 Release
  e) 计算周增长
  f) UPSERT repos 表
  g) 插入新 releases
  h) 更新 repo_topics 关联
  i) 插入 repo_star_history 快照
  j) 更新 FetchLog 为 success
  k) 全程异常捕获，失败时 FetchLog.status=failed 并保留上次数据
"""

import logging
from datetime import datetime

from config import (
    FETCH_TOPICS,
    MIN_STARS,
    MAX_REPOS_PER_TOPIC,
    MAX_RELEASES_PER_REPO,
    TOP_REPO_RELEASE_COUNT,
)
from models.database import get_db_session
from models.repo import Repo
from models.release import Release
from models.topic import Topic, RepoTopic
from models.fetch_log import FetchLog
from models.repo_star_history import RepoStarHistory

from agent.github_client import GitHubClient
from agent.filter import (
    map_repo,
    map_release,
    dedup_repos,
    filter_by_stars,
    classify_topics,
    calculate_weekly_gain,
    get_week_label,
)

logger = logging.getLogger("ai-hub.fetcher")


# ── 辅助函数 ──────────────────────────────────────────────

def _fetch_repos_from_topics(
    client: GitHubClient,
) -> tuple[list[dict], dict[int, set[str]]]:
    """遍历所有预定义主题，从 GitHub 搜索仓库并映射。

    Returns:
        (all_mapped_repos, repo_topics_map)
        - all_mapped_repos: map_repo 后的仓库字典列表（可能含重复）
        - repo_topics_map: {github_id: {topic_name, ...}} 每个仓库匹配的预定义主题
    """
    all_mapped_repos: list[dict] = []
    repo_topics_map: dict[int, set[str]] = {}

    # 预定义主题名称集合，用于补充搜索主题
    predefined_names = {t["name"] for t in FETCH_TOPICS}

    for topic_config in FETCH_TOPICS:
        topic_name = topic_config["name"]
        logger.info(f"拉取主题: {topic_name} ({topic_config['display_name']})")

        try:
            raw_repos = client.search_repositories(
                topic=topic_name,
                sort="stars",
                per_page=min(MAX_REPOS_PER_TOPIC, 100),
                max_results=MAX_REPOS_PER_TOPIC,
            )
        except Exception as exc:
            logger.error(f"拉取主题 {topic_name} 失败: {exc}")
            continue

        logger.info(f"主题 {topic_name}: 获取到 {len(raw_repos)} 个仓库")

        for raw_repo in raw_repos:
            mapped = map_repo(raw_repo)
            gid = mapped.get("github_id")
            if not gid:
                continue

            all_mapped_repos.append(mapped)

            # 分类主题：从仓库自带 topics 中匹配预定义主题
            raw_topics = raw_repo.get("topics", [])
            matched = classify_topics(raw_topics, FETCH_TOPICS)
            # 保险：搜索条件已保证该仓库含此 topic，若 topics 字段缺失则补充
            if topic_name in predefined_names and topic_name not in matched:
                matched.append(topic_name)

            # 累加到主题映射（同一仓库可能出现在多个主题搜索中）
            if gid in repo_topics_map:
                repo_topics_map[gid] |= set(matched)
            else:
                repo_topics_map[gid] = set(matched)

    return all_mapped_repos, repo_topics_map


def _fetch_releases_for_top_repos(
    client: GitHubClient,
    top_repos: list[dict],
) -> dict[int, list[dict]]:
    """对 Top N 仓库拉取 Release 列表。

    Args:
        client: GitHubClient 实例
        top_repos: 排序后的仓库字典列表（取前 TOP_REPO_RELEASE_COUNT 个）

    Returns:
        {github_id: [map_release 后的字典, ...]}
    """
    releases_map: dict[int, list[dict]] = {}

    for mapped_repo in top_repos:
        full_name = mapped_repo.get("full_name", "")
        gid = mapped_repo.get("github_id")
        if not full_name or "/" not in full_name or gid is None:
            continue

        owner, repo_name = full_name.split("/", 1)

        try:
            raw_releases = client.get_releases(
                owner=owner,
                repo=repo_name,
                per_page=MAX_RELEASES_PER_REPO,
            )
            mapped_releases = [map_release(r) for r in raw_releases]
            releases_map[gid] = mapped_releases
            logger.info(f"仓库 {full_name}: 获取到 {len(mapped_releases)} 个 Release")
        except Exception as exc:
            logger.error(f"拉取仓库 {full_name} 的 Release 失败: {exc}")

    return releases_map


def _upsert_to_db(
    session,
    all_mapped_repos: list[dict],
    repo_topics_map: dict[int, set[str]],
    releases_map: dict[int, list[dict]],
    week_label: str,
) -> tuple[int, int, int]:
    """将拉取到的数据 UPSERT 到数据库。

    步骤：
        e) 计算周增长（对比上次记录）
        f) UPSERT repos 表
        g) 插入新 releases（tag_name 不存在才插入）
        h) 更新 repo_topics 关联（先删后插）
        i) 插入 repo_star_history 快照（同周去重）

    Returns:
        (total_fetched, new_count, updated_count)
    """
    total_fetched = len(all_mapped_repos)
    new_count = 0
    updated_count = 0

    # 预加载主题 name → id 映射
    topic_name_to_id: dict[str, int] = {}
    for t in session.query(Topic).all():
        topic_name_to_id[t.name] = t.id

    for mapped_repo in all_mapped_repos:
        gid = mapped_repo["github_id"]

        # ── e) 计算周增长 ──
        existing = session.query(Repo).filter(Repo.github_id == gid).first()
        previous_stars = existing.stars if existing else None
        weekly_gain = calculate_weekly_gain(
            mapped_repo.get("stars", 0), previous_stars
        )

        # ── f) UPSERT repos 表 ──
        if existing:
            # 已存在 → 更新
            existing.full_name = mapped_repo["full_name"]
            existing.name = mapped_repo["name"]
            existing.description = mapped_repo["description"]
            existing.url = mapped_repo["url"]
            existing.stars = mapped_repo["stars"]
            existing.forks = mapped_repo["forks"]
            existing.language = mapped_repo["language"]
            existing.license = mapped_repo["license"]
            existing.weekly_star_gain = weekly_gain
            existing.github_updated_at = mapped_repo["github_updated_at"]
            existing.updated_at = datetime.utcnow()
            repo_obj = existing
            updated_count += 1
        else:
            # 不存在 → 插入
            repo_obj = Repo(
                github_id=gid,
                full_name=mapped_repo["full_name"],
                name=mapped_repo["name"],
                description=mapped_repo["description"],
                url=mapped_repo["url"],
                stars=mapped_repo["stars"],
                forks=mapped_repo["forks"],
                language=mapped_repo["language"],
                license=mapped_repo["license"],
                weekly_star_gain=weekly_gain,
                github_updated_at=mapped_repo["github_updated_at"],
            )
            session.add(repo_obj)
            session.flush()  # 刷新以获取 repo_obj.id
            new_count += 1

        # ── h) 更新 repo_topics 关联（先删后插）──
        session.query(RepoTopic).filter(
            RepoTopic.repo_id == repo_obj.id
        ).delete()

        matched_topic_names = repo_topics_map.get(gid, set())
        for topic_name in matched_topic_names:
            topic_id = topic_name_to_id.get(topic_name)
            if topic_id:
                session.add(RepoTopic(repo_id=repo_obj.id, topic_id=topic_id))

        # ── g) 插入新 releases（tag_name 不存在才插入）──
        mapped_releases = releases_map.get(gid, [])
        for mr in mapped_releases:
            tag = mr.get("tag_name")
            if not tag:
                continue
            # 检查该 tag 是否已存在
            exists = (
                session.query(Release)
                .filter(
                    Release.repo_id == repo_obj.id,
                    Release.tag_name == tag,
                )
                .first()
            )
            if not exists:
                session.add(Release(
                    repo_id=repo_obj.id,
                    tag_name=tag,
                    release_name=mr.get("release_name"),
                    body=mr.get("body"),
                    url=mr.get("url"),
                    is_prerelease=mr.get("is_prerelease", False),
                    published_at=mr.get("published_at"),
                ))

        # ── i) 插入 repo_star_history 快照（同周去重）──
        existing_snapshot = (
            session.query(RepoStarHistory)
            .filter(
                RepoStarHistory.repo_id == repo_obj.id,
                RepoStarHistory.recorded_week == week_label,
            )
            .first()
        )
        if not existing_snapshot:
            session.add(RepoStarHistory(
                repo_id=repo_obj.id,
                stars=mapped_repo.get("stars", 0),
                recorded_week=week_label,
                recorded_at=datetime.utcnow(),
            ))

    return total_fetched, new_count, updated_count


# ── 主入口 ────────────────────────────────────────────────

def fetch_weekly_trending() -> dict:
    """每周拉取主入口：搜索各主题热门仓库 → 映射/去重/筛选 → 拉取 Release → UPSERT 数据库。

    完整流程（步骤 a-k 详见模块文档字符串）。
    全程异常捕获，失败时 FetchLog.status=failed 并保留上次数据。
    """
    week_label = get_week_label()
    logger.info(f"========== 开始本周拉取: {week_label} ==========")

    # a) 创建 FetchLog 记录（status=running）
    #    使用独立 session 提前提交，确保即使后续失败也有日志记录
    with get_db_session() as session:
        fetch_log = FetchLog(
            fetch_week=week_label,
            status="running",
            started_at=datetime.utcnow(),
        )
        session.add(fetch_log)
        session.flush()
        log_id = fetch_log.id

    try:
        client = GitHubClient()

        # b) 遍历主题拉取仓库 + c) 字段映射（去重与筛选稍后统一处理）
        all_mapped_repos, repo_topics_map = _fetch_repos_from_topics(client)
        logger.info(f"各主题合计获取到 {len(all_mapped_repos)} 个仓库（去重前）")

        # c) 去重 + star 筛选
        all_mapped_repos = dedup_repos(all_mapped_repos)
        all_mapped_repos = filter_by_stars(all_mapped_repos, MIN_STARS)

        # 按 star 数降序排列（确保 Top N 取到最热门的）
        all_mapped_repos.sort(key=lambda r: r.get("stars", 0), reverse=True)
        logger.info(
            f"去重筛选后共 {len(all_mapped_repos)} 个仓库"
        )

        # d) 对 Top N 仓库拉取 Release
        top_repos = all_mapped_repos[:TOP_REPO_RELEASE_COUNT]
        releases_map = _fetch_releases_for_top_repos(client, top_repos)
        logger.info(
            f"对 Top {len(top_repos)} 仓库拉取 Release，"
            f"成功获取 {len(releases_map)} 个仓库的 Release"
        )

        client.close()

        # f-i) UPSERT 到数据库（独立 session，失败则回滚，保留上次数据）
        with get_db_session() as session:
            total_fetched, new_count, updated_count = _upsert_to_db(
                session,
                all_mapped_repos,
                repo_topics_map,
                releases_map,
                week_label,
            )

            # j) 更新 FetchLog（status=success，在同一 session 中提交）
            log = session.query(FetchLog).filter(FetchLog.id == log_id).first()
            if log:
                log.status = "success"
                log.total_fetched = total_fetched
                log.new_count = new_count
                log.updated_count = updated_count
                log.finished_at = datetime.utcnow()

        logger.info(
            f"========== 本周拉取完成: {week_label} | "
            f"共 {total_fetched} 个仓库，新增 {new_count}，更新 {updated_count} =========="
        )
        return {
            "status": "success",
            "fetch_week": week_label,
            "total_fetched": total_fetched,
            "new_count": new_count,
            "updated_count": updated_count,
        }

    except Exception as exc:
        # k) 失败处理：记录错误信息，保留上次数据
        #    UPSERT session 已自动回滚，此处只需更新 FetchLog 状态
        logger.exception(f"本周拉取失败: {exc}")

        try:
            with get_db_session() as session:
                log = session.query(FetchLog).filter(FetchLog.id == log_id).first()
                if log:
                    log.status = "failed"
                    log.error_message = str(exc)[:2000]
                    log.finished_at = datetime.utcnow()
        except Exception as log_exc:
            logger.error(f"更新 FetchLog 失败状态时出错: {log_exc}")

        return {
            "status": "failed",
            "fetch_week": week_label,
            "error": str(exc),
            "total_fetched": 0,
            "new_count": 0,
            "updated_count": 0,
        }
