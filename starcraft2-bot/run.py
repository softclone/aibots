import sys
from typing import Optional

from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.player import Bot, Computer

from bot.main import Starcraft2Bot

def main(game_step_override: Optional[int] = None):
    """Main entry point for running the bot.

    Parameters
    ----------
    game_step_override :
        If provided, set the game_step to this value regardless of how it was
        specified elsewhere
    """
    # Create the bot
    bot = Bot(Race.Protoss, Starcraft2Bot(game_step_override))

    # Set up the computer opponent
    computer = Computer(Race.Random, Difficulty.Medium)

    # Run the game
    run_game([bot, computer], realtime=False)

if __name__ == "__main__":
    # Check if a game step override was provided
    game_step_override = None
    if len(sys.argv) > 1:
        try:
            game_step_override = int(sys.argv[1])
        except ValueError:
            print(f"Warning: Could not parse {sys.argv[1]} as an integer. Using default game_step.")
    main(game_step_override)