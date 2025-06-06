from typing import Optional

from ares import AresBot
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId


class MyBot(AresBot):
    def __init__(self, game_step_override: Optional[int] = None):
        """Initiate custom bot

        Parameters
        ----------
        game_step_override :
            If provided, set the game_step to this value regardless of how it was
            specified elsewhere
        """
        super().__init__(game_step_override)
        self.attack_launched: bool = False

    async def on_start(self) -> None:
        await super(MyBot, self).on_start()
        self.client.chat_send("MyBot ready!", team_only=False)

    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)

        await self.distribute_workers()

        cc = self.townhalls.ready.first if self.townhalls else None
        if not cc:
            return

        # train workers up to 22 per townhall
        if (
            self.supply_workers < self.townhalls.amount * 22
            and cc.is_idle
            and self.can_afford(UnitTypeId.SCV)
        ):
            cc.train(UnitTypeId.SCV)

        # build supply depots when running low
        if (
            self.supply_left < 5
            and not self.already_pending(UnitTypeId.SUPPLYDEPOT)
            and self.can_afford(UnitTypeId.SUPPLYDEPOT)
        ):
            await self.build(
                UnitTypeId.SUPPLYDEPOT,
                near=cc.position.towards(self.game_info.map_center, 4),
            )

        # build barracks when we have a supply depot
        if (
            self.structures(UnitTypeId.BARRACKS).amount < 3
            and self.can_afford(UnitTypeId.BARRACKS)
            and self.structures(UnitTypeId.SUPPLYDEPOT).ready
        ):
            await self.build(
                UnitTypeId.BARRACKS,
                near=cc.position.towards(self.game_info.map_center, 8),
            )

        # train marines
        for rax in self.structures(UnitTypeId.BARRACKS).ready.idle:
            if self.can_afford(UnitTypeId.MARINE):
                rax.train(UnitTypeId.MARINE)

        marines = self.units(UnitTypeId.MARINE)

        # attack once enough marines gathered
        if marines.amount >= 12 and not self.attack_launched:
            self.attack_launched = True
            marines.attack(self.enemy_start_locations[0])

        if self.attack_launched and marines.idle:
            marines.idle.attack(self.enemy_start_locations[0])

    """
    Can use `python-sc2` hooks as usual, but make a call the inherited method in the superclass
    Examples:
    """
    # async def on_start(self) -> None:
    #     await super(MyBot, self).on_start()
    #
    #     # on_start logic here ...
    #
    # async def on_end(self, game_result: Result) -> None:
    #     await super(MyBot, self).on_end(game_result)
    #
    #     # custom on_end logic here ...
    #
    # async def on_building_construction_complete(self, unit: Unit) -> None:
    #     await super(MyBot, self).on_building_construction_complete(unit)
    #
    #     # custom on_building_construction_complete logic here ...
    #
    # async def on_unit_created(self, unit: Unit) -> None:
    #     await super(MyBot, self).on_unit_created(unit)
    #
    #     # custom on_unit_created logic here ...
    #
    # async def on_unit_destroyed(self, unit_tag: int) -> None:
    #     await super(MyBot, self).on_unit_destroyed(unit_tag)
    #
    #     # custom on_unit_destroyed logic here ...
    #
    # async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float) -> None:
    #     await super(MyBot, self).on_unit_took_damage(unit, amount_damage_taken)
    #
    #     # custom on_unit_took_damage logic here ...
