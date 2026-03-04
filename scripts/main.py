import argparse
import os
from dotenv import load_dotenv
load_dotenv()


def _load_config(config_path=None):
    """加载 YAML 配置并同步到 env"""
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(_script_dir)
    exp_dir = os.path.join(_root, "experiments")
    if os.path.isdir(exp_dir):
        sys_path = list(__import__("sys").path)
        if exp_dir not in sys_path:
            __import__("sys").path.insert(0, exp_dir)
        from config_loader import load_config
        return load_config(config_path)
    return {}


def main():
    parser = argparse.ArgumentParser(description="Control script for running PersonaRAG functionalities")
    parser.add_argument("--config", "-c", help="YAML 配置路径，如 experiments/configs/persona_rag_baseline.yaml")
    subparsers = parser.add_subparsers(title="Commands", description="Available commands", help="Description")

    # Sub-parser for the 'run' command
    parser_run = subparsers.add_parser('run', help='Run the model')
    parser_run.add_argument('--dataset', required=True, help='Dataset name')
    parser_run.add_argument('--topk', type=int, required=True, help='Top K passages to consider')
    parser_run.set_defaults(func="run")

    # Sub-parser for the 'build' command
    parser_build = subparsers.add_parser('build', help='Build results into a CSV')
    parser_build.add_argument('--dataset', required=True, help='Dataset name')
    parser_build.add_argument('--topk', type=int, required=True, help='Top K passages to consider')
    parser_build.set_defaults(func="build")

    # Sub-parser for the 'evaluate' command
    parser_evaluate = subparsers.add_parser('evaluate', help='Evaluate the model outputs')
    parser_evaluate.add_argument('--dataset', required=True, help='Dataset name')
    parser_evaluate.add_argument('--topk', type=int, required=True, help='Top K passages to consider')
    parser_evaluate.set_defaults(func="evaluate")

    args = parser.parse_args()

    # 先加载配置（在导入 persona_rag 前设置 env）
    config_path = getattr(args, "config", None)
    _load_config(config_path)

    if hasattr(args, "func") and isinstance(args.func, str):
        from scripts.execution.run import main as run_main
        from scripts.execution.build import main as build_main
        from scripts.evaluation.evaluate import evaluate as evaluate_main
        funcs = {"run": run_main, "build": build_main, "evaluate": evaluate_main}
        funcs[args.func](args.dataset, args.topk)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()