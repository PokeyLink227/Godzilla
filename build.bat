@echo off
pyinstaller main.py --noconfirm
mkdir dist/main/debug
xcopy config.json dist/main
xcopy alert_sound.wav dist/main
