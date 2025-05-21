from typing import Optional, Dict
from ares import AresBot
from ares.behaviors.macro import (
    AutoSupply, 
    BuildWorkers,
    GasBuildingController,
    MacroPlan, 
    ProductionController, 
    SpawnController,
)
from ares.behaviors.combat import CombatManeuver
from ares.behaviors.combat.group import AMoveGroup, StutterGroupForward
from ares.consts import UnitRole, UnitTreeQueryType
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

class MyBot(AresBot):
    def __init__(self, game_step_override: Optional[int] = None):
        super().__init__(game_step_override)
        self._assigned_marine_squad: bool = False
        # Initialize build cycle structure
        self._build_data = {
            'build_cycle': ['BioTank'],
            'chosen_opening': 'BioTank',
            'current_build': 'BioTank'
        }
        
    @property
    def marine_tank_comp(self) -> Dict[UnitID, Dict]:
        return {
            UnitID.MARINE: {"proportion": 0.7, "priority": 2},
            UnitID.MARAUDER: {"proportion": 0.2, "priority": 1}, 
            UnitID.SIEGETANK: {"proportion": 0.1, "priority": 0},
        }

    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)
        
        # Handle TechLab construction
        for factory in self.structures(UnitID.FACTORY).ready:
            if not factory.has_techlab and self.can_afford(UnitID.TECHLAB):
                await self.build(UnitID.TECHLAB, near=factory)
        
        # Handle Orbital Command upgrade
        for cc in self.townhalls(UnitID.COMMANDCENTER):
            if not cc.is_flying and self.can_afford(UnitID.ORBITALCOMMAND):
                cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)
        
        # Macro Plan
        macro_plan = MacroPlan()
        macro_plan.add(AutoSupply(self.start_location))
        macro_plan.add(BuildWorkers(to_count=60))
        macro_plan.add(GasBuildingController(to_count=4))
        macro_plan.add(SpawnController(self.marine_tank_comp))
        macro_plan.add(ProductionController(
            self.marine_tank_comp, self.start_location
        ))
        self.register_behavior(macro_plan)
        
        # Army Control
        if army := self.mediator.get_units_from_role(role=UnitRole.ATTACKING):
            if not self._assigned_marine_squad and self.time > 240.0:
                self._assign_marine_squad(army)
                self._assigned_marine_squad = True
            self._micro_army(army)

    def _assign_marine_squad(self, army: Units) -> None:
        """Assign marines to control group for better micro"""
        marines = [u for u in army if u.type_id == UnitID.MARINE]
        for marine in marines[:len(marines)//2]:  # Assign half marines
            self.mediator.assign_role(
                tag=marine.tag, 
                role=UnitRole.CONTROL_GROUP_ONE
            )

    def _micro_army(self, army: Units) -> None:
        """Basic army micro with stutter step and siege tank control"""
        target = self.enemy_start_locations[0]
        
        # Control marine squad
        if marine_squad := self.mediator.get_units_from_role(role=UnitRole.CONTROL_GROUP_ONE):
            squad_pos = marine_squad.center
            enemies = self.mediator.get_units_in_range(
                [squad_pos], 10, UnitTreeQueryType.EnemyGround
            )[0]
            
            maneuver = CombatManeuver()
            maneuver.add(StutterGroupForward(
                group=marine_squad,
                group_tags={u.tag for u in marine_squad},
                group_position=squad_pos,
                target=target,
                enemies=enemies
            ))
            maneuver.add(AMoveGroup(
                group=marine_squad,
                group_tags={u.tag for u in marine_squad},
                target=target
            ))
            self.register_behavior(maneuver)
        
        # AMove rest of army
        for unit in army:
            if unit.type_id == UnitID.SIEGETANK:
                unit.attack(target)

    async def on_start(self) -> None:
        # Initialize build data before parent class
        if hasattr(self, 'manager_hub') and hasattr(self.manager_hub, 'data_manager'):
            self.manager_hub.data_manager.build_cycle = self._build_data['build_cycle']
            self.manager_hub.data_manager.chosen_opening = self._build_data['chosen_opening']
            self.manager_hub.data_manager.current_build = self._build_data['current_build']
            
        await super(MyBot, self).on_start()
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
