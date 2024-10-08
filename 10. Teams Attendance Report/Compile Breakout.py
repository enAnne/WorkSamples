# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 11:53:48 2022

@author: eeann
"""

import os
os.chdir(r'C:\Users\eeann\OneDrive\Documents\GitHub\Python-Repo')
from Utils import readFilesInFolder
import pandas as pd
import pyautogui
import time
from time import sleep
from datetime import datetime
import shutil

folder = r'C:\Users\eeann\OneDrive - Subang Jaya Buddhist Association\Attendance/'
os.chdir(folder)

os.startfile(r"C:\Users\eeann\AppData\Local\Microsoft\Teams\current\Teams.exe")

clicks = ['Metta 1.png','Metta 2.png','Upekkha 1.png','Upekkha 2.png','Upekkha 3.png','Mudita 1.png','Mudita 2.png','Mudita 3.png','Karuna 1.png','Karuna 2.png','Karuna 3.png','Rahula.png','Orientation.png']

chat = pyautogui.locateCenterOnScreen("Chat.png", confidence=.95) 
pyautogui.moveTo(chat)
pyautogui.click()

for i in clicks:
    item = pyautogui.locateCenterOnScreen(i)
    pyautogui.moveTo(item)
    pyautogui.click()
    time.sleep(2)
    attendance = pyautogui.locateCenterOnScreen("Attendance.png", confidence=.95) 
    pyautogui.moveTo(attendance)
    pyautogui.click()
    time.sleep(1)

downloads = r'C:\Users\eeann\Downloads'
files = readFilesInFolder(downloads, extension='.csv', contains='meetingAttendanceReport')
for file in files:
    file_name = file.split('/')[-1]
    shutil.move(file, folder+file_name)
print("Moved", len(files), 'files.')

files = readFilesInFolder(folder, extension='.csv', contains='')
attendance_all = pd.DataFrame()
for file in files:
    class_name = file[file.find("(")+1:file.find(")")]
    attendance = pd.read_csv(file,encoding='UTF-16 LE',skiprows=7,sep='\t')    
    attendance['Class'] = class_name
    attendance = attendance[attendance['Full Name']!='Ee Ann Ng']
    attendance = attendance.groupby(['Class','Full Name'],as_index=False).agg({'Join Time':'min','Leave Time':'max'})
    attendance_all = pd.concat([attendance_all,attendance])

attendance_all.to_excel(folder+'All Attendance.xlsx',index=False)
print("Compiled attendance.")






