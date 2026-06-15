import os
import json
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

GITHUB_API_URL = "https://api.github.com"


class GitHubAPIError(Exception):
    pass


class GitHubRateLimitError(Exception):
    pass


def load_github_token():
    load_dotenv()

    token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise ValueError(
            "GITHUB_TOKEN not found in .env file"
        )

    return token


def create_session(token):
    session = requests.Session()

    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    return session


def handle_response(response):
    if response.status_code == 401:
        raise GitHubAPIError(
            "Invalid GitHub token."
        )

    if response.status_code == 403:
        remaining = response.headers.get(
            "X-RateLimit-Remaining"
        )

        if remaining == "0":
            reset_time = response.headers.get(
                "X-RateLimit-Reset"
            )

            if reset_time:
                reset_datetime = datetime.fromtimestamp(
                    int(reset_time),
                    tz=timezone.utc,
                )

                raise GitHubRateLimitError(
                    f"Rate limit exceeded. "
                    f"Resets at {reset_datetime.isoformat()}"
                )

        raise GitHubAPIError(
            "Access forbidden."
        )

    response.raise_for_status()


def get_paginated_results(session, url):
    results = []

    while url:
        try:
            response = session.get(
                url,
                timeout=30
            )

            handle_response(response)

            results.extend(response.json())

            url = response.links.get(
                "next",
                {}
            ).get("url")

        except requests.exceptions.RequestException as exc:
            raise ConnectionError(
                f"Network error: {exc}"
            ) from exc

    return results


def get_organization_repositories(
    session,
    organization_name
):
    url = (
        f"{GITHUB_API_URL}/orgs/"
        f"{organization_name}/repos?per_page=100"
    )

    repos = get_paginated_results(
        session,
        url
    )

    if not repos:
        raise ValueError(
            f"No repositories found in "
            f"organization '{organization_name}'."
        )

    return repos


def get_repository_commits(
    session,
    owner,
    repo_name
):
    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{owner}/{repo_name}/commits"
        f"?per_page=100"
    )

    return get_paginated_results(
        session,
        url
    )


def get_commit_count(
    session,
    owner,
    repo_name
):
    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{owner}/{repo_name}/commits"
        f"?per_page=1"
    )

    try:
        response = session.get(
            url,
            timeout=30
        )

        handle_response(response)

        if response.status_code == 200:

            if "last" in response.links:
                last_url = response.links["last"][
                    "url"
                ]

                page = (
                    last_url.split("page=")[-1]
                )

                try:
                    return int(page)
                except ValueError:
                    pass

            commits = response.json()

            return len(commits)

        return 0

    except requests.exceptions.RequestException as exc:
        raise ConnectionError(
            f"Network error: {exc}"
        ) from exc


def get_top_contributors(
    session,
    owner,
    repo_name,
    top_n=3
):
    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{owner}/{repo_name}/contributors"
        f"?per_page=100"
    )

    contributors = get_paginated_results(
        session,
        url
    )

    top_contributors = []

    for contributor in contributors[:top_n]:
        top_contributors.append(
            {
                "login": contributor.get(
                    "login"
                ),
                "contributions": contributor.get(
                    "contributions"
                ),
            }
        )

    return top_contributors


def get_last_commit_info(
    session,
    owner,
    repo_name
):
    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{owner}/{repo_name}/commits"
        f"?per_page=1"
    )

    try:
        response = session.get(
            url,
            timeout=30
        )

        handle_response(response)

        commits = response.json()

        if not commits:
            return {
                "last_commit_date": None,
                "last_commit_author": None,
                "last_commit_author_active": False,
            }

        latest_commit = commits[0]

        commit_data = latest_commit.get(
            "commit",
            {}
        )

        author_data = commit_data.get(
            "author",
            {}
        )

        commit_date = author_data.get(
            "date"
        )

        github_author = latest_commit.get(
            "author"
        )

        author_login = (
            github_author.get("login")
            if github_author
            else author_data.get("name")
        )

        is_active = False

        if commit_date:
            commit_datetime = (
                datetime.fromisoformat(
                    commit_date.replace(
                        "Z",
                        "+00:00"
                    )
                )
            )

            threshold = (
                datetime.now(timezone.utc)
                - timedelta(days=90)
            )

            is_active = (
                commit_datetime >= threshold
            )

        return {
            "last_commit_date": commit_date,
            "last_commit_author": author_login,
            "last_commit_author_active": is_active,
        }

    except requests.exceptions.RequestException as exc:
        raise ConnectionError(
            f"Network error: {exc}"
        ) from exc


def analyze_repository(
    session,
    owner,
    repository
):
    repo_name = repository["name"]

    try:
        commit_info = get_last_commit_info(
            session,
            owner,
            repo_name
        )

        commit_count = get_commit_count(
            session,
            owner,
            repo_name
        )

        contributors = get_top_contributors(
            session,
            owner,
            repo_name
        )

        return {
            "repository_name": repo_name,
            "primary_language": repository.get(
                "language"
            ),
            "last_commit_date": commit_info[
                "last_commit_date"
            ],
            "total_commit_count": commit_count,
            "top_contributors": contributors,
            "most_recent_commit_author": commit_info[
                "last_commit_author"
            ],
            "last_commit_author_active": commit_info[
                "last_commit_author_active"
            ],
        }

    except Exception as exc:
        return {
            "repository_name": repo_name,
            "error": str(exc),
        }


def save_results_to_json(
    data,
    filename="repo_analysis.json"
):
    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )


def main():
    organization_name = input(
        "Enter GitHub organization name: "
    ).strip()

    try:
        token = load_github_token()

        session = create_session(token)

        repositories = (
            get_organization_repositories(
                session,
                organization_name
            )
        )

        results = []

        for repository in repositories:
            result = analyze_repository(
                session,
                organization_name,
                repository
            )

            results.append(result)

            time.sleep(0.1)

        save_results_to_json(results)

        print(
            f"Analysis completed. "
            f"Saved to repo_analysis.json"
        )

    except GitHubRateLimitError as exc:
        print(
            f"RATE LIMIT ERROR: {exc}"
        )

    except GitHubAPIError as exc:
        print(
            f"GITHUB API ERROR: {exc}"
        )

    except ConnectionError as exc:
        print(
            f"NETWORK ERROR: {exc}"
        )

    except Exception as exc:
        print(
            f"ERROR: {exc}"
        )


if __name__ == "__main__":
    main()