# ================================================================
#  config.py — настройки и профили сканирования
# ================================================================

URI = "ip:192.168.1.10"

# --- Параметры детекции ---
FFT_SIZE        = 4096
BUFFER_SIZE     = 8192
CONFIRM_REQUIRED = 2       # подтверждений для засчитывания сигнала
MEASURE_PER_FREQ = 3       # замеров на частоту
THRESHOLD_DB     = 12.0    # dB над медианой (фиксированный порог)
BINS_ABOVE_MIN   = 3       # минимум бинов выше порога

LOG_DIR = "rf_scans"

# --- Профили сканирования ---
SCAN_PROFILES = {
    "1": {
        "name":        "TEMPEST (мониторы/компьютеры)",
        "start":       70e6,
        "stop":        1500e6,
        "step":        8e6,
        "sample_rate": 10e6,
        "gain":        40,
    },
    "2": {
        "name":        "Жучки / прослушка",
        "start":       70e6,
        "stop":        3000e6,
        "step":        8e6,
        "sample_rate": 10e6,
        "gain":        50,
    },
    "3": {
        "name":        "FM + Авиация (88-140 МГц)",
        "start":       88e6,
        "stop":        140e6,
        "step":        1e6,
        "sample_rate": 2e6,
        "gain":        30,
    },
    "4": {
        "name":        "GSM/LTE (800-2700 МГц)",
        "start":       800e6,
        "stop":        2700e6,
        "step":        5e6,
        "sample_rate": 10e6,
        "gain":        40,
    },
    "5": {
        "name":        "Wi-Fi 2.4 ГГц",
        "start":       2400e6,
        "stop":        2500e6,
        "step":        1e6,
        "sample_rate": 20e6,
        "gain":        35,
    },
    "6": {
        "name":        "Wi-Fi 5 ГГц",
        "start":       5150e6,
        "stop":        5850e6,
        "step":        5e6,
        "sample_rate": 20e6,
        "gain":        40,
    },
    "7": {
        "name":        "Дроны (900M / 2.4G / 5.8G)",
        "start":       900e6,
        "stop":        5800e6,
        "step":        10e6,
        "sample_rate": 10e6,
        "gain":        45,
    },
    "8": {
        "name":        "Пользовательский диапазон",
        "start":       None,
        "stop":        None,
        "step":        None,
        "sample_rate": 10e6,
        "gain":        40,
    },
}
