from typing import Optional

from ares import AresBot
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.individual import AMove, PathUnitToTarget
from ares.behaviors.macro import (
    AutoSupply,
    BuildWorkers,
    ExpansionController,
    GasBuildingController,
    MacroPlan,
    Mining,
    ProductionController,
    SpawnController,
)
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
import numpy as np

class BasicBot(AresBot):
    def __init__(self, game_step_override: Optional[int] = None):
        """Initialize the basic bot

        Parameters
        ----------
        game_step_override :
            If provided, set the game_step to this value regardless of how it was
            specified elsewhere
        """
        super().__init__(game_step_override)

    @property
    def army_comp(self) -> dict:
        """Define army composition based on race"""
        if self.race == Race.Protoss:
            return {
                UnitTypeId.STALKER: {"proportion": 0.6, "priority": 2},
                UnitTypeId.IMMORTAL: {"proportion": 0.3, "priority": 1},
                UnitTypeId.VOIDRAY: {"proportion": 0.1, "priority": 0},
            }
        elif self.race == Race.Terran:
            return {
                UnitTypeId.MARINE: {"proportion": 0.6, "priority": 2},
                UnitTypeId.MARAUDER: {"proportion": 0.3, "priority": 1},
                UnitTypeId.MEDIVAC: {"proportion": 0.1, "priority": 0},
            }
        else:
            return {
                UnitTypeId.ZERGLING: {"proportion": 0.6, "priority": 2},
                UnitTypeId.ROACH: {"proportion": 0.3, "priority": 1},
                UnitTypeId.HYDRALISK: {"proportion": 0.1, "priority": 0},
            }

    async def on_step(self, iteration: int) -> None:
        await super(BasicBot, self).on_step(iteration)

        # Set up basic macro behaviors
        self.register_behavior(Mining())
        macro_plan: MacroPlan = MacroPlan()
        macro_plan.add(AutoSupply(base_location=self.start_location))
        macro_plan.add(BuildWorkers(70))
        macro_plan.add(ExpansionController(to_count=3, max_pending=1))
        macro_plan.add(GasBuildingController(to_count=2, max_pending=1))

        if self.race != Race.Zerg:
            macro_plan.add(ProductionController(self.army_comp, self.start_location))

        macro_plan.add(SpawnController(self.army_comp))
        self.register_behavior(macro_plan)

        # Set up combat behaviors for army units
        army: list[Unit] = [u for u in self.units if u.type_id != self.worker_type]
        if army:
            grid: np.ndarray = self.mediator.get_ground_grid
            target: Point2 = self.enemy_start_locations[0]

            if self.enemy_units:
                target = self.enemy_units.closest_to(self.start_location).position
            elif self.enemy_structures:
                target = self.enemy_structures.closest_to(self.start_location).position

            for unit in army:
                maneuver: CombatManeuver = CombatManeuver()
                maneuver.add(PathUnitToTarget(unit=unit, grid=grid, target=target, success_at_distance=10.0))
                maneuver.add(AMove(unit=unit, target=target))
                self.register_behavior(maneuver)

    async def on_start(self) -> None:
        await super(BasicBot, self).on_start()
        # Any additional setup can go here