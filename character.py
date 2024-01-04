from collections import defaultdict
import random
from card_template import CardTemplate
from card_templates_list import CARD_TEMPLATES
from utils import basic_lane_animation, generate_unique_id, on_reveal_animation, product
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from lane import Lane
    from game_state import GameState

import logging

logger = logging.getLogger(__name__)


class Character:
    def __init__(self, template: CardTemplate, lane: 'Lane', owner_number: int, owner_username: str, id: str = None):
        if id is not None:
            self.id = id
        else:
            self.id = generate_unique_id()
            
        self.template = template
        self.current_health = template.health
        self.max_health = template.health
        self.current_attack = template.attack
        self.shackled_turns = 0
        self.has_attacked = False
        self.owner_number = owner_number
        self.owner_username = owner_username
        self.lane = lane
        self.new = True
        self.escaped_death = False
        self.did_on_reveal = False
        self.did_end_of_turn = False
        self.silenced = False
        self.shielded = False

    def is_defender(self):
        return self.has_ability('Defender')
    
    def is_attacker(self):
        return self.has_ability('Attacker') or self.lane.lane_reward.effect[0] == 'charactersHereFightAsAttackers'
    
    def has_ability(self, ability_name):
        return (not self.silenced) and any([ability_name == ability.name for ability in self.template.abilities])

    def number_of_ability(self, ability_name) -> int:
        ability = [ability for ability in self.template.abilities if ability.name == ability_name][0]
        assert ability.number is not None
        return ability.number

    def number_2_of_ability(self, ability_name) -> int:
        ability = [ability for ability in self.template.abilities if ability.name == ability_name][0]
        assert ability.number_2 is not None
        return ability.number_2
    
    def creature_type_of_ability(self, ability_name) -> str:
        ability = [ability for ability in self.template.abilities if ability.name == ability_name][0]
        assert ability.creature_type is not None
        return ability.creature_type

    def compute_damage_to_deal(self, damage_by_player: dict[int, int], combat_modification_auras: dict[int, defaultdict[str, int]], defending_character: Optional['Character'] = None, is_tower_attack: bool = False):
        multipliers = []
        if is_tower_attack and self.has_ability('DoubleTowerDamage'):
            multipliers.append(2)
        if self.current_attack > self.current_health:
            multipliers += [2] * (combat_modification_auras[self.owner_number].get('MoreStrengthMeansDoubleDamage') or 0)
        if defending_character is not None and defending_character.shackled_turns > 0 and self.has_ability('DealDoubleDamageAgainstShackled'):
            multipliers.append(2)

        multiplier = product(multipliers)
        extra_for_losing = self.number_of_ability('DealMoreDamageWhenLosing') if self.has_ability('DealMoreDamageWhenLosing') and damage_by_player[1 - self.owner_number] > damage_by_player[self.owner_number] else 0
        extra_for_shield = 0 if not self.shielded else combat_modification_auras[self.owner_number].get('ShieldedCharactersDealExtraDamage') or 0
        base_attack = self.current_health if self.has_ability('DealDamageEqualToCurrentHealth') or combat_modification_auras[self.owner_number]['FriendliesDealDamageEqualToCurrentHealth'] > 0 else self.current_attack
        damage_dealt = (base_attack + extra_for_losing + extra_for_shield) * multiplier
        return damage_dealt

    def deal_tower_damage(self, attacking_player: int, defending_characters: list['Character'], damage_by_player: dict[int, int], lane_number: int, combat_modification_auras: dict[int, defaultdict[str, int]], log: list[str], animations: list, game_state: 'GameState', suppress_hit_tower_bonus_attack_triggers: bool = False):
        damage_dealt = self.compute_damage_to_deal(damage_by_player, combat_modification_auras, is_tower_attack=True)
        damage_by_player[self.owner_number] += damage_dealt

        log.append(f"{self.owner_username}'s {self.template.name} dealt {damage_dealt} damage to the enemy player in Lane {lane_number + 1}.")

        try:
            attacking_character_array_index = [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id)
        except Exception:
            logger.warning('Attacking character not found')
            attacking_character_array_index = None

        animations.append({
                    "event_type": "TowerDamage",
                    'data': {
                        "lane": lane_number,
                        "acting_player": self.owner_number,
                        "from_character_index": attacking_character_array_index,
                    }, 
                    'game_state': game_state.to_json()})

        if self.has_ability('OnTowerAttackDealMassDamage'):
            self.add_basic_animation(animations, game_state)
            for character in defending_characters:
                character.sustain_damage(self.number_of_ability('OnTowerAttackDealMassDamage'), log, animations, game_state)
                log.append(f"{self.owner_username}'s {self.template.name} dealt 2 damage to {character.owner_username}'s {character.template.name} in Lane {lane_number + 1}. "
                            f"{character.template.name}'s health is now {character.current_health}.")
            self.on_trigger_hit_tower_ability(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        if self.has_ability('OnTowerAttackDrawCard'):
            game_state.draw_random_card(attacking_player)
            log.append(f"{self.owner_username}'s {self.template.name} drew a random card.")
            self.add_basic_animation(animations, game_state)
            self.on_trigger_hit_tower_ability(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        if self.has_ability('OnDamageTowerPumpTeam'):
            for character in self.lane.characters_by_player[self.owner_number]:
                if character.id != self.id:
                    character.current_attack += self.number_of_ability('OnDamageTowerPumpTeam')
                    character.current_health += self.number_2_of_ability('OnDamageTowerPumpTeam')
                    character.max_health += self.number_2_of_ability('OnDamageTowerPumpTeam')
                    log.append(f"{self.owner_username}'s {self.template.name} pumped {character.owner_username}'s {character.template.name}.")
            self.add_basic_animation(animations, game_state)
            self.on_trigger_hit_tower_ability(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        if self.has_ability('OnTowerDamageGainMana'):
            game_state.mana_by_player[self.owner_number] += 1
            log.append(f"{self.owner_username}'s {self.template.name} gained 1 mana.")
            self.add_basic_animation(animations, game_state)
            self.on_trigger_hit_tower_ability(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        if self.has_ability('HitTowerPumpSelf'):
            self.current_attack += self.number_of_ability('HitTowerPumpSelf')
            self.current_health += self.number_2_of_ability('HitTowerPumpSelf')
            self.max_health += self.number_2_of_ability('HitTowerPumpSelf')
            log.append(f"{self.owner_username}'s {self.template.name} pumped itself.")
            self.add_basic_animation(animations, game_state)
            self.on_trigger_hit_tower_ability(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        if self.has_ability('HitTowerDamageAllCharacters'):
            self.add_basic_animation(animations, game_state)
            for character in [*self.lane.characters_by_player[self.owner_number], *defending_characters]:
                if character.id != self.id:
                    character.sustain_damage(self.number_of_ability('HitTowerDamageAllCharacters'), log, animations, game_state)
                    log.append(f"{self.owner_username}'s {self.template.name} dealt 2 damage to {character.owner_username}'s {character.template.name} in Lane {lane_number + 1}. "
                                f"{character.template.name}'s health is now {character.current_health}.")
            self.on_trigger_hit_tower_ability(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        if self.has_ability('HitTowerOtherCharactersSwitchLanes'):
            if len(self.lane.characters_by_player[self.owner_number]) > 1:
                self.on_trigger_hit_tower_ability(log, animations, game_state)
                for character in self.lane.characters_by_player[self.owner_number]:
                    if character.id != self.id:
                        character.switch_lanes(log, animations, game_state)

        if self.has_ability('HitTowerGiveShield'):
            friendly_character = self.lane.get_random_friendly_character(self.owner_number, exclude_characters=lambda c: c.shielded or c.id == self.id)
            if friendly_character is not None:
                friendly_character.gain_shield(log, animations, game_state)
            self.on_trigger_hit_tower_ability(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        if self.has_ability('HitTowerShackle'):
            enemy_character = self.lane.get_random_enemy_character(self.owner_number, exclude_characters=lambda c: c.shackled_turns > 0)
            if enemy_character is not None:
                enemy_character.shackle(self, log, animations, game_state)
            self.on_trigger_hit_tower_ability(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        if self.has_ability('HitTowerDamageAllEnemiesEqualToDamage'):
            self.add_basic_animation(animations, game_state)
            for character in self.lane.characters_by_player[1 - self.owner_number]:
                character.sustain_damage(damage_dealt, log, animations, game_state)
            self.on_trigger_hit_tower_ability(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        self.lane.maybe_give_lane_reward(attacking_player, game_state, log, animations)


    def on_trigger_hit_tower_ability(self, log: list[str], animations: list, game_state: 'GameState', suppress_hit_tower_bonus_attack_triggers: bool = False):
        for character in self.lane.characters_by_player[self.owner_number]:
            if character.has_ability('OnTriggerHitTowerPump'):
                self.current_attack += character.number_of_ability('OnTriggerHitTowerPump')
                self.current_health += character.number_2_of_ability('OnTriggerHitTowerPump')
                self.max_health += character.number_2_of_ability('OnTriggerHitTowerPump')
                character.add_basic_animation(animations, game_state)
                log.append(f"{character.owner_username}'s {self.template.name} got +{character.number_of_ability('OnTriggerHitTowerPump')}/+{character.number_2_of_ability('OnTriggerHitTowerPump')} for hitting the enemy tower.")

            if (not suppress_hit_tower_bonus_attack_triggers) and character.has_ability('OnTriggerHitTowerBonusAttack'):
                character.add_basic_animation(animations, game_state)
                self.make_bonus_attack(log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=True)

    def attack(self, attacking_player: int, 
               damage_by_player: dict[int, int], 
               defending_characters: list['Character'], 
               lane_number: int,
               combat_modification_auras: dict[int, defaultdict[str, int]],               
               log: list[str],
               animations: list,
               game_state: 'GameState',
               do_not_set_has_attacked: bool = False,
               suppress_hit_tower_bonus_attack_triggers: bool = False):
        if not do_not_set_has_attacked:
            self.has_attacked = True
        defenders = [character for character in defending_characters if character.is_defender() and character.can_fight()]

        if len(defenders) == 0 and not self.is_attacker():
            self.deal_tower_damage(attacking_player, defending_characters, damage_by_player, lane_number, combat_modification_auras, log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)
        else:
            if len(defenders) == 0:
                if len(defending_characters) > 0:
                    target_character = random.choice(defending_characters)
                else:
                    target_character = None
            else:
                target_character = random.choice(defenders)
            if target_character is not None:
                self.fight(target_character, lane_number, combat_modification_auras, log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)
            else:
                self.deal_tower_damage(attacking_player, defending_characters, damage_by_player, lane_number, combat_modification_auras, log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        if self.exists():
            if self.has_ability('SwitchLanesAfterAttacking'):
                self.switch_lanes(log, animations, game_state)

            if self.has_ability('OnAttackDoubleAttack'):
                self.current_attack *= 2

    def get_damage_to_deal_in_punch(self, defending_character: 'Character', lane_number: int, combat_modification_auras: dict[int, defaultdict[str, int]], log: list[str], animations: list, game_state: 'GameState') -> int:
        if self.shackled_turns > 0 and defending_character.has_ability('InvincibilityAgainstShackled'):
            return 0
        elif self.is_attacker() and (combat_modification_auras[0]['AttackersDontDealDamage'] > 0 or combat_modification_auras[1]['AttackersDontDealDamage'] > 0):
            return 0
        elif self.has_ability('DoNotDamageEnemyCharacters'):
            return 0        
        
        damage_to_deal = self.compute_damage_to_deal(self.lane.damage_by_player, combat_modification_auras, defending_character=defending_character)
        
        if self.has_ability('Deathtouch') and damage_to_deal > 0:
            return defending_character.current_health
        elif defending_character.is_defender() and self.has_ability('DeathtouchAgainstDefenders') and damage_to_deal > 0:
            return defending_character.current_health
        else:
            return damage_to_deal

    def exists(self):
        return self.id in [c.id for c in self.lane.characters_by_player[self.owner_number]]

    def fight(self, defending_character: 'Character', lane_number: int, combat_modification_auras: dict[int, defaultdict[str, int]], log: list[str], animations: list, game_state: 'GameState', friendly: bool = False, do_not_attack_tower: bool = False, suppress_hit_tower_bonus_attack_triggers: bool = False):
        from_character_index = [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id)
        to_character_index = [c.id for c in self.lane.characters_by_player[self.owner_number if friendly else 1 - self.owner_number]].index(defending_character.id)
        attacker_damage_to_deal = self.get_damage_to_deal_in_punch(defending_character, lane_number, combat_modification_auras, log, animations, game_state)
        defender_damage_to_deal = (0 
                                   if (self.has_ability('InvincibilityWhileAttacking') 
                                       or (self.is_attacker() and combat_modification_auras[self.owner_number].get('FriendlyAttackersAreInvincibleWhileAttacking'))) 
                                   else defending_character.get_damage_to_deal_in_punch(self, lane_number, combat_modification_auras, log, animations, game_state))

        fight_animations = []

        defending_character.sustain_damage(attacker_damage_to_deal, log, fight_animations, game_state, suppress_trigger=True)
        self.sustain_damage(defender_damage_to_deal, log, fight_animations, game_state, suppress_trigger=True)

        animations.append({
            "event_type": "FriendlyAttack" if friendly else "CharacterAttack",
            "data": {
                "lane": lane_number,
                "acting_player": self.owner_number,
                "from_character_index": from_character_index,
                "to_character_index": to_character_index,
            },
            "game_state": game_state.to_json(),
        })

        animations.extend(fight_animations)

        if self.is_attacker() and not do_not_attack_tower and self.has_ability('Twinstrike'):
            self.deal_tower_damage(self.owner_number, self.lane.characters_by_player[defending_character.owner_number], self.lane.damage_by_player, lane_number, combat_modification_auras, log, animations, game_state, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

        self.lane.process_dying_characters(log, animations, game_state)

        if self.has_ability('OnDamageCharacterSilenceIt') and attacker_damage_to_deal > 0:
            defending_character.silence(self, log, animations, game_state, do_not_animate=True)
        if defending_character.has_ability('OnDamageCharacterSilenceIt') and defender_damage_to_deal > 0:
            self.silence(defending_character, log, animations, game_state, do_not_animate=True)
        if defender_damage_to_deal > 0 and self.current_health > 0:
            self.do_survive_damage_triggers(log, animations, game_state)
        if attacker_damage_to_deal > 0 and defending_character.current_health > 0:
            defending_character.do_survive_damage_triggers(log, animations, game_state)
        if not defending_character.exists():
            self.do_kill_enemy_triggers(defending_character, log, animations, game_state)
        if not self.exists():
            defending_character.do_kill_enemy_triggers(self, log, animations, game_state)

    def do_kill_enemy_triggers(self, defending_character: 'Character', log: list[str], animations: list, game_state: 'GameState'):
        if self.has_ability('KillEnemySummonNyla'):
            if len(self.lane.characters_by_player[self.owner_number]) < 4 and not any([character.template.name == 'Nyla' for character in self.lane.characters_by_player[self.owner_number]]):
                self.add_basic_animation(animations, game_state)
                nyla_character = Character(CARD_TEMPLATES['Nyla'], self.lane, self.owner_number, game_state.usernames_by_player[self.owner_number])
                self.lane.characters_by_player[self.owner_number].append(nyla_character)
                nyla_character.do_all_on_reveal(log, animations, game_state)
            self.on_trigger_kill_enemy_ability(log, animations, game_state)

        if self.has_ability('OnKillBuffHealth'):
            self.current_attack += self.number_of_ability('OnKillBuffHealth')
            self.current_health += self.number_2_of_ability('OnKillBuffHealth')
            self.max_health += self.number_2_of_ability('OnKillBuffHealth')
            self.add_basic_animation(animations, game_state)

            self.on_trigger_kill_enemy_ability(log, animations, game_state)

        if self.has_ability('KillEnemyAttackAgain'):
            self.on_trigger_kill_enemy_ability(log, animations, game_state)

            if self.exists():
                self.make_bonus_attack(log, animations, game_state)
                self.lane.process_dying_characters(log, animations, game_state)
        
        if self.has_ability('KillEnemyGainShield'):
            self.gain_shield(log, animations, game_state)
            self.add_basic_animation(animations, game_state)

            self.on_trigger_kill_enemy_ability(log, animations, game_state)

    def on_trigger_kill_enemy_ability(self, log: list[str], animations: list, game_state: 'GameState'):
        for character in self.lane.characters_by_player[self.owner_number]:
            if character.has_ability('OnTriggerKillEnemyHealAndPumpSelf'):
                self.fully_heal()
                character.current_attack += character.number_of_ability('OnTriggerKillEnemyHealAndPumpSelf')
                character.current_health += character.number_2_of_ability('OnTriggerKillEnemyHealAndPumpSelf')
                character.max_health += character.number_2_of_ability('OnTriggerKillEnemyHealAndPumpSelf')
                character.add_basic_animation(animations, game_state)
                log.append(f"{character.owner_username}'s {character.template.name} got +{character.number_of_ability('OnTriggerKillEnemyHealAndPumpSelf')}/+{character.number_2_of_ability('OnTriggerKillEnemyHealAndPumpSelf')} for killing an enemy.")

            if character.has_ability('OnTriggerKillEnemyBonusAttack'):
                character.add_basic_animation(animations, game_state)
                character.make_bonus_attack(log, animations, game_state)

    def gain_shield(self, log: list[str], animations: list, game_state: 'GameState'):
        if not self.shielded:
            self.shielded = True
            self.on_trigger_gain_shield(log, animations, game_state)

    def break_shield(self, log: list[str], animations: list, game_state: 'GameState'):
        if self.shielded:
            self.shielded = False
            self.on_trigger_break_shield(log, animations, game_state)

    def on_trigger_gain_shield(self, log: list[str], animations: list, game_state: 'GameState'):
        for character in self.lane.characters_by_player[self.owner_number]:
            if character.has_ability('PumpOnGainShield'):
                self.current_attack += character.number_of_ability('PumpOnGainShield')
                self.current_health += character.number_2_of_ability('PumpOnGainShield')
                self.max_health += character.number_2_of_ability('PumpOnGainShield')
                character.add_basic_animation(animations, game_state)

    def on_trigger_break_shield(self, log: list[str], animations: list, game_state: 'GameState'):
        for character in self.lane.characters_by_player[self.owner_number]:
            if character.has_ability('OnShieldBreakPumpSelf'):
                character.current_attack += character.number_of_ability('OnShieldBreakPumpSelf')
                character.current_health += character.number_2_of_ability('OnShieldBreakPumpSelf')
                character.max_health += character.number_2_of_ability('OnShieldBreakPumpSelf')
                character.add_basic_animation(animations, game_state)

    def sustain_damage(self, damage: int, log: list[str], animations: list, game_state: 'GameState', suppress_trigger: bool = False):
        if damage <= 0:
            return
        
        if self.shielded:
            self.break_shield(log, animations, game_state)
            return
            
        self.current_health -= damage

        if suppress_trigger:
            return

        if self.current_health > 0:
            self.do_survive_damage_triggers(log, animations, game_state)

    def do_survive_damage_triggers(self, log: list[str], animations: list, game_state: 'GameState'):
        if self.has_ability('OnSurviveDamagePump'):
            self.current_attack += self.number_of_ability('OnSurviveDamagePump')
            self.current_health += self.number_2_of_ability('OnSurviveDamagePump')
            self.max_health += self.number_2_of_ability('OnSurviveDamagePump')
            self.add_basic_animation(animations, game_state)
            log.append(f"{self.owner_username}'s {self.template.name} got +{self.number_of_ability('OnSurviveDamagePump')}/+{self.number_2_of_ability('OnSurviveDamagePump')} for surviving damage.")
            self.on_trigger_survive_ability(log, animations, game_state)

        if self.has_ability('OnSurviveDrawCard'):
            game_state.draw_random_card(self.owner_number)
            self.add_basic_animation(animations, game_state)
            log.append(f"{self.owner_username}'s {self.template.name} drew a random card.")
            self.on_trigger_survive_ability(log, animations, game_state)
        
        if self.has_ability('OnSurviveGainMana'):
            game_state.mana_by_player[self.owner_number] += 1
            self.add_basic_animation(animations, game_state)
            log.append(f"{self.owner_username}'s {self.template.name} gained 1 mana.")
            self.on_trigger_survive_ability(log, animations, game_state)

        if self.has_ability('SurviveSwitchLanes'):
            self.on_trigger_survive_ability(log, animations, game_state)
            self.switch_lanes(log, animations, game_state)        

        if self.has_ability('SurvivePumpFriendlyAttackers'):
            for character in self.lane.characters_by_player[self.owner_number]:
                if character.is_attacker():
                    character.current_attack += self.number_of_ability('SurvivePumpFriendlyAttackers')
                    character.current_health += self.number_2_of_ability('SurvivePumpFriendlyAttackers')
                    character.max_health += self.number_2_of_ability('SurvivePumpFriendlyAttackers')
            self.add_basic_animation(animations, game_state)                    
            self.on_trigger_survive_ability(log, animations, game_state)                    

    def on_trigger_survive_ability(self, log: list[str], animations: list, game_state: 'GameState'):
        for character in self.lane.characters_by_player[self.owner_number]:
            if character.has_ability('OnTriggerSurvivePumpSelf'):
                character.current_attack += character.number_of_ability('OnTriggerSurvivePumpSelf')
                character.current_health += character.number_2_of_ability('OnTriggerSurvivePumpSelf')
                character.max_health += character.number_2_of_ability('OnTriggerSurvivePumpSelf')
                character.add_basic_animation(animations, game_state)
                log.append(f"{character.owner_username}'s {character.template.name} got +{character.number_of_ability('OnTriggerSurvivePumpSelf')}/+{character.number_2_of_ability('OnTriggerSurvivePumpSelf')} for {self.owner_username}'s {self.template.name} surviving damage.")
            if character.has_ability('OnTriggerSurvivePump'):
                self.current_attack += character.number_of_ability('OnTriggerSurvivePump')
                self.current_health += character.number_2_of_ability('OnTriggerSurvivePump')
                self.max_health += character.number_2_of_ability('OnTriggerSurvivePump')
                character.add_basic_animation(animations, game_state)
                log.append(f"{self.owner_username}'s {self.template.name} got +{character.number_of_ability('OnTriggerSurvivePump')}/+{character.number_2_of_ability('OnTriggerSurvivePump')} for surviving damage.")

    def can_fight(self):
        return self.current_health > 0

    def can_attack(self, combat_modification_auras: dict[int, defaultdict[str, int]], ignore_has_attacked: bool = False):
        return (self.can_fight() and (not self.has_attacked or ignore_has_attacked) and self.shackled_turns == 0 
                # Redundant or clause is for performance reasons
                and (self.current_attack > 0 or self.compute_damage_to_deal(self.lane.damage_by_player, combat_modification_auras) > 0))

    def switch_lanes(self, log: list[str], animations: list, game_state: 'GameState', lane_number: Optional[int] = None, and_fully_heal_if_switching: bool = False) -> bool:
        if self.has_ability('CannotSwitchLanes'):
            return False
        
        original_spot_array_index = [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id)
        original_lane_number = self.lane.lane_number

        if lane_number is None:
            target_lane = game_state.find_random_empty_slot_in_other_lane(self.lane.lane_number, self.owner_number)
        else:
            target_lane = game_state.lanes[lane_number]
            if len(target_lane.characters_by_player[self.owner_number]) >= 4:
                return False

        if target_lane is None:
            return False

        self.lane.characters_by_player[self.owner_number] = [character for character in self.lane.characters_by_player[self.owner_number] if character.id != self.id]
        if and_fully_heal_if_switching:
            self.fully_heal()
        if self.current_health <= 0:
            return False

        target_lane.characters_by_player[self.owner_number].append(self)
        self.lane = target_lane

        animations.append(
            {
                "event_type": "CharacterSwitchLanes",
                "data": {
                    "acting_player": self.owner_number,
                    "from_character_index": original_spot_array_index,
                    "to_character_index": [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id),
                    "lane": original_lane_number,
                    "to_lane": self.lane.lane_number,
                },
                "game_state": game_state.to_json(),
            }
        )

        self.has_attacked = False

        # pump friendly characters with CharacterMovesHerePumps ability
        for character in target_lane.characters_by_player[self.owner_number]:
            if character.has_ability('CharacterMovesHerePumps') and character.id != self.id:
                character.current_attack += character.number_of_ability('CharacterMovesHerePumps')
                character.current_health += character.number_2_of_ability('CharacterMovesHerePumps')
                character.max_health += character.number_2_of_ability('CharacterMovesHerePumps')

            if character.has_ability('CharacterMovesHereThatCharacterPumps') and character.id != self.id:
                self.current_attack += character.number_of_ability('CharacterMovesHereThatCharacterPumps')
                self.current_health += character.number_2_of_ability('CharacterMovesHereThatCharacterPumps')
                self.max_health += character.number_2_of_ability('CharacterMovesHereThatCharacterPumps')

            if character.has_ability('OnCharacterMoveHereMakeSpirit') and character.id != self.id:
                lane_to_spawn_in = game_state.find_random_empty_slot_in_other_lane(self.lane.lane_number, self.owner_number)
                if lane_to_spawn_in is not None:
                    character = Character(CARD_TEMPLATES['Spirit'], lane_to_spawn_in, self.owner_number, game_state.usernames_by_player[self.owner_number])
                    lane_to_spawn_in.characters_by_player[self.owner_number].append(character)
                    character.do_all_on_reveal(log, animations, game_state)
                
            if character.has_ability('OnCharacterMoveHereShackle') and character.id != self.id:
                random_enemy_character = self.lane.get_random_enemy_character(self.owner_number, exclude_characters=lambda c: c.shackled_turns > 0)
                if random_enemy_character is not None:
                    random_enemy_character.shackle(character, log, animations, game_state)

        return True
    

    def fully_heal(self):
        if self.current_health == self.max_health:
            return
        self.current_health = self.max_health

        # pump friendly characters with the PumpOnFriendlyHeal ability
        for character in self.lane.characters_by_player[self.owner_number]:
            if character.has_ability('PumpOnFriendlyHeal'):
                if character.id != self.id:
                    self.current_attack += character.number_of_ability('PumpOnFriendlyHeal')
                    self.current_health += character.number_2_of_ability('PumpOnFriendlyHeal')
                    self.max_health += character.number_2_of_ability('PumpOnFriendlyHeal')

            if character.has_ability('OnFriendlyHealPumpMyself'):
                if character.id != self.id:
                    character.current_attack += character.number_of_ability('OnFriendlyHealPumpMyself')
                    character.current_health += character.number_2_of_ability('OnFriendlyHealPumpMyself')
                    character.max_health += character.number_2_of_ability('OnFriendlyHealPumpMyself')


    def roll_turn(self, log: list[str], animations: list, game_state: 'GameState'):
        self.new = False

        if self.shackled_turns > 0:
            log.append(f"{self.owner_username}'s {self.template.name} is shackled for {self.shackled_turns} more turns.")
            self.shackled_turns -= 1


    def do_end_of_turn(self, log: list[str], animations: list, game_state: 'GameState'):
        if self.did_end_of_turn:
            return
        if self.has_ability('EndOfTurnFullHeal'):
            self.fully_heal()
            self.add_basic_animation(animations, game_state)
        
        if self.has_ability('EndOfTurnFullHealForAllFriendlies'):
            for character in self.lane.characters_by_player[self.owner_number]:
                if character.id != self.id:
                    character.fully_heal()
            self.add_basic_animation(animations, game_state)

        if self.has_ability('SwitchLanesAtEndOfTurn'):
            self.switch_lanes(log, animations, game_state)

        self.has_attacked = False
        self.did_end_of_turn = True


    def silence(self, silencing_character: 'Character', log: list[str], animations: list, game_state: 'GameState', do_not_animate: bool = False):
        self.silenced = True
        self.current_attack = self.template.attack
        self.current_health = min(self.template.health, self.current_health)
        self.max_health = self.template.health

        shield_animations = []

        self.break_shield(log, shield_animations, game_state)

        log.append(f"{silencing_character.owner_username}'s {silencing_character.template.name} silenced {self.owner_username}'s {self.template.name}.")
        if not do_not_animate:
            animations.append({
                "event_type": "CharacterSilence",
                "data": {
                    "lane": self.lane.lane_number,
                    "acting_player": 1 - self.owner_number,
                    "from_character_index": [c.id for c in self.lane.characters_by_player[1 - self.owner_number]].index(silencing_character.id),
                    "to_character_index": [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id),
                },
                "game_state": game_state.to_json(),
            })

        animations.extend(shield_animations)


    def shackle(self, shackling_character: 'Character', log: list[str], animations: list, game_state: 'GameState', do_not_animate: bool = False):
        num_enemy_characters_that_increase_shackled_turns = len([character for character in self.lane.characters_by_player[1 - self.owner_number] if character.has_ability('ShacklesLastExtraTurn')])
        total_damage_from_shackles = sum([character.number_of_ability('ShacklesDealDamage') for character in self.lane.characters_by_player[1 - self.owner_number] if character.has_ability('ShacklesDealDamage')])
        cards_drawn_from_shackles = len([character for character in self.lane.characters_by_player[1 - self.owner_number] if character.has_ability('OnShackleDrawCard')])

        self.shackled_turns += 1 + num_enemy_characters_that_increase_shackled_turns
        self.sustain_damage(total_damage_from_shackles, log, animations, game_state)

        for _ in range(cards_drawn_from_shackles):
            game_state.draw_random_card(1 - self.owner_number)

        log.append(f"{shackling_character.owner_username}'s {shackling_character.template.name} shackled {self.owner_username}'s {self.template.name}.")
        if not do_not_animate:
            animations.append({
                "event_type": "CharacterShackle",
                "data": {
                    "lane": self.lane.lane_number,
                    "acting_player": 1 - self.owner_number,
                    "from_character_index": [c.id for c in self.lane.characters_by_player[1 - self.owner_number]].index(shackling_character.id),
                    "to_character_index": [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id),
                },
                "game_state": game_state.to_json(),                
            })

        for character in self.lane.characters_by_player[1 - self.owner_number]:
            if character.has_ability('OnShacklePumpSelf'):
                character.current_attack += character.number_of_ability('OnShacklePumpSelf')
                character.current_health += character.number_2_of_ability('OnShacklePumpSelf')
                character.max_health += character.number_2_of_ability('OnShacklePumpSelf')
                character.add_basic_animation(animations, game_state)

        if total_damage_from_shackles > 0:
            self.lane.process_dying_characters(log, animations, game_state)
            

    def do_all_on_reveal(self, log: list[str], animations: list, game_state: 'GameState'):
        self.do_very_early_on_reveal(log, animations, game_state)
        self.do_early_on_reveal(log, animations, game_state)
        self.do_regular_on_reveal(log, animations, game_state)
        self.do_late_on_reveal(log, animations, game_state)
        self.did_on_reveal = True

    def make_bonus_attack(self, log: list[str], animations: list, game_state: 'GameState', suppress_hit_tower_bonus_attack_triggers: bool = False):
        if self.exists():
            combat_modification_auras = self.lane.compute_combat_modification_auras()
            if self.can_attack(combat_modification_auras, ignore_has_attacked=True):
                defending_characters = [character for character in self.lane.characters_by_player[1 - self.owner_number] if character.can_fight()]
                self.attack(self.owner_number, self.lane.damage_by_player, defending_characters, self.lane.lane_number, combat_modification_auras, log, animations, game_state, do_not_set_has_attacked=True, suppress_hit_tower_bonus_attack_triggers=suppress_hit_tower_bonus_attack_triggers)

    def do_very_early_on_reveal(self, log: list[str], animations: list, game_state: 'GameState'):
        if self.did_on_reveal:
            return

        attack_buffs = [character.number_of_ability('PumpCharactersPlayedHere') for character in self.lane.characters_by_player[self.owner_number] if character.has_ability('PumpCharactersPlayedHere') and character.id != self.id]
        defense_buffs = [character.number_2_of_ability('PumpCharactersPlayedHere') for character in self.lane.characters_by_player[self.owner_number] if character.has_ability('PumpCharactersPlayedHere') and character.id != self.id]
        element_specific_attack_buffs = [character.number_of_ability('PumpFriendlyCharactersOfElementPlayedHere') for character in self.lane.characters_by_player[self.owner_number] 
                                            if (character.has_ability('PumpFriendlyCharactersOfElementPlayedHere') and (character.creature_type_of_ability('PumpFriendlyCharactersOfElementPlayedHere') in self.template.creature_types or 'Avatar' in self.template.creature_types)) and character.id != self.id]
        element_specific_defense_buffs = [character.number_2_of_ability('PumpFriendlyCharactersOfElementPlayedHere') for character in self.lane.characters_by_player[self.owner_number] 
                                            if (character.has_ability('PumpFriendlyCharactersOfElementPlayedHere') and (character.creature_type_of_ability('PumpFriendlyCharactersOfElementPlayedHere') in self.template.creature_types or 'Avatar' in self.template.creature_types)) and character.id != self.id]
        
        lane_attack_buff = self.lane.lane_reward.effect[1] if self.lane.lane_reward is not None and self.lane.lane_reward.effect[0] == 'pumpAllCharactersPlayedHere' else 0
        lane_defense_buff = self.lane.lane_reward.effect[2] if self.lane.lane_reward is not None and self.lane.lane_reward.effect[0] == 'pumpAllCharactersPlayedHere' else 0

        self.current_attack += sum(attack_buffs) + sum(element_specific_attack_buffs) + lane_attack_buff  # type: ignore
        self.current_health += sum(defense_buffs) + sum(element_specific_defense_buffs) + lane_defense_buff  # type: ignore
        self.current_health = max(self.current_health, 1)
        self.max_health += sum(defense_buffs) + sum(element_specific_defense_buffs) + lane_defense_buff  # type: ignore
        self.max_health = max(self.max_health, 1)

        if self.has_ability('Shield'):
            self.gain_shield(log, animations, game_state)

        if self.current_attack < 0:
            self.current_attack = 0

    def add_basic_animation(self, animations: list, game_state: 'GameState'):
        if self.exists():
            animations.append(
                on_reveal_animation(self.lane.lane_number, self.owner_number, [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id), game_state)
            )

    def do_early_on_reveal(self, log: list[str], animations: list, game_state: 'GameState'):
        if self.did_on_reveal:
            return

        if self.new:
            if self.has_ability('OnRevealSilenceLastEnemy'):
                enemy_characters = self.lane.characters_by_player[1 - self.owner_number]
                if len(enemy_characters) > 0:
                    enemy_characters[-1].silence(self, log, animations, game_state)

            if self.has_ability('OnRevealSilenceAllCharacters'):
                for character in [*self.lane.characters_by_player[1 - self.owner_number], *self.lane.characters_by_player[self.owner_number]]:
                    if character.id != self.id:
                        character.silence(self, log, animations, game_state, do_not_animate=True)
                self.add_basic_animation(animations, game_state)


    def do_regular_on_reveal(self, log: list[str], animations: list, game_state: 'GameState'):
        if self.did_on_reveal:
            return
        if self.new:
            if self.has_ability('OnRevealShackle'):
                random_enemy_character = self.lane.get_random_enemy_character(self.owner_number, exclude_characters=lambda c: c.shackled_turns > 0)
                if random_enemy_character is not None:
                    random_enemy_character.shackle(self, log, animations, game_state)

            if self.has_ability('OnRevealShackleSeveral'):
                for _ in range(self.number_of_ability('OnRevealShackleSeveral')):
                    random_enemy_character = self.lane.get_random_enemy_character(self.owner_number, exclude_characters=lambda c: c.shackled_turns > 0)
                    if random_enemy_character is not None:
                        random_enemy_character.shackle(self, log, animations, game_state)

            if self.has_ability('OnRevealShackleAllEnemies'):
                for character in self.lane.characters_by_player[1 - self.owner_number]:
                    if character.shackled_turns == 0:
                        character.shackle(self, log, animations, game_state, do_not_animate=True)
                self.add_basic_animation(animations, game_state)


            if self.has_ability('OnRevealPumpFriends'):
                for character in self.lane.characters_by_player[self.owner_number]:
                    if character.id != self.id:
                        character.current_attack += self.number_of_ability('OnRevealPumpFriends')
                        character.current_health += self.number_2_of_ability('OnRevealPumpFriends')
                        character.max_health += self.number_2_of_ability('OnRevealPumpFriends')
                        log.append(f"{self.owner_username}'s {self.template.name} pumped {character.owner_username}'s {character.template.name}.")
                self.add_basic_animation(animations, game_state)

            if self.has_ability('OnRevealPumpAttackers'):
                for character in self.lane.characters_by_player[self.owner_number]:
                    if character.is_attacker() and character.id != self.id:
                        character.current_attack += self.number_of_ability('OnRevealPumpAttackers')
                        character.current_health += self.number_2_of_ability('OnRevealPumpAttackers')
                        character.max_health += self.number_2_of_ability('OnRevealPumpAttackers')
                        log.append(f"{self.owner_username}'s {self.template.name} pumped {character.owner_username}'s {character.template.name}.")
                self.add_basic_animation(animations, game_state)

            if self.has_ability('OnRevealGainMana'):
                number = self.number_of_ability('OnRevealGainMana')
                game_state.mana_by_player[self.owner_number] += number
                log.append(f"{self.owner_username}'s {self.template.name} gained {number} mana.")

            if self.has_ability('HealFriendlyCharacterAndTower'):
                random_friendly_damaged_character = self.get_random_other_friendly_damaged_character()
                if random_friendly_damaged_character is not None:
                    random_friendly_damaged_character.fully_heal()
                    animations.append(
                        {
                            "event_type": "CharacterHeal",
                            "data": {
                                "acting_player": self.owner_number,
                                "lane": self.lane.lane_number,
                                "from_character_index": [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id),
                                "to_character_index": [c.id for c in self.lane.characters_by_player[self.owner_number]].index(random_friendly_damaged_character.id),
                            },
                            "game_state": game_state.to_json(),
                        },
                    )
                self.lane.damage_by_player[1 - self.owner_number] = max(0, self.lane.damage_by_player[1 - self.owner_number] - self.number_of_ability('HealFriendlyCharacterAndTower'))

            if self.has_ability('OnRevealHealAllFriendliesAndTowers'):
                for lane in game_state.lanes:
                    for character in lane.characters_by_player[self.owner_number]:
                        character.fully_heal()
                    lane.damage_by_player[1 - self.owner_number] = max(0, lane.damage_by_player[1 - self.owner_number] - self.number_of_ability('OnRevealHealAllFriendliesAndTowers'))
                self.add_basic_animation(animations, game_state)

            if self.has_ability('OnRevealLaneFightsFirst'):
                self.lane.additional_combat_priority -= 3

            if self.has_ability('OnRevealFriendliesSwitchLanes'):
                friendlies = self.lane.characters_by_player[self.owner_number][:]
                self.add_basic_animation(animations, game_state)                
                for character in friendlies:
                    character.switch_lanes(log, animations, game_state)

            if self.has_ability('OnRevealDrawCards'):
                cards_to_draw = self.number_of_ability('OnRevealDrawCards')
                for _ in range(cards_to_draw):
                    game_state.draw_random_card(self.owner_number)

            if self.has_ability('OnRevealDamageSelf'):
                damage_amount = self.number_of_ability('OnRevealDamageSelf')
                self.current_health -= damage_amount
                log.append(f"{self.owner_username}'s {self.template.name} dealt {damage_amount} damage to itself.")
                self.add_basic_animation(animations, game_state)

            if 'Earth' in self.template.creature_types or 'Avatar' in self.template.creature_types:
                for character in self.lane.characters_by_player[self.owner_number]:
                    if character.has_ability('ShackleOnFriendlyEarth') and character.id != self.id:
                        random_enemy_character = self.lane.get_random_enemy_character(self.owner_number, exclude_characters=lambda c: c.shackled_turns > 0)
                        if random_enemy_character is not None:
                            random_enemy_character.shackle(character, log, animations, game_state)
            
            if self.has_ability('OnRevealPumpFriendlyCharactersOfElement'):
                for character in self.lane.characters_by_player[self.owner_number]:
                    if (self.creature_type_of_ability('OnRevealPumpFriendlyCharactersOfElement') in character.template.creature_types or 'Avatar' in character.template.creature_types) and character.id != self.id:
                        character.current_attack += self.number_of_ability('OnRevealPumpFriendlyCharactersOfElement')
                        character.current_health += self.number_2_of_ability('OnRevealPumpFriendlyCharactersOfElement')
                        character.max_health += self.number_2_of_ability('OnRevealPumpFriendlyCharactersOfElement')
                self.add_basic_animation(animations, game_state)

            if self.has_ability('OnRevealFillEnemyLaneWithCabbages'):
                while len(self.lane.characters_by_player[1 - self.owner_number]) < 4:
                    cabbage_character = Character(CARD_TEMPLATES['Cabbage'], self.lane, 1 - self.owner_number, game_state.usernames_by_player[1 - self.owner_number])
                    self.lane.characters_by_player[1 - self.owner_number].append(cabbage_character)
                    cabbage_character.do_all_on_reveal(log, animations, game_state)

            if self.has_ability('OnRevealSummonDesna'):
                if len(self.lane.characters_by_player[self.owner_number]) < 4:
                    self.add_basic_animation(animations, game_state)
                    desna_character = Character(CARD_TEMPLATES['Desna'], self.lane, self.owner_number, game_state.usernames_by_player[self.owner_number])
                    self.lane.characters_by_player[self.owner_number].append(desna_character)
                    desna_character.do_all_on_reveal(log, animations, game_state)

            if self.has_ability('OnRevealHealAndPumpSelf'):
                random_friendly_damaged_character = self.get_random_other_friendly_damaged_character()
                if random_friendly_damaged_character is not None:
                    amount_to_heal = random_friendly_damaged_character.max_health - random_friendly_damaged_character.current_health
                    random_friendly_damaged_character.fully_heal()
                    self.current_attack += amount_to_heal
                    self.current_health += amount_to_heal
                    self.max_health += amount_to_heal
                    animations.append(
                        {
                            "event_type": "CharacterHeal",
                            "data": {
                                "acting_player": self.owner_number,
                                "lane": self.lane.lane_number,
                                "from_character_index": [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id),
                                "to_character_index": [c.id for c in self.lane.characters_by_player[self.owner_number]].index(random_friendly_damaged_character.id),
                            },
                            "game_state": game_state.to_json(),
                        },
                    )

            if self.has_ability('OnRevealDiscard'):
                if len(game_state.hands_by_player[self.owner_number]) > 0:
                    random_card = random.choice(game_state.hands_by_player[self.owner_number])
                    game_state.discard_card(self.owner_number, random_card.id)
                    log.append(f"{self.owner_username}'s {self.template.name} discarded {random_card.template.name}.")

            if self.has_ability('OnRevealDiscardHandAndPump'):
                num_cards_to_discard = len(game_state.hands_by_player[self.owner_number])
                game_state.discard_all_cards(self.owner_number)
                attack_multiplier = self.number_of_ability('OnRevealDiscardHandAndPump')
                defense_multiplier = self.number_2_of_ability('OnRevealDiscardHandAndPump')
                self.current_attack += num_cards_to_discard * attack_multiplier
                self.current_health += num_cards_to_discard * defense_multiplier
                self.max_health += num_cards_to_discard * defense_multiplier
                self.add_basic_animation(animations, game_state)

            if self.has_ability('OnRevealShieldFriendlies'):
                for character in self.lane.characters_by_player[self.owner_number]:
                    if character.id != self.id:
                        character.gain_shield(log, animations, game_state)
                self.add_basic_animation(animations, game_state)

            if self.has_ability('OnRevealPumpCardsInHand'):
                for card in game_state.hands_by_player[self.owner_number]:
                    card.attack += self.number_of_ability('OnRevealPumpCardsInHand')
                    card.health += self.number_2_of_ability('OnRevealPumpCardsInHand')
                self.add_basic_animation(animations, game_state)    

            if self.has_ability('OnRevealPumpFriendliesIfFullMatchingLane'):
                if len(self.lane.characters_by_player[self.owner_number]) >= 4:
                    for element in ['Fire', 'Water', 'Earth', 'Air']:
                        if all([element in character.template.creature_types or 'Avatar' in character.template.creature_types for character in self.lane.characters_by_player[self.owner_number]]):
                            for character in self.lane.characters_by_player[self.owner_number]:
                                character.current_attack += self.number_of_ability('OnRevealPumpFriendliesIfFullMatchingLane')
                                character.current_health += self.number_2_of_ability('OnRevealPumpFriendliesIfFullMatchingLane')
                                character.max_health += self.number_2_of_ability('OnRevealPumpFriendliesIfFullMatchingLane')
                            self.add_basic_animation(animations, game_state)                                
                            break
            
            if self.lane.lane_reward.effect[0] == 'pumpAllCharactersPlayedHereWhenFilled' and len(self.lane.characters_by_player[self.owner_number]) >= 4:
                for character in self.lane.characters_by_player[self.owner_number]:
                    character.current_attack += self.lane.lane_reward.effect[1]  # type: ignore
                    character.current_health += self.lane.lane_reward.effect[2]  # type: ignore
                    character.max_health += self.lane.lane_reward.effect[2]  # type: ignore
                
                animations.append(basic_lane_animation(self.lane.lane_number, game_state))

    def do_late_on_reveal(self, log: list[str], animations: list, game_state: 'GameState'):
        if self.did_on_reveal:
            return        

        if self.has_ability('OnRevealDiscardRandomCardAndDealDamageEqualToCost'):
            if len(game_state.hands_by_player[self.owner_number]) > 0:
                random_card = random.choice(game_state.hands_by_player[self.owner_number])
                game_state.discard_card(self.owner_number, random_card.id)
                damage_to_deal = random_card.template.cost
                defending_character = self.lane.get_random_enemy_character(self.owner_number)
                if defending_character is not None:
                    animations.append({
                        "event_type": "CharacterAttack",
                        "data": {
                            "lane": self.lane.lane_number,
                            "acting_player": self.owner_number,
                            "from_character_index": [c.id for c in self.lane.characters_by_player[self.owner_number]].index(self.id),
                            "to_character_index": [c.id for c in self.lane.characters_by_player[1 - self.owner_number]].index(defending_character.id),                            
                        },
                        "game_state": game_state.to_json(),
                    })

                    defending_character.sustain_damage(damage_to_deal, log, animations, game_state)

                    self.lane.process_dying_characters(log, animations, game_state) 

        if self.has_ability('OnRevealDamageToAll'):
            self.add_basic_animation(animations, game_state)
            damage_amount = self.number_of_ability('OnRevealDamageToAll')
            for character in [*self.lane.characters_by_player[self.owner_number], *self.lane.characters_by_player[1 - self.owner_number]]:
                character.sustain_damage(damage_amount, log, animations, game_state)
                log.append(f"{self.owner_username}'s {self.template.name} dealt {damage_amount} damage to {character.owner_username}'s {character.template.name} in Lane {self.lane.lane_number + 1}. "
                            f"{character.template.name}'s health is now {character.current_health}.")
            self.lane.process_dying_characters(log, animations, game_state)

        if self.has_ability('OnRevealBonusAttack'):
            for _ in range(self.number_of_ability('OnRevealBonusAttack')):
                self.make_bonus_attack(log, animations, game_state)
            self.lane.process_dying_characters(log, animations, game_state)

        if self.has_ability('OnRevealFriendliesMakeBonusAttack'):
            self.add_basic_animation(animations, game_state)
            for character in self.lane.characters_by_player[self.owner_number]:
                if character.id != self.id:
                    character.make_bonus_attack(log, animations, game_state)
            self.lane.process_dying_characters(log, animations, game_state)

        if self.has_ability('OnRevealAllAttackersMakeBonusAttack'):
            characters_to_bonus_attack = [character for character in [*game_state.lanes[0].characters_by_player[self.owner_number], *game_state.lanes[1].characters_by_player[self.owner_number], *game_state.lanes[2].characters_by_player[self.owner_number]] if character.is_attacker()]

            for character in characters_to_bonus_attack:
                character.make_bonus_attack(log, animations, game_state)


        if self.has_ability('OnRevealStealEnemy'):
            if len(self.lane.characters_by_player[self.owner_number]) < 4:
                self.add_basic_animation(animations, game_state)
                random_enemy_character = self.lane.get_random_enemy_character(self.owner_number)
                if random_enemy_character is not None:
                    starting_character_index = [c.id for c in self.lane.characters_by_player[1 - self.owner_number]].index(random_enemy_character.id)
                    self.lane.characters_by_player[1 - self.owner_number] = [character for character in self.lane.characters_by_player[1 - self.owner_number] if character.id != random_enemy_character.id]
                    self.lane.characters_by_player[self.owner_number].append(random_enemy_character)
                    random_enemy_character.owner_number = self.owner_number
                    random_enemy_character.owner_username = self.owner_username

                    animations.append({
                        'event_type': 'SwitchSides',
                        'data': {
                            "acting_player": 1 - self.owner_number,
                            "lane": self.lane.lane_number,
                            "from_character_index": starting_character_index,
                            "to_character_index": [c.id for c in self.lane.characters_by_player[self.owner_number]].index(random_enemy_character.id),
                        },
                        "game_state": game_state.to_json(),
                    })

        if self.has_ability('OnRevealEnemiesFight'):
            if len(self.lane.characters_by_player[1 - self.owner_number]) > 1:
                self.add_basic_animation(animations, game_state)
                enemy_attacker = self.lane.get_random_enemy_character(self.owner_number)
                if enemy_attacker is not None:
                    enemy_defender = self.lane.get_random_enemy_character(self.owner_number, exclude_characters=lambda c: c.id == enemy_attacker.id)
                    if enemy_defender is not None:
                        combat_modification_auras = self.lane.compute_combat_modification_auras()
                        enemy_attacker.fight(enemy_defender, self.lane.lane_number, combat_modification_auras, log, animations, game_state, friendly=True, do_not_attack_tower=True)

        if self.has_ability('OnRevealEnemiesSwitchLanes'):
            self.add_basic_animation(animations, game_state)
            for character in self.lane.characters_by_player[1 - self.owner_number]:
                character.switch_lanes(log, animations, game_state)

        self.did_on_reveal = True


    def get_random_other_friendly_damaged_character(self) -> Optional['Character']:
        friendly_characters = [character for character in self.lane.characters_by_player[self.owner_number] if character.current_health < character.max_health]
        if len(friendly_characters) == 0:
            return None
        else:
            return random.choice(friendly_characters)


    def to_json(self):
        return {
            "id": self.id,
            "template": self.template.to_json(),
            "current_health": self.current_health,
            "shackled_turns": self.shackled_turns,
            "max_health": self.max_health,
            "current_attack": self.current_attack,
            "has_attacked": self.has_attacked,
            "owner_number": self.owner_number,
            "owner_username": self.owner_username,
            "new": self.new,   
            "escaped_death": self.escaped_death,         
            "did_on_reveal": self.did_on_reveal,
            "did_end_of_turn": self.did_end_of_turn,
            "silenced": self.silenced,
            "shielded": self.shielded,
            # Can't put lane in here because of infinite recursion
        }


    @staticmethod
    def from_json(json: dict, lane: 'Lane'):
        character = Character(
            template=CardTemplate.from_json(json['template']),
            lane=lane,
            owner_number=json['owner_number'],
            owner_username=json['owner_username'],
        )
        character.id = json['id']
        character.current_health = json['current_health']
        character.shackled_turns = json['shackled_turns']
        character.max_health = json['max_health']
        character.current_attack = json['current_attack']
        character.has_attacked = json['has_attacked']
        character.new = json['new']
        character.escaped_death = json['escaped_death']
        character.did_on_reveal = json['did_on_reveal']
        character.did_end_of_turn = json['did_end_of_turn']
        character.silenced = json['silenced']
        character.shielded = json['shielded']
        return character

