import argparse
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import urllib.request
import urllib.error

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


ENDPOINTS_TO_TEST = [
    {"name": "Liveness Probe", "path": "/health/live", "method": "GET"},
    {"name": "Readiness Probe", "path": "/health/ready", "method": "GET"},
    {"name": "Qualifications Catalogue", "path": "/api/v1/catalogue/qualifications", "method": "GET"},
    {"name": "Verified Opportunities", "path": "/api/v1/opportunities?district=Moradabad", "method": "GET"},
    {"name": "Metrics Prometheus", "path": "/metrics", "method": "GET"},
    {"name": "Metrics Summary", "path": "/metrics/summary", "method": "GET"},
]


def calculate_percentiles(latencies: List[float]) -> Dict[str, float]:
    if not latencies:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "min": 0.0, "max": 0.0, "mean": 0.0}
    sorted_l = sorted(latencies)
    n = len(sorted_l)

    def p(pct: float) -> float:
        idx = max(0, min(n - 1, int(math.ceil(pct / 100.0 * n)) - 1))
        return round(sorted_l[idx], 2)

    return {
        "min": round(sorted_l[0], 2),
        "max": round(sorted_l[-1], 2),
        "mean": round(sum(sorted_l) / n, 2),
        "p50": p(50),
        "p90": p(90),
        "p95": p(95),
        "p99": p(99),
    }


def make_request(base_url: str, endpoint: Dict[str, str], timeout_sec: float = 5.0) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}{endpoint['path']}"
    start_time = time.time()
    status_code = 0
    success = False
    error_msg = None

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "JeevanMitra-LoadTest/1.0", "Accept": "*/*"},
        method=endpoint["method"]
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            status_code = response.getcode()
            response.read()
            success = (200 <= status_code < 400)
    except urllib.error.HTTPError as e:
        status_code = e.code
        success = (status_code in (200, 304))
        error_msg = f"HTTP {status_code}"
    except Exception as e:
        error_msg = str(e)
        status_code = 0

    duration_ms = (time.time() - start_time) * 1000
    return {
        "endpoint": endpoint["name"],
        "path": endpoint["path"],
        "status_code": status_code,
        "duration_ms": duration_ms,
        "success": success,
        "error": error_msg,
    }


def run_in_process_benchmark(
    concurrency: int = 10,
    total_requests: int = 60
) -> Dict[str, Any]:
    """Runs load test using FastAPI TestClient in memory without needing a separate daemon."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    latencies: List[float] = []
    endpoint_results: Dict[str, List[float]] = {ep["name"]: [] for ep in ENDPOINTS_TO_TEST}
    failures = 0

    start_total = time.time()

    def do_client_req(ep_index: int):
        ep = ENDPOINTS_TO_TEST[ep_index % len(ENDPOINTS_TO_TEST)]
        t0 = time.time()
        try:
            res = client.get(ep["path"])
            dur = (time.time() - t0) * 1000
            ok = (200 <= res.status_code < 400)
            return ep["name"], dur, ok
        except Exception:
            dur = (time.time() - t0) * 1000
            return ep["name"], dur, False

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(do_client_req, i) for i in range(total_requests)]
        for f in as_completed(futures):
            ep_name, dur, ok = f.result()
            latencies.append(dur)
            endpoint_results[ep_name].append(dur)
            if not ok:
                failures += 1

    total_duration_sec = time.time() - start_total
    rps = round(total_requests / total_duration_sec, 2) if total_duration_sec > 0 else 0
    overall_percentiles = calculate_percentiles(latencies)

    sla_passed = (overall_percentiles["p95"] <= 500.0) and (failures / max(1, total_requests) <= 0.01)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "in_process_test_client",
        "total_requests": total_requests,
        "concurrency": concurrency,
        "failures": failures,
        "error_rate_pct": round((failures / total_requests) * 100, 2),
        "total_duration_sec": round(total_duration_sec, 2),
        "throughput_rps": rps,
        "overall_latency_ms": overall_percentiles,
        "endpoint_latencies_ms": {
            k: calculate_percentiles(v) for k, v in endpoint_results.items()
        },
        "sla_p95_under_500ms": sla_passed,
    }


def run_http_benchmark(
    base_url: str,
    concurrency: int = 20,
    total_requests: int = 100
) -> Dict[str, Any]:
    """Runs concurrent load test over HTTP socket against target server."""
    start_total = time.time()
    latencies: List[float] = []
    endpoint_results: Dict[str, List[float]] = {ep["name"]: [] for ep in ENDPOINTS_TO_TEST}
    failures = 0

    def task(req_idx: int):
        ep = ENDPOINTS_TO_TEST[req_idx % len(ENDPOINTS_TO_TEST)]
        return make_request(base_url, ep)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(task, i) for i in range(total_requests)]
        for f in as_completed(futures):
            res = f.result()
            latencies.append(res["duration_ms"])
            endpoint_results[res["endpoint"]].append(res["duration_ms"])
            if not res["success"]:
                failures += 1

    total_duration_sec = time.time() - start_total
    rps = round(total_requests / total_duration_sec, 2) if total_duration_sec > 0 else 0
    overall_percentiles = calculate_percentiles(latencies)

    sla_passed = (overall_percentiles["p95"] <= 500.0) and (failures / max(1, total_requests) <= 0.01)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "http_socket",
        "target_url": base_url,
        "total_requests": total_requests,
        "concurrency": concurrency,
        "failures": failures,
        "error_rate_pct": round((failures / total_requests) * 100, 2),
        "total_duration_sec": round(total_duration_sec, 2),
        "throughput_rps": rps,
        "overall_latency_ms": overall_percentiles,
        "endpoint_latencies_ms": {
            k: calculate_percentiles(v) for k, v in endpoint_results.items()
        },
        "sla_p95_under_500ms": sla_passed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JeevanMitra 2.0 Load & Latency Benchmark Harness")
    parser.add_argument("--url", default=None, help="Target HTTP URL (e.g. http://127.0.0.1:4000). If omitted, runs in-process benchmark.")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent client workers")
    parser.add_argument("--requests", type=int, default=50, help="Total number of requests to execute")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format only")
    args = parser.parse_args()

    if args.url:
        report = run_http_benchmark(args.url, concurrency=args.concurrency, total_requests=args.requests)
    else:
        report = run_in_process_benchmark(concurrency=args.concurrency, total_requests=args.requests)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n========================================================")
        print("     JEEVAN-MITRA 2.0 LOAD TEST RESULTS SUMMARY")
        print("========================================================")
        print(f"Timestamp:       {report['timestamp']}")
        print(f"Mode:            {report['mode']}")
        print(f"Total Requests:  {report['total_requests']}")
        print(f"Concurrency:     {report['concurrency']} workers")
        print(f"Failures:        {report['failures']} ({report['error_rate_pct']}%)")
        print(f"Throughput:      {report['throughput_rps']} req/sec")
        print("--------------------------------------------------------")
        print("Latency Percentiles (ms):")
        lat = report["overall_latency_ms"]
        print(f"  Min:  {lat['min']} ms | Mean: {lat['mean']} ms | Max: {lat['max']} ms")
        print(f"  p50:  {lat['p50']} ms | p90:  {lat['p90']} ms")
        print(f"  p95:  {lat['p95']} ms | p99:  {lat['p99']} ms")
        print("--------------------------------------------------------")
        print(f"SLA Status (p95 <= 500ms, err < 1%): {'PASSED' if report['sla_p95_under_500ms'] else 'FAILED'}")
        print("========================================================\n")
