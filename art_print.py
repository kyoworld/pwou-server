import win32print
import time
import random
import requests
from datetime import datetime, timedelta
import msvcrt

# ================= 설정 구역 =================
PRINTER_NAME   = "POS-76"
SERVER_URL     = "https://web-production-a4443.up.railway.app"
POLL_INTERVAL  = 2               # 대기 항목 없을 때 재확인 간격 (초)
SEED_INTERVALS = [10, 20, 30, 60]  # 시드 출력 간격 후보 (초)
# ============================================

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
    """서버에서 다음 출력 항목을 가져옴. 실제 제보만 24시간 체크."""
    while True:
        try:
            data = requests.get(f"{SERVER_URL}/pending", timeout=5).json()
        except Exception as e:
            print(f"[ERROR] 서버 연결 실패: {e}")
            return None

        if data is None:
            return None

        # 시드는 서버가 타이밍을 관리하므로 24시간 체크 불필요
        if data.get("type") == "seed":
            return data

        # 실제 제보 24시간 체크
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
            continue

        return data

def _print_entry(data):
    """서버 데이터를 포맷해서 프린터로 전송. real/seed 공용."""
    ts_str    = data.get("timestamp", "")
    date_part = ts_str.split(" ")[0] if " " in ts_str else ts_str
    time_part = ts_str.split(" ")[1] if " " in ts_str else "00:00:00"
    country   = (data.get("country") or "UNKNOWN").upper()
    coord     = _format_coord(data.get("latitude"), data.get("longitude"))
    desc      = data.get("description", "")
    event_id  = f"{abs(data.get('id', 0)):04d}"
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
        label = "[SEED]" if data.get("type") == "seed" else "[REAL]"
        print(f"{label} ID {data.get('id')} | {country} | {coord} 출력 완료")
        return True
    except Exception as e:
        print(f"[ERROR] 프린터 오류: {e}")
        return False


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
        requests.get(f"{SERVER_URL}/pending", timeout=5)
        print(f"✓ 서버 연결 확인: {SERVER_URL}")
    except Exception as e:
        print(f"✗ 서버 연결 실패: {e}")
        print("인터넷 연결 확인 후 다시 실행해주세요.")
        input("계속하려면 Enter...")

    # 24시간 초과 항목 일괄 정리
    try:
        resp = requests.post(f"{SERVER_URL}/flush_expired", timeout=5).json()
        flushed = resp.get("flushed", 0)
        if flushed:
            print(f"[FLUSH] 24시간 초과 항목 {flushed}건 정리 완료")
    except Exception as e:
        print(f"[WARN] flush_expired 실패: {e}")

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

            data = _get_pending()

            if data:
                success = _print_entry(data)
                if success and data.get("type") != "seed":
                    try:
                        requests.post(f"{SERVER_URL}/mark_printed/{data['id']}", timeout=5)
                    except Exception as e:
                        print(f"[WARN] mark_printed 실패: {e}")
                time.sleep(2)
            else:
                # 대기 중에도 1초마다 키보드 체크
                for _ in range(POLL_INTERVAL):
                    time.sleep(1)
                    if msvcrt.kbhit() and msvcrt.getch() == b" ":
                        is_paused = True
                        break

    except KeyboardInterrupt:
        print("\n[!] 종료합니다.")


if __name__ == "__main__":
    main()
