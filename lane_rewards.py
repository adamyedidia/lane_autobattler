from typing import Union


LANE_REWARDS = {reward['name']: {**reward, 'priority': i} for i, reward in enumerate([
    {
        'name': 'Earth Empire',
        'threshold': 50,
        'reward_description': 'Create an 8/8 attacker in another lane.',
        'effect': ['spawn', 'The Colossus'],
    },
    {
        'name': 'Fire Nation',
        'threshold': 45,
        'reward_description': 'ALL friendly characters get +3/+0.',
        'effect': ['pumpAllFriendlies', 3, 0],
    },
    {
        'name': 'Omashu',
        'threshold': 40,
        'reward_description': 'ALL friendly characters make a bonus attack.',
        'effect': ['bonusAttackAllFriendlies'],
    },
    {
        'name': 'Beifong Academy',
        'threshold': 30,
        'reward_description': 'Draw three random cards.',
        'effect': ['drawRandomCards', 3],
    },    
    {
        'name': 'Southern Air Temple',
        'threshold': 25,
        'reward_description': 'Create a 4/4 in another lane.',
        'effect': ['spawn', 'Air Nomads'],
    },    
    {
        'name': 'Hegemon\'s Folly',
        'threshold': 25,
        'reward_description': 'Discard your hand.',
        'effect': ['discardHand'],
    },    
    {
        'name': 'Ba Sing Se',
        'threshold': 25,
        'reward_description': 'Gain 2 mana next turn.',
        'effect': ['gainMana', 2],
    },    
    {
        'name': 'Gaoling',
        'threshold': 20,
        'reward_description': 'ALL friendly characters get +0/+2.',
        'effect': ['pumpAllFriendlies', 0, 2],
    },
    {
        'name': 'Bhanti Island',
        'threshold': 20,
        'reward_description': 'Draw two random cards.',
        'effect': ['drawRandomCards', 2],
    },    
    {
        'name': 'Full Moon Bay',
        'threshold': 10,
        'reward_description': 'Draw a random card.',
        'effect': ['drawRandomCards', 1],
    },
    {
        'name': 'Taihua Mountains',
        'threshold': None,
        'reward_description': 'Characters played here get +0/+2.',
        'effect': ['pumpAllCharactersPlayedHere', 0, 2],
    },
    {
        'name': 'Boiling Rock',
        'threshold': None,
        'reward_description': 'Characters played here get +1/+0.',
        'effect': ['pumpAllCharactersPlayedHere', 1, 0],
    },
    {
        'name': 'Foggy Swamp',
        'threshold': None,
        'reward_description': 'Characters played here get -1/-0.',
        'effect': ['pumpAllCharactersPlayedHere', -1, 0],
    },
    {
        'name': 'Chin Village',
        'threshold': None,
        'reward_description': 'Each player starts with two 1/1s in this lane.',
        'effect': ['spawnAtStart', 'Elephant Rat', 2],
    },
    {
        'name': 'Northern Water Tribe',
        'threshold': None,
        'reward_description': 'At the end of each turn, characters here fully heal.',
        'effect': ['healAllCharactersHereAtEndOfTurn'],
    },
    {
        'name': 'Serpent\'s Pass',
        'threshold': None,
        'reward_description': 'Characters here fight as though they were Attackers.',
        'effect': ['charactersHereFightAsAttackers'],
    },
    {
        'name': 'Shipwreck Cave',
        'threshold': None,
        'reward_description': 'When a character here dies, its owner gains +1 mana next turn.',
        'effect': ['ownerGainsManaNextTurnWhenCharacterDiesHere', 1],
    },
])}

class LaneReward:
    def __init__(self, name: str, threshold: int, reward_description: str, effect: list[Union[str, int]], priority: int):
        self.name = name
        self.threshold = threshold
        self.reward_description = reward_description
        self.effect = effect
        self.priority = priority

    def to_json(self):
        return {
            "name": self.name,
            "threshold": self.threshold,
            "reward_description": self.reward_description,
            "effect": self.effect,
            "priority": self.priority,
        }
    
    @staticmethod
    def from_json(json: dict):
        return LaneReward(json["name"], json["threshold"], json["reward_description"], json["effect"], json["priority"])
    