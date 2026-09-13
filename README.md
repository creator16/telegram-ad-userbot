# Telegram Ad Userbot

A local Pyrogram-based Telegram userbot for managing controlled advertising campaigns through Telegram Saved Messages.

## Features

- Personal Telegram account
- Saved Messages control panel
- SQLite persistent storage
- Archived-group synchronization
- Manual campaign creation
- Configurable target cooldown
- Configurable round cooldown
- Pause / resume / stop
- Campaign history
- Persistent campaign state

## Important

This project does not automatically join groups, archive groups, leave groups, or attempt to bypass Telegram anti-abuse systems.

Only groups that the user has manually joined and placed in Telegram Archive are eligible campaign targets.

## Requirements

Python 3.10+

## Installation

Clone the repository:

```bash
git clone <REPOSITORY_URL>
cd telegram-ad-userbot