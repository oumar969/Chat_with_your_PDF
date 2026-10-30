"""Configure this repository's Pages site using Git's existing credential helper.

Credentials stay in process memory and are never written or printed.
"""

import argparse
import json
import subprocess
import urllib.error
import urllib.request

REPO = "oumar969/Chat_with_your_PDF"
API = f"https://api.github.com/repos/{REPO}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--enable", action="store_true")
    args = parser.parse_args()
    result = subprocess.run(
        ["git", "credential", "fill"],
        input=f"protocol=https\nhost=github.com\npath={REPO}.git\n\n",
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise SystemExit("GitHub authentication unavailable; no credential details displayed.")
    credential = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    token = credential.get("password")
    if not token:
        raise SystemExit("No GitHub credential available.")

    def request(path, method="GET", body=None):
        req = urllib.request.Request(
            API + path,
            method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "PDFsamtale-Pages-setup",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
                return response.status, json.loads(data) if data else {}
        except urllib.error.HTTPError as exc:
            return exc.code, {}

    status, site = request("/pages")
    if args.enable:
        body = {"build_type": "legacy", "source": {"branch": "main", "path": "/docs"}}
        status, site = request("/pages", "POST" if status == 404 else "PUT", body)
        print("Pages configuration HTTP status:", status)
        if status not in (200, 201, 204):
            raise SystemExit(1)
        status, site = request("/pages")
        homepage_status, _ = request("", "PATCH", {"homepage": "https://oumar969.github.io/Chat_with_your_PDF/"})
        print("Repository homepage HTTP status:", homepage_status)
    print("Pages HTTP status:", status)
    if status == 200:
        print("URL:", site.get("html_url"))
        print("Site status:", site.get("status"))
        build_status, build = request("/pages/builds/latest")
        print("Latest build HTTP status:", build_status)
        if build_status == 200:
            print("Build status:", build.get("status"))
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
