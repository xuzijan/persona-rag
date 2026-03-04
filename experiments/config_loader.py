"""
从 YAML 加载配置，并同步到 os.environ 供 PersonaRAG 使用
"""
import os


def load_config(config_path=None):
    """从 YAML 加载配置，未指定时使用默认路径"""
    try:
        import yaml
    except ImportError:
        return {}
    _this = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(_this, "configs", "persona_rag_baseline.yaml")
    path = config_path or os.getenv("EXPERIMENT_CONFIG") or default_path
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    apply_to_env(cfg)
    return cfg


def apply_to_env(cfg):
    """将配置写入 os.environ，供 PersonaRAG 读取"""
    if not cfg:
        return
    m = cfg.get("model", {})
    if m.get("handle"):
        os.environ.setdefault("MODEL", str(m["handle"]))
    if "max_tokens" in m:
        os.environ.setdefault("MAX_TOKENS", str(m["max_tokens"]))
    if "enable_trimming" in m:
        os.environ.setdefault("ENABLE_TRIMMING", "true" if m["enable_trimming"] else "false")
