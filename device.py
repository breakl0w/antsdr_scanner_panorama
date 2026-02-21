# ================================================================
#  device.py — RTL-SDR через pyrtlsdr
# ================================================================

import numpy as np
import time
from rtlsdr import RtlSdr

from config import (RTL_DEVICE_INDEX, RTL_FREQ_MIN, RTL_FREQ_MAX,
                    FFT_SIZE, BUFFER_SIZE, MEASURE_PER_FREQ,
                    THRESHOLD_DB, BINS_ABOVE_MIN, FFT_AVG)


class Device:
    def __init__(self):
        self.sdr   = None
        self._freq = None

    def connect(self, profile: dict):
        print(f"[*] Открываем RTL-SDR (индекс {RTL_DEVICE_INDEX})...")

        try:
            self.sdr = RtlSdr(RTL_DEVICE_INDEX)
        except Exception as e:
            print(f"[!] Не удалось открыть RTL-SDR: {e}")
            print("[!] Проверь подключение и права (возможно нужен udev rule или sudo)")
            exit(1)

        # Ограничиваем частоты диапазоном тюнера
        start = max(profile["start"], RTL_FREQ_MIN)
        stop  = min(profile["stop"],  RTL_FREQ_MAX)
        if start > stop:
            print(f"[!] Диапазон {profile['start']/1e6:.0f}-{profile['stop']/1e6:.0f} МГц "
                  f"выходит за пределы RTL-SDR ({RTL_FREQ_MIN/1e6:.0f}-{RTL_FREQ_MAX/1e6:.0f} МГц)")
            exit(1)
        profile["start"] = start
        profile["stop"]  = stop

        # Sample rate — RTL-SDR поддерживает 225-300 кГц или 900 кГц - 3.2 МГц
        # Диапазон 300-900 кГц нестабилен — избегаем
        sr = profile["sample_rate"]
        if 300e3 < sr < 900e3:
            sr = 2.048e6
            print(f"[!] Sample rate скорректирован до {sr/1e6:.3f} МГц (300-900 кГц нестабильны)")
            profile["sample_rate"] = sr

        self.sdr.sample_rate = sr
        self.sdr.center_freq = int(profile["start"])

        # Gain — 0 = AGC, >0 = manual
        if profile["gain"] == 0:
            self.sdr.gain = "auto"
            actual_gain = "auto (AGC)"
        else:
            self.sdr.gain = profile["gain"]
            actual_gain = f"{self.sdr.gain} dB"

        # Коррекция частоты (ppm) — можно подтюнить под конкретный донгл
        self.sdr.freq_correction = 0

        print(f"[+] RTL-SDR подключён")
        print(f"    Тюнер:   {self.sdr.get_tuner_type()}")
        print(f"    SR:      {self.sdr.sample_rate/1e6:.3f} МГц")
        print(f"    Gain:    {actual_gain}")
        print(f"    Диапазон: {profile['start']/1e6:.1f} – {profile['stop']/1e6:.1f} МГц")
        print(f"    FFT avg: {FFT_AVG} кадров")

    def tune(self, freq_hz: float):
        freq_hz = max(RTL_FREQ_MIN, min(RTL_FREQ_MAX, freq_hz))
        if self._freq != freq_hz:
            self.sdr.center_freq = int(freq_hz)
            time.sleep(0.05)   # RTL-SDR перестраивается быстрее чем AD9361
            self._freq = freq_hz

    def get_spectrum(self) -> np.ndarray:
        """
        Усреднённый FFT-срез по FFT_AVG кадрам.
        Усреднение в линейной шкале (правильно математически).
        """
        accum = np.zeros(FFT_SIZE, dtype=np.float64)

        for _ in range(FFT_AVG):
            # RTL-SDR отдаёт complex64 напрямую
            samples = self.sdr.read_samples(BUFFER_SIZE // 2)
            fft = np.fft.fftshift(np.fft.fft(samples[:FFT_SIZE], FFT_SIZE))
            accum += np.abs(fft) ** 2

        avg_power = accum / FFT_AVG
        return 10 * np.log10(avg_power + 1e-12).astype(np.float32)

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

            median     = np.median(power)
            threshold  = median + THRESHOLD_DB
            bins_above = int(np.sum(power > threshold))

            if bins_above > BINS_ABOVE_MIN:
                confirmations += 1

            powers.append(float(np.mean(power)))

            peak_idx = int(np.argmax(power))
            freq_res = self.sdr.sample_rate / FFT_SIZE
            peak_offsets.append((peak_idx - FFT_SIZE // 2) * freq_res)

            time.sleep(0.02)

        avg_power = float(np.mean(powers))
        peak_freq = freq_hz + float(np.mean(peak_offsets))

        return confirmations, avg_power, peak_freq, last_spectrum

    def close(self):
        if self.sdr:
            self.sdr.close()
            self.sdr = None
