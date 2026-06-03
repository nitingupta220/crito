"""
GitHub Actions Entrypoint
Self-contained script that runs the full 5-agent PR review pipeline
directly from a GitHub Actions runner. No server required.

Usage (from workflow):
  python scripts/action_review.py

Required env vars (set via GitHub Actions secrets + context):
  GITHUB_TOKEN         - auto-minted by Actions (contents:read, pull-requests:write)
  OPENROUTER_API_KEY   - user's own key stored in repo secrets
  GITHUB_REPOSITORY    - e.g. "owner/repo" (auto-set by Actions)
  GITHUB_EVENT_PATH    - path to the event JSON (auto-set by Actions)
"""
import asyncio
import json
import os
import sys

# Add project root to path so we can import app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _load_event() -> dict:
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path or not os.path.exists(event_path):
        print(f"[ERROR] GITHUB_EVENT_PATH not set or file missing: {event_path}")
        sys.exit(1)
    with open(event_path) as f:
        return json.load(f)


def _get_pr_info(event: dict) -> tuple[str, int]:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number = event.get("pull_request", {}).get("number")
    if not repo or not pr_number:
        print("[ERROR] Could not determine repo or PR number from event")
        sys.exit(1)
    return repo, int(pr_number)


async def main():
    # Validate required secrets
    required = ["GITHUB_TOKEN", "OPENROUTER_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[ERROR] Missing required environment variables: {missing}")
        print("Add them as GitHub Actions secrets and reference in the workflow.")
        sys.exit(1)

    # Patch settings before importing app modules
    # (env vars are already set by the workflow)
    event = _load_event()
    repo, pr_number = _get_pr_info(event)

    action = event.get("action", "")
    print(f"[INFO] Event: pull_request.{action} | Repo: {repo} | PR: #{pr_number}")

    # Skip draft PRs
    is_draft = event.get("pull_request", {}).get("draft", False)
    if is_draft:
        print("[INFO] PR is a draft — skipping review.")
        sys.exit(0)

    # Import pipeline (after env is set)
    from app.services.pipeline_service import review_pipeline

    print(f"[INFO] Starting review pipeline for {repo}#{pr_number}")
    result = await review_pipeline.run(repo=repo, pr_number=pr_number)

    status = result.get("status", "unknown")
    if status == "skipped":
        print(f"[INFO] Review skipped: {result.get('reason')}")
    elif status == "failed":
        print(f"[ERROR] Pipeline failed: {result.get('error')}")
        sys.exit(1)
    else:
        verdict = result.get("verdict", "unknown")
        findings = result.get("total_findings", 0)
        elapsed = result.get("elapsed_ms", 0)
        print(f"[INFO] Review complete — verdict={verdict} findings={findings} elapsed={elapsed}ms")
        comment_id = result.get("comment_id")
        if comment_id:
            pr_url = f"https://github.com/{repo}/pull/{pr_number}#issuecomment-{comment_id}"
            print(f"[INFO] Review posted: {pr_url}")

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
