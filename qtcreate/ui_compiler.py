
import os
import shutil

from PyQt5.uic import compileUiDir


for root, dirs, files in os.walk("./"):
    for dirname in dirs:
        compileUiDir(dirname)


shutil.move("./mainwin/mainwindow.py", "../ui/mainwindow.py")
