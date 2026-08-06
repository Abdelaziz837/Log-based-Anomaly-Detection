import requests
import json

class SlackAlerter:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_anomaly(self, log_line, template):
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚨 SentinelLog: Anomaly Detected"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Raw Log:*\n`{log_line}`"}
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"📍 *Pattern:* {template}"}]
                }
            ]
        }
        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code != 200:
                print(f"[!] Slack returned error: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"[!] Failed to connect to Slack: {e}")