# ================================================================
#  scanner.py — цикл сканирования (запускается в фоновом потоке)
# ================================================================

import numpy as np
import pandas as pd
import time
import os
from datetime import datetime

from config import LOG_DIR, CONFIRM_REQUIRED
from device import Device
from identify import identify


class Scanner:
    def __init__(self, viz=None):
        self.device     = Device()
        self.viz        = viz
        self.detections = []
        self.log_path   = None
        self.running    = False

    def _save(self, row: dict):
        self.detections.append(row)
        pd.DataFrame(self.detections).to_csv(self.log_path, index=False)

    def run(self, profile: dict):
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = os.path.join(LOG_DIR, f"scan_{ts}.csv")

        self.device.connect(profile)

        freqs      = np.arange(profile["start"], profile["stop"] + profile["step"], profile["step"])
        total      = len(freqs)
        start_time = time.time()
        self.running = True

        print(f"\n[*] Сканирование: {profile['start']/1e6:.0f} – {profile['stop']/1e6:.0f} МГц")
        print(f"[*] Шагов: {total} | Лог: {self.log_path}")
        print("=" * 60)

        try:
            for i, freq in enumerate(freqs):
                if not self.running:
                    break

                elapsed = time.time() - start_time
                eta_str = "..."
                if i > 0:
                    eta = (elapsed / i) * (total - i)
                    eta_str = time.strftime("%H:%M:%S", time.gmtime(eta))

                print(f"\r[{i+1:>4}/{total}] {freq/1e6:>8.2f} МГц | "
                      f"Детектов: {len(self.detections):>3} | ETA: {eta_str}    ",
                      end="", flush=True)

                try:
                    confirms, avg_power, peak_freq, spectrum = self.device.measure(freq)
                except Exception as e:
                    print(f"\n[!] Ошибка {freq/1e6:.1f} МГц: {e}")
                    continue

                if self.viz:
                    self.viz.update(freq, spectrum)

                if confirms >= CONFIRM_REQUIRED:
                    sig_type = identify(peak_freq)
                    freq_mhz = round(freq / 1e6, 3)
                    peak_mhz = round(peak_freq / 1e6, 3)

                    print(f"\n\033[92m[+] СИГНАЛ: {freq_mhz:.3f} МГц "
                          f"(пик {peak_mhz:.3f} МГц) | "
                          f"{avg_power:.1f} dBFS | {sig_type}\033[0m")

                    if self.viz:
                        self.viz.add_detection(freq_mhz, avg_power, sig_type)

                    self._save({
                        "time":     datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "freq_mhz": freq_mhz,
                        "peak_mhz": peak_mhz,
                        "power_db": round(avg_power, 2),
                        "type":     sig_type,
                        "confirms": confirms,
                    })

        except KeyboardInterrupt:
            print("\n\n[!] Прервано")
        finally:
            self.running = False
            self.device.close()

        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"[+] Время: {time.strftime('%H:%M:%S', time.gmtime(total_time))}")
        print(f"[+] Детектов: {len(self.detections)}")
        if self.detections:
            import pandas as pd
            df = pd.DataFrame(self.detections)
            print(f"[+] Лог: {self.log_path}")
            print(df[["freq_mhz", "peak_mhz", "power_db", "type"]].to_string(index=False))
        print("=" * 60)
