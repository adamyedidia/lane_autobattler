from typing import Callable, Union
from abilities_list import ABILITIES


class CardTemplate:
    def __init__(self, name: str, abilities: list[Union[str, tuple[str, int], tuple[str, int, int], tuple[str, int, int, str]]], cost: int, attack: int, health: int, creature_types: list[str], rarity: str, not_in_card_pool: bool = False):
        self.name = name
        self.abilities = []
        for ability in abilities:
            if isinstance(ability, tuple):
                if len(ability) == 2:
                    self.abilities.append(ABILITIES[ability[0]](ability[1]))  # type: ignore
                elif len(ability) == 3:
                    self.abilities.append(ABILITIES[ability[0]](ability[1], ability[2]))  # type: ignore
                elif len(ability) == 4:
                    self.abilities.append(ABILITIES[ability[0]](ability[1], ability[2], ability[3]))  # type: ignore
            else:
                self.abilities.append(ABILITIES[ability])

        self.cost = cost
        self.attack = attack
        self.health = health
        self.creature_types = creature_types
        self.not_in_card_pool = not_in_card_pool
        self.rarity = rarity

    def to_json(self):
        return {
            "name": self.name,
            "abilities": [a.to_json() for a in self.abilities],
            "cost": self.cost,
            "attack": self.attack,
            "health": self.health,
            "creatureTypes": self.creature_types,
            "rarity": self.rarity,
            **({"notInCardPool": self.not_in_card_pool} if self.not_in_card_pool else {}),
        }
    
    @staticmethod
    def from_json(json: dict):
        abilities = []
        for ability in json["abilities"]:
            number = ability.get("number")
            number_2 = ability.get("number_2")

            creature_type = ability.get("creature_type")

            if number is not None:
                if number_2 is not None:
                    if creature_type is not None:
                        abilities.append((ability["name"], number, number_2, creature_type))
                    else:
                        abilities.append((ability["name"], number, number_2))
                else:
                    abilities.append((ability["name"], number))
            else:
                abilities.append(ability["name"])

        return CardTemplate(json["name"], abilities, 
                            json["cost"], json["attack"], json["health"], json["creatureTypes"],
                            json["rarity"],
                            json["notInCardPool"] if "notInCardPool" in json else False)
    