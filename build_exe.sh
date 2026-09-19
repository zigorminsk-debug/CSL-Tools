#!/bin/bash
echo "=== CSL-Tools Build (Linux/Mac - для теста) ==="
pip3 install psutil requests pillow pyinstaller
rm -rf build dist CSL-Tools.spec
pyinstaller --onefile --windowed --name CSL-Tools main.py
echo "Готово: dist/CSL-Tools"
ls -lh dist/
