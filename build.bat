@echo off
pyinstaller main.py --noconfirm
mkdir C:\Users\thoma\Desktop\projects\Godzilla\dist\main\debug
copy C:\Users\thoma\Desktop\projects\Godzilla\config.json C:\Users\thoma\Desktop\projects\Godzilla\dist\main\config.json /y
copy C:\Users\thoma\Desktop\projects\Godzilla\config.json C:\Users\thoma\Desktop\projects\Godzilla\dist\main\config.json /y
