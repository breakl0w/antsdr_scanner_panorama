#!/usr/bin/env python3
# ================================================================
#  main.py — точка входа
#  Архитектура: сканер в фоновом потоке, matplotlib в главном
# ================================================================

import threading
from config import SCAN_PROFILES
from scanner import Scanner


def show_menu() -> str:
    print("""
╔══════════════════════════════════════════════════════════════╗
║      ANTSDR E200  RF Scanner v4.0  —  libiio + matplotlib   ║
║      AD9361 | 70 МГц – 6 ГГц | подтверждённые детекты      ║
╚══════════════════════════════════════════════════════════════╝""")
    print("=" * 62)
    for k, p in SCAN_PROFILES.items():
        rng = (f"{p['start']/1e6:.0f} – {p['stop']/1e6:.0f} МГц"
               if p["start"] else "задаётся вручную")
        print(f"  {k}.  {p['name']:<38} {rng}")
    print("=" * 62)

    while True:
        choice = input(f"Профиль (1–{len(SCAN_PROFILES)}): ").strip()
        if choice in SCAN_PROFILES:
            return choice
        print("[!] Неверный выбор")


def get_custom(profile: dict) -> dict:
    print("\nПользовательский диапазон:")
    profile["start"]       = float(input("  Начальная частота (МГц): ")) * 1e6
    profile["stop"]        = float(input("  Конечная частота  (МГц): ")) * 1e6
    profile["step"]        = float(input("  Шаг (МГц): ")) * 1e6
    profile["sample_rate"] = float(input("  Sample rate (МГц, напр. 10): ")) * 1e6
    profile["gain"]        = int(input("  Gain dB (напр. 40): "))
    return profile


def main():
    choice  = show_menu()
    profile = dict(SCAN_PROFILES[choice])

    if profile["start"] is None:
        profile = get_custom(profile)

    try:
        ans = input("\nВизуализация спектра? (y/n, по умолчанию y): ").strip().lower()
    except KeyboardInterrupt:
        return
    visualize = (ans != "n")

    if visualize:
        from visualizer import Visualizer
        viz = Visualizer()
    else:
        viz = None

    sc = Scanner(viz=viz)

    # Сканер — в фоновый поток
    scan_thread = threading.Thread(target=sc.run, args=(profile,), daemon=True)
    scan_thread.start()

    if visualize:
        # matplotlib — в главном потоке (обязательно!)
        viz.show()
        # После закрытия окна останавливаем сканер
        sc.running = False

    scan_thread.join()


if __name__ == "__main__":
    main()
