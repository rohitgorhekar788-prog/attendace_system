@echo off
title Face Recognition Attendance System - Setup
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
python app.py
pause
