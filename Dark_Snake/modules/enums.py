from enum import Enum

class GameState(Enum):
    INTRO = 0
    GAME = 1
    PAUSE = 2
    GAME_OVER = 3
    BOSS_FIGHT = 4
    SETTINGS = 5
    LEADERBOARD = 6
    CONTROLS = 7
    CUSTOMIZATION = 8

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class ItemType(Enum):
    FOOD = 0
    SPEED_BOOST = 1
    SPEED_REDUCTION = 2
    SCORE_BOOST = 3
    INVINCIBILITY = 4
    LOOT_BOX = 5
    LENGTH_SHORTENER = 6
    LENGTH_DOUBLE = 7
    DICE_EVENT = 8
    SPECIAL_DAMAGE = 9
    PROJECTILE_SHOOT = 10
