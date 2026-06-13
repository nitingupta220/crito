"""Demo module with intentional issues, for dogfooding the PR review agent.

Not imported by the package. Exists only so a PR has something to review.
"""
import sqlite3


def get_user(db_path, user_id):
    # Resource leak: the connection is never closed.
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # SQL injection: user_id is interpolated straight into the query string.
    cur.execute("SELECT * FROM users WHERE id = %s" % user_id)
    return cur.fetchone()


def first_name(profile):
    # Unguarded access: raises KeyError when "name" is absent.
    return profile["name"].split(" ")[0]


def safe_div(a, b):
    try:
        return a / b
    except:  # bare except swallows everything, including KeyboardInterrupt
        return None
