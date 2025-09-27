"""
ESP32-S3 조이스틱 모듈 라이브러리
GPIO 연결:
- VRX (X축) -> GPIO9 (ADC)
- VRY (Y축) -> GPIO10 (ADC)  
- SW (버튼) -> GPIO11 (디지털 입력)
"""

import machine
from machine import Pin, ADC
import time
import math

class Joystick:
    def __init__(self, vrx_pin=12, vry_pin=13, sw_pin=11):
        """
        조이스틱 초기화
        
        Args:
            vrx_pin (int): X축 아날로그 입력 핀 (기본값: 12 - GPIO12/ADC2_CH1)
            vry_pin (int): Y축 아날로그 입력 핀 (기본값: 13 - GPIO13/ADC2_CH2)
            sw_pin (int): 버튼 디지털 입력 핀 (기본값: 11 - GPIO11/ADC2_CH0)
        """
        # ADC 핀 설정
        self.vrx_adc = ADC(Pin(vrx_pin))
        self.vry_adc = ADC(Pin(vry_pin))
        
        # 핀 번호 저장
        self.vrx_pin_num = vrx_pin
        self.vry_pin_num = vry_pin
        self.sw_pin_num = sw_pin
        
        # ADC 해상도 설정 (12비트, 0-4095 범위)
        self.vrx_adc.atten(ADC.ATTN_11DB)
        self.vry_adc.atten(ADC.ATTN_11DB)
        self.vrx_adc.width(ADC.WIDTH_12BIT)
        self.vry_adc.width(ADC.WIDTH_12BIT)
        
        # 버튼 핀 설정 (내부 풀업 저항 사용)
        self.sw_pin = Pin(sw_pin, Pin.IN, Pin.PULL_UP)
        
        # 캘리브레이션 값 (중앙값)
        self.center_x = 2048
        self.center_y = 2048
        
        # 데드존 설정 (중앙에서 얼마나 움직여야 반응할지)
        self.deadzone = 100
        
        # 최대/최소 값
        self.max_value = 4095
        self.min_value = 0
        
        print("조이스틱 모듈이 초기화되었습니다")
        print(f"VRX 핀: GPIO{vrx_pin} (ADC2_CH{vrx_pin-11})")
        print(f"VRY 핀: GPIO{vry_pin} (ADC2_CH{vry_pin-11})")
        print(f"SW 핀: GPIO{sw_pin} (ADC2_CH{sw_pin-11})")
        
        # 초기 캘리브레이션 수행
        self.calibrate()
    
    def calibrate(self):
        """
        조이스틱 중앙값 캘리브레이션
        조이스틱을 중앙에 놓고 호출하세요
        """
        print("조이스틱 캘리브레이션을 시작합니다...")
        print("조이스틱을 중앙 위치에 놓고 3초 후 자동으로 진행됩니다")
        
        # 3초 대기
        for i in range(3, 0, -1):
            print(f"캘리브레이션 시작까지 {i}초...")
            time.sleep(1)
        
        # 중앙값 측정 (여러 번 읽어서 평균값 계산)
        samples = 50
        x_sum = 0
        y_sum = 0
        
        print("중앙값을 측정하는 중...")
        for i in range(samples):
            # 반전된 값으로 중앙값 계산
            x_sum += 4095 - self.vrx_adc.read()
            y_sum += self.vry_adc.read()
            time.sleep(0.01)
        
        self.center_x = x_sum // samples
        self.center_y = y_sum // samples
        
        print(f"캘리브레이션 완료!")
        print(f"중앙 X값: {self.center_x}")
        print(f"중앙 Y값: {self.center_y}")
    
    def read_raw(self):
        """
        조이스틱 원시 값 읽기
        
        Returns:
            tuple: (x_raw, y_raw, button_state)
                - x_raw: X축 원시 ADC 값 (0-4095)
                - y_raw: Y축 원시 ADC 값 (0-4095)
                - button_state: 버튼 상태 (True: 눌림, False: 안눌림)
        """
        # 조이스틱 방향에 따라 값 반전 (참고 코드 적용)
        x_raw = self.vrx_adc.read()  # X축 반전
        y_raw = self.vry_adc.read()         # Y축 그대로
        button_state = self.sw_pin.value()  # 버튼 반전 (0/1)
        
        return x_raw, y_raw, button_state
    
    def read(self):
        """
        조이스틱 값을 정규화하여 읽기
        
        Returns:
            tuple: (x, y, button_state)
                - x: X축 값 (-1.0 ~ 1.0)
                - y: Y축 값 (-1.0 ~ 1.0)
                - button_state: 버튼 상태 (True: 눌림, False: 안눌림)
        """
        x_raw, y_raw, button_state = self.read_raw()
        
        # 중앙값 기준으로 정규화
        x_offset = x_raw - self.center_x
        y_offset = y_raw - self.center_y
        
        # 데드존 적용
        if abs(x_offset) < self.deadzone:
            x_offset = 0
        if abs(y_offset) < self.deadzone:
            y_offset = 0
        
        # 정규화 (-1.0 ~ 1.0)
        max_offset = (self.max_value - self.min_value) // 2
        x = x_offset / max_offset
        y = y_offset / max_offset
        
        # 범위 제한
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        return x, y, button_state
    
    def read_angle_magnitude(self):
        """
        조이스틱 값을 각도와 크기로 읽기
        
        Returns:
            tuple: (angle, magnitude, button_state)
                - angle: 각도 (0-360도)
                - magnitude: 크기 (0.0-1.0)
                - button_state: 버튼 상태
        """
        x, y, button_state = self.read()
        
        # 각도 계산 (라디안에서 도로 변환)
        angle = math.atan2(y, x) * 180 / math.pi
        
        # 각도를 0-360도 범위로 변환
        if angle < 0:
            angle += 360
        
        # 크기 계산
        magnitude = math.sqrt(x*x + y*y)
        
        return angle, magnitude, button_state
    
    def read_direction(self):
        """
        조이스틱 방향을 8방향으로 읽기
        
        Returns:
            tuple: (direction, button_state)
                - direction: 방향 문자열 ("중앙", "위", "오른쪽위", "오른쪽", "오른쪽아래", "아래", "왼쪽아래", "왼쪽", "왼쪽위")
                - button_state: 버튼 상태
        """
        angle, magnitude, button_state = self.read_angle_magnitude()
        
        # 데드존 체크
        if magnitude < 0.1:
            return "중앙", button_state
        
        # 8방향으로 분할 (각 45도씩)
        if 337.5 <= angle or angle < 22.5:
            direction = "오른쪽"
        elif 22.5 <= angle < 67.5:
            direction = "오른쪽위"
        elif 67.5 <= angle < 112.5:
            direction = "위"
        elif 112.5 <= angle < 157.5:
            direction = "왼쪽위"
        elif 157.5 <= angle < 202.5:
            direction = "왼쪽"
        elif 202.5 <= angle < 247.5:
            direction = "왼쪽아래"
        elif 247.5 <= angle < 292.5:
            direction = "아래"
        else:  # 292.5 <= angle < 337.5
            direction = "오른쪽아래"
        
        return direction, button_state
    
    def is_button_pressed(self):
        """
        버튼이 눌렸는지 확인
        
        Returns:
            bool: 버튼 상태 (True: 눌림, False: 안눌림)
        """
        return not self.sw_pin.value()
    
    def wait_for_button_release(self):
        """
        버튼이 놓일 때까지 대기
        """
        while self.is_button_pressed():
            time.sleep(0.01)
    
    def wait_for_button_press(self):
        """
        버튼이 눌릴 때까지 대기
        """
        while not self.is_button_pressed():
            time.sleep(0.01)
    
    def get_deadzone(self):
        """
        현재 데드존 값 반환
        
        Returns:
            int: 데드존 값
        """
        return self.deadzone
    
    def set_deadzone(self, deadzone):
        """
        데드존 값 설정
        
        Args:
            deadzone (int): 새로운 데드존 값 (0-1000 권장)
        """
        self.deadzone = max(0, min(1000, deadzone))
        print(f"데드존이 {self.deadzone}으로 설정되었습니다")
    
    def test_adc(self):
        """
        ADC 핀 테스트 함수
        """
        print("\n=== ADC 핀 테스트 ===")
        print("조이스틱을 움직여보세요. 값이 변하는지 확인하세요.")
        print("종료하려면 Ctrl+C를 누르세요\n")
        
        try:
            while True:
                x_raw = 4095 - self.vrx_adc.read()  # 반전된 값
                y_raw = self.vry_adc.read()
                button = 1 - self.sw_pin.value()  # 0/1 값
                
                # 값 변화 감지
                x_change = "변화없음" if abs(x_raw - 2048) < 50 else "변화있음"
                y_change = "변화없음" if abs(y_raw - 2048) < 50 else "변화있음"
                
                print(f"VRX: {x_raw:4d} ({x_change}) | VRY: {y_raw:4d} ({y_change}) | SW: {button}")
                time.sleep(0.2)
                
        except KeyboardInterrupt:
            print("\nADC 테스트를 종료합니다")
    
    def check_connections(self):
        """
        하드웨어 연결 상태 확인
        """
        print("\n=== 하드웨어 연결 확인 ===")
        
        # ADC 값 읽기 (여러 번 읽어서 안정성 확인)
        x_values = []
        y_values = []
        for i in range(5):
            x_values.append(4095 - self.vrx_adc.read())  # 반전된 값
            y_values.append(self.vry_adc.read())
            time.sleep(0.01)
        
        x_raw = sum(x_values) // len(x_values)
        y_raw = sum(y_values) // len(y_values)
        button = not self.sw_pin.value()
        
        print(f"현재 ADC 값 (5회 평균):")
        print(f"  VRX (GPIO{self.vrx_pin_num}): {x_raw}")
        print(f"  VRY (GPIO{self.vry_pin_num}): {y_raw}")
        print(f"  SW (GPIO{self.sw_pin_num}): {button}")
        
        # 연결 상태 판단
        if x_raw == 0 and y_raw == 0:
            print("\n⚠️  경고: VRX, VRY 값이 모두 0입니다.")
            print("   - 전원 연결을 확인하세요 (VCC -> 3.3V, GND -> GND)")
            print("   - 핀 연결을 확인하세요")
            print("   - 조이스틱 모듈이 손상되었을 수 있습니다")
        elif x_raw == 4095 and y_raw == 4095:
            print("\n⚠️  경고: VRX, VRY 값이 모두 최대값입니다.")
            print("   - GND 연결을 확인하세요")
            print("   - 조이스틱 모듈이 손상되었을 수 있습니다")
        elif abs(x_raw - 2048) < 50 and abs(y_raw - 2048) < 50:
            print("\n✅ ADC 연결이 정상적으로 보입니다.")
            print("   - 조이스틱이 중앙 위치에 있습니다")
        else:
            print("\n✅ ADC 연결이 정상적으로 보입니다.")
            print("   - 조이스틱이 움직인 상태입니다")
        
        print(f"\n권장 연결:")
        print(f"  조이스틱 VCC -> ESP32-S3 3.3V")
        print(f"  조이스틱 GND -> ESP32-S3 GND")
        print(f"  조이스틱 VRX -> ESP32-S3 GPIO{self.vrx_pin_num}")
        print(f"  조이스틱 VRY -> ESP32-S3 GPIO{self.vry_pin_num}")
        print(f"  조이스틱 SW  -> ESP32-S3 GPIO{self.sw_pin_num}")
        
        print(f"\nESP32-S3 ADC 채널 정보:")
        print(f"  ADC1: GPIO1-GPIO10 (10채널)")
        print(f"  ADC2: GPIO11-GPIO20 (10채널)")
        print(f"  현재 사용: VRX=ADC2_CH{self.vrx_pin_num-11}, VRY=ADC2_CH{self.vry_pin_num-11}, SW=ADC2_CH{self.sw_pin_num-11}")
    
    def read_values_string(self):
        """
        참고 코드와 동일한 형식으로 값 반환
        Returns:
            str: "x|y|button" 형식의 문자열
        """
        x_raw, y_raw, button = self.read_raw()
        return f"{x_raw}|{y_raw}|{button}"

