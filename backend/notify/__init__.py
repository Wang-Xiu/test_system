"""
Multi-channel notification system.
Sends test results to configured channels (DingTalk, Feishu, WeCom, Email).
"""

import json
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """Dispatch notifications to multiple channels based on project config."""

    def __init__(self, notification_config: Dict[str, Any]):
        self.channels: List[Dict[str, Any]] = notification_config.get("channels", [])

    def send(self, task_id: int, status: str, project_name: str, report_url: str = ""):
        """Send notification to all configured channels if status matches."""
        for channel in self.channels:
            notify_on = channel.get("notify_on", ["failed", "error"])
            if status not in notify_on:
                continue

            channel_type = channel.get("type", "")
            webhook_url = channel.get("webhook_url", "")
            if not webhook_url:
                continue

            try:
                if channel_type == "dingtalk":
                    _send_dingtalk(webhook_url, task_id, status, project_name, report_url)
                elif channel_type == "feishu":
                    _send_feishu(webhook_url, task_id, status, project_name, report_url)
                elif channel_type == "wecom":
                    _send_wecom(webhook_url, task_id, status, project_name, report_url)
                else:
                    logger.warning(f"Unknown notification channel type: {channel_type}")
            except Exception as e:
                logger.error(f"Failed to send {channel_type} notification: {e}")


def _build_message(task_id: int, status: str, project_name: str, report_url: str) -> str:
    status_emoji = {"success": "OK", "failed": "FAIL", "error": "ERROR"}.get(status, status)
    lines = [
        f"**自动化测试通知**",
        f"- 项目: {project_name}",
        f"- 任务ID: {task_id}",
        f"- 状态: {status_emoji}",
    ]
    if report_url:
        lines.append(f"- [查看报告]({report_url})")
    return "\n".join(lines)


def _send_dingtalk(webhook_url: str, task_id: int, status: str, project_name: str, report_url: str):
    text = _build_message(task_id, status, project_name, report_url)
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"测试结果: {status}",
            "text": text,
        },
    }
    resp = httpx.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()
    logger.info(f"DingTalk notification sent for task {task_id}")


def _send_feishu(webhook_url: str, task_id: int, status: str, project_name: str, report_url: str):
    text = _build_message(task_id, status, project_name, report_url)
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"测试结果: {status}"},
                "template": "red" if status != "success" else "green",
            },
            "elements": [
                {"tag": "markdown", "content": text},
            ],
        },
    }
    resp = httpx.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()
    logger.info(f"Feishu notification sent for task {task_id}")


def _send_wecom(webhook_url: str, task_id: int, status: str, project_name: str, report_url: str):
    text = _build_message(task_id, status, project_name, report_url)
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": text},
    }
    resp = httpx.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()
    logger.info(f"WeCom notification sent for task {task_id}")


def send_notification(db, task_id: int, status: str, project_id: Optional[int], report_url: str = ""):
    """Helper to send notifications for a completed task."""
    if not project_id:
        return

    from backend.model.models import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.notification_config:
        return

    dispatcher = NotificationDispatcher(project.notification_config)
    dispatcher.send(task_id, status, project.name, report_url)
