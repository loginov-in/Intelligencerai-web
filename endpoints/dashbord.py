import os
import platform
import shutil
import time
from datetime import datetime, timezone

from flask import jsonify, render_template
from flask_login import current_user

from main import app
from db_drowser import FileRecord, Organization, User, db

_APP_STARTED_AT = time.time()

PROJECT_NAME = "IntelligencerAI"
PROJECT_DOMAIN = "cloud.intelligencerai.ru"
PROJECT_ENV = "production"


def _read_meminfo():
    """Возвращает (total, available) байт из /proc/meminfo; на не-Linux — (None, None)."""
    try:
        info = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                key, _, value = line.partition(":")
                info[key] = int(value.strip().split()[0]) * 1024
        total = info.get("MemTotal")
        available = info.get("MemAvailable")
        if total and available is not None:
            return total, available
    except (OSError, ValueError):
        pass
    return None, None


def _system_uptime_seconds():
    try:
        with open("/proc/uptime") as fh:
            return float(fh.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def _server_info():
    total, available = _read_meminfo()
    ram = None
    if total:
        used = total - available
        ram = {
            "total": total,
            "used": used,
            "percent": round(used / total * 100, 1),
        }

    try:
        disk_total, disk_used, _disk_free = shutil.disk_usage("/")
        disk = {
            "total": disk_total,
            "used": disk_used,
            "percent": round(disk_used / disk_total * 100, 1),
        }
    except OSError:
        disk = None

    try:
        load_avg = [round(v, 2) for v in os.getloadavg()]
    except OSError:
        load_avg = None

    return {
        "hostname": platform.node(),
        "system": platform.platform(),
        "cpu_cores": os.cpu_count(),
        "load_avg": load_avg,
        "ram": ram,
        "disk": disk,
        "uptime_seconds": _system_uptime_seconds(),
    }


@app.route("/dashbord")
def dashbord():
    return render_template("dashbord.html")


@app.route("/api/dashbord")
def api_dashbord():
    payload = {
        "project": {
            "name": PROJECT_NAME,
            "domain": PROJECT_DOMAIN,
            "environment": PROJECT_ENV,
            "python": platform.python_version(),
            "started_at": datetime.fromtimestamp(
                _APP_STARTED_AT, tz=timezone.utc
            ).strftime("%d.%m.%Y %H:%M UTC"),
            "uptime_seconds": int(time.time() - _APP_STARTED_AT),
        },
        "server": _server_info(),
        "server_time": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"),
    }

    # Счётчики базы отдаём только вошедшим пользователям
    if current_user.is_authenticated:
        files_size = db.session.query(db.func.coalesce(db.func.sum(FileRecord.size), 0)).scalar()
        payload["database"] = {
            "users": User.query.count(),
            "organizations": Organization.query.count(),
            "files": FileRecord.query.count(),
            "files_size": int(files_size or 0),
        }

    return jsonify(payload), 200
