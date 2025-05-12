#!/bin/bash

echo "✅ Apache 에러 유도 - 존재하지 않는 경로 접근 (404)"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/nonexist

echo "✅ Apache 에러 유도 - 권한 없는 경로 접근 시도 (403 예상)"
mkdir -p /var/www/html/forbidden
chmod 000 /var/www/html/forbidden
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/forbidden

echo "✅ Apache 에러 유도 - script timeout"
echo -e "#!/bin/bash\nsleep 10" > /usr/lib/cgi-bin/test_timeout.sh
chmod +x /usr/lib/cgi-bin/test_timeout.sh
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/cgi-bin/test_timeout.sh

sleep 3  # 로그 수집 대기 (CloudWatch Agent가 로그 수집 주기 고려)

echo "✅ CPU 부하 유도 중 (60% 4코어)"
stress-ng --cpu 4 --cpu-load 60 --timeout 60s 
sleep 5

echo "✅ CPU 부하 유도 중 (80% 4코어)"
stress-ng --cpu 4 --cpu-load 80 --timeout 60s 

echo "✅ 메모리 부하 유도 중 (1GB)"
dd if=/dev/zero of=/dev/shm/memtest bs=1M count=1024 &

echo "✅ 디스크 부하 유도 중 (1GB 파일 생성)"
dd if=/dev/zero of=~/disk_test_file bs=1M count=1024 &

echo "✅ 네트워크 In 유도 (100MB 다운로드)"
wget -O /dev/null https://speed.hetzner.de/100MB.bin &

echo "✅ 네트워크 Out 유도 (50MB 파일 업로드)"
dd if=/dev/zero of=test_upload_file bs=1M count=50
curl -X POST -F "file=@test_upload_file" https://httpbin.org/post

wait  # 백그라운드 부하 종료 대기

echo "✅ 테스트 완료"
