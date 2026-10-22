"""Validated legacy destination maps and action-time form guards.

Names remain the on-disk identity for compatibility. Every successful write
invalidates outstanding forms (including delete/recreate of the same name).
"""
import json
import math
from pathlib import Path

from .storage import atomic_write_json


def load_destinations(path, *, homes=False):
    path = Path(path)
    if not path.exists() and not path.is_symlink():
        content = atomic_write_json(path, {}, expected_content=None)
    else:
        content = path.read_bytes()
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Destination data must be an object")
    maps = data.values() if homes else [data]
    for destinations in maps:
        if not isinstance(destinations, dict):
            raise ValueError("Player destinations must be an object")
        for name, value in destinations.items():
            if not isinstance(name, str) or not name or not isinstance(value, dict):
                raise ValueError("Invalid destination record")
            loc = value.get("loc")
            if (not isinstance(value.get("dim"), str) or not value["dim"]
                    or not isinstance(loc, list) or len(loc) != 3
                    or any(type(n) not in (int, float) or not math.isfinite(n) for n in loc)):
                raise ValueError("Invalid destination coordinates")
    return data, content


def guard_callback(owner, callback, *, admin=False, player=None):
    revision = owner._revision
    identity = (player.name, player.xuid) if player is not None else None

    def guarded(current, *args):
        if (not owner._allowed(current, admin=admin)
                or revision != owner._revision
                or (identity is not None and identity != (current.name, current.xuid))):
            current.send_message("操作已失效，请重新打开菜单。")
            return
        return callback(current, *args)
    return guarded
