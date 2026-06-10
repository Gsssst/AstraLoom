#!/usr/bin/env python3
"""Diagnose AstraLoom PDF proxy responses from a deployed server.

Usage:
    python3 scripts/diagnose_pdf_proxy.py \
      http://YOUR_SERVER/api/papers/pdf-proxy/2605.25979v1
"""

from __future__ import annotations

import argparse
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable


PDF_SIGNATURE = b"%PDF-"


@dataclass
class ProbeResult:
    name: str
    ok: bool
    status: int | None = None
    elapsed: float | None = None
    first_byte_elapsed: float | None = None
    bytes_read: int = 0
    signature: bytes = b""
    headers: dict[str, str] | None = None
    error: str | None = None


def now() -> float:
    return time.perf_counter()


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def print_headers(headers: dict[str, str] | None) -> None:
    if not headers:
        return
    interesting = [
        "content-type",
        "content-length",
        "content-range",
        "accept-ranges",
        "content-disposition",
        "cache-control",
        "x-pdf-cache",
        "server",
        "date",
    ]
    lowered = {k.lower(): v for k, v in headers.items()}
    for key in interesting:
        if key in lowered:
            print(f"{key}: {lowered[key]}")


def probe_dns_and_tcp(url: str, timeout: float) -> list[ProbeResult]:
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname
    if not host:
        return [ProbeResult("url_parse", False, error="URL 缺少 hostname")]

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    results: list[ProbeResult] = []

    start = now()
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        elapsed = now() - start
        unique_addresses = sorted({item[4][0] for item in addresses})
        results.append(
            ProbeResult(
                "dns",
                True,
                elapsed=elapsed,
                error=", ".join(unique_addresses),
            )
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        results.append(ProbeResult("dns", False, elapsed=now() - start, error=repr(exc)))
        return results

    start = now()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            if parsed.scheme == "https":
                context = ssl.create_default_context()
                with context.wrap_socket(sock, server_hostname=host):
                    pass
        results.append(ProbeResult("tcp_connect", True, elapsed=now() - start))
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        results.append(ProbeResult("tcp_connect", False, elapsed=now() - start, error=repr(exc)))

    return results


def request_probe(
    name: str,
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    timeout: float,
    max_bytes: int = 0,
) -> ProbeResult:
    request_headers = {
        "User-Agent": "AstraLoom-PDF-Diagnostic/1.0",
        "Accept": "application/pdf,*/*",
        **(headers or {}),
    }
    request = urllib.request.Request(url, headers=request_headers, method=method)
    start = now()
    first_byte_elapsed: float | None = None
    data = bytearray()

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_headers = dict(response.headers.items())
            status = response.status
            if method == "HEAD":
                return ProbeResult(
                    name,
                    200 <= status < 400,
                    status=status,
                    elapsed=now() - start,
                    headers=response_headers,
                )

            remaining = max_bytes
            while remaining > 0:
                chunk = response.read(min(65536, remaining))
                if not chunk:
                    break
                if first_byte_elapsed is None:
                    first_byte_elapsed = now() - start
                data.extend(chunk)
                remaining -= len(chunk)

            return ProbeResult(
                name,
                200 <= status < 400,
                status=status,
                elapsed=now() - start,
                first_byte_elapsed=first_byte_elapsed,
                bytes_read=len(data),
                signature=bytes(data[:8]),
                headers=response_headers,
            )
    except urllib.error.HTTPError as exc:
        body = b""
        try:
            body = exc.read(512)
        except Exception:
            pass
        return ProbeResult(
            name,
            False,
            status=exc.code,
            elapsed=now() - start,
            bytes_read=len(body),
            signature=body[:8],
            headers=dict(exc.headers.items()) if exc.headers else None,
            error=body.decode("utf-8", "replace")[:300] or repr(exc),
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return ProbeResult(name, False, elapsed=now() - start, error=repr(exc))


def add_cache_buster(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("diag_ts", str(int(time.time()))))
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))


