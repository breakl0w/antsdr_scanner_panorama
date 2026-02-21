# ================================================================
#  visualizer.py — pyqtgraph (OpenGL), быстрый waterfall
# ================================================================

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from collections import deque
import threading
import time

from config import FFT_SIZE, THRESHOLD_DB

pg.setConfigOptions(antialias=False, useOpenGL=True)


class Visualizer:
    HISTORY        = 200   # строк waterfall
    MAX_DETECTIONS = 200

    def __init__(self):
        self._lock       = threading.Lock()
        self._spectrum   = np.full(FFT_SIZE, -100.0, dtype=np.float32)
        self._freq_hz    = 0.0
        self._threshold  = -100.0
        self._detections = deque(maxlen=self.MAX_DETECTIONS)
        self._waterfall  = np.full((self.HISTORY, FFT_SIZE), -100.0, dtype=np.float32)
        self._max_hold   = np.full(FFT_SIZE, -120.0, dtype=np.float32)
        self._dirty      = False   # флаг — есть новые данные

    # ------------------------------------------------------------------
    # Вызывается из фонового потока (сканер)
    # ------------------------------------------------------------------
    def update(self, freq_hz: float, spectrum: np.ndarray):
        with self._lock:
            self._freq_hz   = freq_hz
            self._spectrum  = spectrum.astype(np.float32)
            self._threshold = float(np.median(spectrum) + THRESHOLD_DB)
            # Waterfall: сдвигаем вниз и вставляем новую строку сверху
            self._waterfall = np.roll(self._waterfall, 1, axis=0)
            self._waterfall[0, :] = self._spectrum
            self._max_hold  = np.maximum(self._max_hold, self._spectrum)
            self._dirty = True

    def add_detection(self, freq_mhz: float, power_db: float, sig_type: str):
        with self._lock:
            ts = time.strftime("%H:%M:%S")
            self._detections.appendleft(
                f"{ts}   {freq_mhz:>9.3f} МГц   {power_db:>6.1f} dBFS   {sig_type}"
            )
            self._dirty = True

    def reset_hold(self):
        with self._lock:
            self._max_hold = np.full(FFT_SIZE, -120.0, dtype=np.float32)

    # ------------------------------------------------------------------
    # Вызывается из ГЛАВНОГО потока — блокирующий
    # ------------------------------------------------------------------
    def show(self):
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

        win = QtWidgets.QMainWindow()
        win.setWindowTitle("ANTSDR E200 — RF Scanner")
        win.resize(1280, 800)
        win.setStyleSheet("background-color: #0d0d0d;")

        central = QtWidgets.QWidget()
        win.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)

        # ── Заголовок с частотой ──────────────────────────────────────
        self._freq_label = QtWidgets.QLabel("▶  — МГц")
        self._freq_label.setStyleSheet(
            "color: #00ff88; font-family: monospace; font-size: 13px; padding: 2px 6px;"
        )
        layout.addWidget(self._freq_label)

        # ── Спектр ───────────────────────────────────────────────────
        pw_spec = pg.PlotWidget(background="#0a0a0a")
        pw_spec.setLabel("left",   "dBFS", color="#888888")
        pw_spec.setLabel("bottom", "Bin",  color="#888888")
        pw_spec.setYRange(-120, 80)
        pw_spec.setXRange(0, FFT_SIZE - 1)
        pw_spec.showGrid(x=False, y=True, alpha=0.15)
        pw_spec.setMinimumHeight(220)

        self._curve_spec  = pw_spec.plot(pen=pg.mkPen("#00ff88", width=1))
        self._curve_hold  = pw_spec.plot(pen=pg.mkPen("#ff4444", width=1, style=QtCore.Qt.PenStyle.DashLine))
        self._curve_thr   = pw_spec.plot(pen=pg.mkPen("#ffaa00", width=1, style=QtCore.Qt.PenStyle.DotLine))
        layout.addWidget(pw_spec, stretch=3)

        # ── Waterfall (ImageItem — пиксельный, очень быстрый) ────────
        pw_wf = pg.PlotWidget(background="#0a0a0a")
        pw_wf.setLabel("left", "История", color="#888888")
        pw_wf.setYRange(0, self.HISTORY)
        pw_wf.setXRange(0, FFT_SIZE - 1)
        pw_wf.setMinimumHeight(220)

        self._wf_img = pg.ImageItem()
        pw_wf.addItem(self._wf_img)

        # Цветовая карта inferno
        cmap = pg.colormap.get("inferno")
        self._wf_lut = cmap.getLookupTable(start=0.0, stop=1.0, nPts=256)
        self._wf_img.setLookupTable(self._wf_lut)
        self._wf_img.setLevels([-100, 60])
        layout.addWidget(pw_wf, stretch=3)

        # ── Лог детектов ─────────────────────────────────────────────
        self._det_label = QtWidgets.QLabel("Обнаруженные сигналы")
        self._det_label.setStyleSheet(
            "color: #ffdd44; font-family: monospace; font-size: 10px; "
            "background: #0a0a0a; padding: 4px 6px; border: 1px solid #222;"
        )
        self._det_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        self._det_label.setMinimumHeight(100)
        layout.addWidget(self._det_label, stretch=2)

        # ── Таймер обновления (150 мс) ────────────────────────────────
        timer = QtCore.QTimer()
        timer.setInterval(150)

        def _refresh():
            if not self._dirty:
                return
            with self._lock:
                spec  = self._spectrum.copy()
                hold  = self._max_hold.copy()
                thr   = self._threshold
                wfall = self._waterfall.copy()
                freq  = self._freq_hz
                dets  = list(self._detections)[:12]
                self._dirty = False

            x = np.arange(FFT_SIZE, dtype=np.float32)
            self._curve_spec.setData(x, spec)
            self._curve_hold.setData(x, hold)
            self._curve_thr.setData(x, np.full(FFT_SIZE, thr, dtype=np.float32))

            # ImageItem ожидает (width, height) → транспонируем
            self._wf_img.setImage(wfall.T, autoLevels=False)

            self._freq_label.setText(f"▶  {freq/1e6:.3f} МГц")

            header = "  Время      Частота              Мощность    Тип\n" + "─" * 65
            body   = "\n".join(dets) if dets else "  (нет детектов)"
            self._det_label.setText(header + "\n" + body)

        timer.timeout.connect(_refresh)
        timer.start()

        win.show()
        app.exec()   # блокирует до закрытия окна
