# ================================================================
#  config.py — настройки и профили для RTL-SDR
# ================================================================

# Индекс устройства (0 = первый RTL-SDR)
RTL_DEVICE_INDEX = 0

# --- Параметры детекции ---
FFT_SIZE         = 2048
BUFFER_SIZE      = 256 * 1024
MEASURE_PER_FREQ = 3
CONFIRM_REQUIRED = 2
THRESHOLD_DB     = 12.0    # dB над медианой
BINS_ABOVE_MIN   = 3
FFT_AVG          = 4       # усреднение (1=выкл, 4-8=норм, 16=тихо)

LOG_DIR = "rf_scans"

# RTL-SDR диапазон зависит от тюнера:
#   R820T/R820T2: ~24 МГц – 1766 МГц  (самый распространённый)
#   E4000:        ~52 МГц – 2200 МГц
#   FC0013:       ~22 МГц – 948 МГц
RTL_FREQ_MIN = 24e6
RTL_FREQ_MAX = 1766e6

# --- Профили сканирования ---
SCAN_PROFILES = {
    "1": {
        "name":        "Жучки / прослушка",
        "start":       80e6,
        "stop":        1200e6,
        "step":        1e6,
        "sample_rate": 2.4e6,
        "gain":        40,
    },
    "2": {
        "name":        "FM + Авиация (88-140 МГц)",
        "start":       88e6,
        "stop":        140e6,
        "step":        0.1e6,
        "sample_rate": 2e6,
        "gain":        30,
    },
    "3": {
        "name":        "GSM-900 (880-960 МГц)",
        "start":       880e6,
        "stop":        960e6,
        "step":        0.2e6,
        "sample_rate": 2.4e6,
        "gain":        40,
    },
    "4": {
        "name":        "GSM-1800 / 3G (1700-2100 МГц)",
        "start":       1700e6,
        "stop":        1766e6,
        "step":        0.5e6,
        "sample_rate": 2.4e6,
        "gain":        45,
    },
    "5": {
        "name":        "Погода / Метеоспутники NOAA",
        "start":       137e6,
        "stop":        138.5e6,
        "step":        0.05e6,
        "sample_rate": 1e6,
        "gain":        35,
    },
    "6": {
        "name":        "PMR/LPD/CB (400-470 МГц)",
        "start":       400e6,
        "stop":        470e6,
        "step":        0.025e6,
        "sample_rate": 2e6,
        "gain":        40,
    },
    "7": {
        "name":        "ADS-B самолёты (1090 МГц)",
        "start":       1089e6,
        "stop":        1091e6,
        "step":        0.05e6,
        "sample_rate": 2e6,
        "gain":        50,
    },
    "8": {
        "name":        "Полное сканирование",
        "start":       24e6,
        "stop":        1766e6,
        "step":        2e6,
        "sample_rate": 2.4e6,
        "gain":        40,
    },
    "9": {
        "name":        "Пользовательский диапазон",
        "start":       None,
        "stop":        None,
        "step":        None,
        "sample_rate": 2.4e6,
        "gain":        40,
    },
}
