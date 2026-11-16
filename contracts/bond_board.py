# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Roadmap Bond escrow, frozen promise criteria, challenge, and deterministic settlement."""

import hashlib
import json
import re
from datetime import datetime, timezone
from genlayer import *


RPC_URL = "https://studio.genlayer.com/api"
USER_AGENT = "Mozilla/5.0 RoadmapBond/1.0"
MIN_WINDOW = 1800
MIN_LIVE_DEADLINE = 3600
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def require(ok, message):
    if not ok:
        raise gl.vm.UserError("[EXPECTED] " + message)


def now():
    return int(datetime.now(timezone.utc).timestamp())


def canon(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def lower(value):
    return str(value).lower()


def _text(body):
    if not isinstance(body, str):
        body = body.decode("utf-8", errors="replace")
    body = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", body)
    body = re.sub(r"(?is)<[^>]+>", " ", body)
    for source, target in (("&nbsp;", " "), ("&#160;", " "), ("&amp;", "&"), ("&quot;", '"'), ("&#39;", "'"), ("&rsquo;", "'"), ("&lsquo;", "'"), ("&#8217;", "'"), ("&#x27;", "'"), ("&lt;", "<"), ("&gt;", ">")):
        body = body.replace(source, target)
    return re.sub(r"\s+", " ", body).strip()


def _encode_target(target):
    return target.replace("%", "%25").replace("?", "%3F").replace("&", "%26")


def verify_snapshot(snapshot_url, quote):
    match = re.fullmatch(r"https://web\.archive\.org/web/(\d{14})id_/(https://[^\s#]+)", snapshot_url)
    if not match:
        return {"valid": False, "reason": "Snapshot must use an exact Wayback id_ URL.", "context": ""}
    timestamp, target = match.group(1), match.group(2)
    if re.fullmatch(r"https://(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?:/[^\s]*)?", target) is None:
        return {"valid": False, "reason": "Snapshot target must use a public HTTPS domain.", "context": ""}
    cdx_url = (
        "https://web.archive.org/cdx/search/cdx?url=" + _encode_target(target)
        + "&output=json&fl=timestamp,original,statuscode&filter=timestamp:" + timestamp + "&filter=statuscode:200"
    )
    try:
        cdx = gl.nondet.web.get(cdx_url, headers={"User-Agent": USER_AGENT})
        if int(cdx.status) != 200:
            return {"valid": False, "reason": "Wayback CDX did not return HTTP 200.", "context": ""}
        rows = json.loads(cdx.body.decode("utf-8"))
        exact = False
        if isinstance(rows, list):
            for row in rows[1:]:
                if isinstance(row, list) and len(row) >= 3 and str(row[0]) == timestamp and str(row[1]) == target and str(row[2]) == "200":
                    exact = True
                    break
        if not exact:
            return {"valid": False, "reason": "CDX has no successful capture at the exact snapshot timestamp.", "context": ""}
        page = gl.nondet.web.get(snapshot_url, headers={"User-Agent": USER_AGENT})
        if int(page.status) != 200:
            return {"valid": False, "reason": "Wayback id_ snapshot did not return HTTP 200.", "context": ""}
        body = _text(page.body)
        normalized_quote = re.sub(r"\s+", " ", quote).strip()
        if normalized_quote not in body:
            return {"valid": False, "reason": "Normalized quote was not found in the archived page.", "context": ""}
        start = body.find(normalized_quote)
        return {"valid": True, "reason": "Exact CDX capture and verbatim quote verified.", "context": body[max(0, start - 350):start + len(normalized_quote) + 350]}
    except Exception:
        return {"valid": False, "reason": "Wayback verification failed; the bond is refundable.", "context": ""}


def valid_evidence_url(url, deadline, allow_wayback=True, allow_github_raw=True, allow_npm=True, allow_wikipedia=True):
    if not isinstance(url, str) or len(url) > 1000:
        return False
    archive = re.fullmatch(r"https://web\.archive\.org/web/(\d{14})id_/(https://[^\s#]+)", url)
    if archive:
        deadline_text = datetime.fromtimestamp(int(deadline), timezone.utc).strftime("%Y%m%d%H%M%S")
        return allow_wayback and archive.group(1) >= deadline_text
    if re.fullmatch(r"https://raw\.githubusercontent\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/[0-9a-fA-F]{40}/[A-Za-z0-9_./%+@-]+", url):
        return allow_github_raw and ".." not in url
    if re.fullmatch(r"https://registry\.npmjs\.org/(?:%40[A-Za-z0-9_.-]+%2F)?[A-Za-z0-9_.-]+/\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", url):
        return allow_npm
    if re.fullmatch(r"https://en\.wikipedia\.org/w/index\.php\?title=[A-Za-z0-9%()_ .-]+&oldid=[1-9][0-9]*", url):
        return allow_wikipedia
    return False


@gl.evm.contract_interface
class Recipient:
    class View:
        pass

    class Write:
        pass


class BondBoard(gl.Contract):
    owner: Address
    promise_judge: Address
    next_promise: u256
    next_refund: u256
    promise_ids: DynArray[str]
    promises: TreeMap[str, str]
    refunds: TreeMap[str, str]
    transactions: TreeMap[str, str]
    challenge_window: u256
    defence_window: u256
    grace_period: u256
    allow_wayback: bool
    allow_github_raw: bool
    allow_npm: bool
    allow_wikipedia: bool

    def __init__(self, challenge_window_seconds: int = 1800, defence_window_seconds: int = 1800, grace_seconds: int = 1800, allow_wayback: bool = True, allow_github_raw: bool = True, allow_npm: bool = True, allow_wikipedia: bool = True):
        require(int(challenge_window_seconds) >= MIN_WINDOW, "challenge window must be at least 30 minutes")
        require(int(defence_window_seconds) >= MIN_WINDOW, "defence window must be at least 30 minutes")
        require(int(grace_seconds) >= MIN_WINDOW, "grace period must be at least 30 minutes")
        self.owner = gl.message.sender_address
        self.promise_judge = Address(ZERO_ADDRESS)
        self.next_promise = u256(0)
        self.next_refund = u256(0)
        self.challenge_window = u256(challenge_window_seconds)
        self.defence_window = u256(defence_window_seconds)
        self.grace_period = u256(grace_seconds)
        self.allow_wayback = bool(allow_wayback)
        self.allow_github_raw = bool(allow_github_raw)
        self.allow_npm = bool(allow_npm)
        self.allow_wikipedia = bool(allow_wikipedia)

    def _only_owner(self):
        require(lower(gl.message.sender_address) == lower(self.owner), "owner only")

    def _self_only(self):
        require(lower(gl.message.sender_address) == lower(gl.message.contract_address), "finality callback only")

    def _promise(self, promise_id):
        return json.loads(self.promises.get(promise_id, "{}"))

    def _put(self, record):
        self.promises[record["id"]] = json.dumps(record, sort_keys=True, ensure_ascii=False)

    def _tx_list(self, promise_id):
        return json.loads(self.transactions.get(promise_id, "[]"))

    def _payout(self, record, purpose, recipient, amount):
        amount = int(amount)
        if amount <= 0:
            return
        record.setdefault("payouts", []).append({
            "purpose": purpose,
            "recipient": lower(recipient),
            "amount_wei": str(amount),
            "state": "FINALIZED",
        })
        Recipient(Address(recipient)).emit_transfer(value=u256(amount), on="finalized")

    def _new_refund(self, sender, amount, reason):
        refund_id = "refund-" + str(int(self.next_refund) + 1)
        self.next_refund = u256(int(self.next_refund) + 1)
        self.refunds[refund_id] = json.dumps({"id": refund_id, "recipient": lower(sender), "amount_wei": str(int(amount)), "reason": reason, "status": "REFUND_PENDING"}, sort_keys=True)
        if int(amount) > 0:
            gl.get_contract_at(gl.message.contract_address).emit(on="finalized").pay_refund(refund_id)
        return refund_id

    @gl.public.write
    def set_promise_judge(self, judge_address: str) -> None:
        self._only_owner()
        require(lower(self.promise_judge) == ZERO_ADDRESS, "PromiseJudge already configured")
        require(re.fullmatch(r"0x[0-9a-fA-F]{40}", judge_address) is not None, "PromiseJudge address required")
        self.promise_judge = Address(judge_address)

    @gl.public.write.payable
    def post(self, snapshot_url: str, quote: str, deadline: int) -> str:
        promise_id, problem = self._start_post(snapshot_url, quote, deadline, False, lower(gl.message.sender_address))
        if problem:
            self._refund_post(promise_id, problem)
            return promise_id
        def verify():
            return verify_snapshot(snapshot_url, quote)

        try:
            verified = gl.eq_principle.strict_eq(verify)
        except Exception:
            verified = {"valid": False, "reason": "Validators could not agree on the archived snapshot; the bond is refundable.", "context": ""}
        if not verified.get("valid"):
            self._refund_post(promise_id, str(verified.get("reason", "Archived snapshot verification failed."))[:200])
            return promise_id
        gl.get_contract_at(self.promise_judge).emit(on="finalized").compile(promise_id, quote, verified.get("context", "")[:1800])
        return promise_id

    @gl.public.write.payable
    def post_replay(self, snapshot_url: str, quote: str, deadline: int, poster_address: str) -> str:
        sender = lower(gl.message.sender_address)
        if sender != lower(self.owner):
            return self._new_refund(sender, int(gl.message.value), "Historical replay is owner-only.")
        if re.fullmatch(r"0x[0-9a-fA-F]{40}", poster_address) is None:
            return self._new_refund(sender, int(gl.message.value), "Replay poster address is malformed.")
        promise_id, problem = self._start_post(snapshot_url, quote, deadline, True, lower(poster_address))
        if problem:
            self._refund_post(promise_id, problem)
            return promise_id
        def verify():
            return verify_snapshot(snapshot_url, quote)

        try:
            verified = gl.eq_principle.strict_eq(verify)
        except Exception:
            verified = {"valid": False, "reason": "Validators could not agree on the archived snapshot; the bond is refundable.", "context": ""}
        if not verified.get("valid"):
            self._refund_post(promise_id, str(verified.get("reason", "Archived snapshot verification failed."))[:200])
            return promise_id
        gl.get_contract_at(self.promise_judge).emit(on="finalized").compile(promise_id, quote, verified.get("context", "")[:1800])
        return promise_id

    def _start_post(self, snapshot_url, quote, deadline, replay, poster):
        value = int(gl.message.value)
        number = int(self.next_promise) + 1
        self.next_promise = u256(number)
        promise_id = "promise-" + str(number)
        created = now()
        record = {
            "id": promise_id,
            "poster": lower(poster),
            "snapshot_url": snapshot_url if isinstance(snapshot_url, str) else "",
            "quote": quote if isinstance(quote, str) else "",
            "deadline": int(deadline),
            "bond_wei": str(value),
            "challenge_stake_wei": "0",
            "challenge_window_seconds": str(int(self.challenge_window)),
            "defence_window_seconds": str(int(self.defence_window)),
            "grace_seconds": str(int(self.grace_period)),
            "created_at": created,
            "challenge_close_at": created + int(self.challenge_window) if replay else int(deadline) + int(self.challenge_window),
            "defence_end": 0,
            "replay": bool(replay),
            "status": "COMPILING",
            "criteria": [],
            "criteria_hash": "",
            "not_counted": "",
            "compile_reasons": [],
            "challenge": None,
            "defence_evidence": [],
            "verdicts": [],
            "next_criterion": 0,
            "settlement": "",
            "reason": "",
            "payouts": [],
        }
        self.promise_ids.append(promise_id)
        self.transactions[promise_id] = "[]"
        self._put(record)
        problem = ""
        if value <= 0:
            problem = "Bond must be greater than zero wei."
        elif not isinstance(quote, str) or not 20 <= len(quote) <= 300:
            problem = "Quote must contain 20 to 300 characters."
        elif replay and int(deadline) >= created:
            problem = "Historical replay must use a past deadline."
        elif not replay and int(deadline) < created + MIN_LIVE_DEADLINE:
            problem = "Production deadline must be at least 60 minutes in the future."
        elif lower(self.promise_judge) == ZERO_ADDRESS:
            problem = "PromiseJudge is not configured."
        return promise_id, problem

    def _refund_post(self, promise_id, reason):
        record = self._promise(promise_id)
        record["status"] = "REFUNDABLE_ERROR"
        record["reason"] = str(reason)[:200]
        self._put(record)
        if int(record.get("bond_wei", "0")) > 0:
            gl.get_contract_at(gl.message.contract_address).emit(on="finalized").refund_invalid_promise(promise_id)

    @gl.public.write
    def complete_compile(self, promise_id: str, result_json: str) -> None:
        require(lower(gl.message.sender_address) == lower(self.promise_judge), "PromiseJudge only")
        record = self._promise(promise_id)
        if not record or record.get("status") != "COMPILING":
            return
        result = json.loads(result_json)
        status = result.get("status")
        criteria = result.get("criteria", [])
        if status not in ("SPEC_ACCEPTED", "SPEC_REJECTED") or not isinstance(criteria, list) or not 1 <= len(criteria) <= 3:
            status = "SPEC_REJECTED"
            criteria = []
            result = {"criteria": [], "not_counted": "A name or stub is not proof of delivery.", "reasons": ["Compiler returned an invalid schema; bond is refundable."], "criteria_hash": ""}
        record["criteria"] = criteria
        record["criteria_hash"] = str(result.get("criteria_hash", ""))
        record["not_counted"] = str(result.get("not_counted", ""))[:240]
        record["compile_reasons"] = [str(reason)[:200] for reason in result.get("reasons", [])[:3]]
        record["status"] = "OPEN" if status == "SPEC_ACCEPTED" else "REJECTED"
        record["reason"] = "" if status == "SPEC_ACCEPTED" else "; ".join(record["compile_reasons"])
        self._put(record)

    @gl.public.write
    def refund_rejected(self, promise_id: str) -> None:
        record = self._promise(promise_id)
        require(record.get("status") == "REJECTED", "rejected promise required")
        require(lower(gl.message.sender_address) == record.get("poster"), "poster only")
        record["status"] = "REJECT_REFUND_PENDING"
        self._put(record)
        gl.get_contract_at(gl.message.contract_address).emit(on="finalized").refund_rejected_finalized(promise_id)

    @gl.public.write
    def refund_rejected_finalized(self, promise_id: str) -> None:
        self._self_only()
        record = self._promise(promise_id)
        if record.get("status") != "REJECT_REFUND_PENDING":
            return
        amount = int(record.get("bond_wei", "0"))
        record["bond_wei"] = "0"
        record["status"] = "REJECTED_REFUNDED"
        self._payout(record, "rejected_bond_refund", record["poster"], amount)
        self._put(record)

    @gl.public.write
    def refund_invalid_promise(self, promise_id: str) -> None:
        self._self_only()
        record = self._promise(promise_id)
        if record.get("status") != "REFUNDABLE_ERROR":
            return
        amount = int(record.get("bond_wei", "0"))
        record["bond_wei"] = "0"
        record["status"] = "REFUNDED_INVALID"
        self._payout(record, "invalid_post_refund", record["poster"], amount)
        self._put(record)

    @gl.public.write
    def pay_refund(self, refund_id: str) -> None:
        self._self_only()
        item = json.loads(self.refunds.get(refund_id, "{}"))
        if item.get("status") != "REFUND_PENDING":
            return
        amount = int(item.get("amount_wei", "0"))
        item["amount_wei"] = "0"
        item["status"] = "REFUNDED"
        item["paid_wei"] = str(amount)
        item["payout"] = {"recipient": item["recipient"], "amount_wei": str(amount), "state": "FINALIZED"}
        self.refunds[refund_id] = json.dumps(item, sort_keys=True)
        if amount:
            Recipient(Address(item["recipient"])).emit_transfer(value=u256(amount), on="finalized")

    @gl.public.write.payable
    def challenge(self, promise_id: str, evidence_json: str) -> str:
        sender = lower(gl.message.sender_address)
        value = int(gl.message.value)
        record = self._promise(promise_id)
        reason = ""
        try:
            evidence = json.loads(evidence_json)
        except Exception:
            evidence = []
        if not record:
            reason = "Promise does not exist."
        elif record.get("status") != "OPEN":
            reason = "Promise is not open for challenge."
        elif now() < int(record.get("deadline", 0)):
            reason = "Challenge is only available after the deadline."
        elif now() >= int(record.get("challenge_close_at", 0)):
            reason = "Challenge window has closed."
        elif record.get("poster") == sender:
            reason = "Poster cannot challenge their own promise."
        elif int(record.get("bond_wei", "0")) % 4 != 0 or value != int(record.get("bond_wei", "0")) // 4:
            reason = "Challenge stake must equal exactly 25% of the bond."
        elif not isinstance(evidence, list) or not 1 <= len(evidence) <= 3:
            reason = "Provide one to three immutable evidence URLs."
        elif any(not valid_evidence_url(url, int(record.get("deadline", 0)), bool(self.allow_wayback), bool(self.allow_github_raw), bool(self.allow_npm), bool(self.allow_wikipedia)) for url in evidence):
            reason = "Evidence URL is outside the immutable allowlist."
        if reason:
            return self._new_refund(sender, value, reason)
        record["challenge"] = {"challenger": sender, "stake_wei": str(value), "evidence": evidence, "created_at": now()}
        record["challenge_stake_wei"] = str(value)
        record["defence_end"] = now() + int(self.defence_window)
        record["status"] = "CHALLENGED"
        record["reason"] = "Challenge is live; defence window is open."
        self._put(record)
        return promise_id

    @gl.public.write
    def defend(self, promise_id: str, evidence_json: str) -> None:
        record = self._promise(promise_id)
        require(record.get("status") == "CHALLENGED", "challenged promise required")
        require(lower(gl.message.sender_address) == record.get("poster"), "poster only")
        require(now() <= int(record.get("defence_end", 0)), "defence window has closed")
        evidence = json.loads(evidence_json)
        require(isinstance(evidence, list) and 1 <= len(evidence) <= 2, "provide one or two defence URLs")
        require(len(record.get("defence_evidence", [])) + len(evidence) <= 2, "at most two defence URLs")
        require(all(valid_evidence_url(url, int(record.get("deadline", 0)), bool(self.allow_wayback), bool(self.allow_github_raw), bool(self.allow_npm), bool(self.allow_wikipedia)) for url in evidence), "evidence URL is outside the immutable allowlist")
        record["defence_evidence"] = record.get("defence_evidence", []) + evidence
        self._put(record)

    @gl.public.write
    def judge_next(self, promise_id: str) -> None:
        record = self._promise(promise_id)
        require(record.get("status") in ("CHALLENGED", "READY_TO_JUDGE"), "promise is not ready for judgment")
        require(now() >= int(record.get("defence_end", 0)), "defence window is still open")
        index = int(record.get("next_criterion", 0))
        require(index < len(record.get("criteria", [])), "all criteria have been judged")
        evidence = record.get("challenge", {}).get("evidence", []) + record.get("defence_evidence", [])
        record["status"] = "JUDGING"
        record["judging_started_at"] = now()
        self._put(record)
        gl.get_contract_at(self.promise_judge).emit(on="finalized").judge(
            promise_id,
            index,
            record["criteria"][index],
            json.dumps(evidence, separators=(",", ":")),
            record.get("not_counted", ""),
        )

    @gl.public.write
    def complete_judgment(self, promise_id: str, result_json: str) -> None:
        require(lower(gl.message.sender_address) == lower(self.promise_judge), "PromiseJudge only")
        record = self._promise(promise_id)
        if not record or record.get("status") != "JUDGING":
            return
        index = int(record.get("next_criterion", 0))
        result = json.loads(result_json)
        verdict = result.get("verdict")
        if verdict not in ("MET", "NOT_MET", "INSUFFICIENT_EVIDENCE"):
            verdict = "INSUFFICIENT_EVIDENCE"
            result = {"verdict": verdict, "quote": "", "reason": "Invalid judgment schema; everyone is refunded.", "digest": "", "evidence_class": "INVALID_SCHEMA"}
        record.setdefault("verdicts", []).append({
            "criterion_index": index,
            "criterion": record["criteria"][index],
            "verdict": verdict,
            "quote": str(result.get("quote", ""))[:500],
            "reason": str(result.get("reason", ""))[:200],
            "digest": str(result.get("digest", "")),
            "evidence_class": str(result.get("evidence_class", "UNKNOWN")),
            "recorded_at": now(),
        })
        record["next_criterion"] = index + 1
        record.pop("judging_started_at", None)
        if record["next_criterion"] >= len(record["criteria"]):
            record["status"] = "RESULT_PENDING"
            self._put(record)
            gl.get_contract_at(gl.message.contract_address).emit(on="finalized").settle(promise_id)
            return
        record["status"] = "READY_TO_JUDGE"
        self._put(record)

    def _finalize_settlement(self, record, expired=False):
        verdicts = record.get("verdicts", [])
        if expired:
            criteria = record.get("criteria", [])
            have = {int(item.get("criterion_index", -1)) for item in verdicts}
            for index, criterion in enumerate(criteria):
                if index not in have:
                    verdicts.append({"criterion_index": index, "criterion": criterion, "verdict": "INSUFFICIENT_EVIDENCE", "quote": "", "reason": "Judgment exceeded the on-chain grace period; everyone is refunded.", "digest": "", "evidence_class": "GRACE_FALLBACK", "recorded_at": now()})
        if any(item.get("verdict") == "NOT_MET" for item in verdicts):
            return "BROKEN"
        if len(verdicts) < len(record.get("criteria", [])) or any(item.get("verdict") == "INSUFFICIENT_EVIDENCE" for item in verdicts):
            return "UNPROVEN"
        return "KEPT"

    @gl.public.write
    def settle(self, promise_id: str) -> None:
        self._self_only()
        record = self._promise(promise_id)
        if record.get("status") != "RESULT_PENDING":
            return
        outcome = self._finalize_settlement(record)
        record["status"] = outcome
        record["settlement"] = outcome
        self._put(record)
        bond = int(record.get("bond_wei", "0"))
        stake = int(record.get("challenge_stake_wei", "0"))
        record["bond_wei"] = "0"
        record["challenge_stake_wei"] = "0"
        if outcome == "KEPT":
            self._payout(record, "kept_bond_and_stake", record["poster"], bond + stake)
        elif outcome == "BROKEN":
            self._payout(record, "broken_bond_and_stake", record["challenge"]["challenger"], bond + stake)
        else:
            self._payout(record, "unproven_bond_refund", record["poster"], bond)
            self._payout(record, "unproven_stake_refund", record["challenge"]["challenger"], stake)
        self._put(record)

    @gl.public.write
    def settle_expired(self, promise_id: str) -> None:
        record = self._promise(promise_id)
        require(record.get("status") in ("CHALLENGED", "JUDGING", "READY_TO_JUDGE"), "challenged promise required")
        require(now() >= int(record.get("defence_end", 0)) + int(self.grace_period), "judgment grace period has not elapsed")
        outcome = self._finalize_settlement(record, expired=True)
        record["status"] = outcome
        record["settlement"] = outcome
        record["reason"] = "Unjudged criteria became INSUFFICIENT_EVIDENCE after the grace period."
        bond = int(record.get("bond_wei", "0"))
        stake = int(record.get("challenge_stake_wei", "0"))
        record["bond_wei"] = "0"
        record["challenge_stake_wei"] = "0"
        if outcome == "BROKEN":
            self._payout(record, "expired_broken_bond_and_stake", record["challenge"]["challenger"], bond + stake)
        else:
            self._payout(record, "expired_bond_refund", record["poster"], bond)
            self._payout(record, "expired_stake_refund", record["challenge"]["challenger"], stake)
        self._put(record)

    @gl.public.write
    def release(self, promise_id: str) -> None:
        record = self._promise(promise_id)
        require(record.get("status") == "OPEN", "unchallenged open promise required")
        require(now() >= int(record.get("challenge_close_at", 0)), "challenge window has not elapsed")
        record["status"] = "RELEASE_PENDING"
        self._put(record)
        gl.get_contract_at(gl.message.contract_address).emit(on="finalized").release_finalized(promise_id)

    @gl.public.write
    def release_finalized(self, promise_id: str) -> None:
        self._self_only()
        record = self._promise(promise_id)
        if record.get("status") != "RELEASE_PENDING":
            return
        amount = int(record.get("bond_wei", "0"))
        record["bond_wei"] = "0"
        record["status"] = "RELEASED"
        record["settlement"] = "RELEASED"
        self._payout(record, "unchallenged_bond_release", record["poster"], amount)
        self._put(record)

    @gl.public.write
    def refund_compile_expired(self, promise_id: str) -> None:
        record = self._promise(promise_id)
        require(record.get("status") == "COMPILING", "compiling promise required")
        require(now() >= int(record.get("created_at", 0)) + int(self.grace_period), "compile grace period has not elapsed")
        record["status"] = "REFUNDABLE_ERROR"
        record["reason"] = "Criteria compilation did not finalize before grace elapsed; bond is refundable."
        self._put(record)
        gl.get_contract_at(gl.message.contract_address).emit(on="finalized").refund_invalid_promise(promise_id)

    @gl.public.write
    def record_transaction(self, promise_id: str, action: str, tx_hash: str) -> None:
        self._only_owner()
        record = self._promise(promise_id)
        require(bool(record), "promise required")
        require(re.fullmatch(r"0x[0-9a-fA-F]{64}", tx_hash) is not None, "transaction hash required")
        items = self._tx_list(promise_id)
        items.append({"action": action[:80], "hash": tx_hash})
        self.transactions[promise_id] = json.dumps(items, sort_keys=True)

    @gl.public.view
    def get_promise(self, promise_id: str) -> dict:
        record = self._promise(promise_id)
        if record:
            record["transactions"] = self._tx_list(promise_id)
        return record

    @gl.public.view
    def get_promises(self, start: int = 0, limit: int = 50) -> list:
        start_index = max(0, int(start))
        end_index = min(len(self.promise_ids), start_index + max(0, min(int(limit), 50)))
        items = []
        for index in range(start_index, end_index):
            record = self._promise(self.promise_ids[index])
            record["transactions"] = self._tx_list(record["id"])
            items.append(record)
        return items

    @gl.public.view
    def get_verdicts(self, promise_id: str) -> list:
        return self._promise(promise_id).get("verdicts", [])

    @gl.public.view
    def get_balances(self, promise_id: str) -> dict:
        record = self._promise(promise_id)
        return {
            "contract_balance_wei": str(int(self.balance)),
            "bond_held_wei": str(record.get("bond_wei", "0")),
            "challenge_stake_held_wei": str(record.get("challenge_stake_wei", "0")),
            "poster": record.get("poster", ""),
            "challenger": (record.get("challenge") or {}).get("challenger", ""),
        }
