import win32print
import time
import random
import requests
from datetime import datetime, timedelta
import msvcrt

# ================= 설정 구역 =================
PRINTER_NAME   = "pos76"
SERVER_URL     = "https://web-production-a4443.up.railway.app"
SEED_INTERVALS = [10, 40, 60, 180, 300, 480, 600, 900]  # 시드 출력 후 대기 후보 (초)
# ============================================

# ── 시드 데이터 ──────────────────────────────
country_bounds = {
    "KO":  {"name": "KOREA",   "lat": (34.0, 38.0),  "lon": (126.0, 129.0)},
    "RU":  {"name": "RUSSIA",  "lat": (45.0, 70.0),  "lon": (30.0, 135.0)},
    "USA": {"name": "USA",     "lat": (30.0, 48.0),  "lon": (-120.0, -75.0)},
    "UK":  {"name": "UK",      "lat": (50.0, 58.0),  "lon": (-5.0, 1.5)},
    "JP":  {"name": "JAPAN",   "lat": (31.0, 45.0),  "lon": (130.0, 145.0)},
    "GER": {"name": "GERMANY", "lat": (47.5, 54.8),  "lon": (6.0, 14.8)},
}

details_ko = [
    "모든 섬유의 속성 짝 동일함.\n우연성 유지됨. 약 10켤레.",
    "이동 중 신호 변수 발생.\n연속 활성 상태 유지됨.",
    "거울 속의 상이 실제 본체보다\n0.5초 늦게 반응함. 지연 발생.",
    "그림자의 방향이 태양의\n위치와 15도 어긋나 있음.",
    "동전 던지기 결과가 7회 연속\n'앞면'으로 고정됨.",
    "복권 번호와 전일 영수증\n승인 번호 100% 일치함.",
    "대기권 마찰음이 특정\n화음(Harmony)으로 수신됨.",
    "꿈속의 낯선 건물이 실제\n거리에 나타남. 렌더링 완료.",
    "책의 첫 단어와 길거리\n전광판 단어 일치함.",
    "디지털 숫자가 일시적으로\n고대 상형문자로 변환됨.",
    "신호등이 사람의 심장박동과\n동기화되어 점멸함.",
    "비가 위로 솟구치는 현상이\n2초간 지속됨. 중력 역전.",
    "전화가 오기 전에 벨소리가\n먼저 들림. 인과율 역전.",
    "공중에 던진 물체가 바닥에\n닿기 전 증발함. 데이터 오류.",
    "특정 구역에서 중력이 5%\n감소함. 부유 물질 발생.",
    "모든 문의 잠금 장치가\n동시에 해제됨. 동기화 발생.",
    "하늘의 별들이 QR코드 형태를\n이룸. 우주적 신호 감지.",
    "관측 대상(YOU)의 생애가\n프린터로 자동 기록됨.",
    "시간이 11:11:11에서 멈춘 뒤\n10초 후 점프함.",
    "그림자가 주인과 다른\n동작을 취함. 독립적 위상 발생.",
]

details_ru = [
    "Гравитация снизилась на 5%.\n[Gravity decreased by 5%]",
    "Дождь идет вверх 2 секунды.\n[Rain falling upwards for 2s]",
    "Атмосферный шум как гармония.\n[Atmospheric friction as harmony]",
    "Часы пропустили 10 секунд.\n[Digital clocks skipped 10s]",
    "Отражение в зеркале запаздывает.\n[Mirror reflection latency 0.5s]",
    "Звезды сложились в QR-код.\n[Stars forming a giant QR code]",
    "Здание из сна появилось наяву.\n[Dream building rendered in street]",
    "7 раз подряд выпал орел.\n[7 heads in a row - Prob. error]",
    "Сквозь стены можно пройти.\n[Material permeability increased]",
    "Звук дождя без самого дождя.\n[Sound of rain without rainfall]",
    "Обнаружена системная петля.\n[System loop: identical objects]",
    "Запись вашей жизни началась.\n[Life-logging of (YOU) started]",
]

