"""kraken init | list | run | queue | license | tentacle | doctor | serve-site"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from kraken.core.doctor import inspect
from kraken.core.license import (
    LicenseError,
    load_store,
    set_key,
    upgrade,
    verify_remote,
)
from kraken.core.paths import ensure_user_layout, first_run_init
from kraken.core.queue import Job, WorkflowQueue
from kraken.core.resolve import ResolveError, resolve
from kraken.core.runner import in_process_registry, list_all, run_named
from kraken.core.tentacle import discover_installed, install_any
from kraken.core.workflow import WorkflowError, load_workflow, run_workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kraken", description="Kraken core")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="cmd", required=True)

    init_p = sub.add_parser("init", help="create ~/.kraken layout (or --home)")
    init_p.add_argument("--home", type=Path, default=None)

    sub.add_parser("list", help="list in-process arms and configured binaries")
    sub.add_parser("doctor", help="check layout, protocol, and dependency plans")
    mon = sub.add_parser("monitor", help="write a health snapshot (monitor arm)")
    mon.add_argument("--url", default="")

    run_p = sub.add_parser("run", help="run one arm or tentacle action")
    run_p.add_argument("arm")
    run_p.add_argument("action")
    run_p.add_argument("--payload", default="{}")
    run_p.add_argument("--compose", action="store_true")

    q_p = sub.add_parser("queue", help="enqueue then drain one in-process job")
    q_p.add_argument("arm")
    q_p.add_argument("action")
    q_p.add_argument("--payload", default="{}")
    q_p.add_argument("--trigger", default="manual")

    lic = sub.add_parser("license", help="premium tentacle keys (api.topta.co)")
    lic_sub = lic.add_subparsers(dest="lic_cmd", required=True)
    lic_sub.add_parser("status")
    set_p = lic_sub.add_parser("set")
    set_p.add_argument("tentacle")
    set_p.add_argument("key")
    ver_p = lic_sub.add_parser("verify")
    ver_p.add_argument("tentacle")
    up_p = lic_sub.add_parser("upgrade")
    up_p.add_argument("tentacle")
    up_p.add_argument("--plan", default="beta")
    up_p.add_argument("--email", default="")

    ten = sub.add_parser("tentacle", help="install or list external tentacles")
    ten_sub = ten.add_subparsers(dest="ten_cmd", required=True)
    add_p = ten_sub.add_parser("add")
    add_p.add_argument("path", help="local dir, github.com/org/repo, or git URL")
    ten_sub.add_parser("list")
    plan_p = ten_sub.add_parser("plan")
    plan_p.add_argument("name")

    wf = sub.add_parser("workflow", help="run a sequential/parallel tentacle workflow")
    wf_sub = wf.add_subparsers(dest="wf_cmd", required=True)
    wf_run = wf_sub.add_parser("run")
    wf_run.add_argument("file", type=Path)

    site_p = sub.add_parser("serve-site", help="print how to serve the marketing site")
    site_p.add_argument("--port", default="8080")

    acc = sub.add_parser("account", help="local session + optional api.topta.co sync")
    acc_sub = acc.add_subparsers(dest="acc_cmd", required=True)
    login_p = acc_sub.add_parser("login")
    login_p.add_argument("email")
    login_p.add_argument("--device", default="cli")
    acc_sub.add_parser("logout")
    acc_sub.add_parser("status")
    pin_p = acc_sub.add_parser("pin")
    pin_p.add_argument("key")
    pin_p.add_argument("value")
    acc_sub.add_parser("sync")
    push_p = acc_sub.add_parser("push")
    push_p.add_argument("--on", action="store_true")
    push_p.add_argument("--token", default="")
    acc_sub.add_parser("group")
    join_p = acc_sub.add_parser("join")
    join_p.add_argument("group_key")
    join_p.add_argument("--device", default="cli")
    vanilla = sub.add_parser("vanilla", help="install bundled free tentacles")
    vanilla.add_argument("--home", type=Path, default=None)

    demo_p = sub.add_parser("demo", help="run geo lookup so first JSON lands in 60s")
    demo_p.add_argument("--ip", default="1.1.1.1")

    grant_p = sub.add_parser("grant", help="allow a default-deny capability")
    grant_p.add_argument("name")
    grant_p.add_argument("--revoke", action="store_true")

    self_p = sub.add_parser(
        "self", help="inspect this machine without running tentacles"
    )
    self_sub = self_p.add_subparsers(dest="self_cmd", required=True)
    self_sub.add_parser("plan")

    args = parser.parse_args(argv)
    root = args.root.resolve()
    first_run_init(getattr(args, "home", None))

    if args.cmd == "init":
        print(str(ensure_user_layout(args.home)))
        return 0

    if args.cmd == "list":
        for row in list_all(root):
            actions = ",".join(row.get("actions") or [])
            print(
                f"{row['name']}\t{row.get('version', '')}\t{actions}\t"
                f"{row.get('kind')}\t{row.get('license', 'free')}"
            )
        return 0

    if args.cmd == "doctor":
        report = inspect(root)
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 2

    if args.cmd == "monitor":
        payload = {"root": str(root)}
        snap = run_named(root, "monitor", "snapshot", payload)
        if args.url:
            snap["ping"] = run_named(root, "monitor", "ping", {"url": args.url})
        print(json.dumps(snap, default=str))
        return 0 if snap.get("ok") else 2

    if args.cmd == "workflow":
        try:
            spec = load_workflow(args.file)
            print(json.dumps(run_workflow(root, spec), default=str))
            return 0
        except (WorkflowError, ResolveError, LicenseError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
            return 2

    if args.cmd == "serve-site":
        print(f"python3 -m http.server {args.port} --directory {root / 'website'}")
        return 0

    if args.cmd == "account":
        from kraken.core.sync import (
            load_session,
            login,
            logout,
            pin,
            remote_register,
            set_push,
        )

        if args.acc_cmd == "login":
            print(json.dumps(login(args.email, args.device)))
            return 0
        if args.acc_cmd == "logout":
            print(json.dumps(logout()))
            return 0
        if args.acc_cmd == "status":
            print(json.dumps(load_session(), indent=2))
            return 0
        if args.acc_cmd == "pin":
            print(json.dumps(pin(args.key, args.value)))
            return 0
        if args.acc_cmd == "sync":
            print(json.dumps(remote_register(load_session())))
            return 0
        if args.acc_cmd == "push":
            print(json.dumps(set_push(args.on, args.token)))
            return 0
        if args.acc_cmd == "group":
            from kraken.core.sync import new_group

            print(json.dumps(new_group()))
            return 0
        if args.acc_cmd == "join":
            from kraken.core.sync import join_group

            print(json.dumps(join_group(args.group_key, args.device)))
            return 0

    if args.cmd == "vanilla":
        from kraken.core.vanilla import install_vanilla

        print(json.dumps(install_vanilla(root, args.home)))
        return 0

    if args.cmd == "demo":
        try:
            print(
                json.dumps(
                    run_named(root, "geo", "lookup", {"ip": args.ip}),
                    default=str,
                )
            )
            return 0
        except (ResolveError, LicenseError, KeyError) as exc:
            print(
                json.dumps({"ok": False, "error": str(exc), "hint": "kraken vanilla"})
            )
            return 2

    if args.cmd == "grant":
        from kraken.core.grant import grant

        result = grant(args.name, yes=not args.revoke)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2

    if args.cmd == "self":
        report = inspect(root)
        print(json.dumps({"ok": report["ok"], "plan": report}, indent=2))
        return 0 if report["ok"] else 2

    if args.cmd == "tentacle":
        if args.ten_cmd == "list":
            print(json.dumps(discover_installed(), indent=2))
            return 0
        if args.ten_cmd == "add":
            installed = install_any(str(args.path))
            payload = {
                "ok": True,
                "name": installed.get("name"),
                "root": installed.get("_root"),
            }
            try:
                payload["plan"] = resolve(root, str(installed.get("name"))).as_dict()
            except ResolveError as exc:
                payload["ok"] = False
                payload["error"] = str(exc)
                print(json.dumps(payload))
                return 2
            print(json.dumps(payload))
            return 0
        if args.ten_cmd == "plan":
            try:
                print(json.dumps(resolve(root, args.name).as_dict(), indent=2))
                return 0
            except ResolveError as exc:
                print(json.dumps({"ok": False, "error": str(exc)}))
                return 2

    if args.cmd == "license":
        store = load_store()
        if args.lic_cmd == "status":
            print(json.dumps(store, indent=2))
            return 0
        if args.lic_cmd == "set":
            set_key(args.tentacle, args.key)
            print(json.dumps({"ok": True, "tentacle": args.tentacle, "stored": True}))
            return 0
        if args.lic_cmd == "upgrade":
            try:
                print(
                    json.dumps(upgrade(args.tentacle, plan=args.plan, email=args.email))
                )
                return 0
            except LicenseError as exc:
                print(json.dumps({"ok": False, "error": str(exc)}))
                return 2
        if args.lic_cmd == "verify":
            entry = store.get("keys", {}).get(args.tentacle) or {}
            if not entry.get("key"):
                print(json.dumps({"ok": False, "error": "no local key"}))
                return 2
            try:
                result = verify_remote(
                    args.tentacle, entry["key"], store.get("api_base")
                )
            except LicenseError as exc:
                print(json.dumps({"ok": False, "error": str(exc)}))
                return 2
            print(json.dumps(result))
            return 0

    payload = json.loads(args.payload)
    try:
        if args.cmd == "run":
            print(
                json.dumps(
                    run_named(
                        root, args.arm, args.action, payload, compose=args.compose
                    )
                )
            )
            return 0
        registry = in_process_registry(root)
        queue = WorkflowQueue()
        queue.enqueue(
            Job(arm=args.arm, action=args.action, payload=payload, trigger=args.trigger)
        )
        print(
            json.dumps(
                queue.drain(lambda job: registry.run(job.arm, job.action, job.payload))
            )
        )
        return 0
    except LicenseError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
    except ResolveError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
    except KeyError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
