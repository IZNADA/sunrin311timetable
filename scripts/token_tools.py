#!/usr/bin/env python
import argparse
import json
import os
import sys
from typing import Any, Dict

import requests
from dotenv import load_dotenv

GRAPH = "https://graph.facebook.com/v21.0"


def jprint(obj: Dict[str, Any]):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def require_env(keys):
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        print(f"Missing env: {missing}", file=sys.stderr)
        sys.exit(2)


def do_debug(args):
    load_dotenv()
    token = args.token or os.getenv("IG_USER_ACCESS_TOKEN") or os.getenv("IG_PAGE_ACCESS_TOKEN")
    require_env(["FB_APP_ID", "FB_APP_SECRET"])
    app_access = f"{os.getenv('FB_APP_ID')}|{os.getenv('FB_APP_SECRET')}"
    r = requests.get(
        f"{GRAPH}/debug_token",
        params={"input_token": token, "access_token": app_access},
        timeout=30,
    )
    try:
        r.raise_for_status()
        jprint(r.json())
    except Exception:
        print(r.text)
        raise


def do_exchange(args):
    load_dotenv()
    require_env(["FB_APP_ID", "FB_APP_SECRET"])
    short_tok = args.short or os.getenv("IG_USER_ACCESS_TOKEN")
    r = requests.get(
        f"{GRAPH}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": os.getenv("FB_APP_ID"),
            "client_secret": os.getenv("FB_APP_SECRET"),
            "fb_exchange_token": short_tok,
        },
        timeout=30,
    )
    r.raise_for_status()
    jprint(r.json())


def do_list_pages(args):
    load_dotenv()
    token = args.token or os.getenv("IG_USER_ACCESS_TOKEN")
    r = requests.get(
        f"{GRAPH}/me/accounts",
        params={"fields": "id,name", "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    jprint(r.json())


def do_page_token(args):
    load_dotenv()
    token = args.token or os.getenv("IG_USER_ACCESS_TOKEN")
    page_id = args.page or os.getenv("PAGE_ID")
    r = requests.get(
        f"{GRAPH}/{page_id}",
        params={"fields": "access_token", "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    jprint(r.json())


def do_ig_user(args):
    load_dotenv()
    page_id = args.page or os.getenv("PAGE_ID")
    token = args.token or os.getenv("IG_USER_ACCESS_TOKEN") or os.getenv("IG_PAGE_ACCESS_TOKEN")
    r = requests.get(
        f"{GRAPH}/{page_id}",
        params={"fields": "instagram_business_account{id,username}", "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    jprint(r.json())


def main():
    p = argparse.ArgumentParser(description="Facebook/Instagram Graph token helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("debug", help="debug a token with app creds (env FB_APP_ID/SECRET)")
    s.add_argument("--token", help="user/page token; default from env")
    s.set_defaults(fn=do_debug)

    s = sub.add_parser("exchange", help="exchange short-lived user token to long-lived")
    s.add_argument("--short", help="short-lived user token; default IG_USER_ACCESS_TOKEN env")
    s.set_defaults(fn=do_exchange)

    s = sub.add_parser("list-pages", help="list pages for a user token")
    s.add_argument("--token", help="user token; default IG_USER_ACCESS_TOKEN env")
    s.set_defaults(fn=do_list_pages)

    s = sub.add_parser("page-token", help="derive page token from user token + PAGE_ID")
    s.add_argument("--token", help="user token; default IG_USER_ACCESS_TOKEN env")
    s.add_argument("--page", help="page id; default PAGE_ID env")
    s.set_defaults(fn=do_page_token)

    s = sub.add_parser("ig-user", help="get instagram_business_account from page id")
    s.add_argument("--token", help="user OR page token; default IG_USER_ACCESS_TOKEN or IG_PAGE_ACCESS_TOKEN env")
    s.add_argument("--page", help="page id; default PAGE_ID env")
    s.set_defaults(fn=do_ig_user)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

