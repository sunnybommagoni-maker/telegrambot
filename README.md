---
title: SurfaceWBot
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# SurfaceWBot - Telegram Earning Platform

This is the automated Telegram bot for Surface Hub, hosted on Hugging Face Spaces for 24/7 uptime.

## Configuration
- **SDK**: Docker
- **Port**: 7860
- **Language**: Python 3.10

## How it works
The bot runs a polling task (python-telegram-bot) alongside a Flask health-check server to maintain persistence on free-tier cloud hosting.