details_en = [
    "Gravity decreased by 5% in\nspecific sectors. Floating detected.",
    "Rain falling upwards for 2s.\nTemporary gravity inversion.",
    "All doors unlocked simultaneously.\nGlobal synchronization detected.",
    "Atmospheric friction received\nas a musical harmony.",
    "Digital clocks skipped 10s.\nTime axis deviation recorded.",
    "Reflection in mirror moving\nwith 0.5s latency.",
    "Stars forming a giant QR code.\nCosmic signal received.",
    "Observation of (YOU) started.\nAutomatic life-logging active.",
    "Unknown building from a dream\nrendered in the physical street.",
    "Shadow acting independently\nfrom the owner. Phase shift.",
    "Lottery numbers match previous\nreceipt ID. Causality short circuit.",
    "Coin toss: 7 heads in a row.\nExternal interference trace.",
    "Material permeability increased.\nObjects passing through walls.",
    "Sound of rain heard without\nany actual rainfall. Audio sync error.",
    "System loop detected.\nRepeating identical objects.",
]
# ─────────────────────────────────────────────

def _format_coord(lat, lon):
    if lat is None or lon is None:
        return "UNKNOWN"
    return f"{abs(lat):.4f} {'N' if lat >= 0 else 'S'} / {abs(lon):.4f} {'E' if lon >= 0 else 'W'}"

def _send_to_printer(content: str):
    hp = win32print.OpenPrinter(PRINTER_NAME)
    win32print.StartDocPrinter(hp, 1, ("ArtWork", None, "RAW"))
    win32print.StartPagePrinter(hp)
    win32print.WritePrinter(hp, b"\x1b\x45\x01")
    win32print.WritePrinter(hp, content.encode("cp949", errors="replace"))
    win32print.WritePrinter(hp, b"\x1d\x56\x42\x00")
    win32print.EndPagePrinter(hp)
    win32print.EndDocPrinter(hp)
    win32print.ClosePrinter(hp)

def _build_receipt(date_part, time_part, coord, country, event_id, header, desc, shift):
    date_compact = date_part.replace("-", "")
    return (
        "\n"
        "================================\n"
        "PARALLEL WORLD OBSERVATION UNIT\n"
        "AUTOMATED LOG RECEIPT\n"
        "\n"
        f"DATE  : {date_part}\n"
        f"TIME  : {time_part}\n"
        f"COORD : {coord}\n"
        f"REGION: {country}\n"
        "\n"
        "EVENT NO.\n"
        f"PW-{date_compact}.{event_id}\n"
        f"{header}\n"
        f"{desc}\n"
        "-----------------\n"
        "STATUS : RECORDED\n"
        "CHANNEL: STABILIZING\n"
        f"SHIFT  : {shift}\n"
        "================================\n"
        "\n\n\n\n\n"
    )

def _get_pending():
    """서버에서 출력 가능한 항목을 가져옴. 24시간 초과 항목은 스킵+마킹. 없으면 None."""
    while True:
        try:
            data = requests.get(f"{SERVER_URL}/pending", timeout=5).json()
        except Exception as e:
            print(f"[ERROR] 서버 연결 실패: {e}")
            return None

        if data is None:
            return None

        try:
            ts = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            ts = datetime.now()

        if ts < datetime.now() - timedelta(hours=24):
            try:
                requests.post(f"{SERVER_URL}/mark_printed/{data['id']}", timeout=5)
            except Exception:
                pass
            print(f"[SKIP] 24시간 초과 → ID {data['id']} 스킵")
            continue  # 다음 항목 확인

        return data

def print_real(data):
    """실제 유저 제보 출력."""
    ts_str    = data.get("timestamp", "")
    date_part = ts_str.split(" ")[0] if " " in ts_str else ts_str
    time_part = ts_str.split(" ")[1] if " " in ts_str else "00:00:00"
    country   = (data.get("country") or "UNKNOWN").upper()
    coord     = _format_coord(data.get("latitude"), data.get("longitude"))
    desc      = data.get("description", "")
    event_id  = f"{data['id']:04d}"
    shift     = f"CH +0.{random.randint(10000000, 99999999)}"

    if country == "KOREA":
        header = "---- 세부 기록 ----"
    elif country == "RUSSIA":
        header = "---- ПОДРОБНАЯ ЗАПИСЬ ----"
    else:
        header = "---- LOG DETAILS ----"

    content = _build_receipt(date_part, time_part, coord, country, event_id, header, desc, shift)

    try:
        _send_to_printer(content)
        print(f"[REAL] ID {data['id']} | {country} | {coord} 출력 완료")
    except Exception as e:
        print(f"[ERROR] 프린터 오류: {e}")
        return False

    try:
        requests.post(f"{SERVER_URL}/mark_printed/{data['id']}", timeout=5)
    except Exception as e:
        print(f"[WARN] mark_printed 실패: {e}")

    return True

