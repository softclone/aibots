from typing import Optional

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.units import Units as SC2Units # Renamed to avoid conflict with Ares Units if any

from ares import AresBot
from ares.consts import UnitRole
from ares.behaviors.combat.individual import StutterUnitBack, KeepUnitSafe


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
        self.scout_tag: Optional[int] = None
        self.visited_enemy_starts: set[Point2] = set()
        self.scouting_target_location: Optional[Point2] = None

    async def on_start(self) -> None:
        await super(MyBot, self).on_start()

        # Select an SCV for scouting
        if self.workers:
            scout_scv = self.workers.random_or_first
            self.scout_tag = scout_scv.tag
            self.manager_mediator.assign_role(tag=scout_scv.tag, role=UnitRole.SCOUT)
            print(f"SCV {scout_scv.tag} assigned as scout.")
        else:
            print("No SCVs available to assign as scout at on_start.")

    async def on_step(self, iteration: int) -> None:
        await super(MyBot, self).on_step(iteration)

        # Overall attack target
        overall_attack_target: Optional[Point2] = None
        if self.enemy_start_locations:
            overall_attack_target = self.enemy_start_locations[0]
        elif hasattr(self, 'main_base_ramp') and self.main_base_ramp and hasattr(self.main_base_ramp, 'top_center') and self.main_base_ramp.top_center:
            overall_attack_target = self.main_base_ramp.top_center
        elif self.start_location:
            overall_attack_target = self.start_location

        # Combat logic for ATTACKING units (Marines)
        attacking_marines: SC2Units = self.manager_mediator.get_units_from_role(role=UnitRole.ATTACKING, unit_type=UnitTypeId.MARINE)
        
        for marine in attacking_marines:
            # Find nearby enemy ground units (adjust sight_range as needed, e.g., marine.sight_range or fixed value)
            # Using python-sc2's enemy_units for simplicity here.
            # For performance on larger unit counts, ManagerMediator.get_units_in_range might be better.
            enemy_ground_units_in_sight: SC2Units = self.enemy_units.filter(lambda u: not u.is_flying).closer_than(marine.sight_range, marine.position)

            if enemy_ground_units_in_sight:
                closest_enemy = enemy_ground_units_in_sight.closest_to(marine)
                # Register StutterUnitBack behavior. AresBot's behavior_executioner will run it.
                self.register_behavior(StutterUnitBack(unit=marine, target=closest_enemy))
            else:
                # If no enemies nearby, and Marine is idle, continue attacking overall target
                if marine.is_idle and overall_attack_target:
                    marine.attack(overall_attack_target)
        
        # Scout logic
        if self.scout_tag:
            scout_unit = self.unit_tag_dict.get(self.scout_tag)
            if scout_unit:
                # Check if current scouting target is reached
                if self.scouting_target_location and scout_unit.distance_to(self.scouting_target_location) < 5:
                    self.visited_enemy_starts.add(self.scouting_target_location)
                    print(f"Scout reached {self.scouting_target_location}, added to visited.")
                    self.scouting_target_location = None # Reset target

                # If scout is idle or has no current target, find a new one
                if (not scout_unit.orders or not self.scouting_target_location) and self.enemy_start_locations:
                    for location in self.enemy_start_locations:
                        if location not in self.visited_enemy_starts and location != self.scouting_target_location:
                            scout_unit.move(location)
                            self.scouting_target_location = location
                            print(f"Scout {scout_unit.tag} ordered to scout {location}.")
                            break # Scout one new location at a time
            else:
                # Scout died or is missing
                print(f"Scout SCV {self.scout_tag} no longer exists.")
                self.scout_tag = None
                self.scouting_target_location = None # Reset target if scout dies

        # 1. Train SCVs
        scv_count: int = self.get_own_unit_count(UnitTypeId.SCV, include_pending=True)
        if scv_count < 20 and self.can_afford(UnitTypeId.SCV):
            for th in self.townhalls.idle:
                th.train(UnitTypeId.SCV)
                break  # train one at a time

        # 2. Build Supply Depots
        if (
            self.supply_left <= 3
            and self.supply_cap < 200
            and self.can_afford(UnitTypeId.SUPPLYDEPOT)
            and self.structures(UnitTypeId.SUPPLYDEPOT).not_ready.amount == 0
            and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0
        ):
            if placement_location := self.manager_mediator.request_building_placement(
                base_location=self.start_location,
                structure_type=UnitTypeId.SUPPLYDEPOT,
                reserve_placement=True,
            ):
                if worker := self.manager_mediator.select_worker(
                    target_position=placement_location, force_close=True
                ):
                    self.manager_mediator.assign_role(tag=worker.tag, role=UnitRole.BUILDING)
                    worker.build(UnitTypeId.SUPPLYDEPOT, placement_location)

        # 3. Build Barracks
        if (
            self.structures(UnitTypeId.SUPPLYDEPOT).amount > 0  # Need a depot first
            and self.structures(UnitTypeId.BARRACKS).amount == 0
            and self.already_pending(UnitTypeId.BARRACKS) == 0
            and self.can_afford(UnitTypeId.BARRACKS)
        ):
            if placement_location := self.manager_mediator.request_building_placement(
                base_location=self.start_location,
                structure_type=UnitTypeId.BARRACKS,
                reserve_placement=True,
            ):
                if worker := self.manager_mediator.select_worker(
                    target_position=placement_location, force_close=True
                ):
                    self.manager_mediator.assign_role(tag=worker.tag, role=UnitRole.BUILDING)
                    worker.build(UnitTypeId.BARRACKS, placement_location)

        # 4. Build Refinery
        if (
            self.structures(UnitTypeId.BARRACKS).ready.amount > 0  # Need a barracks first
            and self.structures(UnitTypeId.REFINERY).amount < 2 # Max 2 refineries for now
            and self.already_pending(UnitTypeId.REFINERY) == 0
            and self.can_afford(UnitTypeId.REFINERY)
        ):
            if vespene_geysers := self.vespene_geyser.closer_than(15.0, self.start_location):
                for vg in vespene_geysers:
                    # Check if there's already a refinery on this geyser
                    if not self.structures(UnitTypeId.REFINERY).closer_than(1.0, vg).exists:
                        if worker := self.manager_mediator.select_worker(
                            target_position=vg.position, force_close=True
                        ):
                            self.manager_mediator.assign_role(tag=worker.tag, role=UnitRole.BUILDING)
                            worker.build(UnitTypeId.REFINERY, vg)
                            break # build one at a time

        # 5. Train Marines
        if self.can_afford(UnitTypeId.MARINE):
            for br in self.structures(UnitTypeId.BARRACKS).idle:
                br.train(UnitTypeId.MARINE)
                break # train one at a time

    """
    Can use `python-sc2` hooks as usual, but make a call the inherited method in the superclass
    Examples:
    """
    # async def on_end(self, game_result: Result) -> None:
    #     await super(MyBot, self).on_end(game_result)
    #
    #     # custom on_end logic here ...
    #
    async def on_building_construction_complete(self, unit: Unit) -> None:
        await super(MyBot, self).on_building_construction_complete(unit)

        # ResourceManager will automatically assign workers to the new refinery
        # up to `workers_per_gas` (default 3)
        if unit.type_id == UnitTypeId.REFINERY:
            # Optional: Log or print that the refinery is complete and saturation will be handled.
            print(f"Refinery completed at {unit.position}, ResourceManager will saturate.")
            pass

    async def on_unit_created(self, unit: Unit) -> None:
        await super(MyBot, self).on_unit_created(unit)

        if unit.type_id == UnitTypeId.MARINE: # Or any other combat unit type
            self.manager_mediator.assign_role(tag=unit.tag, role=UnitRole.ATTACKING)
            print(f"Unit {unit.tag} ({unit.type_id.name}) created and assigned role ATTACKING.")
        # custom on_unit_created logic here ...

    async def on_unit_destroyed(self, unit_tag: int) -> None:
        await super(MyBot, self).on_unit_destroyed(unit_tag)

        if unit_tag == self.scout_tag:
            print(f"Scout SCV {unit_tag} was destroyed.")
            self.scout_tag = None
            self.scouting_target_location = None # Reset target
            # Optional: Assign a new scout here if desired

    async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float) -> None:
        await super(MyBot, self).on_unit_took_damage(unit, amount_damage_taken)

        if unit.type_id == UnitTypeId.MARINE and unit.health_percentage < 0.35:
            # Check if unit is already retreating (e.g. has DEFENDING role) to avoid re-issuing
            current_role = self.manager_mediator.get_role_for_tag(unit.tag)
            if current_role != UnitRole.DEFENDING:
                print(f"Marine {unit.tag} is low health ({unit.health_percentage:.2f}), attempting to retreat.")
                ground_grid = self.manager_mediator.get_ground_grid
                self.register_behavior(KeepUnitSafe(unit=unit, grid=ground_grid))
                # Change role to prevent other combat logic from interfering
                self.manager_mediator.assign_role(tag=unit.tag, role=UnitRole.DEFENDING)
        # custom on_unit_took_damage logic here ...
