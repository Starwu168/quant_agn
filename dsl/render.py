def render_text(template: str, ctx: dict) -> str:
    # 简单 format 渲染（后续可升级 Jinja2）
    try:
        return template.format(**ctx)
    except Exception:
        # 模板写错也不要炸监控
        return str(template)
