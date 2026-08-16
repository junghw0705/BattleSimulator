# 🚂 Siecletrain - Visual Battle Simulator & Data Tool

> **쿼터뷰 열차 슈팅 게임 'Siecletrain'의 데이터 기반 전투 밸런스 및 승무원 육성 시뮬레이터**

---

## 🌟 주요 기능 (Key Features)

1. **🚂 통합 열차 & 적 세팅 워크숍 (Workshop)**
   - 기관차, 엔진, 제네레이터, 제동장치 및 객차 파츠 실시간 조합
   - 상단 실시간 조감도(Blueprint) 및 개별 객차 독립 방어력/HP/시너지 연산
   - 승무원 배치 및 승무원 스탯 포인트 배분 시스템 (공격/방어/생산)
   - 1:다 적 몬스터 편대 구성 및 2D 뷰포트 시뮬레이션

2. **📋 전투 로그 시트 (Combat Log Sheet)**
   - 틱(Tick) 단위 프레임별 발사, 피격, 버프/디버프 장판, 관통/폭발 물리 판정 기록
   - 엑셀 호환 CSV 다중 분리 저장 (로그 전용 + 열차/적 구성 보고서)

3. **🔍 Raw 데이터 인스펙터 (Data Inspector)**
   - 엑셀(`[콘텐츠]트레인 및 승무원 데이터.xlsx` 등) 실시간 연동 및 검증 뷰어

4. **🎲 승무원 레벨업 랜덤 성장 시뮬레이터 (Monte Carlo Simulation)**
   - 승무원 유형(전투형, 방어형, 생산형)별 주스탯 자동 감지
   - 주스탯 확률 기반 보조스탯 `(100% - 주스탯%) ÷ 2` 자동 계산
   - 1회~100,000회 대량 몬테카를로 시뮬레이션 및 백분위(Percentiles) 분포 분석
   - 시뮬레이션 결과 워크숍 객차 즉시 동기화 적용

---

## 🚀 빠른 시작 (Quick Start)

### 1. 원클릭 실행 (Windows)
- `run_simulator.bat` 또는 `run_simulator.vbs` 더블 클릭 (필요 패키지 자동 설치 및 실행)

### 2. 수동 실행 (Manual Run)
```bash
# 1. 가상환경 생성 및 활성화 (선택)
python -m venv venv
venv\Scripts\activate

# 2. 필수 패키지 설치
pip install -r requirements.txt

# 3. 시뮬레이터 실행
python main.py
```

---

## 📁 디렉토리 구조 (Directory Structure)

```
Siecletrain-BattleSimulator/
├── main.py                     # GUI 애플리케이션 진입점 (PyQt6)
├── battle_engine.py            # 2D 좌표 기반 실시간 전투 연산 엔진
├── models.py                   # 열차, 포탑, 승무원, 적 데이터 모델
├── data_loader.py              # 엑셀 데이터 동적 로더 및 검증기
├── ui_components.py            # 시각화 대시보드, 블루프린트 등 커스텀 위젯
├── requirements.txt            # 의존성 패키지 목록 (PyQt6, pandas, openpyxl)
├── run_simulator.bat           # 원클릭 실행 배치 스크립트
├── run_simulator.vbs           # 무음 실행 VBS 스크립트
└── README.md                   # 프로젝트 안내 문서
```
