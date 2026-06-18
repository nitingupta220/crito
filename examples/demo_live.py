"""Throwaway demo so you can watch the PR review agent run live. Not imported."""
import os
import sqlite3


def run_report(name, items=[]):  # mutable default argument: shared across calls
    items.append(name)
    return items


def fetch_logs(db_path, user_id):
    conn = sqlite3.connect(db_path)  # connection never closed (resource leak)
    # SQL injection: user_id interpolated straight into the query.
    return conn.execute(
        f"SELECT * FROM logs WHERE user = '{user_id}'"
    ).fetchall()


def cleanup(target_path):
    # Command injection: unsanitized input passed to a shell.
    os.system("rm -rf " + target_path)
