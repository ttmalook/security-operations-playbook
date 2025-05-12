# AWS EC2 모니터링 자동화 예제

![모니터링 흐름도](images/monitoring_flow.png)

이 저장소는 AWS 환경에서 **오토스케일링에 의해 생성되는 EC2 인스턴스 상태 변화 감지하여 자동 알람을 생성**, 
그리고 **CPU 리소스 사용량 모니터링 및 알람 전송**을 기반으로, 
Slack과 Email로 경고를 전달하는 **Lambda 기반 자동화 시스템** 예제를 포함합니다.

---

## 📁 디렉토리 구조

- `/scripts`: Lambda 함수 코드 (알람 생성 및 Slack 연동)
- `/configs`: CloudWatch Agent 메트릭 및 로그 수집 설정
- `/tests`: 부하 유도 테스트 스크립트
- `/images`: 시스템 아키텍처 및 알람 흐름 이미지

---

## ✅ Lambda 함수 설명

### 1. `lambda_cpu_alert.py`
- CloudWatch 알람이 SNS를 통해 전달되면 트리거됨
- 대상 인스턴스의 Apache 로그와 Syslog 최근 5분 조회
- 로그 필터링 후 Slack Webhook으로 알림 메시지 전송

### 2. `lambda_instance_detector.py`
- EventBridge가 EC2 인스턴스 생성/종료 이벤트 감지
- 인스턴스별로 CPU 경고/심각 알람을 자동 생성 또는 삭제
- IAM 역할이 미연결 시 자동 연결 수행

---

## ⚙️ CloudWatch Agent 설정 (`configs/amazon-cloudwatch-agent.json`)

- **수집 메트릭**
  - CPU: `cpu_usage_idle`, `cpu_usage_user`, `cpu_usage_system`, `cpu_usage_iowait`
  - Memory: `mem_used_percent`
  - Disk: `disk_used_percent`
  - Network: `bytes_sent`, `bytes_recv`, `packets_sent`, `packets_recv`

- **로그 수집 경로**
  - `/var/log/syslog`
  - `/var/log/apache2/error.log`

---

## 🧪 부하 테스트 (`tests/cloudwatch-metric-test.sh`)

테스트 스크립트를 통해 다음 항목을 유도할 수 있습니다:

- Apache 오류 유도 (403/404 등)
- CPU 부하 유도 (60%, 80%)
- 디스크 및 메모리 점유
- 외부 다운로드/업로드로 네트워크 트래픽 유발

```bash
chmod +x cloudwatch-metric-test.sh
sudo ./cloudwatch-metric-test.sh
```

---

## 📷 모니터링 및 알람 흐름 예시

![알람 흐름과 Slack 알림 예시](images/alarm_flow_example.png)

---

## 📎 활용 예시

- ISMS-P 인증 대응 시, 로그 수집 및 모니터링 증적 자료로 활용
- EC2 오토스케일링 환경에서 인스턴스별 CPU 알람 자동화 가능
- 운영자 대상 Slack/Email 기반 실시간 경고 연동 구현

⚒ 사용된 주요 AWS 기술 스택
AWS Chatbot – CloudWatch 알람을 Slack 채널에 자동 전달

Amazon EC2 – Auto Scaling 기반 웹 서버 운영

Amazon CloudWatch – 메트릭 수집, 알람 설정, 로그 스트리밍

AWS Lambda – 이벤트 기반 서버리스 함수 실행

Amazon EventBridge – EC2 상태 변경 이벤트 감지

Amazon SNS – 알람 트리거 전달 및 알림 연동

IAM Role – CloudWatch Agent 및 Lambda에 필요한 권한 연결

Slack Webhook – 실시간 경고 전송

# 🙋‍♂️ 작성자

- 백진우 (Jinwoo Baek)
- GitHub: [ttmalook](https://github.com/ttmalook)
- 이 프로젝트는 베스핀글로벌 멀티클라우드 전문가 과정 중 실제 수행한 실습 및 과제를 기반으로 구성되었습니다.
