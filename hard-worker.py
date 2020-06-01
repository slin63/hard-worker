#!/usr/bin/env python3
from typing import Dict, List, Tuple

import random
import argparse
import os
import subprocess

from time import sleep

from datetime import datetime
from datetime import timedelta


# Path to your git binary
GIT = "usr/bin/git"

# How often to check for jobs
WATCH_INTERVAL = 2

# File with jobs in it
QUEUE = "/tmp/hardworkq.txt"
random.seed()


def start_process():
    """Watch QUEUE for jobs to do."""
    jobs_finished: Dict[str, Tuple[datetime, bool]] = {}
    while True:
        jobs: Dict[str, datetime] = {}
        pushed = False
        with open(QUEUE, "r") as queue:
            for job in queue.readlines():
                repo, push_time = job.strip().split("!!")
                push_time = datetime.strptime(
                    push_time, "%Y-%m-%d %H:%M:%S.%f"
                )

                # print(
                #     "@a78 ~/projects/python/hard-worker/hard-worker.py:31\n>",
                #     f"now, later, {datetime.now()}, {push_time}, {datetime.now() >= push_time}",
                # )
                jobs[repo] = push_time

            # Check if jobs should be executed
            for job, push_time in jobs.items():
                if datetime.now() >= push_time:
                    pushed = True
                    print(f"Pushing {'...' + repo[-20:]}!")
                    success = git_push(repo)
                    jobs_finished[repo] = (push_time, success)
                else:
                    jobs[repo] = push_time

            # Remove outdated jobs
            for job in jobs_finished:
                if job in jobs:
                    del jobs[job]

        # If we completed a job, regardless of success, update the queue
        if pushed:
            with open(QUEUE, "w") as queue:
                for repo, push_time in jobs.items():
                    queue.write(f"{repo}!!{push_time}\n")

        sleep(WATCH_INTERVAL)
        print("\n---")
        print(render_jobs(jobs))
        print(render_jobs_finished(jobs_finished))
        print("---")


def render_jobs(jobs: Dict[str, datetime]) -> str:
    out = "Hard work to be done:\n"
    for repo, push_time in jobs.items():
        out += f"  • {'...' + repo[-20:]}: {push_time.strftime('[%I:%M %p]')}\n"

    return out.strip()


def render_jobs_finished(
    jobs_finished: Dict[str, Tuple[datetime, bool]]
) -> str:
    out = "Hard work that has been done:\n"
    for repo, results in jobs_finished.items():
        push_time, success = results
        if success:
            success_str = "✓ successful!"
        else:
            success_str = "⨯ failed!"
        out += f"  • {'...' + repo[-20:]}: {success_str} {push_time.strftime('[%I:%M %p]')}\n"

    return out.strip()


def git_push(repo: str) -> bool:
    p = subprocess.Popen(["git", "push"], cwd=repo)
    # p = subprocess.Popen(
    #     ["touch", f"hardworkertest{datetime.now()}"], cwd=repo
    # )
    p.wait()

    return p.returncode == 0


def add_to_queue(repo: str, push_time: datetime) -> None:
    with open(QUEUE, "a") as queue:
        queue.write(f"{repo}!!{push_time}\n")


def get_current_repo(current_path: str) -> str:
    """Check if the given path is part of a valid repo"""
    repo = subprocess.Popen(
        "git rev-parse --show-toplevel",
        shell=True,
        stdout=subprocess.PIPE,
    )
    stdout, _ = repo.communicate()

    return stdout.decode("utf-8").strip()


def get_push_time(delay: int) -> datetime:
    # If a delay is not specified, push anywhere from
    # 2 - 5 hours after 5PM local.
    if not delay:
        end_of_day = datetime.now().replace(hour=17)
        return datetime.now() + timedelta(
            hours=random.randint(2, 5), minutes=random.randint(0, 60),
        )
        # return datetime.now() + timedelta(
        #     minutes=random.randint(0, 1),
        # )
    # Otherwise, return the current time + <delay> hours
    return datetime.now() + timedelta(hours=delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Let's get some work done."
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=int,
        help="number of hours to delay a push",
    )
    parser.add_argument(
        "-p",
        "--process",
        action="store_true",
        help="run the hardwork process",
    )

    args = parser.parse_args()
    current_path = os.getcwd()

    # Add this to the queue.
    if not args.process:
        push_time = get_push_time(args.delay)
        repo_root = get_current_repo(current_path)
        if not repo_root:
            raise Exception("Not a valid git repo.")

        add_to_queue(repo_root, push_time)
        time_till_push = (
            push_time - datetime.now()
        ).total_seconds() / 3600
        print(
            f"{'...' + repo_root[-20:]} set to push in {time_till_push:.0f} hours! Nice work."
        )
    # Otherwise, start the process.
    else:
        start_process()