def print_result(result: ProbeResult) -> None:
    status = f"status={result.status}" if result.status is not None else "status=-"
    elapsed = f"{result.elapsed:.3f}s" if result.elapsed is not None else "-"
    first = f"{result.first_byte_elapsed:.3f}s" if result.first_byte_elapsed is not None else "-"
    sig = result.signature.decode("latin1", "replace") if result.signature else "-"
    print(f"{result.name}: {'OK' if result.ok else 'FAIL'} {status} elapsed={elapsed} first_byte={first} bytes={result.bytes_read} sig={sig!r}")
    print_headers(result.headers)
    if result.error:
      print(f"detail: {result.error}")


def summarize(results: Iterable[ProbeResult]) -> None:
    by_name = {result.name: result for result in results}
    print_section("Summary")

    tcp = by_name.get("tcp_connect")
    head = by_name.get("head")
    ranged = by_name.get("range_get_0_1023")
    sample = by_name.get("sample_get")

    if tcp and not tcp.ok:
        print("结论：服务器端口无法连接。优先检查 nginx 是否运行、防火墙/安全组是否放行 80/443。")
        return

    if head and head.status and head.status >= 500:
        print("结论：PDF 代理返回 5xx。优先看 backend 日志，通常是 arXiv 下载或缓存读取失败。")
        return

    if sample and sample.ok and not sample.signature.startswith(PDF_SIGNATURE):
        print("结论：GET 返回的不是 PDF 内容。检查是否被登录页、错误页、nginx fallback 或 HTML 响应替代。")
        return

    if sample and sample.error and "timed out" in sample.error.lower():
        print("结论：普通 GET 超时。优先检查后端是否正在从 arXiv 下载、服务器访问 arXiv 是否慢、PDF 缓存目录是否可写。")
        return

    if ranged and ranged.ok and ranged.status == 200:
        print("结论：Range 请求被当成完整 GET 返回。前端已禁用 Range，这通常可接受，但大 PDF 会更慢。")
    elif ranged and ranged.ok and ranged.status == 206:
        print("结论：Range 请求正常返回 206。nginx/backend 基本支持 PDF 分片读取。")
    elif ranged and not ranged.ok:
        print("结论：Range 请求失败。若前端未禁用 Range，会导致 pdf.js 卡住；请继续使用当前禁用 Range 的前端。")

    if sample and sample.ok and sample.signature.startswith(PDF_SIGNATURE):
        print("结论：PDF 代理能返回有效 PDF。若网页仍加载失败，问题更可能在前端 pdf.js worker/缓存/浏览器解析链路。")
    else:
        print("结论：还不能确认 PDF 有效返回。请把完整输出发回来继续判断。")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose AstraLoom PDF proxy behavior.")
    parser.add_argument("url", help="PDF proxy URL, for example http://IP/api/papers/pdf-proxy/2605.25979v1")
    parser.add_argument("--timeout", type=float, default=45.0, help="Per-request timeout seconds.")
    parser.add_argument("--sample-mb", type=float, default=20.0, help="Maximum bytes to read for normal GET, in MB.")
    parser.add_argument("--cache-bust", action="store_true", help="Append a timestamp query string.")
    args = parser.parse_args()

    url = add_cache_buster(args.url) if args.cache_bust else args.url
    max_bytes = max(1024, int(args.sample_mb * 1024 * 1024))

    print("AstraLoom PDF proxy diagnostic")
    print(f"url: {url}")
    print(f"timeout: {args.timeout}s")
    print(f"sample limit: {args.sample_mb} MB")

    results: list[ProbeResult] = []

    print_section("Network")
    for result in probe_dns_and_tcp(url, args.timeout):
        results.append(result)
        print_result(result)

    print_section("HTTP")
    probes = [
        request_probe("head", url, method="HEAD", timeout=args.timeout),
        request_probe(
            "range_get_0_1023",
            url,
            headers={"Range": "bytes=0-1023"},
            timeout=args.timeout,
            max_bytes=1024,
        ),
        request_probe("sample_get", url, timeout=args.timeout, max_bytes=max_bytes),
    ]
    for result in probes:
        results.append(result)
        print_result(result)

    summarize(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
