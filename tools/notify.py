import argparse
import requests
import json
import sys

def send_dingtalk_notification(webhook_url: str, report_url: str, status: str):
    if not webhook_url:
        print("Webhook URL is not provided. Skipping notification.")
        return
        
    color = "#00FF00" if status.lower() == "success" else "#FF0000"
    title = "✅ 接口自动化测试通过" if status.lower() == "success" else "❌ 接口自动化测试失败"
    
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "自动化测试结果通知",
            "text": f"### {title}\n\n"
                    f"**测试状态**: <font color='{color}'>{status.upper()}</font>\n\n"
                    f"**详细报告**: [点击查看 Allure 测试报告]({report_url})\n\n"
        }
    }
    
    try:
        response = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
            timeout=10
        )
        response.raise_for_status()
        print("Notification sent successfully.")
    except Exception as e:
        print(f"Failed to send notification: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Send test result notification")
    parser.add_argument("--webhook", help="DingTalk/WeCom webhook URL")
    parser.add_argument("--report", help="URL of the generated test report")
    parser.add_argument("--status", help="Job status (success/failure)")
    args = parser.parse_args()
    
    send_dingtalk_notification(args.webhook, args.report, args.status)

if __name__ == "__main__":
    main()
