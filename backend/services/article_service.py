"""文章读取与渲染业务逻辑。

负责文章元数据查询、Markdown 正文读取并用 python-markdown + pygments 渲染为 HTML，
以及扫描 content/articles 目录下的 .md 文件，解析 YAML front matter 后 upsert 到 articles 表。
所有函数接收 db: Session 作为第一个参数（render_article 等纯渲染函数除外）。
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import markdown
import yaml
from sqlalchemy.orm import Session

from config import ARTICLES_DIR
from models.article import Article

logger = logging.getLogger("ai-hub.article")

# 匹配文件开头的 YAML front matter 块：以 --- 起始并以 --- 结束
_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _split_front_matter(text: str) -> tuple:
    """将原始 Markdown 文本拆分为 (front_matter 文本, 正文)。

    若文件没有 front matter，则返回 ("", 原文)。
    """
    match = _FRONT_MATTER_RE.match(text)
    if match:
        front_text = match.group(1)
        body = text[match.end():]
        return front_text, body
    return "", text


def get_articles(
    db: Session,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 10,
) -> List[Article]:
    """查询文章列表（仅元数据）。

    Args:
        db: 数据库会话
        topic: 主题/标签筛选（匹配 tags JSON 数组中的某一项），为 None 时不筛选
        difficulty: 难度筛选（beginner / intermediate / advanced），为 None 时不筛选
        limit: 最多返回条数，默认 10

    Returns:
        已发布文章列表，按创建时间降序
    """
    query = db.query(Article).filter(Article.published == True)  # noqa: E712

    # 难度筛选
    if difficulty:
        query = query.filter(Article.difficulty == difficulty)

    # 主题/标签筛选：tags 是 JSON 数组，用 LIKE 做包含匹配（兼容 SQLite）
    if topic:
        query = query.filter(Article.tags.like(f'%"{topic}"%'))

    return query.order_by(Article.created_at.desc()).limit(limit).all()


def get_article_by_slug(db: Session, slug: str) -> Optional[Article]:
    """根据 slug 查询单篇文章元数据。

    Args:
        db: 数据库会话
        slug: 文章 URL 标识

    Returns:
        Article 对象，不存在或未发布则返回 None
    """
    return (
        db.query(Article)
        .filter(Article.slug == slug, Article.published == True)  # noqa: E712
        .first()
    )


def render_article(article: Article) -> str:
    """读取文章 Markdown 文件内容并渲染为 HTML，带代码高亮。

    使用 python-markdown 渲染，codehilite 扩展配合 pygments 实现代码块语法高亮。
    自动剥离文件开头的 YAML front matter，仅渲染正文部分。

    Args:
        article: Article 对象（需有 file_path）

    Returns:
        渲染后的 HTML 字符串
    """
    file_path = Path(article.file_path)
    raw = file_path.read_text(encoding="utf-8")

    # 剥离 front matter，只渲染正文
    _front_text, body = _split_front_matter(raw)

    html = markdown.markdown(
        body,
        extensions=[
            "fenced_code",   # 支持 ``` 围栏代码块
            "codehilite",    # 代码高亮（pygments）
            "tables",        # 表格语法
            "toc",           # 自动生成目录
            "sane_lists",    # 更合理的列表解析
            "nl2br",         # 换行转 <br>
        ],
        extension_configs={
            "codehilite": {
                "guess_lang": True,   # 自动推断代码语言
                "linenums": False,    # 不显示行号
                "noclasses": False,   # 使用 pygments CSS class（前端引入对应样式）
            }
        },
        output_format="html5",
    )
    return html


def get_article_content_html(article: Article) -> str:
    """render_article 的别名，语义化接口：获取文章正文 HTML。"""
    return render_article(article)


def get_related_articles(db: Session, article: Article, limit: int = 3) -> List[Article]:
    """按 tags 交集查找相关文章。

    与当前文章共享标签越多的文章相关性越高；共享标签数相同时按创建时间降序。

    Args:
        db: 数据库会话
        article: 当前文章对象
        limit: 最多返回条数，默认 3

    Returns:
        相关文章列表（已排除当前文章）
    """
    current_tags = set(article.tags or [])
    if not current_tags:
        return []

    # 取其他已发布文章作为候选
    candidates = (
        db.query(Article)
        .filter(Article.published == True, Article.id != article.id)  # noqa: E712
        .all()
    )

    # 计算每篇候选文章与当前文章的共享标签数
    scored: List[tuple] = []
    for cand in candidates:
        shared = len(set(cand.tags or []) & current_tags)
        if shared > 0:
            scored.append((shared, cand))

    # 排序：先按创建时间降序（次要键，稳定排序前置步骤）
    scored.sort(
        key=lambda item: item[1].created_at or datetime.min,
        reverse=True,
    )
    # 再按共享标签数降序（主键，稳定排序保持上面的次序）
    scored.sort(key=lambda item: item[0], reverse=True)

    return [cand for _shared, cand in scored[:limit]]


def _to_int(value, default: int) -> int:
    """安全转换为整数，失败时返回默认值。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sync_articles(db: Session) -> int:
    """扫描 ARTICLES_DIR 目录下的 .md 文件，解析 front matter 后 upsert 到 articles 表。

    front matter 为 YAML 格式（用 --- 分隔），包含字段：
    title, summary, difficulty, read_time, tags, slug（可选 published）。
    file_path 存储实际文件路径。slug 缺省时使用文件名（不含扩展名）。

    Args:
        db: 数据库会话

    Returns:
        本次同步处理的文件数量
    """
    articles_dir = Path(ARTICLES_DIR)
    if not articles_dir.exists():
        logger.warning("文章目录不存在: %s", articles_dir)
        return 0

    count = 0
    for md_file in sorted(articles_dir.glob("*.md")):
        try:
            raw = md_file.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("读取文章文件失败 %s: %s", md_file, exc)
            continue

        front_text, _body = _split_front_matter(raw)
        meta = yaml.safe_load(front_text) if front_text.strip() else {}
        if not isinstance(meta, dict):
            meta = {}

        # 解析元数据，缺省值兜底
        slug = meta.get("slug") or md_file.stem
        title = meta.get("title") or md_file.stem
        summary = meta.get("summary")
        difficulty = meta.get("difficulty") or "beginner"
        read_time = _to_int(meta.get("read_time"), 5)
        tags = meta.get("tags") or []
        if not isinstance(tags, list):
            tags = [tags]
        published = bool(meta.get("published", True))

        # 按 slug upsert：存在则更新，不存在则新增
        existing = db.query(Article).filter(Article.slug == slug).first()
        if existing:
            existing.title = title
            existing.summary = summary
            existing.difficulty = difficulty
            existing.read_time = read_time
            existing.tags = tags
            existing.file_path = str(md_file)
            existing.published = published
        else:
            db.add(Article(
                slug=slug,
                title=title,
                summary=summary,
                difficulty=difficulty,
                read_time=read_time,
                tags=tags,
                file_path=str(md_file),
                published=published,
            ))
        count += 1

    db.commit()
    logger.info("文章同步完成，共处理 %d 篇", count)
    return count
