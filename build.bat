pyinstaller ^
    --onedir ^
    --name "Moza Temp Monitor" ^
    --add-data "moza.ico":"."
    --contents-directory "Lib" ^
    --windowed ^
    --icon moza.ico ^
    start.py 