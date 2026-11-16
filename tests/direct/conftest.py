"""Shared Windows-safe GenLayer direct-mode helpers."""

import os
import tempfile
from datetime import datetime, timezone

from gltest.direct import loader
from gltest.direct.vm import VMContext


def _windows_safe_message_injection(vm):
    try:
        from genlayer.py import calldata
        from genlayer.py.types import Address
    except ImportError:
        return
    sender = Address(vm.sender) if isinstance(vm.sender, bytes) else vm.sender
    contract = Address(vm._contract_address) if isinstance(vm._contract_address, bytes) else vm._contract_address
    origin = Address(vm.origin) if isinstance(vm.origin, bytes) else vm.origin
    message = {
        "contract_address": contract,
        "sender_address": sender,
        "origin_address": origin,
        "stack": [],
        "value": vm._value,
        "datetime": vm._datetime,
        "is_init": False,
        "chain_id": vm._chain_id,
        "entry_kind": 0,
        "entry_data": b"",
        "entry_stage_data": None,
    }
    fd, path = tempfile.mkstemp()
    try:
        os.write(fd, calldata.encode(message))
        os.lseek(fd, 0, 0)
        vm._original_stdin_fd = os.dup(0)
        os.dup2(fd, 0)
        paths = getattr(vm, "_roadmap_bond_temp_paths", [])
        paths.append(path)
        vm._roadmap_bond_temp_paths = paths
    finally:
        os.close(fd)


_original_cleanup = VMContext._cleanup_after_deactivate


def _cleanup(vm):
    _original_cleanup(vm)
    for path in getattr(vm, "_roadmap_bond_temp_paths", []):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    vm._roadmap_bond_temp_paths = []


loader._inject_message_to_fd0 = _windows_safe_message_injection
VMContext._cleanup_after_deactivate = _cleanup


def address_bytes(address):
    return bytes.fromhex(address.removeprefix("0x"))


def selfcall(vm, method, *args):
    previous = vm.sender
    vm.sender = vm._contract_address
    try:
        return method(*args)
    finally:
        vm.sender = previous


def warp(vm, timestamp):
    vm.warp(datetime.fromtimestamp(timestamp, timezone.utc).isoformat())
    import sys

    gl = sys.modules.get("genlayer.gl")
    if gl is not None and getattr(gl, "message_raw", None) is not None:
        gl.message_raw["datetime"] = vm._datetime
