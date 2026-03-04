#!/usr/bin/env python3
"""
Mock 模式验证：启动假 API 服务，跑 1 条样本验证流程
用法: python -m scripts.validate_mock --dataset nq --topk 5
"""
import argparse
import os
import sys
import time
import json
import subprocess
import urllib.request

# 在导入 persona_rag 前设置 env
PORT = 19999
os.environ["OPENAI_API_KEY"] = "sk-dummy"
os.environ["OPENAI_BASE_URL"] = f"http://127.0.0.1:{PORT}/v1"
os.environ["MODEL"] = "gpt-4"

from persona_rag.core.generate import create_agent_group, create_workflow
from persona_rag.prompts.prompt import Prompt


def wait_for_mock(port, timeout=10):
    for _ in range(timeout):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def run_one(dataset, topk):
    filename = f"data/data_{dataset}_sampled.jsonl"
    if not os.path.exists(filename):
        print(f"Error: {filename} not found")
        sys.exit(1)

    directory = f"logs/{os.environ['MODEL']}/{dataset}/top{topk}"
    os.makedirs(directory, exist_ok=True)

    with open(filename, "r", encoding="utf-8") as f:
        line = f.readline()
    data = json.loads(line)
    question = data["question"]
    answers = data["answers"]
    passages = data["passages"][:topk]

    print(f"Question: {question[:80]}...")
    input_dict = {
        "question": question,
        "passages": passages,
        "global_memory": "",
        "__answers__": answers,
    }

    agent_group = create_agent_group(Prompt())
    workflow = create_workflow(agent_group, init_input=input_dict)
    workflow.execute()

    log_path = f"{directory}/{dataset}_idx_0.json"
    workflow.save_log(log_path)
    print(f"Saved: {log_path}")
    print("Mock validation OK.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="nq")
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--config", "-c", help="YAML 配置路径")
    args = parser.parse_args()

    # 加载 YAML 配置（若指定）
    if args.config and os.path.isfile(args.config):
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        _root = os.path.dirname(_script_dir)
        exp_dir = os.path.join(_root, "experiments")
        if os.path.isdir(exp_dir) and exp_dir not in sys.path:
            sys.path.insert(0, exp_dir)
        try:
            from config_loader import load_config
            load_config(args.config)
        except Exception:
            pass

    port = args.port
    os.environ["OPENAI_BASE_URL"] = f"http://127.0.0.1:{port}/v1"  # Mock 模式固定

    # 启动 mock 服务
    proc = subprocess.Popen(
        [sys.executable, "-m", "scripts.mock_openai_server", str(port)],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(1)
        if not wait_for_mock(port, timeout=5):
            print("Mock server failed to start")
            proc.kill()
            sys.exit(1)
        run_one(args.dataset, args.topk)
    finally:
        proc.terminate()
        proc.wait(timeout=3)


if __name__ == "__main__":
    main()
