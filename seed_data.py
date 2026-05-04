import random
from datetime import datetime
from timezonefinder import TimezoneFinder
import pytz

_tf = TimezoneFinder()

def _local_time(utc_dt, lat, lon):
    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    if not tz_name:
        return utc_dt.strftime("%Y-%m-%d %H:%M:%S")
    local_dt = pytz.utc.localize(utc_dt).astimezone(pytz.timezone(tz_name))
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")

country_bounds = {
    "KO":  {"name": "SOUTH KOREA",   "lat": (34.0, 38.0),  "lon": (126.0, 129.0)},
    "RU":  {"name": "RUSSIAN FEDERATION",  "lat": (45.0, 70.0),  "lon": (30.0, 135.0)},
    "USA": {"name": "UNITED STATES",     "lat": (30.0, 48.0),  "lon": (-120.0, -75.0)},
    "UK":  {"name": "UNITED KINGDOM",      "lat": (50.0, 58.0),  "lon": (-5.0, 1.5)},
    "JP":  {"name": "JAPAN",   "lat": (31.0, 45.0),  "lon": (130.0, 145.0)},
    "GER": {"name": "GERMANY", "lat": (47.5, 54.8),  "lon": (6.0, 14.8)},
    "CN":  {"name": "CHINA", "lat": (25.0, 45.0),  "lon": (100.0, 125.0)},
    "FR":  {"name": "FRANCE", "lat": (42.0, 52.0),  "lon": (-5.0, 8.0)},
    "IT":  {"name": "ITALY", "lat": (35.0, 47.0),  "lon": (10.0, 18.0)},
    "ES":  {"name": "SPAIN", "lat": (36.0, 44.0),  "lon": (-5.0, 4.0)},
    "NL":  {"name": "NETHERLANDS", "lat": (50.0, 54.0),  "lon": (4.0, 7.0)},
    "BE":  {"name": "BELGIUM", "lat": (50.0, 52.0),  "lon": (3.0, 6.0)},
    "SE":  {"name": "SWEDEN", "lat": (55.0, 68.0),  "lon": (10.0, 24.0)},
    "NO":  {"name": "NORWAY", "lat": (58.0, 72.0),  "lon": (5.0, 15.0)},
    "DK":  {"name": "DENMARK", "lat": (54.0, 58.0),  "lon": (8.0, 12.0)},
    "FI":  {"name": "FINLAND", "lat": (59.0, 70.0),  "lon": (20.0, 32.0)},
    "IS":  {"name": "ICELAND", "lat": (63.0, 68.0),  "lon": (-25.0, -13.0)},
    "NO":  {"name": "NORWAY", "lat": (58.0, 72.0),  "lon": (5.0, 15.0)},
    "DK":  {"name": "DENMARK", "lat": (54.0, 58.0),  "lon": (8.0, 12.0)},
    "FI":  {"name": "FINLAND", "lat": (59.0, 70.0),  "lon": (20.0, 32.0)},
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

_EN_COUNTRIES = ["USA", "UK", "JP", "GER"]

_SEED_RAW = (
    [("KO", d) for d in details_ko] +
    [("RU", d) for d in details_ru] +
    [(_EN_COUNTRIES[i % len(_EN_COUNTRIES)], d) for i, d in enumerate(details_en)]
)

def get_random_seed_entry():
    code, description = random.choice(_SEED_RAW)
    b = country_bounds[code]
    lat = b["lat"][0] + (b["lat"][1] - b["lat"][0]) * random.random()
    lon = b["lon"][0] + (b["lon"][1] - b["lon"][0]) * random.random()
    return {
        "description": description,
        "country":     b["name"],
        "latitude":    round(lat, 4),
        "longitude":   round(lon, 4),
        "timestamp":   _local_time(datetime.utcnow(), lat, lon),
    }
