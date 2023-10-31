from typing import TYPE_CHECKING, Callable
import random
from typing import Optional
from card_templates_list import CARD_TEMPLATES
from character import Character
from lane_rewards import LANE_REWARDS, LaneReward
from utils import basic_lane_animation, shuffled
if TYPE_CHECKING:
    from game_state import GameState


class Lane:
    def __init__(self, lane_number: int, lane_reward_str: str):
        self.damage_by_player: dict[int, int] = {0: 0, 1: 0}
        self.characters_by_player: dict[int, list[Character]] = {0: [], 1: []}
        self.lane_number = lane_number
        self.additional_combat_priority = 0
        self.lane_reward = LaneReward.from_json(LANE_REWARDS[lane_reward_str])
        self.earned_rewards_by_player: dict[int, bool] = {0: False, 1: False}


    def maybe_give_lane_reward(self, player_num: int, game_state: 'GameState', log: list[str], animations: list) -> None:
        if not self.earned_rewards_by_player[player_num] and self.lane_reward.threshold is not None and self.damage_by_player[player_num] >= self.lane_reward.threshold:
            early_animation = self.lane_reward.effect[0] in ['bonusAttackAllFriendlies']
            self.earned_rewards_by_player[player_num] = True
            if early_animation:
                animations.append(basic_lane_animation(self.lane_number, game_state))
            self.give_lane_reward(player_num, game_state, log, animations)
            if not early_animation:
                animations.append(basic_lane_animation(self.lane_number, game_state))


    def give_lane_reward(self, player_num: int, game_state: 'GameState', log: list[str], animations: list) -> None:
        if self.lane_reward.effect[0] == 'pumpAllFriendlies':
            for lane in game_state.lanes:
                for character in lane.characters_by_player[player_num]:
                    character.current_attack += self.lane_reward.effect[1]  # type: ignore
                    character.current_health += self.lane_reward.effect[2]  # type: ignore
                    character.max_health += self.lane_reward.effect[2]  # type: ignore
        elif self.lane_reward.effect[0] == 'spawn':
            lane_to_spawn_in = game_state.find_random_empty_slot_in_other_lane(self.lane_number, player_num)
            if lane_to_spawn_in is not None:
                character = Character(CARD_TEMPLATES[self.lane_reward.effect[1]], lane_to_spawn_in, player_num, game_state.usernames_by_player[player_num])  # type: ignore
                lane_to_spawn_in.characters_by_player[player_num].append(character)
                character.do_all_on_reveal(log, animations, game_state)
        elif self.lane_reward.effect[0] == 'drawRandomCards':
            for _ in range(self.lane_reward.effect[1]):  # type: ignore
                game_state.draw_random_card(player_num)
        elif self.lane_reward.effect[0] == 'bonusAttackAllFriendlies':
            characters_to_bonus_attack = [*game_state.lanes[0].characters_by_player[player_num], *game_state.lanes[1].characters_by_player[player_num], *game_state.lanes[2].characters_by_player[player_num]]

            for character in characters_to_bonus_attack:
                character.make_bonus_attack(log, animations, game_state)


        elif self.lane_reward.effect[0] == 'discardHand':
            game_state.discard_all_cards(player_num)

        elif self.lane_reward.effect[0] == 'gainMana':
            game_state.mana_by_player[player_num] += self.lane_reward.effect[1]  # type: ignore


    def do_start_of_game(self, log: list[str], animations: list, game_state: 'GameState') -> None:
        if self.lane_reward.effect[0] == 'spawnAtStart':
            for player_num in [0, 1]:
                for _ in range(self.lane_reward.effect[2]):  # type: ignore
                    character = Character(CARD_TEMPLATES[self.lane_reward.effect[1]], self, player_num, game_state.usernames_by_player[player_num])  # type: ignore
                    self.characters_by_player[player_num].append(character)
        self.do_start_of_turn(log, animations, game_state)
        self.do_end_of_turn(log, animations, game_state)


    def do_start_of_turn(self, log: list[str], animations: list, game_state: 'GameState') -> None:
        for player_num in [0, 1]:
            for character in self.characters_by_player[player_num]:
                character.escaped_death = False
                character.did_end_of_turn = False

        characters_to_do_on_reveal = [*[character for character in self.characters_by_player[0] if not character.did_on_reveal], 
                                      *[character for character in self.characters_by_player[1] if not character.did_on_reveal]]
        random.shuffle(characters_to_do_on_reveal)

        for character in characters_to_do_on_reveal:
            character.do_very_early_on_reveal(log, animations, game_state)

        for character in characters_to_do_on_reveal:
            character.do_early_on_reveal(log, animations, game_state)

        for character in characters_to_do_on_reveal:
            character.do_regular_on_reveal(log, animations, game_state)

        for character in characters_to_do_on_reveal:
            character.do_late_on_reveal(log, animations, game_state)


    def roll_turn(self, log: list[str], animations: list, game_state: 'GameState') -> None:
        self.resolve_combat(log, animations, game_state)

        for player_num in [0, 1]:
            for character in self.characters_by_player[player_num]:
                character.roll_turn(log, animations, game_state)

        self.additional_combat_priority = 0


    def do_end_of_turn(self, log: list[str], animations: list, game_state: 'GameState') -> None:
        for player_num in [0, 1]:
            for character in self.characters_by_player[player_num]:
                character.do_end_of_turn(log, animations, game_state)

        if self.lane_reward.effect[0] == 'healAllCharactersHereAtEndOfTurn':
            for character in [*self.characters_by_player[0], *self.characters_by_player[1]]:
                character.fully_heal()
            if game_state.turn > 1:
                animations.append(basic_lane_animation(self.lane_number, game_state))

        if self.lane_reward.effect[0] == 'dealDamageToAllCharactersHereAtEndOfTurn':
            for character in [*self.characters_by_player[0], *self.characters_by_player[1]]:
                character.sustain_damage(self.lane_reward.effect[1], log, animations, game_state)  # type: ignore
            if game_state.turn > 1:
                animations.append(basic_lane_animation(self.lane_number, game_state))

            self.process_dying_characters(log, animations, game_state)


    def resolve_combat(self, 
                       log: list[str], 
                       animations: list,
                       game_state: 'GameState') -> None:

        done_attacking_by_player_first_strike = {0: False, 1: False}
        done_attacking_by_player = {0: False, 1: False}

        self.resolve_combat_inner(done_attacking_by_player_first_strike, log, animations, game_state, first_strikers_only=True)
        self.resolve_combat_inner(done_attacking_by_player, log, animations, game_state)


    def resolve_combat_inner(self, 
                             done_attacking_by_player: dict[int, bool], 
                             log: list[str], 
                             animations: list,
                             game_state: 'GameState',
                             first_strikers_only: bool = False,
                             attacking_player: Optional[int] = None) -> None:
        if attacking_player is None:
            # The player with more characters attacks first
            player_0_characters = [c for c in self.characters_by_player[0] if not first_strikers_only or c.has_ability('EarlyFighter')]
            player_1_characters = [c for c in self.characters_by_player[1] if not first_strikers_only or c.has_ability('EarlyFighter')]

            attacking_player = (0 if len(player_0_characters) > len(player_1_characters)
                                else 1 if len(player_1_characters) > len(player_0_characters) 
                                else random.randint(0, 1))
        self.player_single_attack(attacking_player, done_attacking_by_player, log, animations, game_state, first_strikers_only=first_strikers_only)
        if done_attacking_by_player[1 - attacking_player]:
            if done_attacking_by_player[attacking_player]:
                return
            else:
                self.resolve_combat_inner(done_attacking_by_player, log, animations, game_state, first_strikers_only=first_strikers_only, attacking_player=attacking_player)
        else:
            self.resolve_combat_inner(done_attacking_by_player, log, animations, game_state, first_strikers_only=first_strikers_only, attacking_player=1 - attacking_player)


    def process_dying_characters(self, log: list[str], animations: list, game_state: 'GameState') -> None:
        dying_characters = [character for character in self.characters_by_player[0] + self.characters_by_player[1] if character.current_health <= 0]

        truly_dead_characters = []

        for dying_character in dying_characters:
            was_saved = False
            for lane in shuffled([lane for lane in game_state.lanes if not lane.lane_number == self.lane_number]):
                for character in lane.characters_by_player[dying_character.owner_number]:
                    if character.has_ability('OnFriendlyCharacterDeathHealFullyAndSwitchLanes'):
                        if dying_character.switch_lanes(log, animations, game_state, lane_number=lane.lane_number, and_fully_heal_if_switching=True):
                            was_saved = True
                        

            if dying_character.has_ability('SwitchLanesInsteadOfDying') and not was_saved and not dying_character.escaped_death:
                if dying_character.switch_lanes(log, animations, game_state, and_fully_heal_if_switching=True):
                    dying_character.escaped_death = True      
            
            if not dying_character.escaped_death and not was_saved:
                if dying_character.lane.lane_reward.effect[0] == 'ownerGainsManaNextTurnWhenCharacterDiesHere':
                    game_state.mana_by_player[dying_character.owner_number] += dying_character.lane.lane_reward.effect[1]  # type: ignore

                truly_dead_characters.append(dying_character)

        for player_num in self.characters_by_player:
            self.characters_by_player[player_num] = [character for character in self.characters_by_player[player_num] if character.current_health > 0]

        for dead_character in truly_dead_characters:
            if dead_character.has_ability('DeathMoveCharactersHereAndPumpThem'):
                friendly_characters_not_in_this_lane = [character for character in [*game_state.lanes[0].characters_by_player[dead_character.owner_number], *game_state.lanes[1].characters_by_player[dead_character.owner_number], *game_state.lanes[2].characters_by_player[dead_character.owner_number]] if not character.lane.lane_number == self.lane_number]
                random.shuffle(friendly_characters_not_in_this_lane)

                for character_to_switch in friendly_characters_not_in_this_lane:
                    if len(self.characters_by_player[dead_character.owner_number]) < 4:
                        character_to_switch.switch_lanes(log, animations, game_state, lane_number=self.lane_number)
                        character_to_switch.current_attack += dead_character.number_of_ability('DeathMoveCharactersHereAndPumpThem')
                        character_to_switch.current_health += dead_character.number_of_ability('DeathMoveCharactersHereAndPumpThem')
                        character_to_switch.max_health += dead_character.number_of_ability('DeathMoveCharactersHereAndPumpThem')


    def player_single_attack(self, 
                             attacking_player: int,
                             done_attacking_by_player: dict[int, bool], 
                             log: list[str],
                             animations: list,
                             game_state: 'GameState', 
                             first_strikers_only: bool = False):
        characters_that_can_attack = [character for character in self.characters_by_player[attacking_player] if character.can_attack() and (not first_strikers_only or character.has_ability('EarlyFighter'))]
        
        characters_that_can_attack_without_last_strike = [character for character in characters_that_can_attack if not character.has_ability('LateFighter')]
        characters_that_can_attack_with_last_strike = [character for character in characters_that_can_attack if character.has_ability('LateFighter')]

        characters_that_can_attack = [*characters_that_can_attack_without_last_strike, *characters_that_can_attack_with_last_strike]

        if len(characters_that_can_attack) == 0:
            done_attacking_by_player[attacking_player] = True
        else:
            character = characters_that_can_attack[0]
            defending_characters = [character for character in self.characters_by_player[1 - attacking_player] if character.can_fight()]
            character.attack(attacking_player, self.damage_by_player, defending_characters, self.lane_number, log, animations, game_state)

        self.process_dying_characters(log, animations, game_state)


    def get_random_enemy_character(self, player_num: int, exclude_characters: Optional[Callable] = None) -> Optional[Character]:
        characters_available = [character for character in self.characters_by_player[1 - player_num] if character.can_fight() and (exclude_characters is None or not exclude_characters(character))]
        return random.choice(characters_available) if len(characters_available) > 0 else None

    def get_random_friendly_character(self, player_num: int, exclude_characters: Optional[Callable] = None) -> Optional[Character]:
        characters_available = [character for character in self.characters_by_player[player_num] if character.can_fight() and (exclude_characters is None or not exclude_characters(character))]
        return random.choice(characters_available) if len(characters_available) > 0 else None


    def compute_winner(self) -> Optional[int]:
        if self.damage_by_player[0] > self.damage_by_player[1]:
            return 0
        elif self.damage_by_player[1] > self.damage_by_player[0]:
            return 1
        else:
            return None


    def to_json(self):
        return {
            "damage_by_player": self.damage_by_player.copy(),
            "characters_by_player": {player: [character.to_json() for character in self.characters_by_player[player].copy()] for player in self.characters_by_player},
            "lane_number": self.lane_number,
            "lane_reward": self.lane_reward.to_json(),
            "earned_rewards_by_player": self.earned_rewards_by_player.copy(),
        }

    @staticmethod
    def from_json(json):
        lane = Lane(json["lane_number"], json["lane_reward"]["name"])
        lane.damage_by_player = {int(k): v for k, v in json["damage_by_player"].items()}
        lane.characters_by_player = {int(player): [Character.from_json(character, lane) for character in json["characters_by_player"][player]] for player in json["characters_by_player"]}
        lane.earned_rewards_by_player = {int(k): v for k, v in json["earned_rewards_by_player"].items()}
        return lane
