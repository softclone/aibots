from typing import Optional

from ares import AresBot
from ares.behaviors.macro import Mining
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.unit import Unit

from bot.production_manager import ProductionManager
from bot.terrain_manager import TerrainManager
from bot.unit_manager import UnitManager

class Starcraft2Bot(AresBot):
    production_manager: ProductionManager
    unit_manager: UnitManager
    terrain_manager: TerrainManager

    def __init__(self, game_step_override: Optional[int] = None):
        """Initiate custom bot

        Parameters
        ----------
        game_step_override :
            If provided, set the game_step to this value regardless of how it was
            specified elsewhere
        """
        super().__init__(game_step_override)
        self.unselectable_worker_tags = set()
        self.sent_bm: bool = False

        # Initialize managers
        self.production_manager = ProductionManager()
        self.unit_manager = UnitManager()
        self.terrain_manager = TerrainManager()

    async def on_step(self, iteration: int) -> None:
        await super(Starcraft2Bot, self).on_step(iteration)

        # Register basic mining behavior
        self.register_behavior(Mining())

        # Update managers
        await self.terrain_manager.update(iteration)
        await self.unit_manager.update(iteration)
        await self.production_manager.update(iteration)

        # Example: Print a message when we have a certain number of workers
        if self.workers.amount >= 20 and not self.sent_bm:
            await self.chat_send("I have 20 workers now!")
            self.sent_bm = True

        # Add more bot logic here...