# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Network reachability probe for immutable Roadmap Bond evidence sources."""

import hashlib
import json
import re
from genlayer import *


USER_AGENT = "Mozilla/5.0 RoadmapBond/1.0"


def _get(url):
    response = gl.nondet.web.get(url, headers={"User-Agent": USER_AGENT})
    body = response.body
    if not isinstance(body, bytes):
        body = str(body).encode("utf-8")
    return int(response.status), body


def _fingerprint(label, status, body):
    return {
        "source": label,
        "status": status,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "reachable": status == 200,
    }


def _safe_fingerprint(label, url):
    try:
        status, body = _get(url)
        return _fingerprint(label, status, body)
    except Exception:
        return _fingerprint(label, 0, b"")


class AccessProbe(gl.Contract):
    last_result: str

    def __init__(self):
        self.last_result = "{}"

    @gl.public.write
    def probe(self, wayback_target: str, raw_url: str, npm_url: str, wikipedia_url: str) -> None:
        def collect():
            results = []
            cdx_url = (
                "https://web.archive.org/cdx/search/cdx?url="
                + wayback_target
                + "&output=json&filter=statuscode:200&collapse=timestamp:4&limit=1"
                + "&fl=timestamp"
            )
            try:
                cdx_status, cdx_body = _get(cdx_url)
            except Exception:
                cdx_status, cdx_body = 0, b""
            results.append(_fingerprint("wayback_cdx", cdx_status, cdx_body))
            capture_ts = ""
            try:
                rows = json.loads(cdx_body.decode("utf-8"))
                if isinstance(rows, list):
                    for row in rows[1:]:
                        if isinstance(row, list) and row and re.fullmatch(r"\d{14}", str(row[0])):
                            capture_ts = str(row[0])
                            break
            except Exception:
                pass
            if capture_ts:
                snapshot_url = "https://web.archive.org/web/" + capture_ts + "id_/" + wayback_target
                item = _safe_fingerprint("wayback_id_snapshot", snapshot_url)
                item["capture_ts"] = capture_ts
                results.append(item)
            else:
                results.append({"source": "wayback_id_snapshot", "status": 0, "bytes": 0, "sha256": hashlib.sha256(b"").hexdigest(), "reachable": False, "reason": "CDX returned no exact capture row."})
            for label, url in (("github_raw", raw_url), ("npm_exact_version", npm_url), ("wikipedia_oldid", wikipedia_url)):
                results.append(_safe_fingerprint(label, url))
            return {"results": results}

        def validate(proposed):
            if not isinstance(proposed, gl.vm.Return):
                return False
            candidate = proposed.calldata.get("results", [])
            own = collect()["results"]
            if len(candidate) != len(own):
                return False
            for left, right in zip(candidate, own):
                if left.get("source") != right.get("source") or left.get("status") != right.get("status"):
                    return False
                if left.get("reachable") != right.get("reachable"):
                    return False
                if left.get("bytes", 0) <= 100_000 and left.get("sha256") != right.get("sha256"):
                    return False
            return True

        result = gl.vm.run_nondet_unsafe(collect, validate)
        self.last_result = json.dumps(result, sort_keys=True)

    @gl.public.view
    def get_result(self) -> str:
        return self.last_result
