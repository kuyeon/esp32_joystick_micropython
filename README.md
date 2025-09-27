# ESP32-S3 조이스틱 라이브러리

ESP32-S3 보드용 조이스틱 모듈 라이브러리입니다.

## 📸 이미지

### 하드웨어 연결 이미지
<!-- 여기에 하드웨어 연결 이미지를 추가하세요 -->
<!-- 예: ![하드웨어 연결](images/hardware_connection.jpg) -->

### 조이스틱 모듈 이미지
<!-- 여기에 HW-504 조이스틱 모듈 이미지를 추가하세요 -->
<!-- 예: ![HW-504 조이스틱](images/hw504_joystick.jpg) -->

### 사용 예제 이미지
<!-- 여기에 사용 예제나 테스트 결과 이미지를 추가하세요 -->
<!-- 예: ![사용 예제](images/usage_example.jpg) -->

## 📋 시스템 요구사항

- **보드**: ESP32-S3
- **조이스틱 모듈**: HW-504
- **펌웨어**: MicroPython v1.26.1
- **펌웨어 파일**: `ESP32_GENERIC_S3-20250911-v1.26.1.bin`

## 📌 하드웨어 연결

```
HW-504 조이스틱    ESP32-S3
VCC              -> 3.3V
GND              -> GND
VRX              -> GPIO12
VRY              -> GPIO13
SW               -> GPIO11
```

## 🚀 빠른 시작

### 1. 펌웨어 설치
ESP32-S3에 MicroPython 펌웨어를 설치합니다:
- 펌웨어 파일: `ESP32_GENERIC_S3-20250911-v1.26.1.bin`
- 설치 도구: esptool.py 또는 ESP32 Flash Tool

### 2. 라이브러리 업로드
`joystick.py` 파일을 ESP32-S3에 업로드합니다.

### 3. 기본 사용법
```python
from joystick import Joystick

# 조이스틱 객체 생성
joy = Joystick()

# 값 읽기
x, y, button = joy.read()
print(f"X: {x:.2f}, Y: {y:.2f}, 버튼: {button}")
```

## 📋 주요 메서드

| 메서드 | 설명 | 반환값 |
|--------|------|--------|
| `read()` | 정규화된 값 읽기 | (-1.0~1.0, -1.0~1.0, True/False) |
| `read_raw()` | 원시 ADC 값 읽기 | (0~4095, 0~4095, 0/1) |
| `read_direction()` | 8방향 문자열 | ("중앙", "위", "오른쪽" 등) |
| `read_angle_magnitude()` | 각도와 크기 | (0~360도, 0.0~1.0) |
| `read_values_string()` | 문자열 형식 | "x|y|button" |

## 💡 사용 예제

### 기본 읽기
```python
from joystick import Joystick

joy = Joystick()

while True:
    x, y, button = joy.read()
    print(f"X: {x:.2f}, Y: {y:.2f}, 버튼: {button}")
```

### 방향 확인
```python
direction, button = joy.read_direction()
if direction == "오른쪽":
    print("오른쪽으로 이동")
elif direction == "위":
    print("위로 이동")
```

### 원시값 읽기
```python
x_raw, y_raw, button = joy.read_raw()
print(f"원시값: X={x_raw}, Y={y_raw}")
```

## 🔧 설정 옵션

### 데드존 설정
```python
joy.set_deadzone(200)  # 기본값: 100
```

### 수동 캘리브레이션
```python
joy.calibrate()
```

## 🎮 조이스틱 방향

```
    위(위)
      |
왼쪽(왼쪽) --+-- 오른쪽(오른쪽)
      |
    아래(아래)
```

- **중앙**: (0, 0)
- **오른쪽**: (1, 0)
- **왼쪽**: (-1, 0)
- **위**: (0, 1)
- **아래**: (0, -1)

## 🔍 문제 해결

### 조이스틱이 동작하지 않는 경우
1. 전원 연결 확인 (VCC -> 3.3V, GND -> GND)
2. 핀 연결 확인 (VRX->GPIO12, VRY->GPIO13, SW->GPIO11)
3. 연결 상태 확인: `joy.check_connections()`

### 값이 이상한 경우
1. 조이스틱을 중앙에 놓고 `joy.calibrate()` 실행
2. 데드존 조정: `joy.set_deadzone(값)`

## 📊 ADC 채널 정보

- **ADC1**: GPIO1~GPIO10 (10채널)
- **ADC2**: GPIO11~GPIO20 (10채널)
- **현재 사용**: GPIO12(ADC2_CH1), GPIO13(ADC2_CH2), GPIO11(ADC2_CH0)

## 🧪 테스트 실행

```python
# 전체 테스트 실행
from joystick import main
main()
```