def main():
    """
    조이스틱 테스트 메인 함수
    """
    # 조이스틱 객체 생성
    joy = Joystick()
    
    # 연결 상태 확인
    joy.check_connections()
    
    print("\n조이스틱 테스트를 시작합니다")
    print("조이스틱을 움직이거나 버튼을 눌러보세요")
    print("종료하려면 Ctrl+C를 누르세요\n")
    
    try:
        while True:
            # 방법 1: 정규화된 값 읽기
            x, y, button = joy.read()
            
            # 방법 2: 원시 값 읽기
            x_raw, y_raw, button_raw = joy.read_raw()
            
            # 방법 3: 방향 읽기
            direction, button_dir = joy.read_direction()
            
            # 방법 4: 각도와 크기 읽기
            angle, magnitude, button_ang = joy.read_angle_magnitude()
            
            # 결과 출력
            print(f"정규화: X={x:.2f}, Y={y:.2f}, 버튼={button}")
            print(f"원시값: X={x_raw:4d}, Y={y_raw:4d}, 버튼={button_raw}")
            print(f"방향: {direction}, 크기: {magnitude:.2f}, 각도: {angle:.1f}도")
            print(f"문자열: {joy.read_values_string()}")
            print("-" * 50)
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n조이스틱 테스트를 종료합니다")

# 메인 실행
if __name__ == "__main__":
    main()
