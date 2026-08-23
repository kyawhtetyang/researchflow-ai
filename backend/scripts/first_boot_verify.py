from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from typing import Any


def request_json(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(f"{base_url.rstrip('/')}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_api(base_url: str, timeout_sec: int) -> None:
    deadline = time.monotonic() + timeout_sec
    last_error = None
    while time.monotonic() < deadline:
        try:
            health = request_json(base_url, "GET", "/health")
            if health.get("status") == "ok":
                return
        except Exception as exc:
            last_error = str(exc)
        time.sleep(2)
    raise RuntimeError(f"API did not become healthy: {last_error}")


def wait_for_job(base_url: str, job_id: int, timeout_sec: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        detail = request_json(base_url, "GET", f"/api/research/{job_id}")
        status = detail["job"]["status"]
        if status == "completed":
            return detail
        if status == "failed":
            raise RuntimeError(f"research job failed: {detail['job'].get('error')}")
        time.sleep(2)
    raise RuntimeError(f"research job {job_id} did not finish within {timeout_sec}s")


def request_text(base_url: str, path: str) -> str:
    with urllib.request.urlopen(f"{base_url.rstrip('/')}{path}", timeout=10) as response:
        return response.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ResearchFlow AI first boot and async worker flow.")
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout-sec", type=int, default=180)
    args = parser.parse_args()

    wait_for_api(args.base_url, args.timeout_sec)
    frontend_html = request_text(args.base_url, "/")
    if "ResearchFlow AI" not in frontend_html:
        raise RuntimeError("frontend did not render expected ResearchFlow AI page")

    created = request_json(
        args.base_url,
        "POST",
        "/api/research/",
        {"query": "What AI Engineer project should follow a production RAG assistant?", "run_now": False},
    )
    if created["status"] != "queued":
        raise RuntimeError(f"expected queued async job, got: {created}")

    detail = wait_for_job(args.base_url, created["id"], args.timeout_sec)
    chat = request_json(args.base_url, "GET", f"/api/research/{created['id']}/chat")
    summary = request_json(args.base_url, "GET", f"/api/research/{created['id']}/summary")
    eval_run = request_json(args.base_url, "POST", "/api/eval/run")

    if len(detail["steps"]) < 4:
        raise RuntimeError("expected at least 4 workflow steps")
    if not detail["sources"]:
        raise RuntimeError("expected at least one research source")
    if not detail.get("report") or not detail["report"].get("markdown"):
        raise RuntimeError("expected a persisted research report")
    if chat["status"] != "completed" or not chat["answer"]:
        raise RuntimeError(f"chat endpoint did not return a completed answer: {chat}")
    if summary["readiness_score"] <= 0:
        raise RuntimeError(f"readiness score too low: {summary}")
    if eval_run["average_readiness_score"] <= 0:
        raise RuntimeError(f"eval run did not score jobs: {eval_run}")

    print(
        json.dumps(
            {
                "status": "ok",
                "job_id": created["id"],
                "steps": len(detail["steps"]),
                "sources": len(detail["sources"]),
                "readiness": summary["readiness_score"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"first boot verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
