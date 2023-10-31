from typing import Callable, Union
from ability import Ability
from utils import element_to_color, plural


ABILITIES: dict[str, Union[Ability, Callable]] = {
    'Defender': Ability(
        name='Defender',
        description='Defender',
        is_keyword=True,
    ),
    'Attacker': Ability(
        name='Attacker',
        description='Attacker',
        is_keyword=True,
    ),
    'OnRevealShackle': Ability(
        name='OnRevealShackle',
        description='On reveal: shackle a random enemy character.',
    ),
    'OnRevealShackleSeveral': lambda x: Ability(
        name='OnRevealShackleSeveral',
        description=f'On reveal: shackle {x} random enemy character{plural(x)}.',
        number=x,
    ),
    'OnSurviveDamagePump': lambda x, y: Ability(
        name='OnSurviveDamagePump',
        description=f'Survive: I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'Deathtouch': Ability(
        name='Deathtouch',
        description='I kill any character I fight with.',
    ),
    'InvincibilityWhileAttacking': Ability(
        name='InvincibilityWhileAttacking',
        description='When I attack I don\'t take damage back.',
    ),
    'DoubleTowerDamage': Ability(
        name='DoubleTowerDamage',
        description='When I attack the enemy tower, I deal double damage.',
    ),
    'EndOfTurnFullHeal': Ability(
        name='EndOfTurnFullHeal',
        description='At the end of each turn, I fully heal.',
    ),
    'OnRevealPumpFriends': lambda x, y: Ability(
        name='OnRevealPumpFriends',
        description=f'On reveal: give +{x}/+{y} to other friendly characters.',
        number=x,
        number_2=y,
    ),
    'OnTowerAttackDealMassDamage': lambda x: Ability(
        name='OnTowerAttackDealMassDamage',
        description=f'Hit tower: deal {x} damage to enemy characters.',
        number=x,
    ),
    'OnRevealPumpAttackers': lambda x, y: Ability(
        name='OnRevealPumpAttackers',
        description=f'On reveal: give +{x}/+{y} to other friendly attackers.',
        number=x,
        number_2=y,
    ),
    'PumpCharactersPlayedHere': lambda x, y: Ability(
        name='PumpCharactersPlayedHere',
        description=f'Other characters played here get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnTowerAttackDrawCard': Ability(
        name='OnTowerAttackDrawCard',
        description='Hit tower: draw a random card.',
    ),
    'ShacklesLastExtraTurn': Ability(
        name='ShacklesLastExtraTurn',
        description='Shackles on enemy characters last an additional turn.',
    ),
    'OnRevealGainMana': lambda x: Ability(
        name='OnRevealGainMana',
        description=f'On reveal: gain {x} mana next turn only.',
        number=x,
    ),
    'OnRevealShackleAllEnemies': Ability(
        name='OnRevealShackleAllEnemies',
        description='On reveal: shackle the enemy characters here.',
    ),
    'ShacklesDealDamage': lambda x: Ability(
        name='ShacklesDealDamage',
        description=f'When you shackle an enemy character, deal {x} damage to it.',
        number=x,
    ),
    'DealMoreDamageWhenLosing': lambda x: Ability(
        name='DealMoreDamageWhenLosing',
        description=f'I deal {x} more damage when my team is losing my lane.',
        number=x,
    ),
    'SwitchLanesAfterAttacking': Ability(
        name='SwitchLanesAfterAttacking',
        description='After I attack, I switch lanes.',
    ),
    'HealFriendlyCharacterAndTower': lambda x: Ability(
        name='HealFriendlyCharacterAndTower',
        description=f'On reveal: heal a friendly character fully and your tower for {x}.',
        number=x,
    ),
    'SwitchLanesInsteadOfDying': Ability(
        name='SwitchLanesInsteadOfDying',
        description='When I would die for the first time each turn, I heal fully and switch lanes instead.',
    ),
    'CharacterMovesHerePumps': lambda x, y: Ability(
        name='CharacterMovesHerePumps',
        description=f'Whenever another friendly character switches into this lane, I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnRevealHealAllFriendliesAndTowers': lambda x: Ability(
        name='OnRevealHealAllFriendliesAndTowers',
        description=f'On reveal: fully heal friendly characters in ALL lanes and ALL friendly towers for {x}.',
        number=x,
    ),
    'OnRevealBonusAttack': lambda x: Ability(
        name='OnRevealBonusAttack',
        description=f'On reveal: I make {x} bonus attack{plural(x)}.',
        number=x,
    ),
    'OnRevealLaneFightsFirst': Ability(
        name='OnRevealLaneFightsFirst',
        description='On reveal: this lane fights first this turn.',
    ),
    'PumpOnFriendlyHeal': lambda x, y: Ability(
        name='PumpOnFriendlyHeal',
        description=f'Whenever another friendly character is healed, that character gets +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnKillBuffHealth': lambda x, y: Ability(
        name='OnKillBuffHealth',
        description=f'Kill enemy: I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnRevealFriendliesSwitchLanes': Ability(
        name='OnRevealFriendliesSwitchLanes',
        description='On reveal: all friendly characters here (including me) switch lanes.',
    ),
    'CharacterMovesHereThatCharacterPumps': lambda x, y: Ability(
        name='CharacterMovesHereThatCharacterPumps',
        description=f'Whenever another friendly character switches into this lane, it gets +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnRevealDamageToAll': lambda x: Ability(
        name='OnRevealDamageToAll',
        description=f'On reveal: deal {x} damage to all characters here (including your own).',
        number=x,
    ),
    'EndOfTurnFullHealForAllFriendlies': Ability(
        name='EndOfTurnFullHealForAllFriendlies',
        description='At the end of each turn, fully heal other friendly characters.',
    ),
    'OnFriendlyHealPumpMyself': lambda x, y: Ability(
        name='OnFriendlyHealPumpMyself',
        description=f'Whenever another friendly character is healed, I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnRevealDamageSelf': lambda x: Ability(
        name='OnRevealDamageSelf',
        description=f'On reveal: I deal {x} damage to myself.',
        number=x,
    ),
    'OnRevealDrawCards': lambda x: Ability(
        name='OnRevealDrawCards',
        description=f'On reveal: draw {x} random card{plural(x)}.',
        number=x,
    ),
    'OnDrawCardPump': lambda x, y: Ability(
        name='OnDrawCardPump',
        description=f'When you draw a card, I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnDamageTowerPumpTeam': lambda x, y: Ability(
        name='OnDamageTowerPumpTeam',
        description=f'Hit tower: other friendly characters get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnTowerDamageGainMana': lambda x: Ability(
        name='OnTowerDamageGainMana',
        description=f'Hit tower: gain {x} mana next turn.',
        number=x,
    ),
    'DoNotDamageEnemyCharacters': Ability(
        name='DoNotDamageEnemyCharacters',
        description='I do not damage enemy characters.',
    ),
    'ShackleOnFriendlyEarth': Ability(
        name='ShackleOnFriendlyEarth',
        description='When another friendly Earth (green) character is played here, shackle a random enemy character.',
    ),
    'OnShackleDrawCard': Ability(
        name='OnShackleDrawCard',
        description='When you shackle an enemy character, draw a random card.',
    ),
    'OnRevealPumpFriendlyCharactersOfElement': lambda x, y, z: Ability(
        name='OnRevealPumpFriendlyCharactersOfElement',
        description=f'On reveal: give +{x}/+{y} to other friendly {z} ({element_to_color(z)}) characters.',
        number=x,
        number_2=y,
        creature_type=z,
    ),
    'OnCharacterMoveHereMakeSpirit': Ability(
        name='OnCharacterMoveHereMakeSpirit',
        description='Whenever another friendly character moves into this lane, make a 4/2 Spirit in another lane.',
    ),
    'PumpFriendlyCharactersOfElementPlayedHere': lambda x, y, z: Ability(
        name='PumpFriendlyCharactersOfElementPlayedHere',
        description=f'Whenever you play another {z} ({element_to_color(z)}) character in this lane, it gets +{x}/+{y}.',
        number=x,
        number_2=y,
        creature_type=z,
    ),
    'OnAttackDoubleAttack': Ability(
        name='OnAttackDoubleAttack',
        description='After I attack, double my strength.',
    ),
    'OnFriendlyCharacterDeathHealFullyAndSwitchLanes': Ability(
        name='OnFriendlyCharacterDeathHealFullyAndSwitchLanes',
        description='If a friendly character in ANY other lane would die, heal it fully and switch it to my lane instead.',
    ),
    'OnCharacterMoveHereShackle': Ability(
        name='OnCharacterMoveHereShackle',
        description='Whenever a friendly character moves into this lane, shackle a random enemy character.',
    ),
    'SwitchLanesAtEndOfTurn': Ability(
        name='SwitchLanesAtEndOfTurn',
        description='At the end of each turn, I switch lanes.',
    ),
    'OnRevealFillEnemyLaneWithCabbages': Ability(
        name='OnRevealFillEnemyLaneWithCabbages',
        description='On reveal: fill the enemy lane with 0/1 Cabbages.',
    ),
    'DealDamageEqualToCurrentHealth': Ability(
        name='DealDamageEqualToCurrentHealth',
        description='I deal damage equal to my current health.',
    ),
    'OnRevealDiscardRandomCardAndDealDamageEqualToCost': Ability(
        name='OnRevealDiscardRandomCardAndDealDamageEqualToCost',
        description='On reveal: discard a random card and deal damage to a random enemy equal to its cost.',
    ),
    'OnRevealAllAttackersMakeBonusAttack': Ability(
        name='OnRevealAllAttackersMakeBonusAttack',
        description='On reveal: your friendly attackers in ALL lanes (including me) make a bonus attack.',
    ),
    'OnRevealSilenceRandomEnemy': Ability(
        name='OnRevealSilenceRandomEnemy',
        description='On reveal: silence a random enemy character. This can counter on reveals.',
    ),
    'OnRevealSilenceAllCharacters': Ability(
        name='OnRevealSilenceAllCharacters',
        description='On reveal: silence all other characters in this lane (including your own). This can counter on reveals.',
    ),
    'OnDamageCharacterSilenceIt': Ability(
        name='OnDamageCharacterSilenceIt',
        description='After I damage a character, silence it.',
    ),
    'OnShacklePumpSelf': lambda x, y: Ability(
        name='OnShacklePumpSelf',
        description=f'When an enemy character is shackled, I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnSurviveGainMana': lambda x: Ability(
        name='OnSurviveGainMana',
        description=f'Survive: gain {x} mana.',
        number=x,
    ),
    'OnSurviveDrawCard': Ability(
        name='OnSurviveDrawCard',
        description='Survive: draw a random card.',
    ),
    'OnRevealSummonDesna': Ability(
        name='OnRevealSummonDesna',
        description='On reveal: summon Desna, a 2/5 defender.',
    ),
    'OnRevealStealEnemy': Ability(
        name='OnRevealStealEnemy',
        description='On reveal: steal a random enemy character.',
    ),
    'OnTriggerSurvivePump': lambda x, y: Ability(
        name='OnTriggerSurvivePump',
        description=f'When a friendly character triggers a Survive ability, that character gets +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnTriggerSurvivePumpSelf': lambda x, y: Ability(
        name='OnTriggerSurvivePumpSelf',
        description=f'When a friendly character triggers a Survive ability, I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnRevealHealAndPumpSelf': Ability(
        name='OnRevealHealAndPumpSelf',
        description=f'On reveal: heal a friendly character fully, then I get +X/+X, where X is the amount healed.',
    ),
    'SurviveSwitchLanes': Ability(
        name='SurviveSwitchLanes',
        description='Survive: I switch lanes.',
    ),
    'OnRevealEnemiesFight': Ability(
        name='OnRevealEnemiesFight',
        description='On reveal: two enemy characters fight each other.',
    ),
    'OnRevealDiscard': Ability(
        name='OnRevealDiscard',
        description='On reveal: discard a random card.',
    ),
    'HitTowerPumpSelf': lambda x, y: Ability(
        name='HitTowerPumpSelf',
        description=f'Hit tower: I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnRevealEnemiesSwitchLanes': Ability(
        name='OnRevealEnemiesSwitchLanes',
        description='On reveal: enemy characters here switch lanes.',
    ),
    'OnDiscardPump': lambda x, y: Ability(
        name='OnDiscardPump',
        description=f'When you discard a card, I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'HitTowerDamageAllCharacters': lambda x: Ability(
        name='HitTowerDamageAllCharacters',
        description=f'Hit tower: I deal {x} damage to all other characters here (including yours).',
        number=x,
    ),
    'OnTriggerHitTowerPump': lambda x, y: Ability(
        name='OnTriggerHitTowerPump',
        description=f'When a friendly character triggers a Hit Tower ability, that character gets +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'HitTowerOtherCharactersSwitchLanes': Ability(
        name='HitTowerOtherCharactersSwitchLanes',
        description='Hit tower: other friendly characters switch lanes.',
    ),
    'OnTriggerKillEnemyHealAndPumpSelf': lambda x, y: Ability(
        name='OnTriggerKillEnemyHealAndPumpSelf',
        description=f'When a friendly character triggers a kill enemy ability, heal that character fully and I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'KillEnemyAttackAgain': Ability(
        name='KillEnemyAttackAgain',
        description='Kill enemy: I make a bonus attack.',
    ),
    'InvincibilityAgainstShackled': Ability(
        name='InvincibilityAgainstShackled',
        description='I take no damage from shackled characters.',
    ),
    'AttackersDontDealDamage': Ability(
        name='AttackersDontDealDamage',
        description='Attackers here (including yours) don\'t deal damage to other characters.',
    ),
    'HitTowerGiveShield': Ability(
        name='HitTowerGiveShield',
        description='Hit tower: give another friendly character a shield.',
    ),
    'OnRevealDiscardHandAndPump': lambda x, y: Ability(
        name='OnRevealDiscardHandAndPump',
        description=f'On reveal: discard your hand and give me +{x}/+{y} for each card discarded.',
        number=x,
        number_2=y,
    ),
    'OnShieldBreakPumpSelf': lambda x, y: Ability(
        name='OnShieldBreakPumpSelf',
        description=f'When a friendly character\'s shield breaks, I get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'Shield': Ability(
        name='Shield',
        description='Shield',
        is_keyword=True,
    ),
    'HitTowerShackle': Ability(
        name='HitTowerShackle',
        description='Hit tower: shackle a random enemy character.',
    ),
    'OnTriggerHitTowerBonusAttack': Ability(
        name='OnTriggerHitTowerBonusAttack',
        description='When a friendly character triggers a Hit Tower ability, that character makes a bonus attack (without re-triggering this ability).',
    ),
    'DeathtouchAgainstDefenders': Ability(
        name='DeathtouchAgainstDefenders',
        description='I kill any defender I fight with.',
    ),
    'OnRevealShieldFriendlies': Ability(
        name='OnRevealShieldFriendlies',
        description='On reveal: give a shield to other friendly characters.',
    ),
    'HitTowerDamageAllEnemiesEqualToDamage': Ability(
        name='HitTowerDamageAllEnemiesEqualToDamage',
        description='Hit tower: I deal damage to all enemy characters here equal to the damage I dealt.',
    ),
    'EarlyFighter': Ability(
        name='EarlyFighter',
        description='I always attack first.',
    ),
    'PumpOnGainShield': lambda x, y: Ability(
        name='PumpOnGainShield',
        description=f'When a friendly character gains a shield, that character gets +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'FriendliesDealDamageEqualToCurrentHealth': Ability(
        name='FriendliesDealDamageEqualToCurrentHealth',
        description='Friendly characters (including me) deal damage equal to their current health.',
    ),
    'OnTriggerKillEnemyBonusAttack': Ability(
        name='OnTriggerKillEnemyBonusAttack',
        description='When a friendly character triggers a Kill Enemy ability, I make a bonus attack.',
    ),
    'MoreStrengthMeansDoubleDamage': Ability(
        name='MoreStrengthMeansDoubleDamage',
        description='Friendly characters with more strength than health (including me) deal double damage.',
    ),
    'KillEnemySummonNyla': Ability(
        name='KillEnemySummonNyla',
        description='Kill enemy: if Nyla isn\'t already here, summon Nyla, a 4/3 attacker.',
    ),
    'DealDoubleDamageAgainstShackled': Ability(
        name='DealDoubleDamageAgainstShackled',
        description='I deal double damage to shackled characters.',
    ),
    'ShieldedCharactersDealExtraDamage': lambda x: Ability(
        name='ShieldedCharactersDealExtraDamage',
        description=f'Friendly characters with a shield deal {x} extra damage.',
        number=x,
    ),
    'KillEnemyGainShield': Ability(
        name='KillEnemyGainShield',
        description='Kill enemy: I gain a shield.',
    ),
    'OnRevealPumpCardsInHand': lambda x, y: Ability(
        name='OnRevealPumpCardsInHand',
        description=f'On reveal: your cards in hand get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'FriendlyAttackersAreInvincibleWhileAttacking': Ability(
        name='FriendlyAttackersAreInvincibleWhileAttacking',
        description='Friendly attackers (including me) don\'t take damage while attacking.',
    ),
    'OnRevealPumpFriendliesIfFullMatchingLane': lambda x, y: Ability(
        name='OnRevealPumpFriendliesIfFullMatchingLane',
        description=f'On reveal: if your side of the lane has four characters that share an element, all four characters (including me) get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'OnRevealFriendliesMakeBonusAttack': Ability(
        name='OnRevealFriendliesMakeBonusAttack',
        description='On reveal: other friendly characters make a bonus attack.',
    ),
    'SurvivePumpFriendlyAttackers': lambda x, y: Ability(
        name='SurvivePumpFriendlyAttackers',
        description=f'Survive: your friendly attackers here (including me) get +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'DeathMoveCharactersHereAndPumpThem': lambda x, y: Ability(
        name='DeathMoveCharactersHereAndPumpThem',
        description=f'Death: until the lane is full, friendly characters switch into this lane. Each one gets +{x}/+{y}.',
        number=x,
        number_2=y,
    ),
    'Twinstrike': Ability(
        name='Twinstrike',
        description='Twinstrike',
        is_keyword=True,
    ),
    'CannotSwitchLanes': Ability(
        name='CannotSwitchLanes',
        description='I can\'t switch lanes.',
    ),
    'LateFighter': Ability(
        name='LateFighter',
        description='I attack after your other characters.',
    ),
}