def print_seed():
    """시드 데이터 랜덤 출력."""
    cat   = random.choice(list(country_bounds.keys()))
    bound = country_bounds[cat]
    lat   = random.uniform(*bound["lat"])
    lon   = random.uniform(*bound["lon"])

    if cat == "KO":
        desc   = random.choice(details_ko)
        header = "---- 세부 기록 ----"
    elif cat == "RU":
        desc   = random.choice(details_ru)
        header = "---- ПОДРОБНАЯ ЗАПИСЬ ----"
    else:
        desc   = random.choice(details_en)
        header = "---- LOG DETAILS ----"

    now        = datetime.now()
    date_part  = now.strftime("%Y-%m-%d")
    time_part  = now.strftime("%H:%M:%S")
    country    = bound["name"]
    coord      = _format_coord(lat, lon)
    event_id   = f"{random.randint(1, 9999):04d}"
    shift      = f"CH +0.{random.randint(10000000, 99999999)}"

    content = _build_receipt(date_part, time_part, coord, country, event_id, header, desc, shift)

    try:
        _send_to_printer(content)
        print(f"[SEED] {country} | {coord} 출력 완료")
    except Exception as e:
        print(f"[ERROR] 프린터 오류: {e}")
        return False

    return True


def main():
    is_paused = False
    print("-" * 50)
    # 프린터 연결 확인
    try:
        printers = [p[2] for p in win32print.EnumPrinters(2)]
        if PRINTER_NAME in printers:
            print(f"✓ 프린터 연결 확인: {PRINTER_NAME}")
        else:
            print(f"✗ 프린터 없음! 연결된 프린터 목록:")
            for p in printers:
                print(f"  - {p}")
            print("PRINTER_NAME을 위 목록 중 하나로 바꿔주세요.")
            input("계속하려면 Enter...")
    except Exception as e:
        print(f"✗ 프린터 확인 오류: {e}")

    # 서버 연결 확인
    try:
        r = requests.get(f"{SERVER_URL}/pending", timeout=5)
        print(f"✓ 서버 연결 확인: {SERVER_URL}")
    except Exception as e:
        print(f"✗ 서버 연결 실패: {e}")
        print("인터넷 연결 확인 후 다시 실행해주세요.")
        input("계속하려면 Enter...")
    print("PWOU 프린터 시스템 가동")
    print(f"서버: {SERVER_URL}")
    print(f"프린터: {PRINTER_NAME}")
    print("[Space]: 일시정지/재개  [Ctrl+C]: 종료")
    print("-" * 50)

    try:
        while True:
            if msvcrt.kbhit():
                if msvcrt.getch() == b" ":
                    is_paused = not is_paused
                    print(f"\n[{'PAUSED' if is_paused else 'RUNNING'}] {time.strftime('%H:%M:%S')}")

            if is_paused:
                time.sleep(0.5)
                continue

            # ── 실제 제보 우선 확인 ──
            data = _get_pending()
            if data:
                print_real(data)
                time.sleep(2)   # 연속 출력 시 짧은 간격
                continue

            # ── 실제 제보 없으면 시드 출력 ──
            print_seed()
            wait = random.choice(SEED_INTERVALS)
            print(f"대기 중... ({wait//60}분 {wait%60}초)  [실제 제보 감지 시 즉시 출력]")

            # 대기 중에도 1초마다 실제 제보 체크
            for _ in range(wait):
                time.sleep(1)
                if msvcrt.kbhit() and msvcrt.getch() == b" ":
                    is_paused = True
                    break
                data = _get_pending()
                if data:
                    print(f"\n[!] 실제 제보 감지 → 즉시 출력")
                    print_real(data)
                    time.sleep(2)
                    break

    except KeyboardInterrupt:
        print("\n[!] 종료합니다.")


if __name__ == "__main__":
    main()
