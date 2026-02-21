# ================================================================
#  device.py — подключение к ANTSDR E200 и замеры через libiio
#  Фиксы: BW = SR, диапазон 70MHz-6GHz
# ================================================================

import iio
import numpy as np
import time

from config import URI, FFT_SIZE, BUFFER_SIZE, MEASURE_PER_FREQ
from config import THRESHOLD_DB, BINS_ABOVE_MIN, CONFIRM_REQUIRED


class Device:
    def __init__(self):
        self.ctx   = None
        self.lo    = None
        self.buf   = None
        self._freq = None

    def connect(self, profile: dict):
        print(f"[*] Подключение к {URI}...")
        self.ctx = iio.Context(URI)

        rx  = self.ctx.find_device("cf-ad9361-lpc")
        phy = self.ctx.find_device("ad9361-phy")

        rx_chan = rx.find_channel("voltage0", False)
        rx_chan.enabled = True

        # Sample rate + BW для обоих каналов (I и Q)
        for ch_name in ["voltage0", "voltage1"]:
            ch = phy.find_channel(ch_name, False)
            if ch:
                try:
                    ch.attrs["sampling_frequency"].value = str(int(profile["sample_rate"]))
                except Exception as e:
                    print(f"[!] sampling_frequency ch {ch_name}: {e}")
                try:
                    # BW должен быть равен SR — иначе фильтр режет полосу
                    ch.attrs["rf_bandwidth"].value = str(int(profile["sample_rate"]))
                except Exception as e:
                    print(f"[!] rf_bandwidth ch {ch_name}: {e}")

        # Gain — manual, отключаем AGC
        try:
            ch = phy.find_channel("voltage0", False)
            ch.attrs["gain_control_mode"].value = "manual"
            ch.attrs["hardwaregain"].value = str(profile["gain"])
            actual_gain = ch.attrs["hardwaregain"].value
        except Exception as e:
            actual_gain = "?"
            print(f"[!] Gain не установлен: {e}")

        self.lo  = phy.find_channel("altvoltage0", True)
        self.buf = iio.Buffer(rx, BUFFER_SIZE, False)

        # Читаем реальный диапазон с устройства
        try:
            freq_range = self.lo.attrs["frequency_available"].value
        except Exception:
            freq_range = "70MHz-6GHz"

        print(f"[+] Подключено")
        print(f"    SR:    {profile['sample_rate']/1e6:.1f} МГц")
        print(f"    BW:    {profile['sample_rate']/1e6:.1f} МГц  (= SR, полная полоса)")
        print(f"    Gain:  {actual_gain} dB")
        print(f"    Диапазон устройства: {freq_range}")

    def tune(self, freq_hz: float, settle_s: float = 0.08):
        """Перестроить LO. Ограничиваем частоту диапазоном AD9361."""
        freq_hz = max(70e6, min(6000e6, freq_hz))
        if self._freq != freq_hz:
            self.lo.attrs["frequency"].value = str(int(freq_hz))
            time.sleep(settle_s)
            self._freq = freq_hz

    def get_spectrum(self) -> np.ndarray:
        """Одиночный FFT-срез, возвращает мощность в dBFS."""
        self.buf.refill()
        raw = np.frombuffer(self.buf.read(), dtype=np.int16)
        iq  = raw[::2].astype(np.float32) + 1j * raw[1::2].astype(np.float32)
        fft = np.fft.fftshift(np.fft.fft(iq, FFT_SIZE))
        return 20 * np.log10(np.abs(fft) + 1e-12)

    def measure(self, freq_hz: float):
        """
        MEASURE_PER_FREQ замеров на частоте.
        Возвращает (confirmations, avg_power_db, peak_freq_hz, last_spectrum).
        """
        self.tune(freq_hz)

        confirmations = 0
        powers        = []
        peak_offsets  = []
        last_spectrum = None

        for _ in range(MEASURE_PER_FREQ):
            power = self.get_spectrum()
            last_spectrum = power

            median    = np.median(power)
            threshold = median + THRESHOLD_DB
            bins_above = int(np.sum(power > threshold))

            if bins_above > BINS_ABOVE_MIN:
                confirmations += 1

            powers.append(float(np.mean(power)))

            peak_idx = int(np.argmax(power))
            freq_res = 20e6 / FFT_SIZE
            peak_offsets.append((peak_idx - FFT_SIZE // 2) * freq_res)

            time.sleep(0.03)

        avg_power = float(np.mean(powers))
        peak_freq = freq_hz + float(np.mean(peak_offsets))

        return confirmations, avg_power, peak_freq, last_spectrum

    def close(self):
        self.ctx = None
