from typing import TYPE_CHECKING
from character import Character

from utils import generate_unique_id
from card_template import CardTemplate


class Card:
    def __init__(self, template: 'CardTemplate'):
        self.template = template
        self.id = generate_unique_id()
        self.attack = template.attack
        self.health = template.health

    def to_character(self, lane, owner_number, owner_username):
        character = Character(self.template, lane, owner_number, owner_username, self.id)
        character.current_attack = self.attack
        character.current_health = self.health
        character.max_health = self.health
        return character

    def to_json(self):
        return {
            "id": self.id,
            "template": self.template.to_json(),
            "attack": self.attack,
            "health": self.health,
        }
    
    @staticmethod
    def from_json(json):
        card = Card(CardTemplate.from_json(json['template']))
        card.id = json['id']
        card.attack = json['attack']
        card.health = json['health']
        return card

    @staticmethod
    def from_template(template: 'CardTemplate'):
        return Card(template)


    def __repr__(self):
        return f"Card {self.id}: {self.template.name}"
