# TgSpeechRecognition bot
Telegram bot for recognizing voice messages in public chats and private messages. The main purpose of this bot is recognizing big (several hours) audio files.

## Features:
- Can recognize and send as reply message with recognized text in chat or private message.
- It passes less than 10 seconds long messages.
- If long less than 50 seconds it send recognized text, if greater than 50 secs then write into text file and send it into chat.
- If it is big file, can write percentage of process.
- By default uses google engine, and optimized to divide file on 10 sec parts, but engine can be changed.
- Optional whitelist of user IDs to prevent unauthorized using

## Usage:
Add the bot into chat and open access to read all mesages, or just use PM. If the audio is caught then recognition process starts.

### Whitelist
Whitelist can be turned on optionally by creating python file near `speech_recog_bot.py` a `whitelist.py` with code like:
```
whitelist = [12345, 12346]
```

## Run
```
python speech_recog_bot.py "<your tg bot token>"
```