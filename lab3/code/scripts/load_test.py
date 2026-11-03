"""真实 HTTP 混合负载；20 个独立 cookie 会话，原始计数与时延均落盘。"""

import argparse
import concurrent.futures
import http.cookiejar
import json
import math
import platform
import random
import ssl
import statistics
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path


class Client:
    def __init__(self, base, insecure=False):
        self.base = base.rstrip("/")
        context = ssl._create_unverified_context() if insecure else ssl.create_default_context()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
            urllib.request.HTTPSHandler(context=context),
        )
        self.csrf = ""

    def call(self, path, data=None):
        headers = {"X-CSRFToken": self.csrf, "Referer": self.base + "/"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(self.base + path, data=body, headers=headers)
        try:
            with self.opener.open(request, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    def login(self, index):
        if not self.csrf:
            self.csrf = self.call("/api/session")[1]["csrf_token"]
        status, payload = self.call(
            "/api/login",
            {
                "email": f"demo-buyer{index + 1}@nju.edu.cn",
                "password": "Campus-demo-2026",
            },
        )
        if status == 200:
            self.csrf = payload["csrf_token"]
        return status, payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="https://127.0.0.1:5003")
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--duration", type=int, default=300)
    parser.add_argument("--insecure-local-tls", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    clients = [Client(args.base, args.insecure_local_tls) for _ in range(args.users)]
    for index, client in enumerate(clients):
        assert client.login(index)[0] == 200, "负载账号初始化失败"
    products = clients[0].call("/api/products")[1]["items"]
    assert len(products) >= 500, "至少需要 500 条有效商品"
    started = time.time()
    deadline = time.perf_counter() + args.duration

    def worker(index):
        rng = random.Random(index)
        client = clients[index]
        samples, counts, errors = [], Counter(), []
        schedule = ["login"] + ["list"] * 4 + ["detail"] * 3 + ["reserve"] * 2
        iteration = index
        while time.perf_counter() < deadline:
            kind = schedule[iteration % 10]
            iteration += 1
            product = products[rng.randrange(len(products))]
            begin = time.perf_counter()
            try:
                if kind == "login":
                    status, _ = client.login(index)
                elif kind == "list":
                    status, _ = client.call("/api/products?sort=price_asc")
                elif kind == "detail":
                    status, _ = client.call(f"/api/products/{product['id']}")
                else:
                    status, _ = client.call(
                        "/api/actions/reserve",
                        {
                            "id": product["id"],
                            "revision": product["revision"],
                        },
                    )
                expected = status == 200 or (kind == "reserve" and status == 409)
                counts[f"{kind}:{status}"] += 1
                if not expected:
                    errors.append({"kind": kind, "status": status})
            except Exception as exc:
                counts[f"{kind}:exception"] += 1
                errors.append({"kind": kind, "error": type(exc).__name__})
            samples.append(time.perf_counter() - begin)
        return samples, counts, errors

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.users) as pool:
        results = list(pool.map(worker, range(args.users)))
    latencies = sorted(sample for result in results for sample in result[0])
    counts = sum((result[1] for result in results), Counter())
    errors = [error for result in results for error in result[2]]
    p95 = latencies[max(0, math.ceil(len(latencies) * 0.95) - 1)]
    ratio = len(errors) / len(latencies)
    summary = {
        "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "base_url": args.base,
        "tls_certificate_verified": not args.insecure_local_tls,
        "duration_requested_seconds": args.duration,
        "wall_seconds": round(time.time() - started, 3),
        "concurrent_users": args.users,
        "initial_products": len(products),
        "sample_count": len(latencies),
        "counts": dict(counts),
        "mean_seconds": round(statistics.mean(latencies), 6),
        "p95_seconds": round(p95, 6),
        "max_seconds": round(max(latencies), 6),
        "unexpected_failures": len(errors),
        "unexpected_failure_rate": ratio,
        "error_examples": errors[:20],
        "passed": args.duration >= 300 and args.users >= 20 and p95 <= 3 and ratio <= 0.01,
        "notes": "仅统计四类目标 HTTP 请求，预热不计时；抢约 409 为预期业务拒绝。"
        "使用 500 条初始商品的版本快照，后续已锁定商品的旧版本拒绝单列；"
        "没有把这项负载当作浏览器端到端渲染耗时。",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
