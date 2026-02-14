#!/usr/bin/env python3
"""
CI/CD自动跟踪和处理脚本
自动获取GitHub Actions状态，根据结果做出相应处理
"""
import requests
import time
import json
from datetime import datetime

# GitHub配置
import os
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER = "shuge-x"
REPO_NAME = "opencode-platform"
GITHUB_API = "https://api.github.com"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
} if GITHUB_TOKEN else {
    "Accept": "application/vnd.github.v3+json"
}


def get_latest_workflow_run():
    """获取最新的workflow运行"""
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
    params = {"per_page": 1}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    runs = response.json()["workflow_runs"]
    if runs:
        return runs[0]
    return None


def get_workflow_status(run_id):
    """获取workflow详细状态"""
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_job_status(run_id):
    """获取jobs详细状态"""
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/jobs"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    jobs = response.json()["jobs"]
    job_status = {}

    for job in jobs:
        job_name = job["name"]
        job_status[job_name] = {
            "status": job["status"],
            "conclusion": job.get("conclusion"),
            "started_at": job.get("started_at"),
            "completed_at": job.get("completed_at"),
            "steps": []
        }

        for step in job.get("steps", []):
            job_status[job_name]["steps"].append({
                "name": step["name"],
                "status": step["status"],
                "conclusion": step.get("conclusion")
            })

    return job_status


def track_workflow_progress(run_id, interval=30):
    """实时跟踪workflow进度"""
    print(f"\n{'='*60}")
    print(f"开始跟踪 CI/CD 进度 (Run ID: {run_id})")
    print(f"{'='*60}\n")

    while True:
        try:
            run_info = get_workflow_status(run_id)
            status = run_info["status"]
            conclusion = run_info.get("conclusion")

            # 获取jobs详细状态
            job_status = get_job_status(run_id)

            # 打印当前状态
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Workflow状态: {status}")

            for job_name, job_info in job_status.items():
                print(f"  - {job_name}: {job_info['status']}", end="")
                if job_info['conclusion']:
                    print(f" ({job_info['conclusion']})")
                else:
                    print()

                # 打印步骤进度
                for step in job_info['steps']:
                    if step['status'] == 'completed':
                        icon = "✅" if step['conclusion'] == 'success' else "❌"
                        print(f"    {icon} {step['name']}")
                    elif step['status'] == 'in_progress':
                        print(f"    🔄 {step['name']} (进行中)")

            # 判断是否完成
            if status == "completed":
                print(f"\n{'='*60}")
                print(f"CI/CD 已完成！")
                print(f"{'='*60}\n")

                if conclusion == "success":
                    print("✅ 所有测试通过！")
                    print("📧 准备通知术哥验收...")
                    return True, job_status
                else:
                    print("❌ 测试失败！")
                    print("🔧 需要立即修复...")
                    return False, job_status

            time.sleep(interval)

        except Exception as e:
            print(f"❌ 错误: {e}")
            time.sleep(interval)


def analyze_failure(job_status):
    """分析失败原因"""
    print("\n分析失败原因...")

    for job_name, job_info in job_status.items():
        if job_info['conclusion'] == 'failure':
            print(f"\n失败的Job: {job_name}")

            for step in job_info['steps']:
                if step.get('conclusion') == 'failure':
                    print(f"  失败步骤: {step['name']}")

                    # TODO: 获取详细日志
                    # 这里可以调用GitHub API获取失败的详细日志
                    # 然后自动分析并修复


def notify_success():
    """通知成功"""
    message = """
✅ CI/CD 测试全部通过！

📦 项目：opencode-platform
🔗 仓库：https://github.com/shuge-x/opencode-platform
📊 Actions：https://github.com/shuge-x/opencode-platform/actions

所有自动化测试已通过，可以验收！
    """
    print(message)
    # TODO: 调用术哥的通知接口（飞书/邮件等）


def auto_fix_issues():
    """自动修复问题（未来功能）"""
    print("\n🔧 自动修复模式启动...")
    print("1. 分析失败日志")
    print("2. 定位问题代码")
    print("3. 自动修复")
    print("4. 重新提交")
    print("5. 重新触发CI/CD")


def main():
    """主流程"""
    print("🚀 CI/CD 自动跟踪系统启动\n")

    # 1. 获取最新的workflow运行
    latest_run = get_latest_workflow_run()

    if not latest_run:
        print("❌ 没有找到workflow运行")
        return

    run_id = latest_run["id"]
    print(f"最新 Workflow: {latest_run['name']}")
    print(f"触发事件: {latest_run['event']}")
    print(f"分支: {latest_run['head_branch']}")
    print(f"提交: {latest_run['head_sha'][:7]}")

    # 2. 实时跟踪进度
    success, job_status = track_workflow_progress(run_id)

    # 3. 根据结果处理
    if success:
        notify_success()
    else:
        analyze_failure(job_status)
        # auto_fix_issues()  # 未来功能


if __name__ == "__main__":
    main()
