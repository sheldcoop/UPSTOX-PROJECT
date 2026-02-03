# AI Assistant Setup Guide

This guide explains how to use the new AI functionalities powered by **Google Gemini** and **Telegram**.

## 1. Setup

### Google Gemini
The API Key has been configured in your `.env` file:
`GOOGLE_API_KEY=...`

### Telegram Bot
1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the instructions to create a bot.
3. specific the Bot Token provided by BotFather.
4. Update your `.env` file:
   ```bash
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

## 2. Running the Assistant

Run the following command in your terminal:

```bash
./scripts/start_ai_assistant.sh
```

Or manually:
```bash
python3 scripts/ai_assistant_bot.py
```

## 3. Features

The AI Assistant is read-only and can answer questions like:

*   "What are the top gainers today?"
*   "Show me my portfolio holdings."
*   "What is the price of RELIANCE?"
*   "Who is winning in the market, bulls or bears?" (Analyzing gainers/losers)

## 4. Architecture

*   **`scripts/ai_service.py`**: The core brain. It initializes Gemini and defines "Tools" (functions) that the AI can call to fetch real data from your backend.
*   **`scripts/ai_assistant_bot.py`**: The Telegram interface. It listens for messages and forwards them to the AI Service.
*   **`requirements.txt`**: Added `google-generativeai` and `python-telegram-bot`.

## 5. Troubleshooting

*   **Quota Exceeded**: The system uses `gemini-flash-latest`. If you hit rate limits, try upgrading your Google AI Studio plan or switching the model in `scripts/ai_service.py`.
*   **Bot Not Responding**: Ensure `TELEGRAM_BOT_TOKEN` is correct and the script is running in the terminal.
