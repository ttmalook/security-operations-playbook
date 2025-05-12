import boto3
import os
import time

ec2 = boto3.client('ec2')
cw = boto3.client('cloudwatch')

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
THRESHOLDS = [int(v.strip()) for v in os.environ.get("ALARM_THRESHOLD", "60,80").split(",")]
REGION = os.environ.get("AWS_REGION", "ap-northeast-2")
IAM_INSTANCE_PROFILE_NAME = "EC2CloudWatchAgentRole"  # 연결할 IAM 역할 이름

def lambda_handler(event, context):
    try:
        detail = event.get("detail", {})
        state = detail.get("state")
        instance_id = detail.get("instance-id")

        # ✅ 보완: instance-id가 없으면 resources에서 추출
        if not instance_id and "resources" in event and event["resources"]:
            arn = event["resources"][0]
            if arn.startswith("arn:aws:ec2:"):
                instance_id = arn.split("/")[-1]

        if not instance_id:
            print("❗ 인스턴스 ID 없음")
            return

        print(f"✅ 인스턴스 ID 추출 성공: {instance_id}")

        # 📌 인스턴스 종료 시: 알람 삭제
        if state == "terminated":
            print(f"🗑️ 종료된 인스턴스 감지: {instance_id}")
            alarm_names = [f"{instance_id}-CPU-Warning", f"{instance_id}-CPU-Critical"]
            for alarm_name in alarm_names:
                try:
                    cw.delete_alarms(AlarmNames=[alarm_name])
                    print(f"✅ 알람 삭제 완료: {alarm_name}")
                except Exception as e:
                    print(f"⚠️ 알람 삭제 실패: {alarm_name} - {str(e)}")
            return {"status": "alarms_deleted", "instance_id": instance_id}

        # 📌 IAM 역할 연결
        desc = ec2.describe_instances(InstanceIds=[instance_id])
        instance = desc['Reservations'][0]['Instances'][0]
        profile = instance.get('IamInstanceProfile')

        if not profile:
            print(f"🔗 IAM 역할 연결 중: {IAM_INSTANCE_PROFILE_NAME}")
            ec2.associate_iam_instance_profile(
                IamInstanceProfile={'Name': IAM_INSTANCE_PROFILE_NAME},
                InstanceId=instance_id
            )
            time.sleep(5)  # IAM 역할 연결이 완전히 적용될 때까지 대기

        # 📌 알람 존재 여부 확인
        existing_alarms = cw.describe_alarms()
        alarm_names = set(alarm['AlarmName'] for alarm in existing_alarms['MetricAlarms'])

        created = 0
        for threshold in THRESHOLDS:
            if threshold == 60:
                alarm_name = f"{instance_id}-CPU-Warning"
                period = 300  # 5분
            elif threshold == 80:
                alarm_name = f"{instance_id}-CPU-Critical"
                period = 60  # 1분
            else:
                alarm_name = f"{instance_id}-CPU-{threshold}"
                period = 60

            if alarm_name in alarm_names:
                print(f"✅ 알람 존재: {alarm_name}")
                continue

            print(f"🚨 알람 생성: {alarm_name}")
            cw.put_metric_alarm(
                AlarmName=alarm_name,
                MetricName='CPUUtilization',
                Namespace='AWS/EC2',
                Statistic='Average',
                Period=period,
                EvaluationPeriods=1,
                Threshold=threshold,
                ComparisonOperator='GreaterThanThreshold',
                AlarmActions=[SNS_TOPIC_ARN],
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                TreatMissingData='missing'
            )
            created += 1

        return {
            "status": "alarms_created",
            "created": created,
            "instance_id": instance_id
        }

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        raise
