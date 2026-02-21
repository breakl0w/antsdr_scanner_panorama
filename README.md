# RTL-SDR RF Scanner v1.0

## Структура

```
rtl_scanner/
├── main.py        — точка входа, меню
├── config.py      — настройки, профили
├── device.py      — RTL-SDR через pyrtlsdr
├── scanner.py     — цикл сканирования (общий с ANTSDR)
├── identify.py    — идентификация сигналов (общий)
├── visualizer.py  — спектр + waterfall (общий)
└── rf_scans/      — CSV логи
```

## Установка

```bash
pip install pyrtlsdr pyqtgraph PyQt6 numpy pandas

# Udev правило чтобы не нужен был sudo:
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", GROUP="plugdev", MODE="0666"' \
  | sudo tee /etc/udev/rules.d/20-rtlsdr.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
# добавь себя в группу plugdev:
sudo usermod -aG plugdev $USER
```

## Запуск

```bash
cd rtl_scanner
python3 main.py
```

## Тюнинг (config.py)

| Параметр         | По умолчанию | Описание                              |
|------------------|--------------|---------------------------------------|
| RTL_DEVICE_INDEX | 0            | Индекс донгла (если несколько)        |
| THRESHOLD_DB     | 12.0         | dB над медианой для детекта           |
| FFT_AVG          | 4            | Усреднение FFT кадров                 |
| CONFIRM_REQUIRED | 2            | Подтверждений для засчитывания        |

## Коррекция частоты (ppm)

Все RTL-SDR доноглы уплывают по частоте. Определить уход:
```bash
rtl_test -p
```
Потом в device.py:
```python
self.sdr.freq_correction = 51  # твоё значение ppm
```

## Диапазон по тюнерам

| Тюнер    | Диапазон           |
|----------|--------------------|
| R820T/T2 | 24 МГц – 1766 МГц  |
| E4000    | 52 МГц – 2200 МГц  |
| FC0013   | 22 МГц – 948 МГц   |
