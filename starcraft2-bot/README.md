# StarCraft 2 Bot

This is a StarCraft 2 bot built using the Ares framework.

## Getting Started

1. Install the required dependencies:
   ```bash
   cd /workspace/aibots
   poetry install
   ```

2. Run the bot:
   ```bash
   cd /workspace/aibots/starcraft2-bot
   python run.py
   ```

## Bot Structure

- `bot/main.py`: The main bot class that inherits from `AresBot`
- `bot/__init__.py`: Package initialization
- `bot/production_manager.py`: Manages unit production
- `bot/unit_manager.py`: Manages unit behaviors
- `bot/terrain_manager.py`: Manages terrain-related information
- `run.py`: Entry point for running the bot

## Customization

To customize the bot, modify the `Starcraft2Bot` class in `bot/main.py`. You can add new behaviors, modify existing ones, or create entirely new ones.

## Documentation

For more information about the Ares framework, see the [Ares documentation](https://deepwiki.com/aressc2/ares-sc2).

For examples of bot implementations, see the [QueenBot repository](https://github.com/AresSC2/QueenBot).