import requests
import json

class SlackAlerter:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_anomaly(self, log_line, template):
        if not self.webhook_url:
            return

        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚨 LogSheild: Anomaly Detected"}
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn", 
                        "text": f"*Raw Log:*\n`{log_line}`"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Template ID:*\nCluster Mode"},
                        {"type": "mrkdwn", "text": f"*Pattern:*\n`{template[:50]}...`"}
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": "📌 *Reason:* Statistical outlier detected by Expert Committee."}
                    ]
                }
            ]
        }
        
        try:
            requests.post(self.webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        except Exception as e:
            print(f"[!] Failed to send Slack alert: {e}")