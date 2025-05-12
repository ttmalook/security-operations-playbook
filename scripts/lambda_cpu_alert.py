import boto3
import json
import urllib.request
import os
from datetime import timedelta, timezone
from dateutil import parser

# ✅ Slack Webhook 환경변수
SLACK_URL = os.environ['SLACK_WEBHOOK_URL']

def lambda_handler(event, context):
    try:
        sns_msg = json.loads(event['Records'][0]['Sns']['Message'])
        print("📨 SNS 메시지:", json.dumps(sns_msg, ensure_ascii=False))

        # 알람 시간 파싱 및 변환
        alarm_time = parser.parse(sns_msg['StateChangeTime'])
        alarm_time_kst = alarm_time.astimezone(timezone(timedelta(hours=9)))

        # 알람 메타 정보
        instance_id = sns_msg['Trigger']['Dimensions'][0]['value']
        alarm_name = sns_msg.get('AlarmName', '알람 이름 없음')
        threshold = sns_msg['Trigger'].get('Threshold', 0)

        # 심각도 판단
        if threshold >= 80:
            severity = "🔥 *심각 알람*"
        elif threshold >= 60:
            severity = "⚠️ *경고 알람*"
        else:
            severity = "ℹ️ *알람 감지됨*"

        # 로그 조회 구간
        start_ts = int((alarm_time - timedelta(minutes=5)).timestamp() * 1000)
        end_ts = int(alarm_time.timestamp() * 1000)

        # 대상 로그 그룹 및 인스턴스별 스트림명
        log_groups = {
            "/ubuntu/syslog": f"{instance_id}-syslog",
            "/apache/error.log": f"{instance_id}-apache-error"
        }

        logs = boto3.client('logs')
        all_events = []

        for log_group, stream_name in log_groups.items():
            try:
                response = logs.get_log_events(
                    logGroupName=log_group,
                    logStreamName=stream_name,
                    startTime=start_ts,
                    endTime=end_ts,
                    limit=20,
                    startFromHead=False
                )
                events = response.get('events', [])
                if events:
                    all_events.append(f"[{log_group}/{stream_name}]")
                    for event in events:
                        all_events.append(event['message'])
            except Exception as e:
                all_events.append(f"[{log_group}] 로그 조회 실패: {str(e)}")

        log_messages = "\n".join(all_events) if all_events else "관련 에러 로그 없음"

        # Slack 메시지 구성
        message = {
            "text": f"{severity} - EC2 CPU 로그 감지\n"
                    f"• 인스턴스 ID: `{instance_id}`\n"
                    f"• 시각: {alarm_time_kst.strftime('%Y-%m-%d %H:%M:%S')} (KST)\n"
                    f"• 알람 이름: {alarm_name}\n"
                    f"• 기준 임계값: {threshold:.1f}%\n"
                    f"• 최근 5분간 로그:\n```{log_messages}```"
        }

        req = urllib.request.Request(
            SLACK_URL,
            data=json.dumps(message).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req)
        print("✅ Slack 메시지 전송 완료")

    except Exception as e:
        print(f"❌ Lambda 처리 오류: {str(e)}")
        raise
