#!/usr/bin/env python3
from __future__ import annotations

import curses
import curses.ascii
import json
import os
import random
import re
import secrets
import sqlite3
import tempfile
import textwrap
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple


MAP_WIDTH = 96
MAP_HEIGHT = 48
STARTING_WOOD = 180
TICK_MS = 90
LOG_LIMIT = 6
VISION_PADDING = 1
ENEMY_ENABLED = True
FAST_SCROLL = 5
DAMAGE_FLASH_TICKS = 12
DAMAGE_MARKER_TICKS = 2
VILLAGER_TRAIN_TIME = (25_000 + TICK_MS - 1) // TICK_MS
HOUSE_BUILD_TIME = (25_000 + TICK_MS - 1) // TICK_MS
BARRACKS_UNIT_TRAIN_TIME = (21_000 + TICK_MS - 1) // TICK_MS
BARRACKS_BUILD_TIME = (50_000 + TICK_MS - 1) // TICK_MS
GATHER_RATES = {
    "gazelle": 0.41,
    "berries": 0.31,
    "tree": 0.39,
    "gold": 0.38,
    "stone": 0.36,
}
TILE_WIDTH = 2
APP_TITLE = "SSH OF EMPIRES"
MULTIPLAYER_CIV = "Hittite"
ROOM_MAX_PLAYERS = 3
ROOM_MIN_PLAYERS = 2
ROOM_CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_NAME_MAX_LEN = 24
PLAYER_NAME_MAX_LEN = 16
CHAT_MESSAGE_MAX_LEN = 120
LOBBY_DB_PATH = os.path.join(tempfile.gettempdir(), "ssh_of_empires_lobby.sqlite3")
MATCH_LEASE_SECONDS = 0.45
MATCH_MAX_CATCHUP_STEPS = 4
CURSES_ESCDELAY_MS = 250
ESCAPE_SEQUENCE_PEEK_MS = 35
ROOM_NAME_PATTERN = re.compile(r"^[A-Za-z0-9 '\-]{0,24}$")
PLAYER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9 _'\-]{1,16}$")

CTRL_B = ord("b") & 0x1F
CTRL_F = ord("f") & 0x1F
CTRL_N = ord("n") & 0x1F
CTRL_P = ord("p") & 0x1F

AGE_NAMES = ["Stone Age", "Tool Age", "Bronze Age"]

BUILDING_STATS = {
    "town_center": {"name": "Town Center", "glyph": "町", "hp": 400, "vision": 7, "cost": {"wood": 0}},
    "house": {"name": "House", "glyph": "家", "hp": 120, "vision": 4, "cost": {"wood": 35}, "pop": 4, "build_time": HOUSE_BUILD_TIME},
    "lumber_camp": {"name": "Lumber Camp", "glyph": "伐", "hp": 150, "vision": 4, "cost": {"wood": 70}},
    "mill": {"name": "Mill", "glyph": "粉", "hp": 140, "vision": 4, "cost": {"wood": 60}},
    "barracks": {"name": "Barracks", "glyph": "陣", "hp": 180, "vision": 5, "cost": {"wood": 90}, "build_time": BARRACKS_BUILD_TIME},
}

BUILD_MENU_OPTIONS = {
    ord("1"): "house",
    ord("h"): "house",
    ord("2"): "lumber_camp",
    ord("l"): "lumber_camp",
    ord("3"): "mill",
    ord("m"): "mill",
    ord("4"): "barracks",
    ord("r"): "barracks",
}

UNIT_STATS = {
    "villager": {
        "name": "Villager",
        "glyph": "民",
        "hp": 28,
        "attack": 2,
        "vision": 5,
        "speed": 1,
        "cost": {"food": 50},
        "train_time": VILLAGER_TRAIN_TIME,
        "carry": 18,
    },
    "scout": {
        "name": "Scout",
        "glyph": "馬",
        "hp": 36,
        "attack": 3,
        "vision": 8,
        "speed": 1,
        "cost": {"food": 0},
        "train_time": 0,
        "age": 0,
    },
    "clubman": {
        "name": "Clubman",
        "glyph": "兵",
        "hp": 42,
        "attack": 7,
        "vision": 5,
        "speed": 1,
        "cost": {"food": 55, "wood": 20},
        "train_time": BARRACKS_UNIT_TRAIN_TIME,
        "age": 0,
    },
    "axeman": {
        "name": "Axeman",
        "glyph": "斧",
        "hp": 56,
        "attack": 10,
        "vision": 5,
        "speed": 1,
        "cost": {"food": 65, "wood": 30},
        "train_time": BARRACKS_UNIT_TRAIN_TIME,
        "age": 1,
    },
    "swordsman": {
        "name": "Swordsman",
        "glyph": "剣",
        "hp": 72,
        "attack": 13,
        "vision": 5,
        "speed": 1,
        "cost": {"food": 80, "wood": 40},
        "train_time": BARRACKS_UNIT_TRAIN_TIME,
        "age": 2,
    },
}

ARROW_FINAL_KEYS = {
    ord("A"): curses.KEY_UP,
    ord("B"): curses.KEY_DOWN,
    ord("C"): curses.KEY_RIGHT,
    ord("D"): curses.KEY_LEFT,
}


def decode_escape_sequence(sequence: List[int]) -> Optional[int]:
    if len(sequence) < 2:
        return None
    prefix = sequence[0]
    final = sequence[-1]
    if prefix not in (ord("["), ord("O")) or final not in ARROW_FINAL_KEYS:
        return None
    modifier = "".join(chr(item) for item in sequence[1:-1] if 0 <= item < 256)
    if ";2" in modifier:
        return {
            ord("A"): getattr(curses, "KEY_SR", curses.KEY_UP),
            ord("B"): getattr(curses, "KEY_SF", curses.KEY_DOWN),
            ord("C"): getattr(curses, "KEY_SRIGHT", curses.KEY_RIGHT),
            ord("D"): getattr(curses, "KEY_SLEFT", curses.KEY_LEFT),
        }[final]
    return ARROW_FINAL_KEYS[final]


def normalize_input_key(stdscr: Optional[curses.window], key: int, restore_timeout_ms: int) -> int:
    if key != 27 or stdscr is None:
        return key
    sequence: List[int] = []
    try:
        stdscr.timeout(ESCAPE_SEQUENCE_PEEK_MS)
        for _ in range(5):
            follow_up = stdscr.getch()
            if follow_up == -1:
                break
            sequence.append(follow_up)
            if 64 <= follow_up <= 126:
                break
    finally:
        stdscr.timeout(restore_timeout_ms)
    decoded = decode_escape_sequence(sequence)
    if decoded is not None:
        return decoded
    for follow_up in reversed(sequence):
        curses.ungetch(follow_up)
    return key


def movement_delta_for_key(key: int) -> Optional[Tuple[int, int]]:
    if key in (curses.KEY_LEFT, CTRL_B):
        return (-1, 0)
    if key in (curses.KEY_DOWN, CTRL_N):
        return (0, 1)
    if key in (curses.KEY_UP, CTRL_P):
        return (0, -1)
    if key in (curses.KEY_RIGHT, CTRL_F):
        return (1, 0)
    if key == getattr(curses, "KEY_SLEFT", -1):
        return (-FAST_SCROLL, 0)
    if key == getattr(curses, "KEY_SF", -1):
        return (0, FAST_SCROLL)
    if key == getattr(curses, "KEY_SR", -1):
        return (0, -FAST_SCROLL)
    if key == getattr(curses, "KEY_SRIGHT", -1):
        return (FAST_SCROLL, 0)
    return None

AGE_ADVANCE = {
    0: {"cost": {"food": 220, "wood": 60}, "time": 80},
    1: {"cost": {"food": 360, "wood": 120}, "time": 110},
}

TECHS = {
    "economy": {
        "name": "Harvesting",
        "cost": [{"food": 80, "wood": 30}, {"food": 130, "wood": 60}],
        "time": [65, 90],
    },
    "military": {
        "name": "Weapons",
        "cost": [{"food": 90, "wood": 45}, {"food": 150, "wood": 90}],
        "time": [75, 100],
    },
}

PAIR_GRASS = 1
PAIR_FOG = 2
PAIR_UNSEEN = 3
PAIR_TREE = 4
PAIR_BERRY = 5
PAIR_GAZELLE = 6
PAIR_GOLD = 7
PAIR_STONE = 8
PAIR_PLAYER_1 = 9
PAIR_PLAYER_2 = 10
PAIR_PLAYER_3 = 11
PAIR_PANEL = 12
PAIR_PANEL_TITLE = 13
PAIR_PANEL_MUTED = 14
PAIR_ALERT = 15
PAIR_CURSOR = 16
PAIR_TEXT = 17
PAIR_FOOD = 18
PAIR_WOOD = 19
PAIR_GOLD_TEXT = 20
PAIR_STONE_TEXT = 21
PAIR_SUCCESS = 22
PAIR_PROMPT = 23
PAIR_TREE_MEMORY = 24
PAIR_BERRY_MEMORY = 25
PAIR_GAZELLE_MEMORY = 26
PAIR_GOLD_MEMORY = 27
PAIR_STONE_MEMORY = 28
PAIR_DAMAGE = 29

# Neutral UI gray with readable contrast on both black and white terminal backgrounds.
UI_CONTRAST_256 = 243

EXTENDED_THEME_PAIRS = {
    PAIR_GRASS: (120, 22),
    PAIR_FOG: (242, 236),
    PAIR_UNSEEN: (235, 233),
    PAIR_TREE: (157, 22),
    PAIR_BERRY: (218, 22),
    PAIR_GAZELLE: (223, 22),
    PAIR_GOLD: (221, 22),
    PAIR_STONE: (250, 22),
    PAIR_PLAYER_1: (51, 22),
    PAIR_PLAYER_2: (210, 22),
    PAIR_PLAYER_3: (159, 22),
    PAIR_PANEL: (UI_CONTRAST_256, -1),
    PAIR_PANEL_TITLE: (UI_CONTRAST_256, -1),
    PAIR_PANEL_MUTED: (UI_CONTRAST_256, -1),
    PAIR_ALERT: (UI_CONTRAST_256, -1),
    PAIR_CURSOR: (232, 229),
    PAIR_TEXT: (UI_CONTRAST_256, -1),
    PAIR_FOOD: (UI_CONTRAST_256, -1),
    PAIR_WOOD: (UI_CONTRAST_256, -1),
    PAIR_GOLD_TEXT: (UI_CONTRAST_256, -1),
    PAIR_STONE_TEXT: (UI_CONTRAST_256, -1),
    PAIR_SUCCESS: (UI_CONTRAST_256, -1),
    PAIR_PROMPT: (UI_CONTRAST_256, -1),
    PAIR_TREE_MEMORY: (108, -1),
    PAIR_BERRY_MEMORY: (181, -1),
    PAIR_GAZELLE_MEMORY: (187, -1),
    PAIR_GOLD_MEMORY: (186, -1),
    PAIR_STONE_MEMORY: (245, -1),
    PAIR_DAMAGE: (231, 160),
}

BASIC_THEME_PAIRS = {
    PAIR_GRASS: (curses.COLOR_GREEN, -1),
    PAIR_FOG: (curses.COLOR_BLUE, -1),
    PAIR_UNSEEN: (curses.COLOR_BLACK, -1),
    PAIR_TREE: (curses.COLOR_GREEN, -1),
    PAIR_BERRY: (curses.COLOR_RED, -1),
    PAIR_GAZELLE: (curses.COLOR_YELLOW, -1),
    PAIR_GOLD: (curses.COLOR_YELLOW, -1),
    PAIR_STONE: (curses.COLOR_WHITE, -1),
    PAIR_PLAYER_1: (curses.COLOR_BLUE, -1),
    PAIR_PLAYER_2: (curses.COLOR_RED, -1),
    PAIR_PLAYER_3: (curses.COLOR_CYAN, -1),
    PAIR_PANEL: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_PANEL_TITLE: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_PANEL_MUTED: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_ALERT: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_CURSOR: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_TEXT: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_FOOD: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_WOOD: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_GOLD_TEXT: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_STONE_TEXT: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_SUCCESS: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_PROMPT: (curses.COLOR_BLACK, curses.COLOR_WHITE),
    PAIR_TREE_MEMORY: (curses.COLOR_GREEN, -1),
    PAIR_BERRY_MEMORY: (curses.COLOR_RED, -1),
    PAIR_GAZELLE_MEMORY: (curses.COLOR_YELLOW, -1),
    PAIR_GOLD_MEMORY: (curses.COLOR_YELLOW, -1),
    PAIR_STONE_MEMORY: (curses.COLOR_WHITE, -1),
    PAIR_DAMAGE: (curses.COLOR_WHITE, curses.COLOR_RED),
}


def initialize_terminal_theme() -> str:
    if not curses.has_colors():
        return "mono"
    curses.start_color()
    try:
        curses.use_default_colors()
    except curses.error:
        pass
    pair_limit = getattr(curses, "COLOR_PAIRS", 0)
    supports_extended = getattr(curses, "COLORS", 0) >= 256 and pair_limit > max(EXTENDED_THEME_PAIRS)
    pairs = EXTENDED_THEME_PAIRS if supports_extended else BASIC_THEME_PAIRS
    for pair_id, (fg, bg) in pairs.items():
        try:
            curses.init_pair(pair_id, fg, bg)
        except curses.error:
            continue
    return "extended" if supports_extended else "basic"


def theme_color(pair_id: int) -> int:
    if not curses.has_colors():
        return 0
    return curses.color_pair(pair_id)


@dataclass
class ResourceNode:
    x: int
    y: int
    kind: str
    amount: int
    alive: bool = True
    hp: int = 0
    gatherable: bool = True

    @property
    def glyph(self) -> str:
        if self.kind == "berries":
            return "果"
        if self.kind == "tree":
            return "木"
        if self.kind == "gold":
            return "金"
        if self.kind == "stone":
            return "石"
        if self.kind == "gazelle":
            return "鹿" if self.alive else "肉"
        return "?"

    @property
    def name(self) -> str:
        if self.kind == "berries":
            return "Berry Bush"
        if self.kind == "tree":
            return "Tree"
        if self.kind == "gold":
            return "Gold Vein"
        if self.kind == "stone":
            return "Stone Outcrop"
        if self.kind == "gazelle":
            return "Gazelle" if self.alive else "Carcass"
        return self.kind

    @property
    def resource_type(self) -> str:
        if self.kind == "tree":
            return "wood"
        if self.kind == "gold":
            return "gold"
        if self.kind == "stone":
            return "stone"
        return "food"

    def visible_name(self) -> str:
        if self.kind == "gazelle" and self.alive:
            return f"{self.name} hp:{self.hp}"
        if self.kind == "gazelle" and not self.gatherable:
            return self.name
        return f"{self.name} {self.amount}"


@dataclass
class ProductionItem:
    kind: str
    target: Optional[str]
    time_left: int


@dataclass
class Building:
    id: int
    owner: int
    kind: str
    x: int
    y: int
    hp: int
    max_hp: int
    complete: bool = True
    build_progress: int = 0
    build_time: int = 0
    queue: List[ProductionItem] = field(default_factory=list)

    @property
    def glyph(self) -> str:
        glyph = BUILDING_STATS[self.kind]["glyph"]
        return glyph if self.complete else "+"

    @property
    def name(self) -> str:
        return BUILDING_STATS[self.kind]["name"]

    @property
    def vision(self) -> int:
        return BUILDING_STATS[self.kind]["vision"]

    @property
    def pop_bonus(self) -> int:
        return BUILDING_STATS[self.kind].get("pop", 0)


@dataclass
class Unit:
    id: int
    owner: int
    kind: str
    x: int
    y: int
    hp: int
    max_hp: int
    state: str = "idle"
    target: Optional[Tuple[str, int]] = None
    destination: Optional[Tuple[int, int]] = None
    attack_cooldown: int = 0
    carrying: Dict[str, int] = field(default_factory=lambda: {"food": 0, "wood": 0, "gold": 0, "stone": 0})
    build_target: Optional[int] = None
    gather_progress: float = 0.0

    @property
    def glyph(self) -> str:
        return UNIT_STATS[self.kind]["glyph"]

    @property
    def name(self) -> str:
        return UNIT_STATS[self.kind]["name"]

    @property
    def vision(self) -> int:
        return UNIT_STATS[self.kind]["vision"]

    @property
    def attack(self) -> int:
        return UNIT_STATS[self.kind]["attack"]

    @property
    def carry_capacity(self) -> int:
        return UNIT_STATS[self.kind].get("carry", 0)

    def total_carry(self) -> int:
        return sum(self.carrying.values())


@dataclass
class PlayerState:
    id: int
    name: str
    civ: str
    food: int = 200
    wood: int = STARTING_WOOD
    gold: int = 0
    stone: int = 0
    age: int = 0
    economy_level: int = 0
    military_level: int = 0
    ageing: Optional[ProductionItem] = None
    pop_cap: int = 4
    explored: List[List[bool]] = field(default_factory=list)
    visible: Set[Tuple[int, int]] = field(default_factory=set)
    discovered_resources: Set[int] = field(default_factory=set)
    logs_prefix: str = ""

    def resource_dict(self) -> Dict[str, int]:
        return {"food": self.food, "wood": self.wood, "gold": self.gold, "stone": self.stone}

    def can_afford(self, cost: Dict[str, int]) -> bool:
        return (
            self.food >= cost.get("food", 0)
            and self.wood >= cost.get("wood", 0)
            and self.gold >= cost.get("gold", 0)
            and self.stone >= cost.get("stone", 0)
        )

    def spend(self, cost: Dict[str, int]) -> bool:
        if not self.can_afford(cost):
            return False
        self.food -= cost.get("food", 0)
        self.wood -= cost.get("wood", 0)
        self.gold -= cost.get("gold", 0)
        self.stone -= cost.get("stone", 0)
        return True


class Game:
    def __init__(
        self,
        stdscr: Optional[curses.window],
        local_player_id: int = 0,
        player_specs: Optional[List[Tuple[str, str]]] = None,
        enable_ai: bool = ENEMY_ENABLED,
        seed: int = 7,
        init_world: bool = True,
    ) -> None:
        self.stdscr = stdscr
        self.local_player_id = local_player_id
        self.enable_ai = enable_ai
        self.seed = seed
        self.rng = random.Random(seed)
        self.next_id = 1
        self.resources: Dict[int, ResourceNode] = {}
        self.buildings: Dict[int, Building] = {}
        self.units: Dict[int, Unit] = {}
        specs = player_specs or [("You", "Yamato")] + ([("Enemy", "Shang")] if enable_ai else [])
        self.players = [PlayerState(idx, name, civ) for idx, (name, civ) in enumerate(specs)]
        self.base_starts = self.default_spawn_positions(len(self.players))
        for player in self.players:
            player.explored = [[False for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.player_logs: List[List[str]] = [[] for _ in self.players]
        self.cursor_x = 10
        self.cursor_y = 10
        self.camera_x = 0
        self.camera_y = 0
        self.selected_kind: Optional[str] = None
        self.selected_id: Optional[int] = None
        self.selected_unit_ids: List[int] = []
        self.build_menu_open = False
        self.command_mode = False
        self.command_buffer = ""
        self.vim_count = ""
        self.vim_pending = ""
        self.vim_marks: Dict[str, Tuple[int, int]] = {}
        self.last_colon_command: Optional[str] = None
        self.running = True
        self.tick = 0
        self.winner: Optional[int] = None
        self.theme_mode = "mono"
        self.damage_flashes: Dict[str, int] = {}
        self.ai_memory = {"last_house_tick": -999, "last_attack_tick": -999, "last_scout_tick": -999} if enable_ai else {}
        if init_world:
            self._init_world()
            self.reveal_visibility()

    def _append_log(self, player_id: int, line: str) -> None:
        if player_id < 0 or player_id >= len(self.player_logs):
            return
        self.player_logs[player_id].append(line)
        self.player_logs[player_id] = self.player_logs[player_id][-LOG_LIMIT:]

    def _log(self, message: str, player_id: Optional[int] = None) -> None:
        stamp = f"[{self.tick:04d}] {message}"
        target = self.local_player_id if player_id is None else player_id
        self._append_log(target, stamp)

    def _log_many(self, message: str, player_ids: Iterable[int]) -> None:
        stamp = f"[{self.tick:04d}] {message}"
        seen: Set[int] = set()
        for player_id in player_ids:
            if player_id in seen:
                continue
            seen.add(player_id)
            self._append_log(player_id, stamp)

    def visible_logs(self) -> List[str]:
        if self.local_player_id < 0 or self.local_player_id >= len(self.player_logs):
            return []
        return self.player_logs[self.local_player_id]

    def _new_id(self) -> int:
        value = self.next_id
        self.next_id += 1
        return value

    def glyph_display_width(self, text: str) -> int:
        if not text:
            return 0
        width = 0
        for char in text:
            width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
        return width

    def safe_addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        if self.stdscr is None:
            return
        height, width = self.stdscr.getmaxyx()
        if y < 0 or y >= height or x >= width:
            return
        available = max(0, width - x)
        if available <= 0:
            return
        try:
            self.stdscr.addstr(y, x, text[:available], attr)
        except curses.error:
            pass

    def theme_attr(self, pair_id: int, extra: int = 0) -> int:
        return theme_color(pair_id) | extra

    def draw_box(
        self,
        y: int,
        x: int,
        h: int,
        w: int,
        title: Optional[str] = None,
        border_attr: int = 0,
        title_attr: int = 0,
        fill_attr: int = 0,
    ) -> None:
        if h < 3 or w < 4:
            return
        self.safe_addstr(y, x, "╔" + ("═" * (w - 2)) + "╗", border_attr)
        fill = " " * max(0, w - 2)
        for row in range(1, h - 1):
            self.safe_addstr(y + row, x, "║", border_attr)
            if fill_attr:
                self.safe_addstr(y + row, x + 1, fill, fill_attr)
            self.safe_addstr(y + row, x + w - 1, "║", border_attr)
        self.safe_addstr(y + h - 1, x, "╚" + ("═" * (w - 2)) + "╝", border_attr)
        if title:
            label = f" {title[: max(0, w - 4)]} "
            start = x + max(1, (w - len(label)) // 2)
            self.safe_addstr(y, start, label[: max(0, w - 2)], title_attr or border_attr)

    @staticmethod
    def meter(current: int, total: int, width: int) -> str:
        width = max(1, width)
        if total <= 0:
            return "░" * width
        filled = max(0, min(width, int(round((current / total) * width))))
        return ("█" * filled) + ("░" * (width - filled))

    def wrap_panel_lines(self, lines: List[str], width: int) -> List[str]:
        wrapped: List[str] = []
        for line in lines:
            wrapped.extend(textwrap.wrap(line, max(8, width)) or [""])
        return wrapped

    def describe_target_ref(self, target: Optional[Tuple[str, int]]) -> str:
        if not target:
            return "None"
        kind, target_id = target
        if kind == "resource":
            node = self.resources.get(target_id)
            return node.visible_name() if node else "resource"
        if kind == "unit":
            unit = self.units.get(target_id)
            return f"{self.owner_label(unit.owner)} {unit.name}" if unit else "unit"
        if kind == "building":
            building = self.buildings.get(target_id)
            return f"{self.owner_label(building.owner)} {building.name}" if building else "building"
        return kind

    def production_total_time(self, building: Building, item: ProductionItem) -> int:
        if item.kind == "unit" and item.target in UNIT_STATS:
            return int(UNIT_STATS[item.target]["train_time"])
        owner = self.players[building.owner]
        if item.kind == "tech" and item.target == "economy":
            return int(TECHS["economy"]["time"][owner.economy_level])
        if item.kind == "tech" and item.target == "military":
            return int(TECHS["military"]["time"][owner.military_level])
        return max(1, item.time_left)

    def remembered_resource_attr(self, kind: str) -> int:
        if kind == "tree":
            return self.theme_attr(PAIR_TREE_MEMORY, curses.A_DIM)
        if kind == "berries":
            return self.theme_attr(PAIR_BERRY_MEMORY, curses.A_DIM)
        if kind == "gold":
            return self.theme_attr(PAIR_GOLD_MEMORY, curses.A_DIM)
        if kind == "stone":
            return self.theme_attr(PAIR_STONE_MEMORY, curses.A_DIM)
        return self.theme_attr(PAIR_GAZELLE_MEMORY, curses.A_DIM)

    @staticmethod
    def damage_flash_key(entity_kind: str, entity_id: int) -> str:
        return f"{entity_kind}:{entity_id}"

    def mark_damage(self, entity_kind: str, entity_id: int) -> None:
        if entity_kind not in {"unit", "building"}:
            return
        self.damage_flashes[self.damage_flash_key(entity_kind, entity_id)] = self.tick + DAMAGE_FLASH_TICKS

    def damage_flash_remaining(self, entity_kind: str, entity_id: int) -> int:
        expires_at = self.damage_flashes.get(self.damage_flash_key(entity_kind, entity_id), -1)
        return max(0, expires_at - self.tick)

    def prune_damage_flashes(self) -> None:
        expired = [key for key, expires_at in self.damage_flashes.items() if expires_at <= self.tick]
        for key in expired:
            del self.damage_flashes[key]

    def selected_panel_lines(self, obj: object, width: int) -> List[str]:
        meter_w = max(8, min(14, width - 10))
        if obj is None:
            return ["No unit or building selected."]
        lines: List[str] = []
        if isinstance(obj, Unit):
            lines.append(f"{obj.name} · {self.owner_label(obj.owner)}")
            if self.damage_flash_remaining("unit", obj.id):
                lines.append("!! UNDER ATTACK")
            lines.append(f"State {obj.state} · ATK {obj.attack} · VIS {obj.vision}")
            lines.append(f"HP {obj.hp}/{obj.max_hp} {self.meter(obj.hp, obj.max_hp, meter_w)}")
            if obj.kind == "villager":
                carry_bits = [f"{kind[0].upper()}{amount}" for kind, amount in obj.carrying.items() if amount]
                carry_text = " ".join(carry_bits) if carry_bits else "empty"
                lines.append(f"Carry {carry_text} / {obj.carry_capacity}")
            if obj.target:
                lines.append(f"Target {self.describe_target_ref(obj.target)}")
            elif obj.destination:
                lines.append(f"Move to {obj.destination[0]},{obj.destination[1]}")
        elif isinstance(obj, Building):
            lines.append(f"{obj.name} · {self.owner_label(obj.owner)}")
            if self.damage_flash_remaining("building", obj.id):
                lines.append("!! UNDER ATTACK")
            lines.append(f"HP {obj.hp}/{obj.max_hp} {self.meter(obj.hp, obj.max_hp, meter_w)}")
            if not obj.complete:
                lines.append(f"Build {obj.build_progress}/{obj.build_time} {self.meter(obj.build_progress, obj.build_time, meter_w)}")
            if obj.queue:
                current = obj.queue[0]
                target = current.target or current.kind
                total = self.production_total_time(obj, current)
                lines.append(f"Queue {target} ({current.time_left}t)")
                lines.append(f"Prod {self.meter(total - current.time_left, total, meter_w)}")
        elif isinstance(obj, ResourceNode):
            lines.append(obj.name)
            if obj.kind == "gazelle" and obj.alive:
                lines.append(f"HP {obj.hp} · Food {obj.amount}")
            elif obj.kind == "gazelle" and not obj.gatherable:
                lines.append("No usable food remains.")
            else:
                lines.append(f"Remaining {obj.amount}")
        return self.wrap_panel_lines(lines, width)

    def cell_text(self, glyph: str) -> str:
        width = self.glyph_display_width(glyph)
        if width >= TILE_WIDTH:
            return glyph
        return glyph + (" " * (TILE_WIDTH - width))

    @staticmethod
    def default_spawn_positions(player_count: int) -> List[Tuple[int, int]]:
        starts = [
            (8, 8),
            (MAP_WIDTH - 9, MAP_HEIGHT - 9),
            (MAP_WIDTH - 9, 8),
        ]
        return starts[:player_count]

    def current_player(self) -> PlayerState:
        return self.players[self.local_player_id]

    def owner_label(self, owner: int) -> str:
        return "You" if owner == self.local_player_id else self.players[owner].name

    def initialize_curses(self) -> None:
        if self.stdscr is None:
            return
        if hasattr(curses, "set_escdelay"):
            curses.set_escdelay(CURSES_ESCDELAY_MS)
        self.stdscr.keypad(True)
        self.theme_mode = initialize_terminal_theme()

    def owner_color_pair(self, owner: int) -> int:
        palette = [PAIR_PLAYER_1, PAIR_PLAYER_2, PAIR_PLAYER_3]
        return self.theme_attr(palette[owner % len(palette)])

    def serialize_state(self) -> str:
        return json.dumps(
            {
                "seed": self.seed,
                "enable_ai": self.enable_ai,
                "next_id": self.next_id,
                "tick": self.tick,
                "winner": self.winner,
                "player_logs": [list(lines) for lines in self.player_logs],
                "damage_flashes": dict(self.damage_flashes),
                "ai_memory": self.ai_memory,
                "players": [
                    {
                        "id": player.id,
                        "name": player.name,
                        "civ": player.civ,
                        "food": player.food,
                        "wood": player.wood,
                        "gold": player.gold,
                        "stone": player.stone,
                        "age": player.age,
                        "economy_level": player.economy_level,
                        "military_level": player.military_level,
                        "ageing": (
                            {
                                "kind": player.ageing.kind,
                                "target": player.ageing.target,
                                "time_left": player.ageing.time_left,
                            }
                            if player.ageing
                            else None
                        ),
                        "pop_cap": player.pop_cap,
                        "explored": player.explored,
                        "discovered_resources": sorted(player.discovered_resources),
                    }
                    for player in self.players
                ],
                "resources": [
                    {
                        "id": rid,
                        "x": node.x,
                        "y": node.y,
                        "kind": node.kind,
                        "amount": node.amount,
                        "alive": node.alive,
                        "hp": node.hp,
                        "gatherable": node.gatherable,
                    }
                    for rid, node in sorted(self.resources.items())
                ],
                "buildings": [
                    {
                        "id": building.id,
                        "owner": building.owner,
                        "kind": building.kind,
                        "x": building.x,
                        "y": building.y,
                        "hp": building.hp,
                        "max_hp": building.max_hp,
                        "complete": building.complete,
                        "build_progress": building.build_progress,
                        "build_time": building.build_time,
                        "queue": [
                            {"kind": item.kind, "target": item.target, "time_left": item.time_left}
                            for item in building.queue
                        ],
                    }
                    for building in sorted(self.buildings.values(), key=lambda item: item.id)
                ],
                "units": [
                    {
                        "id": unit.id,
                        "owner": unit.owner,
                        "kind": unit.kind,
                        "x": unit.x,
                        "y": unit.y,
                        "hp": unit.hp,
                        "max_hp": unit.max_hp,
                        "state": unit.state,
                        "target": list(unit.target) if unit.target else None,
                        "destination": list(unit.destination) if unit.destination else None,
                        "attack_cooldown": unit.attack_cooldown,
                        "carrying": unit.carrying,
                        "build_target": unit.build_target,
                        "gather_progress": unit.gather_progress,
                    }
                    for unit in sorted(self.units.values(), key=lambda item: item.id)
                ],
            },
            separators=(",", ":"),
        )

    def restore_serialized_state(self, serialized: str) -> None:
        self.restore_state_dict(json.loads(serialized))

    def restore_state_dict(self, data: Dict[str, object]) -> None:
        self.seed = int(data.get("seed", 7))
        self.enable_ai = bool(data.get("enable_ai", False))
        self.next_id = int(data["next_id"])
        self.tick = int(data["tick"])
        winner = data.get("winner")
        self.winner = None if winner is None else int(winner)
        self.damage_flashes = {str(key): int(value) for key, value in dict(data.get("damage_flashes", {})).items()}
        self.ai_memory = dict(data.get("ai_memory", {}))
        self.players = []
        for item in data["players"]:
            ageing_data = item.get("ageing")
            player = PlayerState(
                id=int(item["id"]),
                name=str(item["name"]),
                civ=str(item["civ"]),
                food=int(item["food"]),
                wood=int(item["wood"]),
                gold=int(item["gold"]),
                stone=int(item["stone"]),
                age=int(item["age"]),
                economy_level=int(item["economy_level"]),
                military_level=int(item["military_level"]),
                ageing=(
                    ProductionItem(
                        kind=str(ageing_data["kind"]),
                        target=ageing_data["target"],
                        time_left=int(ageing_data["time_left"]),
                    )
                    if ageing_data
                    else None
                ),
                pop_cap=int(item["pop_cap"]),
                explored=item["explored"],
                discovered_resources={int(rid) for rid in item.get("discovered_resources", [])},
            )
            self.players.append(player)
        self.player_logs = [[] for _ in self.players]
        raw_player_logs = data.get("player_logs")
        if isinstance(raw_player_logs, list):
            for idx, lines in enumerate(raw_player_logs[: len(self.player_logs)]):
                if isinstance(lines, list):
                    self.player_logs[idx] = [str(line) for line in lines[-LOG_LIMIT:]]
        else:
            legacy_logs = data.get("logs", [])
            if isinstance(legacy_logs, list):
                shared_lines = [str(line) for line in legacy_logs[-LOG_LIMIT:]]
                self.player_logs = [list(shared_lines) for _ in self.players]
        self.base_starts = self.default_spawn_positions(len(self.players))
        self.resources = {}
        for item in data["resources"]:
            self.resources[int(item["id"])] = ResourceNode(
                x=int(item["x"]),
                y=int(item["y"]),
                kind=str(item["kind"]),
                amount=int(item["amount"]),
                alive=bool(item["alive"]),
                hp=int(item["hp"]),
                gatherable=bool(item.get("gatherable", True)),
            )
        self.buildings = {}
        for item in data["buildings"]:
            self.buildings[int(item["id"])] = Building(
                id=int(item["id"]),
                owner=int(item["owner"]),
                kind=str(item["kind"]),
                x=int(item["x"]),
                y=int(item["y"]),
                hp=int(item["hp"]),
                max_hp=int(item["max_hp"]),
                complete=bool(item["complete"]),
                build_progress=int(item["build_progress"]),
                build_time=int(item["build_time"]),
                queue=[
                    ProductionItem(kind=str(queue_item["kind"]), target=queue_item["target"], time_left=int(queue_item["time_left"]))
                    for queue_item in item["queue"]
                ],
            )
        self.units = {}
        for item in data["units"]:
            target = item.get("target")
            destination = item.get("destination")
            self.units[int(item["id"])] = Unit(
                id=int(item["id"]),
                owner=int(item["owner"]),
                kind=str(item["kind"]),
                x=int(item["x"]),
                y=int(item["y"]),
                hp=int(item["hp"]),
                max_hp=int(item["max_hp"]),
                state=str(item["state"]),
                target=(str(target[0]), int(target[1])) if target else None,
                destination=(int(destination[0]), int(destination[1])) if destination else None,
                attack_cooldown=int(item["attack_cooldown"]),
                carrying={key: int(value) for key, value in item["carrying"].items()},
                build_target=None if item["build_target"] is None else int(item["build_target"]),
                gather_progress=float(item["gather_progress"]),
            )
        self.reveal_visibility()

    @classmethod
    def from_serialized(cls, stdscr: Optional[curses.window], serialized: str, local_player_id: int) -> "Game":
        data = json.loads(serialized)
        player_specs = [(str(player["name"]), str(player["civ"])) for player in data["players"]]
        game = cls(
            stdscr,
            local_player_id=local_player_id,
            player_specs=player_specs,
            enable_ai=bool(data.get("enable_ai", False)),
            seed=int(data.get("seed", 7)),
            init_world=False,
        )
        game.restore_state_dict(data)
        return game

    def _init_world(self) -> None:
        self._generate_resources()
        self._spawn_starting_base(0, 8, 8)
        if self.enable_ai:
            self._spawn_starting_base(1, MAP_WIDTH - 9, MAP_HEIGHT - 9)
        elif len(self.base_starts) > 1:
            for owner, (x, y) in enumerate(self.base_starts[1:], start=1):
                self._spawn_starting_base(owner, x, y)
        self.cursor_x = 8
        self.cursor_y = 8
        self._log("SSH of Empires ready. Select with <space>, act with a, build with b.")

    def _generate_resources(self) -> None:
        for center_x, center_y in [(12, 12), (MAP_WIDTH - 13, MAP_HEIGHT - 13), (MAP_WIDTH // 2, MAP_HEIGHT // 2)]:
            self._berry_patch(center_x, center_y, 8)
            self._tree_patch(center_x + 6, center_y - 3, 12)
            self._gold_patch(center_x - 1, center_y - 5, 5)
            self._stone_patch(center_x + 3, center_y + 5, 5)
            self._gazelles(center_x - 5, center_y + 3, 4)
        for _ in range(10):
            self._berry_patch(self.rng.randint(5, MAP_WIDTH - 6), self.rng.randint(5, MAP_HEIGHT - 6), 6)
            self._tree_patch(self.rng.randint(5, MAP_WIDTH - 6), self.rng.randint(5, MAP_HEIGHT - 6), 8)
            self._gold_patch(self.rng.randint(5, MAP_WIDTH - 6), self.rng.randint(5, MAP_HEIGHT - 6), 4)
            self._stone_patch(self.rng.randint(5, MAP_WIDTH - 6), self.rng.randint(5, MAP_HEIGHT - 6), 4)
            self._gazelles(self.rng.randint(5, MAP_WIDTH - 6), self.rng.randint(5, MAP_HEIGHT - 6), 3)

    def _berry_patch(self, cx: int, cy: int, count: int) -> None:
        for _ in range(count):
            x = max(1, min(MAP_WIDTH - 2, cx + self.rng.randint(-2, 2)))
            y = max(1, min(MAP_HEIGHT - 2, cy + self.rng.randint(-2, 2)))
            if not self.resource_at(x, y) and not self.is_base_start(x, y):
                node = ResourceNode(x, y, "berries", self.rng.randint(70, 100))
                self.resources[self._new_id()] = node

    def _tree_patch(self, cx: int, cy: int, count: int) -> None:
        for _ in range(count):
            x = max(1, min(MAP_WIDTH - 2, cx + self.rng.randint(-3, 3)))
            y = max(1, min(MAP_HEIGHT - 2, cy + self.rng.randint(-2, 2)))
            if not self.resource_at(x, y) and not self.is_base_start(x, y):
                node = ResourceNode(x, y, "tree", self.rng.randint(90, 130))
                self.resources[self._new_id()] = node

    def _gold_patch(self, cx: int, cy: int, count: int) -> None:
        for _ in range(count):
            x = max(1, min(MAP_WIDTH - 2, cx + self.rng.randint(-2, 2)))
            y = max(1, min(MAP_HEIGHT - 2, cy + self.rng.randint(-2, 2)))
            if not self.resource_at(x, y) and not self.is_base_start(x, y):
                node = ResourceNode(x, y, "gold", self.rng.randint(140, 190))
                self.resources[self._new_id()] = node

    def _stone_patch(self, cx: int, cy: int, count: int) -> None:
        for _ in range(count):
            x = max(1, min(MAP_WIDTH - 2, cx + self.rng.randint(-2, 2)))
            y = max(1, min(MAP_HEIGHT - 2, cy + self.rng.randint(-2, 2)))
            if not self.resource_at(x, y) and not self.is_base_start(x, y):
                node = ResourceNode(x, y, "stone", self.rng.randint(130, 180))
                self.resources[self._new_id()] = node

    def _gazelles(self, cx: int, cy: int, count: int) -> None:
        for _ in range(count):
            x = max(1, min(MAP_WIDTH - 2, cx + self.rng.randint(-2, 2)))
            y = max(1, min(MAP_HEIGHT - 2, cy + self.rng.randint(-2, 2)))
            if not self.resource_at(x, y) and not self.is_base_start(x, y):
                node = ResourceNode(x, y, "gazelle", self.rng.randint(65, 85), alive=True, hp=14)
                self.resources[self._new_id()] = node

    def is_base_start(self, x: int, y: int) -> bool:
        return any(abs(x - px) <= 4 and abs(y - py) <= 4 for px, py in self.base_starts)

    def _spawn_starting_base(self, owner: int, x: int, y: int) -> None:
        tc = self.add_building(owner, "town_center", x, y, complete=True)
        self.players[owner].pop_cap = 4
        for dx, dy in [(1, 0), (0, 1), (1, 1)]:
            self.add_unit(owner, "villager", x + dx, y + dy)
        self.add_unit(owner, "scout", x + 2, y)
        self._log(f"{self.players[owner].name} starts with a Town Center, 3 villagers, and 1 scout.", player_id=owner)
        if owner == self.local_player_id and self.selected_id is None:
            self.selected_kind = "building"
            self.selected_id = tc.id

    def add_building(self, owner: int, kind: str, x: int, y: int, complete: bool = False) -> Building:
        stats = BUILDING_STATS[kind]
        building = Building(
            id=self._new_id(),
            owner=owner,
            kind=kind,
            x=x,
            y=y,
            hp=stats["hp"] if complete else max(1, stats["hp"] // 5),
            max_hp=stats["hp"],
            complete=complete,
            build_progress=stats["hp"] if complete else 0,
            build_time=stats.get("build_time", max(20, stats["hp"] // 4)),
        )
        self.buildings[building.id] = building
        if complete:
            self.players[owner].pop_cap += building.pop_bonus
        return building

    def add_unit(self, owner: int, kind: str, x: int, y: int) -> Optional[Unit]:
        if not self.tile_open(x, y):
            for nx, ny in self.neighbors8(x, y):
                if self.tile_open(nx, ny):
                    x, y = nx, ny
                    break
            else:
                return None
        stats = UNIT_STATS[kind]
        unit = Unit(
            id=self._new_id(),
            owner=owner,
            kind=kind,
            x=x,
            y=y,
            hp=stats["hp"],
            max_hp=stats["hp"],
        )
        self.units[unit.id] = unit
        return unit

    def neighbors8(self, x: int, y: int) -> Iterable[Tuple[int, int]]:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                    yield nx, ny

    def resource_at(self, x: int, y: int) -> Optional[Tuple[int, ResourceNode]]:
        for rid, node in self.resources.items():
            if node.x == x and node.y == y and node.amount > 0:
                return rid, node
        return None

    def resource_memory_at(self, owner: int, x: int, y: int) -> Optional[Tuple[int, ResourceNode]]:
        resource = self.resource_at(x, y)
        if resource and resource[0] in self.players[owner].discovered_resources:
            return resource
        return None

    def unit_at(self, x: int, y: int) -> Optional[Unit]:
        for unit in self.units.values():
            if unit.x == x and unit.y == y:
                return unit
        return None

    def building_at(self, x: int, y: int) -> Optional[Building]:
        for building in self.buildings.values():
            if building.x == x and building.y == y:
                return building
        return None

    def tile_open(self, x: int, y: int) -> bool:
        if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
            return False
        if self.unit_at(x, y) or self.building_at(x, y):
            return False
        return True

    def player_population(self, owner: int) -> int:
        return sum(1 for unit in self.units.values() if unit.owner == owner)

    def tile_visible_to(self, owner: int, x: int, y: int) -> bool:
        return (x, y) in self.players[owner].visible

    def reveal_visibility(self) -> None:
        for player in self.players:
            player.visible = set()
        for unit in self.units.values():
            self._reveal_owner(unit.owner, unit.x, unit.y, unit.vision)
        for building in self.buildings.values():
            if building.complete:
                self._reveal_owner(building.owner, building.x, building.y, building.vision)

    def _reveal_owner(self, owner: int, cx: int, cy: int, radius: int) -> None:
        player = self.players[owner]
        for y in range(max(0, cy - radius), min(MAP_HEIGHT, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(MAP_WIDTH, cx + radius + 1)):
                if abs(x - cx) + abs(y - cy) <= radius + VISION_PADDING:
                    player.visible.add((x, y))
                    player.explored[y][x] = True
                    resource = self.resource_at(x, y)
                    if resource:
                        player.discovered_resources.add(resource[0])

    def sanitize_selection_visibility(self) -> None:
        selected = self.get_selected()
        if not isinstance(selected, Unit):
            return
        if selected.owner == self.local_player_id:
            return
        if self.tile_visible_to(self.local_player_id, selected.x, selected.y):
            return
        self.selected_kind = None
        self.selected_id = None

    def run(self) -> None:
        if self.stdscr is None:
            return
        curses.curs_set(0)
        self.initialize_curses()
        self.stdscr.nodelay(True)
        self.stdscr.timeout(TICK_MS)
        while self.running:
            self.handle_input()
            self.update()
            self.render()
        self.stdscr.nodelay(False)

    def handle_input(self) -> None:
        key = self.stdscr.getch()
        if key == -1:
            return
        key = normalize_input_key(self.stdscr, key, TICK_MS)
        vim_result = self.handle_vim_input(key)
        if vim_result == "quit":
            self.running = False
            return
        if vim_result == "handled":
            return
        if self.build_menu_open:
            self.handle_build_menu_input(key)
            return
        if key == ord("q"):
            self.running = False
            return
        movement = movement_delta_for_key(key)
        if movement is not None:
            self.move_cursor(*movement)
        elif key in (ord(" "), 10, 13):
            self.select_at_cursor()
        elif key == 9:
            self.cycle_selection()
        elif key in (ord("x"), 27):
            self.selected_id = None
            self.selected_kind = None
            self.selected_unit_ids = []
            self.build_menu_open = False
        elif key in (ord("a"), curses.ascii.NUL):
            self.issue_context_command()
        elif key == ord("b"):
            self.open_build_menu()
        elif key == ord("v"):
            self.queue_villager()
        elif key == ord("s"):
            self.queue_military()
        elif key == ord("n"):
            self.try_advance_age()
        elif key == ord("t"):
            self.try_research()

    def move_cursor(self, dx: int, dy: int) -> None:
        self.cursor_x = max(0, min(MAP_WIDTH - 1, self.cursor_x + dx))
        self.cursor_y = max(0, min(MAP_HEIGHT - 1, self.cursor_y + dy))

    def handle_vim_input(
        self,
        key: int,
        queue_payload: Optional[Callable[[Dict[str, object]], None]] = None,
    ) -> Optional[str]:
        if self.command_mode:
            return self.handle_command_mode_input(key, queue_payload)
        if self.build_menu_open:
            return None
        if key == ord(":"):
            self.command_mode = True
            self.command_buffer = ""
            self.vim_count = ""
            self.vim_pending = ""
            return "handled"
        if key == ord("."):
            if self.last_colon_command:
                return self.execute_colon_command(self.last_colon_command, queue_payload, from_repeat=True)
            self._log("No command to repeat.")
            return "handled"
        if key == 27:
            self.vim_count = ""
            self.vim_pending = ""
            return None
        if not 0 <= key < 256:
            self.vim_count = ""
            self.vim_pending = ""
            return None

        ch = chr(key)
        if self.vim_pending == "g":
            self.vim_pending = ""
            if ch == "g":
                self.jump_home()
                return "handled"
            self._log("Unknown g command.")
            return "handled"
        if self.vim_pending == "m":
            self.vim_pending = ""
            if ch.isalnum():
                self.vim_marks[ch] = (self.cursor_x, self.cursor_y)
                self._log(f"Marked {ch} at {self.cursor_x},{self.cursor_y}.")
            return "handled"
        if self.vim_pending == "'":
            self.vim_pending = ""
            mark = self.vim_marks.get(ch)
            if mark:
                self.cursor_x, self.cursor_y = mark
                self.keep_cursor_visible()
                self._log(f"Jumped to mark {ch}.")
            else:
                self._log(f"Mark {ch} is not set.")
            return "handled"

        if ch.isdigit() and (ch != "0" or self.vim_count):
            self.vim_count += ch
            return "handled"

        count = int(self.vim_count) if self.vim_count else 1
        self.vim_count = ""
        if ch in ("h", "j", "k", "l"):
            dx, dy = {"h": (-count, 0), "j": (0, count), "k": (0, -count), "l": (count, 0)}[ch]
            self.move_cursor(dx, dy)
            return "handled"
        if ch == "g":
            self.vim_pending = "g"
            return "handled"
        if ch == "G":
            self.jump_to_alert_or_enemy()
            return "handled"
        if ch == "m":
            self.vim_pending = "m"
            return "handled"
        if ch == "'":
            self.vim_pending = "'"
            return "handled"
        if count > 1 and ch == "v":
            self.queue_selected_production("villager", count, queue_payload)
            return "handled"
        if count > 1 and ch == "s":
            self.queue_selected_production("military", count, queue_payload)
            return "handled"
        return None

    def handle_command_mode_input(
        self,
        key: int,
        queue_payload: Optional[Callable[[Dict[str, object]], None]],
    ) -> Optional[str]:
        if key in (27,):
            self.command_mode = False
            self.command_buffer = ""
            self._log("Command cancelled.")
            return "handled"
        if key in (10, 13, curses.KEY_ENTER):
            text = self.command_buffer.strip()
            self.command_mode = False
            self.command_buffer = ""
            if not text:
                return "handled"
            return self.execute_colon_command(text, queue_payload)
        if key in (curses.KEY_BACKSPACE, 127, 8):
            self.command_buffer = self.command_buffer[:-1]
            return "handled"
        if 0 <= key < 256:
            ch = chr(key)
            if ch.isprintable() and len(self.command_buffer) < 96:
                self.command_buffer += ch
            return "handled"
        return "handled"

    def execute_colon_command(
        self,
        text: str,
        queue_payload: Optional[Callable[[Dict[str, object]], None]] = None,
        from_repeat: bool = False,
    ) -> Optional[str]:
        command = text.strip()
        if not command:
            return "handled"
        lowered = command.lower()
        if lowered in ("q", "quit", "leave"):
            return "quit"
        if lowered in ("help", "commands"):
            self._log("Agent commands: select, gather, attack, queue, build, jump, mark.")
            return "handled"
        tokens = lowered.split()
        if not tokens:
            return "handled"
        handled = False
        if tokens[0] == "select":
            handled = self.command_select(tokens[1:])
        elif tokens[0] == "gather":
            handled = self.command_gather(tokens[1:], queue_payload)
        elif tokens[0] == "attack":
            handled = self.command_attack(tokens[1:], queue_payload)
        elif tokens[0] == "queue":
            handled = self.command_queue(tokens[1:], queue_payload)
        elif tokens[0] == "build":
            handled = self.command_build(tokens[1:], queue_payload)
        elif tokens[0] == "jump":
            handled = self.command_jump(tokens[1:])
        elif tokens[0] == "mark":
            handled = self.command_mark(tokens[1:])
        elif tokens[0] == "move":
            handled = self.command_move(tokens[1:], queue_payload)
        if handled:
            if not from_repeat:
                self.last_colon_command = command
            return "handled"
        self._log("Unknown command. Try :help.")
        return "handled"

    def emit_player_command(
        self,
        payload: Dict[str, object],
        queue_payload: Optional[Callable[[Dict[str, object]], None]],
    ) -> None:
        payload["owner"] = self.local_player_id
        if queue_payload is not None:
            queue_payload(payload)
        else:
            self.apply_command(payload)

    def selected_owned_units(self) -> List[Unit]:
        units: List[Unit] = []
        seen: Set[int] = set()
        for unit_id in self.selected_unit_ids:
            unit = self.units.get(unit_id)
            if unit and unit.owner == self.local_player_id and unit.id not in seen:
                units.append(unit)
                seen.add(unit.id)
        selected = self.get_selected()
        if isinstance(selected, Unit) and selected.owner == self.local_player_id and selected.id not in seen:
            units.append(selected)
        self.selected_unit_ids = [unit.id for unit in units if unit.hp > 0]
        return [unit for unit in units if unit.hp > 0]

    def set_selected_units(self, units: List[Unit]) -> bool:
        owned = [unit for unit in units if unit.owner == self.local_player_id and unit.hp > 0]
        if not owned:
            self._log("No matching units found.")
            return False
        self.selected_unit_ids = [unit.id for unit in owned]
        first = owned[0]
        self.selected_kind = "unit"
        self.selected_id = first.id
        self.cursor_x = first.x
        self.cursor_y = first.y
        self.build_menu_open = False
        self.keep_cursor_visible()
        label = first.name if len(owned) == 1 else f"{len(owned)} units"
        self._log(f"Selected {label}.")
        return True

    def command_count(self, tokens: List[str], default: int = 1) -> int:
        for token in reversed(tokens):
            if token.isdigit():
                return max(1, min(50, int(token)))
        return default

    def owned_units_matching(self, tokens: List[str]) -> List[Unit]:
        idle = "idle" in tokens
        army = "army" in tokens or "military" in tokens
        kind: Optional[str] = None
        if any(token in tokens for token in ("villager", "villagers", "worker", "workers")):
            kind = "villager"
        elif "scout" in tokens:
            kind = "scout"
        elif any(token in tokens for token in ("clubman", "axeman", "swordsman")):
            kind = next(token for token in tokens if token in ("clubman", "axeman", "swordsman"))
        units = [unit for unit in self.units.values() if unit.owner == self.local_player_id and unit.hp > 0]
        if army:
            units = [unit for unit in units if unit.kind != "villager"]
        if kind:
            units = [unit for unit in units if unit.kind == kind]
        if idle:
            units = [unit for unit in units if unit.state == "idle"]
        units.sort(key=lambda unit: (abs(unit.x - self.cursor_x) + abs(unit.y - self.cursor_y), unit.id))
        return units

    def owned_building_matching(self, tokens: List[str]) -> Optional[Building]:
        aliases = {
            "tc": "town_center",
            "town_center": "town_center",
            "town": "town_center",
            "barracks": "barracks",
            "mill": "mill",
            "lumber": "lumber_camp",
            "lumber_camp": "lumber_camp",
            "house": "house",
        }
        kind = next((aliases[token] for token in tokens if token in aliases), None)
        if not kind:
            return None
        buildings = [
            building
            for building in self.buildings.values()
            if building.owner == self.local_player_id and building.kind == kind
        ]
        if not buildings:
            return None
        buildings.sort(key=lambda building: (abs(building.x - self.cursor_x) + abs(building.y - self.cursor_y), building.id))
        return buildings[0]

    def command_select(self, tokens: List[str]) -> bool:
        building = self.owned_building_matching(tokens)
        if building:
            self.selected_kind = "building"
            self.selected_id = building.id
            self.selected_unit_ids = []
            self.cursor_x = building.x
            self.cursor_y = building.y
            self.keep_cursor_visible()
            self._log(f"Selected {building.name}.")
            return True
        units = self.owned_units_matching(tokens)
        if not units:
            return False
        default_count = len(units) if any(token in tokens for token in ("all", "army", "military")) else 1
        count = self.command_count(tokens, default_count)
        return self.set_selected_units(units[:count])

    def resource_kind_from_tokens(self, tokens: List[str]) -> Optional[str]:
        if any(token in tokens for token in ("wood", "tree", "trees")):
            return "tree"
        if any(token in tokens for token in ("food", "berry", "berries")):
            return "berries"
        if any(token in tokens for token in ("gazelle", "hunt")):
            return "gazelle"
        if "gold" in tokens:
            return "gold"
        if "stone" in tokens:
            return "stone"
        return None

    def group_origin(self, units: List[Unit]) -> Tuple[int, int]:
        if not units:
            return (self.cursor_x, self.cursor_y)
        return (sum(unit.x for unit in units) // len(units), sum(unit.y for unit in units) // len(units))

    def nearest_resource_node(self, kind: Optional[str], origin: Tuple[int, int]) -> Optional[Tuple[int, ResourceNode]]:
        candidates: List[Tuple[int, ResourceNode]] = []
        for rid, node in self.resources.items():
            if kind and node.kind != kind:
                continue
            if node.amount <= 0 and node.kind != "gazelle":
                continue
            if node.kind == "gazelle" and not node.alive and not node.gatherable:
                continue
            pos = (node.x, node.y)
            if pos not in self.current_player().visible and rid not in self.current_player().discovered_resources:
                continue
            candidates.append((rid, node))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (abs(item[1].x - origin[0]) + abs(item[1].y - origin[1]), item[0]))
        return candidates[0]

    def command_gather(
        self,
        tokens: List[str],
        queue_payload: Optional[Callable[[Dict[str, object]], None]],
    ) -> bool:
        units = [unit for unit in self.selected_owned_units() if unit.kind == "villager"]
        if not units:
            self._log("Select villagers before gathering.")
            return True
        resource = self.nearest_resource_node(self.resource_kind_from_tokens(tokens), self.group_origin(units))
        if not resource:
            self._log("No known matching resource.")
            return True
        _, node = resource
        for unit in units:
            self.emit_player_command({"kind": "context", "unit_id": unit.id, "x": node.x, "y": node.y}, queue_payload)
        self._log(f"Sent {len(units)} villager(s) to {node.name}.")
        return True

    def nearest_visible_enemy(self, tokens: List[str], origin: Tuple[int, int]) -> Optional[Tuple[int, int, str]]:
        want_building = "building" in tokens or "buildings" in tokens
        want_tc = "tc" in tokens or "town_center" in tokens
        want_villager = any(token in tokens for token in ("villager", "villagers", "worker", "workers", "enemy_villager"))
        options: List[Tuple[int, int, str, int]] = []
        if not want_building and not want_tc:
            for unit in self.units.values():
                if unit.owner == self.local_player_id or unit.hp <= 0:
                    continue
                if not self.tile_visible_to(self.local_player_id, unit.x, unit.y):
                    continue
                if want_villager and unit.kind != "villager":
                    continue
                priority = 0 if unit.kind == "villager" else 1
                options.append((unit.x, unit.y, unit.name, priority))
        if not want_villager:
            for building in self.buildings.values():
                if building.owner == self.local_player_id or not self.tile_visible_to(self.local_player_id, building.x, building.y):
                    continue
                if want_tc and building.kind != "town_center":
                    continue
                priority = 0 if not building.complete else 2
                options.append((building.x, building.y, building.name, priority))
        if not options:
            return None
        options.sort(key=lambda item: (item[3], abs(item[0] - origin[0]) + abs(item[1] - origin[1]), item[2]))
        x, y, name, _ = options[0]
        return (x, y, name)

    def command_attack(
        self,
        tokens: List[str],
        queue_payload: Optional[Callable[[Dict[str, object]], None]],
    ) -> bool:
        units = self.owned_units_matching(["army"]) if "army" in tokens or "military" in tokens else self.selected_owned_units()
        units = [unit for unit in units if unit.kind != "villager" or "villager" in tokens]
        if not units:
            self._log("No selected attackers.")
            return True
        target = self.nearest_visible_enemy(tokens, self.group_origin(units))
        if not target:
            self._log("No visible matching enemy.")
            return True
        x, y, name = target
        for unit in units:
            self.emit_player_command({"kind": "context", "unit_id": unit.id, "x": x, "y": y}, queue_payload)
        self._log(f"Sent {len(units)} unit(s) to attack {name}.")
        return True

    def command_move(
        self,
        tokens: List[str],
        queue_payload: Optional[Callable[[Dict[str, object]], None]],
    ) -> bool:
        units = self.selected_owned_units()
        if not units:
            self._log("No selected units to move.")
            return True
        for unit in units:
            self.emit_player_command({"kind": "context", "unit_id": unit.id, "x": self.cursor_x, "y": self.cursor_y}, queue_payload)
        self._log(f"Moved {len(units)} unit(s) to cursor.")
        return True

    def command_queue(
        self,
        tokens: List[str],
        queue_payload: Optional[Callable[[Dict[str, object]], None]],
    ) -> bool:
        count = self.command_count(tokens)
        if any(token in tokens for token in ("villager", "villagers", "worker", "workers")):
            building = self.owned_building_matching(tokens) or self.owned_building_matching(["tc"])
            if not building:
                self._log("No Town Center found.")
                return True
            for _ in range(count):
                self.emit_player_command({"kind": "queue_villager", "building_id": building.id}, queue_payload)
            self._log(f"Submitted villager queue x{count}.")
            return True
        if any(token in tokens for token in ("soldier", "soldiers", "military", "unit", "units")):
            building = self.owned_building_matching(tokens) or self.owned_building_matching(["barracks"])
            if not building:
                self._log("No Barracks found.")
                return True
            for _ in range(count):
                self.emit_player_command({"kind": "queue_military", "building_id": building.id}, queue_payload)
            self._log(f"Submitted military queue x{count}.")
            return True
        return False

    def building_kind_from_tokens(self, tokens: List[str]) -> Optional[str]:
        aliases = {
            "house": "house",
            "h": "house",
            "lumber": "lumber_camp",
            "lumber_camp": "lumber_camp",
            "camp": "lumber_camp",
            "mill": "mill",
            "barracks": "barracks",
            "rax": "barracks",
        }
        return next((aliases[token] for token in tokens if token in aliases), None)

    def command_build(
        self,
        tokens: List[str],
        queue_payload: Optional[Callable[[Dict[str, object]], None]],
    ) -> bool:
        kind = self.building_kind_from_tokens(tokens)
        if not kind:
            return False
        villagers = [unit for unit in self.selected_owned_units() if unit.kind == "villager"]
        if not villagers:
            villagers = self.owned_units_matching(["idle", "villager"])[:1] or self.owned_units_matching(["villager"])[:1]
        if not villagers:
            self._log("No villager available to build.")
            return True
        x, y = self.cursor_x, self.cursor_y
        if "near" in tokens:
            anchor = self.owned_building_matching(tokens[tokens.index("near") + 1 :]) if tokens.index("near") + 1 < len(tokens) else None
            near_x, near_y = (anchor.x, anchor.y) if anchor else (self.cursor_x, self.cursor_y)
            site = self.find_build_site(near_x, near_y)
            if not site:
                self._log("No nearby build site found.")
                return True
            x, y = site
        self.emit_player_command({"kind": "build", "unit_id": villagers[0].id, "building_kind": kind, "x": x, "y": y}, queue_payload)
        self._log(f"Submitted {BUILDING_STATS[kind]['name']} build at {x},{y}.")
        return True

    def command_jump(self, tokens: List[str]) -> bool:
        if not tokens:
            return False
        if tokens[0] in self.vim_marks:
            self.cursor_x, self.cursor_y = self.vim_marks[tokens[0]]
            self.keep_cursor_visible()
            self._log(f"Jumped to mark {tokens[0]}.")
            return True
        if tokens[0] in ("tc", "town_center", "home"):
            self.jump_home()
            return True
        if tokens[0] in ("alert", "enemy"):
            self.jump_to_alert_or_enemy()
            return True
        building = self.owned_building_matching(tokens)
        if building:
            self.cursor_x, self.cursor_y = building.x, building.y
            self.keep_cursor_visible()
            self._log(f"Jumped to {building.name}.")
            return True
        return False

    def command_mark(self, tokens: List[str]) -> bool:
        if not tokens or len(tokens[0]) != 1 or not tokens[0].isalnum():
            self._log("Use :mark <letter>.")
            return True
        self.vim_marks[tokens[0]] = (self.cursor_x, self.cursor_y)
        self._log(f"Marked {tokens[0]} at {self.cursor_x},{self.cursor_y}.")
        return True

    def queue_selected_production(
        self,
        kind: str,
        count: int,
        queue_payload: Optional[Callable[[Dict[str, object]], None]],
    ) -> None:
        selected = self.get_selected()
        if not isinstance(selected, Building) or selected.owner != self.local_player_id:
            self._log("Select a production building first.")
            return
        payload_kind = "queue_villager" if kind == "villager" else "queue_military"
        for _ in range(count):
            self.emit_player_command({"kind": payload_kind, "building_id": selected.id}, queue_payload)
        self._log(f"Submitted {kind} queue x{count}.")

    def jump_home(self) -> None:
        town_center = self.owned_building_matching(["tc"])
        if not town_center:
            self._log("No Town Center found.")
            return
        self.cursor_x, self.cursor_y = town_center.x, town_center.y
        self.keep_cursor_visible()
        self._log("Jumped home.")

    def jump_to_alert_or_enemy(self) -> None:
        target = self.nearest_visible_enemy([], (self.cursor_x, self.cursor_y))
        if not target:
            self._log("No visible enemy alert.")
            return
        self.cursor_x, self.cursor_y = target[0], target[1]
        self.keep_cursor_visible()
        self._log(f"Jumped to {target[2]}.")

    def handle_build_menu_input(self, key: int) -> None:
        if key == ord("q"):
            self.running = False
            return
        if key in (ord("b"), ord("x"), 27):
            self.build_menu_open = False
            self._log("Closed build menu.")
            return
        building_kind = BUILD_MENU_OPTIONS.get(key)
        if building_kind is None:
            return
        self.build_menu_open = False
        self.try_place_building(building_kind)

    def open_build_menu(self) -> None:
        selected = self.get_selected()
        if not isinstance(selected, Unit) or selected.owner != self.local_player_id or selected.kind != "villager":
            self._log("Select one of your villagers first.")
            return
        self.build_menu_open = True
        self._log("Build menu: 1 House, 2 Lumber Camp, 3 Mill, 4 Barracks.")

    def select_at_cursor(self) -> None:
        pos = (self.cursor_x, self.cursor_y)
        visible = self.current_player().visible
        unit = self.unit_at(self.cursor_x, self.cursor_y)
        if unit and (unit.owner == self.local_player_id or pos in visible):
            self.selected_kind = "unit"
            self.selected_id = unit.id
            self.selected_unit_ids = [unit.id] if unit.owner == self.local_player_id else []
            self.build_menu_open = False
            self._log(f"Selected {unit.name}.")
            return
        building = self.building_at(self.cursor_x, self.cursor_y)
        if building and (building.owner == self.local_player_id or pos in visible):
            self.selected_kind = "building"
            self.selected_id = building.id
            self.selected_unit_ids = []
            self.build_menu_open = False
            self._log(f"Selected {building.name}.")
            return
        resource = self.resource_at(self.cursor_x, self.cursor_y)
        if resource and resource[0] not in self.current_player().discovered_resources and pos not in visible:
            resource = None
        if resource:
            rid, node = resource
            self.selected_kind = "resource"
            self.selected_id = rid
            self.selected_unit_ids = []
            self.build_menu_open = False
            self._log(f"Selected {node.name}.")
            return
        self.build_menu_open = False
        self.selected_unit_ids = []
        self._log("Nothing here to select.")

    def cycle_selection(self) -> None:
        entities: List[Tuple[str, int, int, int]] = []
        for unit in self.units.values():
            if unit.owner == self.local_player_id:
                entities.append(("unit", unit.id, unit.y, unit.x))
        for building in self.buildings.values():
            if building.owner == self.local_player_id:
                entities.append(("building", building.id, building.y, building.x))
        if not entities:
            return
        entities.sort(key=lambda item: (item[2], item[3], item[0], item[1]))
        ids = [(kind, ident) for kind, ident, _, _ in entities]
        if self.selected_id is None or (self.selected_kind, self.selected_id) not in ids:
            self.selected_kind, self.selected_id = ids[0]
        else:
            index = ids.index((self.selected_kind, self.selected_id))
            self.selected_kind, self.selected_id = ids[(index + 1) % len(ids)]
        entity = self.get_selected()
        if entity:
            self.build_menu_open = False
            self.cursor_x = entity.x
            self.cursor_y = entity.y
            if isinstance(entity, Unit) and entity.owner == self.local_player_id:
                self.selected_unit_ids = [entity.id]
            else:
                self.selected_unit_ids = []

    def get_selected(self) -> Optional[object]:
        if self.selected_id is None:
            return None
        if self.selected_kind == "unit":
            return self.units.get(self.selected_id)
        if self.selected_kind == "building":
            return self.buildings.get(self.selected_id)
        if self.selected_kind == "resource":
            return self.resources.get(self.selected_id)
        return None

    def issue_context_command(self) -> None:
        entity = self.get_selected()
        if isinstance(entity, Unit) and entity.owner == self.local_player_id:
            self.command_unit(entity)
            return
        self._log("Select a unit to move, gather, hunt, or build.")

    def command_unit(self, unit: Unit, target_x: Optional[int] = None, target_y: Optional[int] = None) -> None:
        log_owner = unit.owner
        tx = self.cursor_x if target_x is None else target_x
        ty = self.cursor_y if target_y is None else target_y
        enemy_unit = self.unit_at(tx, ty)
        if enemy_unit and enemy_unit.owner != unit.owner and self.tile_visible_to(unit.owner, tx, ty):
            unit.state = "attack"
            unit.target = ("unit", enemy_unit.id)
            unit.destination = None
            self._log(f"{unit.name} ordered to attack {enemy_unit.name}.", player_id=log_owner)
            return
        enemy_building = self.building_at(tx, ty)
        if enemy_building and enemy_building.owner != unit.owner:
            unit.state = "attack"
            unit.target = ("building", enemy_building.id)
            unit.destination = None
            self._log(f"{unit.name} ordered to attack {enemy_building.name}.", player_id=log_owner)
            return
        resource = self.resource_at(tx, ty)
        if resource:
            rid, node = resource
            if node.kind == "gazelle" and node.alive and unit.kind != "villager":
                unit.state = "attack"
                unit.target = ("resource", rid)
                unit.destination = None
                unit.build_target = None
                unit.gather_progress = 0.0
                self._log(f"{unit.name} ordered to kill the gazelle.", player_id=log_owner)
                return
        if unit.kind == "villager":
            if resource:
                rid, node = resource
                if node.kind == "gazelle" and not node.alive and not node.gatherable:
                    self._log("This carcass has no usable food.", player_id=log_owner)
                    return
                unit.target = ("resource", rid)
                unit.destination = None
                unit.gather_progress = 0.0
                if node.kind == "gazelle" and node.alive:
                    unit.state = "hunt"
                    self._log("Villager ordered to hunt the gazelle.", player_id=log_owner)
                else:
                    unit.state = "gather"
                    self._log(f"Villager ordered to gather from {node.name}.", player_id=log_owner)
                return
            building = self.building_at(tx, ty)
            if building and building.owner == unit.owner and not building.complete:
                unit.state = "build"
                unit.build_target = building.id
                unit.gather_progress = 0.0
                self._log(f"Villager ordered to construct {building.name}.", player_id=log_owner)
                return
        unit.state = "move"
        unit.destination = (tx, ty)
        unit.target = None
        unit.build_target = None
        unit.gather_progress = 0.0
        self._log(f"{unit.name} moving to {tx},{ty}.", player_id=log_owner)

    def command_unit_for_player(self, owner: int, unit_id: int, target_x: int, target_y: int) -> None:
        unit = self.units.get(unit_id)
        if not unit or unit.owner != owner:
            return
        self.command_unit(unit, target_x, target_y)

    def try_place_building(self, kind: str) -> None:
        selected = self.get_selected()
        if not isinstance(selected, Unit) or selected.owner != self.local_player_id or selected.kind != "villager":
            self._log("Select one of your villagers first.")
            return
        if not self.tile_open(self.cursor_x, self.cursor_y) or self.resource_at(self.cursor_x, self.cursor_y):
            self._log("Building location blocked.")
            return
        cost = BUILDING_STATS[kind]["cost"]
        player = self.current_player()
        if not player.spend(cost):
            self._log(f"Not enough resources for {BUILDING_STATS[kind]['name']}.")
            return
        building = self.add_building(self.local_player_id, kind, self.cursor_x, self.cursor_y, complete=False)
        selected.state = "build"
        selected.build_target = building.id
        selected.destination = None
        selected.target = None
        selected.gather_progress = 0.0
        self._log(f"Started {building.name} foundation.")

    def place_building_for_player(self, owner: int, unit_id: int, kind: str, x: int, y: int) -> None:
        unit = self.units.get(unit_id)
        if not unit or unit.owner != owner or unit.kind != "villager":
            return
        if kind not in BUILDING_STATS:
            return
        if not self.tile_open(x, y) or self.resource_at(x, y):
            return
        player = self.players[owner]
        cost = BUILDING_STATS[kind]["cost"]
        if not player.spend(cost):
            return
        building = self.add_building(owner, kind, x, y, complete=False)
        unit.state = "build"
        unit.build_target = building.id
        unit.destination = None
        unit.target = None
        unit.gather_progress = 0.0
        self._log(f"{player.name} started {building.name} foundation.", player_id=owner)

    def queue_villager(self) -> None:
        selected = self.get_selected()
        if (
            not isinstance(selected, Building)
            or selected.kind != "town_center"
            or selected.owner != self.local_player_id
            or not selected.complete
        ):
            self._log("Select your completed Town Center.")
            return
        player = self.current_player()
        if self.player_population(self.local_player_id) >= player.pop_cap:
            self._log("Population capped. Build houses.")
            return
        cost = UNIT_STATS["villager"]["cost"]
        if not player.spend(cost):
            self._log("Need more food for a villager.")
            return
        selected.queue.append(ProductionItem("unit", "villager", UNIT_STATS["villager"]["train_time"]))
        self._log("Villager queued.")

    def queue_villager_for_player(self, owner: int, building_id: int) -> None:
        building = self.buildings.get(building_id)
        if not building or building.owner != owner or building.kind != "town_center" or not building.complete:
            return
        player = self.players[owner]
        if self.player_population(owner) >= player.pop_cap:
            return
        cost = UNIT_STATS["villager"]["cost"]
        if not player.spend(cost):
            return
        building.queue.append(ProductionItem("unit", "villager", UNIT_STATS["villager"]["train_time"]))
        self._log(f"{player.name} queued a Villager.", player_id=owner)

    def available_military(self, age: int) -> str:
        if age >= 2:
            return "swordsman"
        if age >= 1:
            return "axeman"
        return "clubman"

    def queue_military(self) -> None:
        selected = self.get_selected()
        if (
            not isinstance(selected, Building)
            or selected.kind != "barracks"
            or selected.owner != self.local_player_id
            or not selected.complete
        ):
            self._log("Select your completed Barracks.")
            return
        player = self.current_player()
        if self.player_population(self.local_player_id) >= player.pop_cap:
            self._log("Population capped. Build houses.")
            return
        kind = self.available_military(player.age)
        stats = UNIT_STATS[kind]
        if not player.spend(stats["cost"]):
            self._log(f"Need more resources for {stats['name']}.")
            return
        selected.queue.append(ProductionItem("unit", kind, stats["train_time"]))
        self._log(f"{stats['name']} queued.")

    def queue_military_for_player(self, owner: int, building_id: int) -> None:
        building = self.buildings.get(building_id)
        if not building or building.owner != owner or building.kind != "barracks" or not building.complete:
            return
        player = self.players[owner]
        if self.player_population(owner) >= player.pop_cap:
            return
        kind = self.available_military(player.age)
        stats = UNIT_STATS[kind]
        if not player.spend(stats["cost"]):
            return
        building.queue.append(ProductionItem("unit", kind, stats["train_time"]))
        self._log(f"{player.name} queued {stats['name']}.", player_id=owner)

    def try_advance_age(self) -> None:
        selected = self.get_selected()
        player = self.current_player()
        if (
            not isinstance(selected, Building)
            or selected.kind != "town_center"
            or selected.owner != self.local_player_id
            or not selected.complete
        ):
            self._log("Select your Town Center to advance age.")
            return
        if player.age >= len(AGE_NAMES) - 1:
            self._log("Already in the final available age for this prototype.")
            return
        if player.ageing is not None:
            self._log("Age advance already in progress.")
            return
        data = AGE_ADVANCE[player.age]
        if not player.spend(data["cost"]):
            self._log("Need more resources to advance.")
            return
        player.ageing = ProductionItem("age", None, data["time"])
        self._log(f"Advancing to {AGE_NAMES[player.age + 1]}.")

    def try_advance_age_for_player(self, owner: int, building_id: int) -> None:
        building = self.buildings.get(building_id)
        if not building or building.owner != owner or building.kind != "town_center" or not building.complete:
            return
        player = self.players[owner]
        if player.age >= len(AGE_NAMES) - 1 or player.ageing is not None:
            return
        data = AGE_ADVANCE.get(player.age)
        if not data or not player.spend(data["cost"]):
            return
        player.ageing = ProductionItem("age", None, data["time"])
        self._log(f"{player.name} advancing to {AGE_NAMES[player.age + 1]}.", player_id=owner)

    def try_research(self) -> None:
        selected = self.get_selected()
        player = self.current_player()
        if not isinstance(selected, Building) or not selected.complete or selected.owner != self.local_player_id:
            self._log("Select a completed mill or barracks.")
            return
        if selected.kind == "mill":
            level = player.economy_level
            if level >= len(TECHS["economy"]["cost"]):
                self._log("Economy techs already maxed.")
                return
            if self.queue_contains(selected, "tech", "economy"):
                self._log("Harvesting tech already queued here.")
                return
            cost = TECHS["economy"]["cost"][level]
            if not player.spend(cost):
                self._log("Need more resources for harvesting tech.")
                return
            selected.queue.append(ProductionItem("tech", "economy", TECHS["economy"]["time"][level]))
            self._log("Harvesting tech queued.")
            return
        if selected.kind == "barracks":
            level = player.military_level
            if level >= len(TECHS["military"]["cost"]):
                self._log("Military techs already maxed.")
                return
            if self.queue_contains(selected, "tech", "military"):
                self._log("Weapons tech already queued here.")
                return
            cost = TECHS["military"]["cost"][level]
            if not player.spend(cost):
                self._log("Need more resources for weapons tech.")
                return
            selected.queue.append(ProductionItem("tech", "military", TECHS["military"]["time"][level]))
            self._log("Weapons tech queued.")
            return
        self._log("This building has no research in the prototype.")

    def try_research_for_player(self, owner: int, building_id: int) -> None:
        building = self.buildings.get(building_id)
        if not building or building.owner != owner or not building.complete:
            return
        player = self.players[owner]
        if building.kind == "mill":
            level = player.economy_level
            if level >= len(TECHS["economy"]["cost"]) or self.queue_contains(building, "tech", "economy"):
                return
            cost = TECHS["economy"]["cost"][level]
            if not player.spend(cost):
                return
            building.queue.append(ProductionItem("tech", "economy", TECHS["economy"]["time"][level]))
            self._log(f"{player.name} queued Harvesting.", player_id=owner)
            return
        if building.kind == "barracks":
            level = player.military_level
            if level >= len(TECHS["military"]["cost"]) or self.queue_contains(building, "tech", "military"):
                return
            cost = TECHS["military"]["cost"][level]
            if not player.spend(cost):
                return
            building.queue.append(ProductionItem("tech", "military", TECHS["military"]["time"][level]))
            self._log(f"{player.name} queued Weapons.", player_id=owner)

    def apply_command(self, command: Dict[str, object]) -> None:
        kind = str(command.get("kind", ""))
        owner = int(command.get("owner", -1))
        if owner < 0 or owner >= len(self.players):
            return
        if kind == "context":
            self.command_unit_for_player(owner, int(command["unit_id"]), int(command["x"]), int(command["y"]))
        elif kind == "build":
            self.place_building_for_player(owner, int(command["unit_id"]), str(command["building_kind"]), int(command["x"]), int(command["y"]))
        elif kind == "queue_villager":
            self.queue_villager_for_player(owner, int(command["building_id"]))
        elif kind == "queue_military":
            self.queue_military_for_player(owner, int(command["building_id"]))
        elif kind == "advance_age":
            self.try_advance_age_for_player(owner, int(command["building_id"]))
        elif kind == "research":
            self.try_research_for_player(owner, int(command["building_id"]))

    def update(self) -> None:
        if self.winner is not None:
            return
        self.tick += 1
        self.update_age_progress()
        self.update_buildings()
        self.update_units()
        self.update_ai()
        self.cleanup_destroyed()
        self.prune_damage_flashes()
        self.reveal_visibility()
        self.sanitize_selection_visibility()
        self.check_victory()
        self.keep_cursor_visible()

    def update_age_progress(self) -> None:
        for player in self.players:
            if player.ageing is None:
                continue
            player.ageing.time_left -= 1
            if player.ageing.time_left <= 0:
                player.age += 1
                player.ageing = None
                self._log(f"{player.name} advanced to {AGE_NAMES[player.age]}.", player_id=player.id)

    def update_buildings(self) -> None:
        for building in list(self.buildings.values()):
            if not building.complete:
                continue
            if building.queue:
                building.queue[0].time_left -= 1
                if building.queue[0].time_left <= 0:
                    self.finish_queue_item(building, building.queue.pop(0))

    def finish_queue_item(self, building: Building, item: ProductionItem) -> None:
        player = self.players[building.owner]
        if item.kind == "unit" and item.target:
            unit = self.add_unit(building.owner, item.target, building.x + 1, building.y)
            if unit:
                self._log(f"{player.name} trained {unit.name}.", player_id=building.owner)
            else:
                refund = UNIT_STATS[item.target]["cost"]
                player.food += refund.get("food", 0)
                player.wood += refund.get("wood", 0)
                player.gold += refund.get("gold", 0)
                player.stone += refund.get("stone", 0)
                self._log(f"{player.name} training failed: no free spawn tile.", player_id=building.owner)
        elif item.kind == "tech" and item.target == "economy":
            player.economy_level += 1
            self._log(f"{player.name} completed {TECHS['economy']['name']} {player.economy_level}.", player_id=building.owner)
        elif item.kind == "tech" and item.target == "military":
            player.military_level += 1
            self._log(f"{player.name} completed {TECHS['military']['name']} {player.military_level}.", player_id=building.owner)

    def queue_contains(self, building: Building, kind: str, target: str) -> bool:
        return any(item.kind == kind and item.target == target for item in building.queue)

    def update_units(self) -> None:
        ordered = sorted(self.units.values(), key=lambda unit: unit.id)
        for unit in ordered:
            if unit.attack_cooldown > 0:
                unit.attack_cooldown -= 1
            self.auto_acquire_visible_enemy(unit)
            if unit.state == "move":
                self.step_toward_destination(unit)
            elif unit.state in ("gather", "hunt"):
                self.update_worker(unit)
            elif unit.state == "return":
                self.return_resources(unit)
            elif unit.state == "build":
                self.update_builder(unit)
            elif unit.state == "attack":
                self.update_attack(unit)

    def auto_acquire_visible_enemy(self, unit: Unit) -> None:
        if unit.kind == "villager" or unit.state == "attack" or unit.hp <= 0:
            return
        target = self.closest_visible_enemy_unit(unit)
        if not target:
            return
        unit.state = "attack"
        unit.target = ("unit", target.id)
        unit.destination = None
        unit.build_target = None
        unit.gather_progress = 0.0

    def closest_visible_enemy_unit(self, unit: Unit) -> Optional[Unit]:
        enemies = [
            enemy
            for enemy in self.units.values()
            if enemy.owner != unit.owner
            and enemy.hp > 0
            and self.distance(unit.x, unit.y, enemy.x, enemy.y) <= unit.vision
            and self.tile_visible_to(unit.owner, enemy.x, enemy.y)
        ]
        if not enemies:
            return None
        enemies.sort(
            key=lambda enemy: (
                self.distance(unit.x, unit.y, enemy.x, enemy.y),
                0 if enemy.kind == "villager" else 1,
                enemy.hp,
                enemy.id,
            )
        )
        return enemies[0]

    def step_toward_destination(self, unit: Unit) -> None:
        if not unit.destination:
            unit.state = "idle"
            return
        if (unit.x, unit.y) == unit.destination:
            unit.state = "idle"
            unit.destination = None
            return
        self.move_unit_toward(unit, unit.destination)

    def update_worker(self, unit: Unit) -> None:
        if not unit.target or unit.target[0] != "resource":
            unit.state = "idle"
            return
        resource = self.resources.get(unit.target[1])
        if not resource or resource.amount <= 0:
            unit.state = "idle"
            unit.target = None
            return
        if resource.kind == "gazelle" and not resource.alive and not resource.gatherable:
            unit.state = "idle"
            unit.target = None
            return
        if unit.total_carry() >= unit.carry_capacity:
            unit.state = "return"
            return
        if self.distance(unit.x, unit.y, resource.x, resource.y) > 1:
            self.move_unit_toward(unit, (resource.x, resource.y), adjacent=True)
            return
        if resource.kind == "gazelle" and resource.alive:
            if unit.attack_cooldown == 0:
                resource.hp -= 3
                unit.attack_cooldown = 8
                if resource.hp <= 0:
                    resource.alive = False
                    self._log(f"{self.players[unit.owner].name} killed a gazelle.", player_id=unit.owner)
            return
        rate_multiplier = 1 + 0.15 * self.players[unit.owner].economy_level
        unit.gather_progress += GATHER_RATES[resource.kind] * rate_multiplier * (TICK_MS / 1000)
        collected = min(int(unit.gather_progress), resource.amount, unit.carry_capacity - unit.total_carry())
        if collected > 0:
            unit.gather_progress -= collected
            resource.amount -= collected
            unit.carrying[resource.resource_type] += collected
        if resource.amount <= 0 and resource.kind == "tree":
            self._log("A tree has been exhausted.", player_id=unit.owner)
        if unit.total_carry() >= unit.carry_capacity or resource.amount <= 0:
            unit.state = "return"

    def return_resources(self, unit: Unit) -> None:
        resource_type = next((kind for kind in ("wood", "food", "gold", "stone") if unit.carrying[kind] > 0), None)
        dropoff = self.nearest_dropoff(unit.owner, unit.x, unit.y, resource_type)
        if not dropoff:
            unit.state = "idle"
            return
        if self.distance(unit.x, unit.y, dropoff.x, dropoff.y) > 1:
            self.move_unit_toward(unit, (dropoff.x, dropoff.y), adjacent=True)
            return
        player = self.players[unit.owner]
        player.food += unit.carrying["food"]
        player.wood += unit.carrying["wood"]
        player.gold += unit.carrying["gold"]
        player.stone += unit.carrying["stone"]
        unit.carrying = {"food": 0, "wood": 0, "gold": 0, "stone": 0}
        unit.gather_progress = 0.0
        if unit.target and unit.target[0] == "resource":
            resource = self.resources.get(unit.target[1])
            if resource and resource.amount > 0:
                unit.state = "gather" if not (resource.kind == "gazelle" and resource.alive) else "hunt"
            else:
                unit.state = "idle"
                unit.target = None
        else:
            unit.state = "idle"

    def update_builder(self, unit: Unit) -> None:
        if unit.build_target is None:
            unit.state = "idle"
            return
        building = self.buildings.get(unit.build_target)
        if not building:
            unit.state = "idle"
            unit.build_target = None
            return
        if building.complete:
            unit.state = "idle"
            unit.build_target = None
            return
        if self.distance(unit.x, unit.y, building.x, building.y) > 1:
            self.move_unit_toward(unit, (building.x, building.y), adjacent=True)
            return
        building.build_progress += 5
        building.hp = min(building.max_hp, max(1, building.build_progress))
        if building.build_progress >= building.build_time:
            building.complete = True
            building.hp = building.max_hp
            self.players[building.owner].pop_cap += building.pop_bonus
            unit.state = "idle"
            unit.build_target = None
            self._log(f"{self.players[building.owner].name} finished {building.name}.", player_id=building.owner)

    def update_attack(self, unit: Unit) -> None:
        if not unit.target:
            unit.state = "idle"
            return
        target_kind, target_id = unit.target
        if target_kind == "unit":
            target_obj = self.units.get(target_id)
        elif target_kind == "building":
            target_obj = self.buildings.get(target_id)
        elif target_kind == "resource":
            target_obj = self.resources.get(target_id)
        else:
            target_obj = None
        if not target_obj:
            unit.state = "idle"
            unit.target = None
            return
        if target_kind == "resource":
            if target_obj.kind != "gazelle" or not target_obj.alive:
                unit.state = "idle"
                unit.target = None
                return
        if self.distance(unit.x, unit.y, target_obj.x, target_obj.y) > 1:
            self.move_unit_toward(unit, (target_obj.x, target_obj.y), adjacent=True)
            return
        if unit.attack_cooldown > 0:
            return
        damage = unit.attack + self.players[unit.owner].military_level
        target_obj.hp -= damage
        self.mark_damage(target_kind, target_id)
        self.handle_combat_damage(unit, target_kind, target_obj)
        if target_kind == "resource" and target_obj.hp <= 0:
            target_obj.alive = False
            target_obj.gatherable = False
            unit.state = "idle"
            unit.target = None
            self._log(f"{self.players[unit.owner].name}'s {unit.name} killed a gazelle.", player_id=unit.owner)
            return
        unit.attack_cooldown = 10

    def handle_combat_damage(self, attacker: Unit, target_kind: str, target_obj: object) -> None:
        if target_kind not in ("unit", "building") or not isinstance(target_obj, (Unit, Building)):
            return
        defender_owner = target_obj.owner
        if defender_owner == attacker.owner or not self.is_ai_owner(defender_owner):
            return
        self.ai_respond_to_attack(defender_owner, attacker, target_obj)

    def is_ai_owner(self, owner: int) -> bool:
        return self.enable_ai and owner != self.local_player_id

    def ai_order_attack_unit(self, unit: Unit, target: Unit) -> None:
        unit.state = "attack"
        unit.target = ("unit", target.id)
        unit.destination = None
        unit.build_target = None
        unit.gather_progress = 0.0

    def ai_respond_to_attack(self, owner: int, attacker: Unit, target_obj: object) -> None:
        if attacker.hp <= 0:
            return
        if isinstance(target_obj, Unit) and target_obj.owner == owner and target_obj.hp > 0:
            self.ai_order_attack_unit(target_obj, attacker)

        tx = target_obj.x if isinstance(target_obj, (Unit, Building)) else attacker.x
        ty = target_obj.y if isinstance(target_obj, (Unit, Building)) else attacker.y
        military: List[Unit] = []
        workers: List[Unit] = []
        for defender in self.units.values():
            if defender.owner != owner or defender.id == attacker.id or defender.hp <= 0:
                continue
            if isinstance(target_obj, Unit) and defender.id == target_obj.id:
                continue
            target_distance = self.distance(defender.x, defender.y, tx, ty)
            attacker_distance = self.distance(defender.x, defender.y, attacker.x, attacker.y)
            if defender.kind == "villager":
                if min(target_distance, attacker_distance) <= 7:
                    workers.append(defender)
            elif min(target_distance, attacker_distance) <= 13:
                military.append(defender)

        military.sort(key=lambda unit: self.distance(unit.x, unit.y, attacker.x, attacker.y))
        workers.sort(key=lambda unit: self.distance(unit.x, unit.y, attacker.x, attacker.y))
        responders = military[:5] + workers[:4]
        for defender in responders:
            self.ai_order_attack_unit(defender, attacker)

        key = f"last_defense_log_{owner}"
        if responders and self.tick - self.ai_memory.get(key, -999) > 30:
            self.ai_memory[key] = self.tick
            self._log(f"{self.players[owner].name} calls nearby units to defend.", player_id=owner)

    def move_unit_toward(self, unit: Unit, destination: Tuple[int, int], adjacent: bool = False) -> None:
        tx, ty = destination
        if adjacent and self.distance(unit.x, unit.y, tx, ty) <= 1:
            return
        candidates = []
        for nx, ny in self.neighbors8(unit.x, unit.y):
            if not self.tile_open(nx, ny):
                continue
            score = abs(tx - nx) + abs(ty - ny)
            tie_breaker = abs(nx - unit.x) + abs(ny - unit.y) + (unit.id % 7) + nx + (ny * MAP_WIDTH)
            candidates.append((score, tie_breaker, nx, ny))
        if not candidates:
            return
        candidates.sort()
        _, _, nx, ny = candidates[0]
        unit.x = nx
        unit.y = ny

    def nearest_dropoff(self, owner: int, x: int, y: int, resource_type: Optional[str] = None) -> Optional[Building]:
        dropoff_kinds = {"town_center"}
        if resource_type == "food":
            dropoff_kinds.add("mill")
        elif resource_type == "wood":
            dropoff_kinds.add("lumber_camp")
        elif resource_type is None:
            dropoff_kinds.update({"mill", "lumber_camp"})
        options = [
            building
            for building in self.buildings.values()
            if building.owner == owner and building.complete and building.kind in dropoff_kinds
        ]
        if not options:
            return None
        return min(options, key=lambda building: abs(building.x - x) + abs(building.y - y))

    def distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        return max(abs(x1 - x2), abs(y1 - y2))

    def cleanup_destroyed(self) -> None:
        dead_units = [unit_id for unit_id, unit in self.units.items() if unit.hp <= 0]
        for unit_id in dead_units:
            unit = self.units.pop(unit_id)
            self.damage_flashes.pop(self.damage_flash_key("unit", unit_id), None)
            if (self.selected_kind, self.selected_id) == ("unit", unit_id):
                self.selected_kind = None
                self.selected_id = None
            self._log(f"{self.players[unit.owner].name}'s {unit.name} died.", player_id=unit.owner)
        dead_buildings = [bid for bid, building in self.buildings.items() if building.hp <= 0]
        for bid in dead_buildings:
            building = self.buildings.pop(bid)
            self.damage_flashes.pop(self.damage_flash_key("building", bid), None)
            if building.complete:
                self.players[building.owner].pop_cap -= building.pop_bonus
            if (self.selected_kind, self.selected_id) == ("building", bid):
                self.selected_kind = None
                self.selected_id = None
            self._log(f"{self.players[building.owner].name}'s {building.name} was destroyed.", player_id=building.owner)
        spent = [rid for rid, node in self.resources.items() if node.amount <= 0]
        for rid in spent:
            if (self.selected_kind, self.selected_id) == ("resource", rid):
                self.selected_kind = None
                self.selected_id = None
            del self.resources[rid]

    def check_victory(self) -> None:
        if len(self.players) < 2:
            return
        alive = []
        for owner in range(len(self.players)):
            has_buildings = any(building.owner == owner for building in self.buildings.values())
            has_units = any(unit.owner == owner for unit in self.units.values())
            if has_buildings or has_units:
                alive.append(owner)
        if len(alive) == 1:
            self.winner = alive[0]
            self._log_many(f"{self.players[self.winner].name} wins.", range(len(self.players)))

    def keep_cursor_visible(self) -> None:
        if self.stdscr is None:
            return
        height, width = self.stdscr.getmaxyx()
        sidebar = 31
        map_w = max(20, (width - sidebar) // TILE_WIDTH)
        map_h = max(10, height - 9)
        if self.cursor_x < self.camera_x + 2:
            self.camera_x = max(0, self.cursor_x - 2)
        if self.cursor_y < self.camera_y + 2:
            self.camera_y = max(0, self.cursor_y - 2)
        if self.cursor_x >= self.camera_x + map_w - 2:
            self.camera_x = min(MAP_WIDTH - map_w, self.cursor_x - map_w + 3)
        if self.cursor_y >= self.camera_y + map_h - 2:
            self.camera_y = min(MAP_HEIGHT - map_h, self.cursor_y - map_h + 3)
        self.camera_x = max(0, self.camera_x)
        self.camera_y = max(0, self.camera_y)

    def update_ai(self) -> None:
        if not self.enable_ai or len(self.players) < 2:
            return
        ai = self.players[1]
        if self.tick % 4 != 0:
            return
        workers = [unit for unit in self.units.values() if unit.owner == 1 and unit.kind == "villager"]
        tc = next((b for b in self.buildings.values() if b.owner == 1 and b.kind == "town_center"), None)
        barracks = next((b for b in self.buildings.values() if b.owner == 1 and b.kind == "barracks"), None)
        mill = next((b for b in self.buildings.values() if b.owner == 1 and b.kind == "mill"), None)
        if tc and tc.complete and len(workers) < 7 and not tc.queue and self.player_population(1) < ai.pop_cap and ai.can_afford(UNIT_STATS["villager"]["cost"]):
            ai.spend(UNIT_STATS["villager"]["cost"])
            tc.queue.append(ProductionItem("unit", "villager", UNIT_STATS["villager"]["train_time"]))
        if self.player_population(1) >= ai.pop_cap - 1 and self.tick - self.ai_memory["last_house_tick"] > 40:
            builder = self.idle_worker(1)
            if builder and ai.can_afford(BUILDING_STATS["house"]["cost"]):
                pos = self.find_build_site(tc.x - 3 if tc else MAP_WIDTH - 10, tc.y - 1 if tc else MAP_HEIGHT - 10)
                if pos:
                    ai.spend(BUILDING_STATS["house"]["cost"])
                    house = self.add_building(1, "house", pos[0], pos[1], complete=False)
                    builder.state = "build"
                    builder.build_target = house.id
                    self.ai_memory["last_house_tick"] = self.tick
        if not mill:
            builder = self.idle_worker(1)
            if builder and ai.can_afford(BUILDING_STATS["mill"]["cost"]):
                berry = self.closest_resource(tc.x, tc.y, {"berries"}) if tc else None
                if berry:
                    pos = self.find_build_site(berry.x + 1, berry.y)
                    if pos:
                        ai.spend(BUILDING_STATS["mill"]["cost"])
                        mill = self.add_building(1, "mill", pos[0], pos[1], complete=False)
                        builder.state = "build"
                        builder.build_target = mill.id
        if ai.age == 0 and len(workers) >= 5 and ai.ageing is None and ai.can_afford(AGE_ADVANCE[0]["cost"]):
            ai.spend(AGE_ADVANCE[0]["cost"])
            ai.ageing = ProductionItem("age", None, AGE_ADVANCE[0]["time"])
        if ai.age == 1 and len(workers) >= 6 and ai.ageing is None and ai.can_afford(AGE_ADVANCE[1]["cost"]):
            ai.spend(AGE_ADVANCE[1]["cost"])
            ai.ageing = ProductionItem("age", None, AGE_ADVANCE[1]["time"])
        if (
            mill
            and mill.complete
            and ai.economy_level < len(TECHS["economy"]["cost"])
            and not self.queue_contains(mill, "tech", "economy")
            and ai.can_afford(TECHS["economy"]["cost"][ai.economy_level])
        ):
            ai.spend(TECHS["economy"]["cost"][ai.economy_level])
            mill.queue.append(ProductionItem("tech", "economy", TECHS["economy"]["time"][ai.economy_level]))
        if not barracks and len(workers) >= 4:
            builder = self.idle_worker(1)
            if builder and ai.can_afford(BUILDING_STATS["barracks"]["cost"]):
                pos = self.find_build_site((tc.x - 4) if tc else MAP_WIDTH - 12, (tc.y + 3) if tc else MAP_HEIGHT - 7)
                if pos:
                    ai.spend(BUILDING_STATS["barracks"]["cost"])
                    barracks = self.add_building(1, "barracks", pos[0], pos[1], complete=False)
                    builder.state = "build"
                    builder.build_target = barracks.id
        if barracks and barracks.complete and not barracks.queue and self.player_population(1) < ai.pop_cap:
            kind = self.available_military(ai.age)
            if ai.can_afford(UNIT_STATS[kind]["cost"]):
                ai.spend(UNIT_STATS[kind]["cost"])
                barracks.queue.append(ProductionItem("unit", kind, UNIT_STATS[kind]["train_time"]))
        if (
            barracks
            and barracks.complete
            and ai.military_level < len(TECHS["military"]["cost"])
            and not self.queue_contains(barracks, "tech", "military")
            and ai.can_afford(TECHS["military"]["cost"][ai.military_level])
        ):
            ai.spend(TECHS["military"]["cost"][ai.military_level])
            barracks.queue.append(ProductionItem("tech", "military", TECHS["military"]["time"][ai.military_level]))
        for worker in workers:
            if worker.state == "idle":
                target = self.closest_resource(worker.x, worker.y, {"berries", "tree", "gazelle"})
                if target:
                    rid = self.resource_id(target)
                    if rid is not None:
                        worker.target = ("resource", rid)
                        worker.state = "hunt" if target.kind == "gazelle" and target.alive else "gather"
        army = [unit for unit in self.units.values() if unit.owner == 1 and unit.kind != "villager"]
        target = self.ai_choose_attack_target(1, army)
        if target and army and self.tick - self.ai_memory["last_attack_tick"] > 32:
            attackers = self.ai_attackers_for_target(army, target)
            if attackers:
                self.ai_memory["last_attack_tick"] = self.tick
                for soldier in attackers:
                    soldier.state = "attack"
                    soldier.target = target
                    soldier.destination = None
        self.ai_scout_with_idle_units(1, army, tc)

    def ai_choose_attack_target(self, owner: int, army: List[Unit]) -> Optional[Tuple[str, int]]:
        visible_enemy_units = [
            unit
            for unit in self.units.values()
            if unit.owner != owner and self.tile_visible_to(owner, unit.x, unit.y)
        ]
        if visible_enemy_units:
            visible_enemy_units.sort(
                key=lambda unit: (
                    0 if unit.kind == "villager" else 1,
                    unit.hp,
                    self.ai_army_distance(army, unit.x, unit.y),
                )
            )
            return ("unit", visible_enemy_units[0].id)

        visible_enemy_buildings = [
            building
            for building in self.buildings.values()
            if building.owner != owner and self.tile_visible_to(owner, building.x, building.y)
        ]
        if not visible_enemy_buildings:
            return None

        ready_for_base_push = len(army) >= 4
        building_targets = [
            building
            for building in visible_enemy_buildings
            if building.kind != "town_center" or ready_for_base_push
        ]
        if not building_targets:
            return None

        building_targets.sort(
            key=lambda building: (
                0 if not building.complete else 1,
                1 if building.kind in ("mill", "lumber_camp", "barracks") else 2,
                building.hp,
                self.ai_army_distance(army, building.x, building.y),
            )
        )
        return ("building", building_targets[0].id)

    def ai_attackers_for_target(self, army: List[Unit], target: Tuple[str, int]) -> List[Unit]:
        if target[0] == "building":
            building = self.buildings.get(target[1])
            if not building:
                return []
            if building.kind == "town_center" and len(army) < 4:
                return []
            if building.kind != "town_center" and len(army) == 1 and army[0].kind == "scout":
                return []
        if target[0] == "unit":
            unit = self.units.get(target[1])
            if not unit:
                return []
            if unit.kind != "villager" and len(army) < 2:
                return []
        return [
            unit
            for unit in army
            if unit.state != "attack" or unit.target != target
        ]

    def ai_army_distance(self, army: List[Unit], x: int, y: int) -> int:
        if not army:
            return MAP_WIDTH + MAP_HEIGHT
        return min(abs(unit.x - x) + abs(unit.y - y) for unit in army)

    def ai_scout_with_idle_units(self, owner: int, army: List[Unit], tc: Optional[Building]) -> None:
        if self.tick - self.ai_memory.get("last_scout_tick", -999) < 36:
            return
        scouts = [unit for unit in army if unit.kind == "scout" and unit.state in ("idle", "move")]
        if not scouts:
            return
        waypoints = self.ai_scout_waypoints(owner, tc)
        if not waypoints:
            return
        self.ai_memory["last_scout_tick"] = self.tick
        for scout in scouts:
            if scout.destination and self.distance(scout.x, scout.y, scout.destination[0], scout.destination[1]) > 2:
                continue
            target_x, target_y = self.rng.choice(waypoints)
            scout.state = "move"
            scout.destination = (target_x, target_y)
            scout.target = None

    def ai_scout_waypoints(self, owner: int, tc: Optional[Building]) -> List[Tuple[int, int]]:
        waypoints: List[Tuple[int, int]] = []
        if tc:
            for node in self.resources.values():
                if 7 <= abs(node.x - tc.x) + abs(node.y - tc.y) <= 28:
                    waypoints.append((node.x, node.y))
        for enemy_tc in self.buildings.values():
            if enemy_tc.owner != owner and enemy_tc.kind == "town_center":
                for dx, dy in [(-7, -4), (-5, 6), (6, -5), (7, 4)]:
                    x = max(1, min(MAP_WIDTH - 2, enemy_tc.x + dx))
                    y = max(1, min(MAP_HEIGHT - 2, enemy_tc.y + dy))
                    if self.tile_open(x, y):
                        waypoints.append((x, y))
        waypoints.extend([(8, 8), (MAP_WIDTH - 9, 8), (8, MAP_HEIGHT - 9), (MAP_WIDTH - 9, MAP_HEIGHT - 9)])
        return waypoints

    def idle_worker(self, owner: int) -> Optional[Unit]:
        workers = [unit for unit in self.units.values() if unit.owner == owner and unit.kind == "villager" and unit.state in ("idle", "gather", "hunt", "return")]
        return min(workers, key=lambda u: u.id) if workers else None

    def closest_resource(self, x: int, y: int, kinds: Set[str]) -> Optional[ResourceNode]:
        options = [node for node in self.resources.values() if node.kind in kinds and node.amount > 0]
        if not options:
            return None
        return min(options, key=lambda node: abs(node.x - x) + abs(node.y - y))

    def resource_id(self, node: ResourceNode) -> Optional[int]:
        for rid, candidate in self.resources.items():
            if candidate is node:
                return rid
        return None

    def find_build_site(self, near_x: int, near_y: int) -> Optional[Tuple[int, int]]:
        for radius in range(1, 7):
            for y in range(max(1, near_y - radius), min(MAP_HEIGHT - 1, near_y + radius + 1)):
                for x in range(max(1, near_x - radius), min(MAP_WIDTH - 1, near_x + radius + 1)):
                    if self.tile_open(x, y) and not self.resource_at(x, y):
                        return x, y
        return None

    def entity_summary(self, obj: object) -> str:
        if isinstance(obj, Unit):
            owner = self.owner_label(obj.owner)
            carry = ""
            if obj.kind == "villager":
                carry = (
                    f" carry F{obj.carrying['food']} W{obj.carrying['wood']}"
                    f" G{obj.carrying['gold']} S{obj.carrying['stone']}"
                )
            return f"{owner} {obj.name} hp {obj.hp}/{obj.max_hp} atk {obj.attack} vis {obj.vision} state {obj.state}{carry}"
        if isinstance(obj, Building):
            owner = self.owner_label(obj.owner)
            text = f"{owner} {obj.name} hp {obj.hp}/{obj.max_hp}"
            if not obj.complete:
                text += f" building {obj.build_progress}/{obj.build_time}"
            if obj.queue:
                current = obj.queue[0]
                target = current.target or current.kind
                text += f" queue {target}({current.time_left})"
            return text
        if isinstance(obj, ResourceNode):
            if obj.kind == "gazelle" and obj.alive:
                return f"{obj.name} hp {obj.hp} food {obj.amount}"
            if obj.kind == "gazelle" and not obj.gatherable:
                return f"{obj.name} no usable food"
            return f"{obj.name} remaining {obj.amount}"
        return ""

    def render(self) -> None:
        if self.stdscr is None:
            return
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if height < 22 or width < 90:
            self.safe_addstr(0, 0, "Resize terminal to at least 90x22.", self.theme_attr(PAIR_ALERT, curses.A_BOLD))
            self.stdscr.refresh()
            return
        log_h = LOG_LIMIT + 2
        content_h = height - log_h
        sidebar_w = 36
        max_map_panel_w = max(24, width - sidebar_w)
        map_w = max(20, (max_map_panel_w - 2) // TILE_WIDTH)
        map_panel_w = min(max_map_panel_w, map_w * TILE_WIDTH + 2)
        sidebar_x = map_panel_w
        sidebar_w = width - sidebar_x
        map_h = max(8, content_h - 2)
        player = self.current_player()
        self.camera_x = min(self.camera_x, max(0, MAP_WIDTH - map_w))
        self.camera_y = min(self.camera_y, max(0, MAP_HEIGHT - map_h))
        self.draw_box(
            0,
            0,
            content_h,
            map_panel_w,
            "Battlefield",
            border_attr=self.theme_attr(PAIR_PANEL),
            title_attr=self.theme_attr(PAIR_PANEL_TITLE, curses.A_BOLD),
            fill_attr=self.theme_attr(PAIR_UNSEEN),
        )
        self.draw_box(
            0,
            sidebar_x,
            content_h,
            sidebar_w,
            f"{player.name} · {player.civ}",
            border_attr=self.theme_attr(PAIR_PANEL),
            title_attr=self.theme_attr(PAIR_PANEL_TITLE, curses.A_BOLD),
        )
        self.draw_map(1, 1, map_w, map_h)
        self.draw_sidebar(sidebar_x + 1, 1, sidebar_w - 2, content_h - 2)
        self.draw_log(content_h, width, log_h)
        if self.winner is not None:
            overlay = f"{self.players[self.winner].name} wins. Press q."
            overlay_w = min(map_panel_w - 4, max(28, len(overlay) + 6))
            overlay_y = max(1, (content_h - 5) // 2)
            overlay_x = max(2, (map_panel_w - overlay_w) // 2)
            self.draw_box(
                overlay_y,
                overlay_x,
                5,
                overlay_w,
                "Empire Falls",
                border_attr=self.theme_attr(PAIR_ALERT),
                title_attr=self.theme_attr(PAIR_PANEL_TITLE, curses.A_BOLD),
                fill_attr=self.theme_attr(PAIR_UNSEEN),
            )
            self.safe_addstr(overlay_y + 2, overlay_x + 3, overlay[: max(0, overlay_w - 6)], self.theme_attr(PAIR_ALERT, curses.A_BOLD))
        self.stdscr.refresh()

    def draw_map(self, origin_y: int, origin_x: int, map_w: int, map_h: int) -> None:
        visible = self.current_player().visible
        explored = self.current_player().explored
        selected = self.get_selected()
        selected_pos = None
        if isinstance(selected, (Unit, Building, ResourceNode)):
            selected_pos = (selected.x, selected.y)
        for sy in range(map_h):
            wy = self.camera_y + sy
            if wy >= MAP_HEIGHT:
                continue
            for sx in range(map_w):
                wx = self.camera_x + sx
                if wx >= MAP_WIDTH:
                    continue
                ch = "  "
                attr = self.theme_attr(PAIR_UNSEEN)
                damage_entity: Optional[Tuple[str, int]] = None
                if not explored[wy][wx]:
                    ch = "  "
                else:
                    resource = self.resource_at(wx, wy)
                    building = self.building_at(wx, wy)
                    unit = self.unit_at(wx, wy)
                    if (wx, wy) in visible:
                        attr = self.theme_attr(PAIR_GRASS)
                        if resource:
                            _, node = resource
                            ch = node.glyph
                            if node.kind == "tree":
                                attr = self.theme_attr(PAIR_TREE, curses.A_BOLD)
                            elif node.kind == "berries":
                                attr = self.theme_attr(PAIR_BERRY, curses.A_BOLD)
                            elif node.kind == "gold":
                                attr = self.theme_attr(PAIR_GOLD, curses.A_BOLD)
                            elif node.kind == "stone":
                                attr = self.theme_attr(PAIR_STONE, curses.A_BOLD)
                            else:
                                attr = self.theme_attr(PAIR_GAZELLE, curses.A_BOLD)
                        if building:
                            ch = building.glyph
                            attr = self.owner_color_pair(building.owner) | curses.A_BOLD
                            damage_entity = ("building", building.id)
                            if not building.complete:
                                attr = self.theme_attr(PAIR_ALERT, curses.A_BOLD)
                        if unit:
                            ch = unit.glyph.upper() if unit.owner == self.local_player_id else unit.glyph
                            attr = self.owner_color_pair(unit.owner) | curses.A_BOLD
                            damage_entity = ("unit", unit.id)
                        if damage_entity:
                            remaining = self.damage_flash_remaining(*damage_entity)
                            if remaining > 0:
                                if remaining > DAMAGE_FLASH_TICKS - DAMAGE_MARKER_TICKS:
                                    ch = "!!"
                                    attr = self.theme_attr(PAIR_DAMAGE, curses.A_BOLD)
                                elif (remaining // 2) % 2 == 0:
                                    attr = self.theme_attr(PAIR_DAMAGE, curses.A_BOLD)
                                else:
                                    attr |= curses.A_REVERSE | curses.A_BOLD
                    else:
                        remembered_resource = self.resource_memory_at(self.local_player_id, wx, wy)
                        if remembered_resource:
                            _, node = remembered_resource
                            ch = node.glyph
                            attr = self.remembered_resource_attr(node.kind)
                        else:
                            ch = "░░"
                            attr = self.theme_attr(PAIR_FOG, curses.A_DIM)
                text = self.cell_text(ch)
                if selected_pos == (wx, wy):
                    attr |= curses.A_BOLD
                if wx == self.cursor_x and wy == self.cursor_y:
                    attr |= curses.A_REVERSE | curses.A_BOLD
                self.safe_addstr(origin_y + sy, origin_x + (sx * TILE_WIDTH), text, attr)

    def draw_sidebar(self, x0: int, y0: int, width: int, height: int) -> None:
        player = self.current_player()
        y = y0
        max_y = y0 + height

        def add_line(text: str, attr: Optional[int] = None) -> bool:
            nonlocal y
            if y >= max_y:
                return False
            self.safe_addstr(y, x0, text[:width], self.theme_attr(PAIR_TEXT) if attr is None else attr)
            y += 1
            return True

        def add_header(title: str) -> bool:
            nonlocal y
            if y >= max_y:
                return False
            label = f" {title.upper()} "
            filler = "·" * max(0, width - len(label))
            self.safe_addstr(y, x0, label[:width], self.theme_attr(PAIR_PANEL_TITLE, curses.A_BOLD))
            if len(label) < width:
                self.safe_addstr(y, x0 + len(label), filler[: width - len(label)], self.theme_attr(PAIR_PANEL_MUTED))
            y += 1
            return True

        def add_resource_row(
            left_label: str,
            left_value: int,
            left_pair: int,
            right_label: str,
            right_value: int,
            right_pair: int,
        ) -> None:
            nonlocal y
            if y >= max_y:
                return
            right_x = x0 + max(14, width // 2)
            self.safe_addstr(y, x0, left_label, self.theme_attr(left_pair, curses.A_BOLD))
            self.safe_addstr(y, x0 + len(left_label), f" {left_value}", self.theme_attr(PAIR_TEXT))
            if right_x < x0 + width:
                self.safe_addstr(y, right_x, right_label, self.theme_attr(right_pair, curses.A_BOLD))
                self.safe_addstr(y, right_x + len(right_label), f" {right_value}", self.theme_attr(PAIR_TEXT))
            y += 1

        add_header("Empire")
        add_line(f"Age {AGE_NAMES[player.age]}")
        add_line(
            f"Pop {self.player_population(self.local_player_id)}/{player.pop_cap} · "
            f"Eco {player.economy_level}/{len(TECHS['economy']['cost'])} · "
            f"Mil {player.military_level}/{len(TECHS['military']['cost'])}"
        )
        add_resource_row("Food", player.food, PAIR_FOOD, "Wood", player.wood, PAIR_WOOD)
        add_resource_row("Gold", player.gold, PAIR_GOLD_TEXT, "Stone", player.stone, PAIR_STONE_TEXT)
        if player.ageing:
            next_age = AGE_NAMES[min(player.age + 1, len(AGE_NAMES) - 1)]
            total = AGE_ADVANCE.get(player.age, {"time": player.ageing.time_left})["time"]
            add_line(f"Advancing to {next_age}", self.theme_attr(PAIR_SUCCESS))
            add_line(
                f"{self.meter(total - player.ageing.time_left, total, max(8, min(width - 10, 16)))} "
                f"{player.ageing.time_left:>3}t",
                self.theme_attr(PAIR_PROMPT),
            )

        opponents = [other for other in self.players if other.id != self.local_player_id]
        if opponents:
            add_header("Opponents")
            for other in opponents[:2]:
                add_line(f"{other.name} · {other.civ}", self.owner_color_pair(other.id) | curses.A_BOLD)
                add_line(f"Age {AGE_NAMES[other.age]}", self.theme_attr(PAIR_PANEL_MUTED))

        selected = self.get_selected()
        add_header("Selection")
        selected_group = self.selected_owned_units()
        if len(selected_group) > 1:
            add_line(f"Group {len(selected_group)} units", self.theme_attr(PAIR_PROMPT))
        for line in self.selected_panel_lines(selected, width):
            if not add_line(line):
                break

        if self.command_mode or self.vim_count or self.vim_pending:
            add_header("Input")
            prefix = ":" if self.command_mode else ""
            pending = self.command_buffer if self.command_mode else f"{self.vim_count}{self.vim_pending}"
            add_line((prefix + pending)[: max(1, width - 2)], self.theme_attr(PAIR_PROMPT))

        if self.build_menu_open:
            add_header("Build")
            for line in ["1/h House", "2/l Lumber", "3/m Mill", "4/r Barracks", "b/x close"]:
                if not add_line(line, self.theme_attr(PAIR_PROMPT)):
                    break

        add_header("Cursor")
        for line in self.wrap_panel_lines([f"{self.cursor_x},{self.cursor_y} · {self.describe_cursor_tile()[6:]}"], width):
            if not add_line(line, self.theme_attr(PAIR_PANEL_MUTED)):
                break

        add_header("Commands")
        command_lines = [
            "hjkl/count · gg home",
            ": agent command mode",
            "Space select · a act",
            "b build · v villager",
            "s soldier · n age · t tech",
            "Tab cycle · x clear · q quit",
        ]
        for line in command_lines:
            if not add_line(line, self.theme_attr(PAIR_PANEL_MUTED)):
                break

    def describe_cursor_tile(self) -> str:
        visible = self.current_player().visible
        pos = (self.cursor_x, self.cursor_y)
        if pos not in visible:
            remembered_resource = self.resource_memory_at(self.local_player_id, self.cursor_x, self.cursor_y)
            if remembered_resource:
                _, node = remembered_resource
                return f"Tile: {node.visible_name()} (fog)"
            if self.current_player().explored[self.cursor_y][self.cursor_x]:
                return "Tile: explored fog"
            return "Tile: unseen"
        unit = self.unit_at(*pos)
        if unit:
            owner = self.owner_label(unit.owner)
            return f"Tile: {owner} {unit.name}"
        building = self.building_at(*pos)
        if building:
            owner = self.owner_label(building.owner)
            return f"Tile: {owner} {building.name}"
        resource = self.resource_at(*pos)
        if resource:
            _, node = resource
            return f"Tile: {node.visible_name()}"
        return "Tile: grass"

    def draw_log(self, y0: int, width: int, height: int) -> None:
        self.draw_box(
            y0,
            0,
            height,
            width,
            "Chronicle",
            border_attr=self.theme_attr(PAIR_PANEL),
            title_attr=self.theme_attr(PAIR_PANEL_TITLE, curses.A_BOLD),
        )
        logs = self.visible_logs()[-(height - 2) :]
        if not logs:
            self.safe_addstr(y0 + 1, 2, "No recent events yet.", self.theme_attr(PAIR_PANEL_MUTED))
            return
        inner_width = max(8, width - 4)
        for idx, line in enumerate(logs):
            line_y = y0 + 1 + idx
            if line.startswith("[") and "] " in line:
                stamp, message = line.split("] ", 1)
                stamp += "]"
                self.safe_addstr(line_y, 2, stamp, self.theme_attr(PAIR_PANEL_MUTED))
                self.safe_addstr(line_y, 2 + len(stamp) + 1, message[: max(0, inner_width - len(stamp) - 1)], self.theme_attr(PAIR_TEXT))
            else:
                self.safe_addstr(line_y, 2, line[:inner_width], self.theme_attr(PAIR_TEXT))


class LobbyStore:
    def __init__(self, db_path: str = LOBBY_DB_PATH) -> None:
        self.db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS rooms (
                    room_id TEXT PRIMARY KEY,
                    room_code TEXT NOT NULL UNIQUE,
                    room_name TEXT NOT NULL,
                    host_player_id TEXT NOT NULL,
                    max_players INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    countdown_end REAL,
                    created_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    civilization TEXT NOT NULL,
                    ready INTEGER NOT NULL,
                    seat INTEGER NOT NULL,
                    joined_at REAL NOT NULL,
                    FOREIGN KEY(room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    sender_type TEXT NOT NULL,
                    sender_player_id TEXT,
                    sender_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY(room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS matches (
                    room_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    game_state TEXT NOT NULL,
                    last_command_id INTEGER NOT NULL DEFAULT 0,
                    lease_holder TEXT,
                    lease_expires REAL,
                    updated_at REAL NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY(room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS match_commands (
                    command_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id TEXT NOT NULL,
                    player_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY(room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
                );
                """
            )

    def _now(self) -> float:
        return time.time()

    def _clean_room_name(self, room_name: str) -> str:
        cleaned = "".join(ch for ch in room_name.strip() if ch.isprintable())[:ROOM_NAME_MAX_LEN]
        if not ROOM_NAME_PATTERN.fullmatch(cleaned):
            cleaned = "".join(ch for ch in cleaned if ch.isalnum() or ch in " '-")[:ROOM_NAME_MAX_LEN]
        return cleaned.strip()

    def _clean_player_name(self, name: str) -> str:
        cleaned = "".join(ch for ch in name.strip() if ch.isprintable())[:PLAYER_NAME_MAX_LEN]
        if not PLAYER_NAME_PATTERN.fullmatch(cleaned):
            cleaned = "".join(ch for ch in cleaned if ch.isalnum() or ch in " _'-")[:PLAYER_NAME_MAX_LEN]
        return cleaned.strip()

    def _clean_message(self, content: str) -> str:
        cleaned = "".join(ch for ch in content if ch.isprintable())
        return cleaned.strip()[:CHAT_MESSAGE_MAX_LEN]

    def _default_room_name(self, room_code: str) -> str:
        username = "".join(ch for ch in os.environ.get("USER", "").strip() if ch.isalnum() or ch in " '-")
        if username:
            return f"{username}'s Room"[:ROOM_NAME_MAX_LEN]
        return f"Hittite Hall {room_code}"

    def _insert_message(
        self,
        conn: sqlite3.Connection,
        room_id: str,
        sender_type: str,
        sender_name: str,
        content: str,
        sender_player_id: Optional[str] = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO chat_messages (
                message_id, room_id, sender_type, sender_player_id, sender_name, content, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (uuid.uuid4().hex, room_id, sender_type, sender_player_id, sender_name, content, self._now()),
        )

    def _generate_room_code(self, conn: sqlite3.Connection) -> str:
        while True:
            code = "".join(secrets.choice(ROOM_CODE_CHARS) for _ in range(4))
            exists = conn.execute(
                "SELECT 1 FROM rooms WHERE room_code = ? AND state != 'closed'",
                (code,),
            ).fetchone()
            if not exists:
                return code

    def _next_open_seat(self, conn: sqlite3.Connection, room_id: str) -> Optional[int]:
        used = {
            row["seat"]
            for row in conn.execute("SELECT seat FROM players WHERE room_id = ?", (room_id,)).fetchall()
        }
        for seat in range(1, ROOM_MAX_PLAYERS + 1):
            if seat not in used:
                return seat
        return None

    def _room_player_count(self, conn: sqlite3.Connection, room_id: str) -> int:
        row = conn.execute("SELECT COUNT(*) AS count FROM players WHERE room_id = ?", (room_id,)).fetchone()
        return int(row["count"]) if row else 0

    def create_room(self, requested_name: str) -> Tuple[str, str]:
        with self._connect() as conn:
            room_id = uuid.uuid4().hex
            room_code = self._generate_room_code(conn)
            player_id = uuid.uuid4().hex
            room_name = self._clean_room_name(requested_name) or self._default_room_name(room_code)
            now = self._now()
            conn.execute(
                """
                INSERT INTO rooms (
                    room_id, room_code, room_name, host_player_id, max_players, state, countdown_end, created_at
                ) VALUES (?, ?, ?, ?, ?, 'lobby', NULL, ?)
                """,
                (room_id, room_code, room_name, player_id, ROOM_MAX_PLAYERS, now),
            )
            conn.execute(
                """
                INSERT INTO players (
                    player_id, room_id, display_name, civilization, ready, seat, joined_at
                ) VALUES (?, ?, ?, ?, 0, 1, ?)
                """,
                (player_id, room_id, "Player1", MULTIPLAYER_CIV, now),
            )
            self._insert_message(conn, room_id, "system", "[System]", f"Room created. Share code {room_code} with other players.")
            return room_id, player_id

    def join_room(self, raw_code: str) -> Tuple[Optional[Tuple[str, str]], Optional[str]]:
        room_code = raw_code.strip().upper()
        with self._connect() as conn:
            room = conn.execute("SELECT * FROM rooms WHERE room_code = ?", (room_code,)).fetchone()
            if not room:
                return None, "Room not found."
            if room["state"] == "closed":
                return None, "This room is no longer available."
            if room["state"] in ("starting", "in_game"):
                return None, "This room is already in a game. Joining is not allowed."
            if self._room_player_count(conn, room["room_id"]) >= ROOM_MAX_PLAYERS:
                return None, "Room is full."
            seat = self._next_open_seat(conn, room["room_id"])
            if seat is None:
                return None, "Room is full."
            player_id = uuid.uuid4().hex
            display_name = f"Player{seat}"
            conn.execute(
                """
                INSERT INTO players (
                    player_id, room_id, display_name, civilization, ready, seat, joined_at
                ) VALUES (?, ?, ?, ?, 0, ?, ?)
                """,
                (player_id, room["room_id"], display_name, MULTIPLAYER_CIV, seat, self._now()),
            )
            self._insert_message(conn, room["room_id"], "system", "[System]", f"{display_name} joined the room.")
            return (room["room_id"], player_id), None

    def _advance_room_state(self, conn: sqlite3.Connection, room_id: str) -> None:
        room = conn.execute("SELECT state, countdown_end FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
        if room and room["state"] == "starting" and room["countdown_end"] and room["countdown_end"] <= self._now():
            self._create_match(conn, room_id)
            conn.execute("UPDATE rooms SET state = 'in_game' WHERE room_id = ?", (room_id,))
            self._insert_message(conn, room_id, "system", "[System]", "Match started.")

    def _create_match(self, conn: sqlite3.Connection, room_id: str) -> None:
        existing = conn.execute("SELECT 1 FROM matches WHERE room_id = ?", (room_id,)).fetchone()
        if existing:
            return
        players = conn.execute(
            "SELECT * FROM players WHERE room_id = ? ORDER BY seat ASC, joined_at ASC",
            (room_id,),
        ).fetchall()
        if len(players) < ROOM_MIN_PLAYERS:
            return
        game = Game(
            None,
            local_player_id=0,
            player_specs=[(player["display_name"], player["civilization"]) for player in players],
            enable_ai=False,
        )
        now = self._now()
        conn.execute(
            """
            INSERT OR IGNORE INTO matches (
                room_id, state, game_state, last_command_id, lease_holder, lease_expires, updated_at, created_at
            ) VALUES (?, 'in_game', ?, 0, NULL, NULL, ?, ?)
            """,
            (room_id, game.serialize_state(), now, now),
        )

    def get_snapshot(self, room_id: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            self._advance_room_state(conn, room_id)
            room = conn.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
            if not room:
                return None
            players = conn.execute(
                "SELECT * FROM players WHERE room_id = ? ORDER BY seat ASC, joined_at ASC",
                (room_id,),
            ).fetchall()
            messages = conn.execute(
                "SELECT * FROM chat_messages WHERE room_id = ? ORDER BY created_at DESC LIMIT 50",
                (room_id,),
            ).fetchall()
            return {
                "room": dict(room),
                "players": [dict(player) for player in players],
                "messages": [dict(message) for message in reversed(messages)],
            }

    def set_ready(self, player_id: str, ready: bool) -> Optional[str]:
        with self._connect() as conn:
            player = conn.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()
            if not player:
                return "Player not found."
            room = conn.execute("SELECT * FROM rooms WHERE room_id = ?", (player["room_id"],)).fetchone()
            if not room or room["state"] != "lobby":
                return "Room is no longer accepting lobby changes."
            if bool(player["ready"]) == ready:
                return None
            conn.execute("UPDATE players SET ready = ? WHERE player_id = ?", (1 if ready else 0, player_id))
            state_text = "READY" if ready else "NOT READY"
            self._insert_message(conn, room["room_id"], "system", "[System]", f"{player['display_name']} is now {state_text}.")
            return None

    def change_name(self, player_id: str, new_name: str) -> Optional[str]:
        cleaned = self._clean_player_name(new_name)
        if not cleaned:
            return "Invalid name."
        with self._connect() as conn:
            player = conn.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()
            if not player:
                return "Player not found."
            room = conn.execute("SELECT * FROM rooms WHERE room_id = ?", (player["room_id"],)).fetchone()
            if not room or room["state"] != "lobby":
                return "Room is no longer accepting lobby changes."
            taken = conn.execute(
                """
                SELECT 1 FROM players
                WHERE room_id = ? AND player_id != ? AND LOWER(display_name) = LOWER(?)
                """,
                (player["room_id"], player_id, cleaned),
            ).fetchone()
            if taken:
                return "That name is already taken in this room."
            old_name = player["display_name"]
            if cleaned == old_name:
                return None
            conn.execute("UPDATE players SET display_name = ? WHERE player_id = ?", (cleaned, player_id))
            self._insert_message(conn, room["room_id"], "system", "[System]", f"{old_name} changed name to {cleaned}.")
            return None

    def post_chat(self, player_id: str, content: str) -> Optional[str]:
        cleaned = self._clean_message(content)
        if not cleaned:
            return None
        with self._connect() as conn:
            player = conn.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()
            if not player:
                return "Player not found."
            room = conn.execute("SELECT * FROM rooms WHERE room_id = ?", (player["room_id"],)).fetchone()
            if not room or room["state"] != "lobby":
                return "Room is no longer accepting lobby chat."
            self._insert_message(conn, room["room_id"], "player", player["display_name"], cleaned, player_id)
            return None

    def start_room(self, player_id: str) -> Optional[str]:
        with self._connect() as conn:
            player = conn.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()
            if not player:
                return "Player not found."
            room = conn.execute("SELECT * FROM rooms WHERE room_id = ?", (player["room_id"],)).fetchone()
            if not room or room["state"] != "lobby":
                return "Room is not in lobby state."
            if room["host_player_id"] != player_id:
                return "Only the host can start the match."
            players = conn.execute("SELECT * FROM players WHERE room_id = ? ORDER BY joined_at ASC", (room["room_id"],)).fetchall()
            if len(players) < ROOM_MIN_PLAYERS:
                return "At least 2 players are required to start."
            not_ready = [row["display_name"] for row in players if not row["ready"]]
            if not_ready:
                if len(not_ready) == 1:
                    return f"Cannot start: {not_ready[0]} is not ready."
                return "All players must be ready before starting."
            conn.execute(
                "UPDATE rooms SET state = 'starting', countdown_end = ? WHERE room_id = ?",
                (self._now() + 3.0, room["room_id"]),
            )
            self._insert_message(conn, room["room_id"], "system", "[System]", "All players ready.")
            self._insert_message(conn, room["room_id"], "system", "[System]", "Host started the match.")
            return None

    def leave_room(self, player_id: str) -> None:
        with self._connect() as conn:
            player = conn.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()
            if not player:
                return
            room = conn.execute("SELECT * FROM rooms WHERE room_id = ?", (player["room_id"],)).fetchone()
            if not room:
                return
            room_id = room["room_id"]
            display_name = player["display_name"]
            was_host = room["host_player_id"] == player_id
            conn.execute("DELETE FROM players WHERE player_id = ?", (player_id,))
            remaining = conn.execute(
                "SELECT * FROM players WHERE room_id = ? ORDER BY joined_at ASC",
                (room_id,),
            ).fetchall()
            if room["state"] == "lobby":
                self._insert_message(conn, room_id, "system", "[System]", f"{display_name} left the room.")
            if not remaining:
                conn.execute("UPDATE rooms SET state = 'closed' WHERE room_id = ?", (room_id,))
                return
            if room["state"] == "lobby" and was_host:
                new_host = remaining[0]
                conn.execute("UPDATE rooms SET host_player_id = ? WHERE room_id = ?", (new_host["player_id"], room_id))
                self._insert_message(conn, room_id, "system", "[System]", f"{new_host['display_name']} is now the host.")

    def enqueue_match_command(self, room_id: str, player_id: str, payload: Dict[str, object]) -> bool:
        with self._connect() as conn:
            room = conn.execute("SELECT state FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
            player = conn.execute(
                "SELECT 1 FROM players WHERE room_id = ? AND player_id = ?",
                (room_id, player_id),
            ).fetchone()
            match = conn.execute("SELECT 1 FROM matches WHERE room_id = ?", (room_id,)).fetchone()
            if not room or room["state"] != "in_game" or not player or not match:
                return False
            conn.execute(
                "INSERT INTO match_commands (room_id, player_id, payload, created_at) VALUES (?, ?, ?, ?)",
                (room_id, player_id, json.dumps(payload, separators=(",", ":")), self._now()),
            )
            return True

    def advance_match(self, room_id: str, player_id: str) -> None:
        with self._connect() as conn:
            room = conn.execute("SELECT state FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
            player = conn.execute(
                "SELECT * FROM players WHERE room_id = ? AND player_id = ?",
                (room_id, player_id),
            ).fetchone()
            match = conn.execute("SELECT * FROM matches WHERE room_id = ?", (room_id,)).fetchone()
            if not room or room["state"] != "in_game" or not player or not match:
                return
            now = self._now()
            conn.execute(
                """
                UPDATE matches
                SET lease_holder = ?, lease_expires = ?
                WHERE room_id = ?
                  AND (lease_holder IS NULL OR lease_holder = ? OR lease_expires <= ?)
                """,
                (player_id, now + MATCH_LEASE_SECONDS, room_id, player_id, now),
            )
            match = conn.execute("SELECT * FROM matches WHERE room_id = ?", (room_id,)).fetchone()
            if not match or match["lease_holder"] != player_id:
                return
            owner_index = max(0, int(player["seat"]) - 1)
            game = Game.from_serialized(None, str(match["game_state"]), owner_index)
            command_rows = conn.execute(
                """
                SELECT command_id, payload FROM match_commands
                WHERE room_id = ? AND command_id > ?
                ORDER BY command_id ASC
                """,
                (room_id, int(match["last_command_id"])),
            ).fetchall()
            last_command_id = int(match["last_command_id"])
            had_commands = False
            for row in command_rows:
                game.apply_command(json.loads(row["payload"]))
                last_command_id = int(row["command_id"])
                had_commands = True
            step_length = TICK_MS / 1000.0
            elapsed = max(0.0, now - float(match["updated_at"]))
            steps = min(MATCH_MAX_CATCHUP_STEPS, int(elapsed / step_length))
            for _ in range(steps):
                game.update()
                if game.winner is not None:
                    break
            if not had_commands and steps == 0:
                conn.execute(
                    "UPDATE matches SET lease_expires = ? WHERE room_id = ?",
                    (now + MATCH_LEASE_SECONDS, room_id),
                )
                return
            updated_at = float(match["updated_at"]) + (steps * step_length)
            if had_commands and steps == 0:
                updated_at = now
            conn.execute(
                """
                UPDATE matches
                SET game_state = ?, last_command_id = ?, updated_at = ?, lease_holder = ?, lease_expires = ?, state = ?
                WHERE room_id = ?
                """,
                (
                    game.serialize_state(),
                    last_command_id,
                    updated_at,
                    player_id,
                    now + MATCH_LEASE_SECONDS,
                    "finished" if game.winner is not None else "in_game",
                    room_id,
                ),
            )
            if last_command_id:
                conn.execute(
                    "DELETE FROM match_commands WHERE room_id = ? AND command_id <= ?",
                    (room_id, last_command_id),
                )

    def get_match_state(self, room_id: str, player_id: str) -> Optional[Dict[str, object]]:
        with self._connect() as conn:
            room = conn.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
            player = conn.execute(
                "SELECT * FROM players WHERE room_id = ? AND player_id = ?",
                (room_id, player_id),
            ).fetchone()
            match = conn.execute("SELECT * FROM matches WHERE room_id = ?", (room_id,)).fetchone()
            if not room or not player or not match:
                return None
            return {
                "room_code": room["room_code"],
                "room_state": room["state"],
                "match_state": match["state"],
                "owner_index": max(0, int(player["seat"]) - 1),
                "game_state": match["game_state"],
            }


class SSHOfEmpiresApp:
    def __init__(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        self.store = LobbyStore()
        self.theme_mode = "mono"
        if hasattr(curses, "set_escdelay"):
            curses.set_escdelay(CURSES_ESCDELAY_MS)
        self.stdscr.keypad(True)
        self.theme_mode = initialize_terminal_theme()

    def safe_addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        height, width = self.stdscr.getmaxyx()
        if y < 0 or y >= height or x >= width:
            return
        available = max(0, width - x)
        if available <= 0:
            return
        try:
            self.stdscr.addstr(y, x, text[:available], attr)
        except curses.error:
            pass

    def theme_attr(self, pair_id: int, extra: int = 0) -> int:
        return theme_color(pair_id) | extra

    def draw_box(self, y: int, x: int, h: int, w: int, title: Optional[str] = None) -> None:
        if h < 3 or w < 4:
            return
        border_attr = self.theme_attr(PAIR_PANEL)
        title_attr = self.theme_attr(PAIR_PANEL_TITLE, curses.A_BOLD)
        self.safe_addstr(y, x, "╔" + ("═" * (w - 2)) + "╗", border_attr)
        for row in range(1, h - 1):
            self.safe_addstr(y + row, x, "║", border_attr)
            self.safe_addstr(y + row, x + w - 1, "║", border_attr)
        self.safe_addstr(y + h - 1, x, "╚" + ("═" * (w - 2)) + "╝", border_attr)
        if title:
            label = f" {title} "
            start = x + max(1, (w - len(label)) // 2)
            self.safe_addstr(y, start, label[: max(0, w - 2)], title_attr)

    def menu(self, title: str, options: List[str], subtitle: str = "") -> int:
        index = 0
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        while True:
            self.stdscr.erase()
            height, width = self.stdscr.getmaxyx()
            panel_w = min(56, width - 4)
            panel_h = len(options) + 8
            y = max(1, (height - panel_h) // 2)
            x = max(2, (width - panel_w) // 2)
            self.draw_box(y, x, panel_h, panel_w, title)
            if subtitle:
                self.safe_addstr(y + 2, x + 2, subtitle[: panel_w - 4], self.theme_attr(PAIR_PANEL_MUTED))
            for idx, option in enumerate(options):
                prefix = "›" if idx == index else " "
                attr = self.theme_attr(PAIR_CURSOR, curses.A_BOLD) if idx == index else self.theme_attr(PAIR_TEXT)
                self.safe_addstr(y + 4 + idx, x + 4, f"{prefix} {option}"[: panel_w - 8], attr)
            self.safe_addstr(y + panel_h - 2, x + 2, "[ Enter ] Select    [ Esc ] Back", self.theme_attr(PAIR_PANEL_MUTED))
            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key in (27, ord("q")):
                return -1
            if key in (curses.KEY_UP, ord("k")):
                index = (index - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord("j")):
                index = (index + 1) % len(options)
            elif key in (10, 13, curses.KEY_ENTER):
                return index

    def input_screen(
        self,
        title: str,
        label: str,
        max_len: int,
        allow_char,
        footer_lines: List[str],
        transform=lambda value: value,
    ) -> Optional[str]:
        buffer = ""
        notice = ""
        curses.curs_set(1)
        self.stdscr.nodelay(False)
        while True:
            self.stdscr.erase()
            height, width = self.stdscr.getmaxyx()
            panel_w = min(62, width - 4)
            panel_h = 12 + len(footer_lines)
            y = max(1, (height - panel_h) // 2)
            x = max(2, (width - panel_w) // 2)
            self.draw_box(y, x, panel_h, panel_w, title)
            self.safe_addstr(y + 2, x + 2, label, self.theme_attr(PAIR_TEXT))
            self.safe_addstr(y + 3, x + 2, f"> {buffer}", self.theme_attr(PAIR_PROMPT))
            for idx, line in enumerate(footer_lines):
                self.safe_addstr(y + 5 + idx, x + 2, line[: panel_w - 4], self.theme_attr(PAIR_PANEL_MUTED))
            if notice:
                self.safe_addstr(y + panel_h - 3, x + 2, notice[: panel_w - 4], self.theme_attr(PAIR_ALERT))
            self.safe_addstr(y + panel_h - 2, x + 2, "[ Enter ] Confirm    [ Esc ] Cancel", self.theme_attr(PAIR_PANEL_MUTED))
            cursor_x = min(width - 1, x + 4 + len(buffer))
            self.stdscr.move(y + 3, cursor_x)
            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key == 27:
                return None
            if key in (10, 13, curses.KEY_ENTER):
                return transform(buffer)
            if key in (curses.KEY_BACKSPACE, 127, 8):
                buffer = buffer[:-1]
                continue
            if 0 <= key < 256:
                ch = chr(key)
                if allow_char(ch) and len(buffer) < max_len:
                    buffer += ch
                    notice = ""
                else:
                    notice = "Invalid character."

    def run(self) -> None:
        while True:
            choice = self.menu(APP_TITLE, ["Single Player", "Multiplayer", "Quit"], "Choose a mode.")
            if choice in (-1, 2):
                return
            if choice == 0:
                game = Game(self.stdscr)
                game.run()
                continue
            self.run_multiplayer_menu()

    def run_multiplayer_menu(self) -> None:
        while True:
            choice = self.menu(f"{APP_TITLE} — MULTIPLAYER", ["Create Room", "Join Room", "Back"], "Private rooms for up to 3 Hittites.")
            if choice in (-1, 2):
                return
            if choice == 0:
                room_name = self.input_screen(
                    f"{APP_TITLE} — CREATE ROOM",
                    "Room Name (optional):",
                    ROOM_NAME_MAX_LEN,
                    lambda ch: ch.isalnum() or ch in " '-",
                    [
                        "Create a private multiplayer room for up to 3 users.",
                        "",
                        f"Civilization: {MULTIPLAYER_CIV}",
                        f"Max Players: {ROOM_MAX_PLAYERS}",
                        "Join Method: Room Code",
                    ],
                    lambda value: value.strip(),
                )
                if room_name is None:
                    continue
                room_id, player_id = self.store.create_room(room_name)
                self.run_lobby(room_id, player_id)
            elif choice == 1:
                room_code = self.input_screen(
                    f"{APP_TITLE} — JOIN ROOM",
                    "Room Code:",
                    6,
                    lambda ch: ch.isalnum(),
                    ["Enter a room code from the host.", "", "Codes are case-insensitive."],
                    lambda value: value.strip().upper(),
                )
                if room_code is None:
                    continue
                result, error = self.store.join_room(room_code)
                if error:
                    self.show_message("Join Room", error)
                    continue
                assert result is not None
                self.run_lobby(result[0], result[1])

    def show_message(self, title: str, message: str) -> None:
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        while True:
            self.stdscr.erase()
            height, width = self.stdscr.getmaxyx()
            panel_w = min(64, width - 4)
            lines = textwrap.wrap(message, max(10, panel_w - 4))
            panel_h = max(7, len(lines) + 5)
            y = max(1, (height - panel_h) // 2)
            x = max(2, (width - panel_w) // 2)
            self.draw_box(y, x, panel_h, panel_w, title)
            for idx, line in enumerate(lines):
                self.safe_addstr(y + 2 + idx, x + 2, line, self.theme_attr(PAIR_TEXT))
            self.safe_addstr(y + panel_h - 2, x + 2, "[ Enter ] OK", self.theme_attr(PAIR_PANEL_MUTED))
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (10, 13, curses.KEY_ENTER, 27):
                return

    def format_chat_lines(self, messages: List[Dict[str, object]], width: int, max_lines: int) -> List[str]:
        rendered: List[str] = []
        for msg in messages[-20:]:
            prefix = "[System] " if msg["sender_type"] == "system" else f"{msg['sender_name']}: "
            wrapped = textwrap.wrap(prefix + str(msg["content"]), max(10, width))
            rendered.extend(wrapped or [""])
        return rendered[-max_lines:]

    def run_lobby(self, room_id: str, player_id: str) -> None:
        input_buffer = ""
        local_notice = ""
        help_overlay = False
        self.stdscr.nodelay(True)
        self.stdscr.timeout(150)
        curses.curs_set(1)
        try:
            while True:
                snapshot = self.store.get_snapshot(room_id)
                if not snapshot:
                    return
                room = snapshot["room"]
                players = snapshot["players"]
                you = next((player for player in players if player["player_id"] == player_id), None)
                if room["state"] == "closed" or you is None:
                    return
                if room["state"] == "in_game":
                    self.run_multiplayer_match(room_id, player_id)
                    return

                host_player_id = room["host_player_id"]
                for player in players:
                    player["is_host"] = player["player_id"] == host_player_id

                self.render_lobby(snapshot, you, input_buffer, local_notice, help_overlay)
                key = self.stdscr.getch()
                if key == -1:
                    continue
                if help_overlay and key in (27, ord("q"), 10, 13, curses.KEY_ENTER):
                    help_overlay = False
                    continue
                if room["state"] == "starting":
                    continue
                if key in (curses.KEY_BACKSPACE, 127, 8):
                    input_buffer = input_buffer[:-1]
                    continue
                if key in (10, 13, curses.KEY_ENTER):
                    text = input_buffer.strip()
                    input_buffer = ""
                    local_notice = ""
                    if not text:
                        continue
                    if text.startswith("/"):
                        command, _, args = text.partition(" ")
                        args = args.strip()
                        if command == "/name":
                            error = self.store.change_name(player_id, args)
                            local_notice = f"[System] {error}" if error else ""
                        elif command == "/ready":
                            error = self.store.set_ready(player_id, True)
                            local_notice = f"[System] {error}" if error else ""
                        elif command == "/unready":
                            error = self.store.set_ready(player_id, False)
                            local_notice = f"[System] {error}" if error else ""
                        elif command == "/leave":
                            self.store.leave_room(player_id)
                            return
                        elif command == "/help":
                            help_overlay = True
                        elif command == "/start":
                            error = self.store.start_room(player_id)
                            local_notice = f"[System] {error}" if error else ""
                        else:
                            local_notice = "[System] Unknown command. Type /help."
                    else:
                        error = self.store.post_chat(player_id, text)
                        local_notice = f"[System] {error}" if error else ""
                    continue
                if key == 27:
                    help_overlay = False
                    continue
                if 0 <= key < 256:
                    ch = chr(key)
                    if ch.isprintable() and len(input_buffer) < CHAT_MESSAGE_MAX_LEN:
                        input_buffer += ch
        finally:
            curses.curs_set(0)

    def render_lobby(
        self,
        snapshot: Dict[str, object],
        you: Dict[str, object],
        input_buffer: str,
        local_notice: str,
        help_overlay: bool,
    ) -> None:
        room = snapshot["room"]
        players = snapshot["players"]
        messages = snapshot["messages"]
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if width < 80 or height < 24:
            self.safe_addstr(0, 0, "Resize terminal to at least 80x24 for multiplayer.")
            self.stdscr.refresh()
            return

        header_h = 5
        bottom_h = 7
        mid_h = height - header_h - bottom_h
        left_w = max(34, min(40, width // 3 + 4)) if width >= 100 else width
        right_w = width - left_w - 3

        self.draw_box(0, 0, header_h, width, f"{APP_TITLE} — ROOM {room['room_code']}")
        host = next((player["display_name"] for player in players if player["player_id"] == room["host_player_id"]), "Unknown")
        player_count = len(players)
        self.safe_addstr(1, 2, f"Room: {room['room_name']}")
        self.safe_addstr(1, max(2, width // 2), f"Host: {host}")
        self.safe_addstr(2, 2, f"Code: {room['room_code']}")
        self.safe_addstr(2, max(2, width // 2), f"Status: {'Waiting in lobby' if room['state'] == 'lobby' else 'Match starting'}")
        self.safe_addstr(3, 2, f"Players: {player_count}/{ROOM_MAX_PLAYERS}")
        self.safe_addstr(3, max(2, width // 2), f"Civilization: {MULTIPLAYER_CIV}")

        if width >= 100:
            self.draw_box(header_h, 0, mid_h, left_w, "Players")
            self.draw_box(header_h, left_w + 1, mid_h, right_w, "Chat")
            player_lines: List[str] = []
            for seat in range(1, ROOM_MAX_PLAYERS + 1):
                player = next((entry for entry in players if entry["seat"] == seat), None)
                if not player:
                    player_lines.append(f"{seat}. Empty slot")
                    player_lines.append("")
                    continue
                ready = "[READY    ]" if player["ready"] else "[NOT READY]"
                host_badge = " (HOST)" if player["player_id"] == room["host_player_id"] else ""
                player_lines.append(f"{seat}. {player['display_name']}{host_badge} {ready}")
                player_lines.append(f"   Civ: {MULTIPLAYER_CIV}")
            for idx, line in enumerate(player_lines[: mid_h - 2]):
                self.safe_addstr(header_h + 1 + idx, 1, line[: left_w - 2])

            chat_lines = self.format_chat_lines(messages, right_w - 2, mid_h - 2)
            for idx, line in enumerate(chat_lines):
                self.safe_addstr(header_h + 1 + idx, left_w + 2, line[: right_w - 2])
        else:
            players_h = 8
            chat_h = max(6, mid_h - players_h - 1)
            self.draw_box(header_h, 0, players_h, width, "Players")
            player_lines = []
            for seat in range(1, ROOM_MAX_PLAYERS + 1):
                player = next((entry for entry in players if entry["seat"] == seat), None)
                if not player:
                    player_lines.append(f"{seat}. Empty slot")
                    continue
                ready = "[READY]" if player["ready"] else "[NOT READY]"
                host_badge = " (HOST)" if player["player_id"] == room["host_player_id"] else ""
                player_lines.append(f"{seat}. {player['display_name']}{host_badge} {ready}")
            for idx, line in enumerate(player_lines[: players_h - 2]):
                self.safe_addstr(header_h + 1 + idx, 1, line[: width - 2])
            self.draw_box(header_h + players_h, 0, chat_h, width, "Chat")
            chat_lines = self.format_chat_lines(messages, width - 2, chat_h - 2)
            for idx, line in enumerate(chat_lines):
                self.safe_addstr(header_h + players_h + 1 + idx, 1, line[: width - 2])

        self.draw_box(height - bottom_h, 0, bottom_h, width, "You")
        self.safe_addstr(height - bottom_h + 1, 2, f"Name: {you['display_name']}")
        self.safe_addstr(height - bottom_h + 1, max(24, width // 2), f"Civilization: {MULTIPLAYER_CIV}")
        self.safe_addstr(height - bottom_h + 2, 2, f"Status: {'READY' if you['ready'] else 'NOT READY'}")
        self.safe_addstr(height - bottom_h + 3, 2, "Type chat and press Enter")
        self.safe_addstr(height - bottom_h + 4, 2, "/name <new_name>   /ready   /unready   /leave   /help")
        self.safe_addstr(height - bottom_h + 5, 2, "Host only: /start")
        if local_notice:
            self.safe_addstr(height - bottom_h - 1, 2, local_notice[: width - 4])
        prompt = "> " + input_buffer
        self.safe_addstr(height - 1, 0, " " * width)
        self.safe_addstr(height - 1, 0, prompt[: width - 1])
        self.stdscr.move(height - 1, min(width - 1, len(prompt)))

        if room["state"] == "starting":
            remaining = max(1, int(round(float(room["countdown_end"]) - time.time() + 0.5)))
            overlay_w = min(28, width - 4)
            overlay_h = 5
            y = max(1, (height - overlay_h) // 2)
            x = max(2, (width - overlay_w) // 2)
            self.draw_box(y, x, overlay_h, overlay_w)
            self.safe_addstr(y + 1, x + 4, "MATCH STARTING...")
            self.safe_addstr(y + 2, x + overlay_w // 2, str(remaining), curses.A_BOLD)

        if help_overlay:
            overlay_lines = [
                "Type chat and press Enter",
                "",
                "/name <new_name>",
                "/ready  /unready",
                "/leave  /help",
                "Host: /start",
                "Esc to close",
            ]
            overlay_w = min(34, width - 4)
            overlay_h = len(overlay_lines) + 3
            y = max(1, (height - overlay_h) // 2)
            x = max(2, (width - overlay_w) // 2)
            self.draw_box(y, x, overlay_h, overlay_w, "Lobby Help")
            for idx, line in enumerate(overlay_lines):
                self.safe_addstr(y + 1 + idx, x + 2, line)

        self.stdscr.refresh()

    def restore_match_view(self, game: Optional[Game], snapshot: Dict[str, object]) -> Game:
        owner_index = int(snapshot["owner_index"])
        if game is None:
            game = Game.from_serialized(self.stdscr, str(snapshot["game_state"]), owner_index)
            town_center = next(
                (
                    building
                    for building in game.buildings.values()
                    if building.owner == owner_index and building.kind == "town_center"
                ),
                None,
            )
            if town_center:
                game.cursor_x = town_center.x
                game.cursor_y = town_center.y
                game.selected_kind = "building"
                game.selected_id = town_center.id
            return game
        cursor_x = game.cursor_x
        cursor_y = game.cursor_y
        camera_x = game.camera_x
        camera_y = game.camera_y
        selected_kind = game.selected_kind
        selected_id = game.selected_id
        build_menu_open = game.build_menu_open
        game.local_player_id = owner_index
        game.stdscr = self.stdscr
        game.restore_serialized_state(str(snapshot["game_state"]))
        game.cursor_x = cursor_x
        game.cursor_y = cursor_y
        game.camera_x = camera_x
        game.camera_y = camera_y
        game.selected_kind = selected_kind
        game.selected_id = selected_id
        game.build_menu_open = build_menu_open
        if game.selected_id is not None and game.get_selected() is None:
            game.selected_kind = None
            game.selected_id = None
            game.selected_unit_ids = []
            game.build_menu_open = False
        game.keep_cursor_visible()
        return game

    def queue_match_command(self, room_id: str, player_id: str, payload: Dict[str, object]) -> None:
        self.store.enqueue_match_command(room_id, player_id, payload)

    def run_multiplayer_match(self, room_id: str, player_id: str) -> None:
        self.stdscr.nodelay(True)
        self.stdscr.timeout(TICK_MS)
        curses.curs_set(0)
        game: Optional[Game] = None
        while True:
            self.store.advance_match(room_id, player_id)
            snapshot = self.store.get_match_state(room_id, player_id)
            if not snapshot:
                return
            game = self.restore_match_view(game, snapshot)
            game.initialize_curses()
            game.render()
            key = self.stdscr.getch()
            if key == -1:
                continue
            key = normalize_input_key(self.stdscr, key, TICK_MS)
            def queue_payload(payload: Dict[str, object]) -> None:
                self.queue_match_command(room_id, player_id, payload)

            vim_result = game.handle_vim_input(key, queue_payload)
            if vim_result == "quit":
                self.store.leave_room(player_id)
                return
            if vim_result == "handled":
                continue
            if game.build_menu_open:
                if key == ord("q"):
                    self.store.leave_room(player_id)
                    return
                if key in (ord("b"), ord("x"), 27):
                    game.build_menu_open = False
                    continue
                building_kind = BUILD_MENU_OPTIONS.get(key)
                selected = game.get_selected()
                if building_kind and isinstance(selected, Unit) and selected.owner == game.local_player_id and selected.kind == "villager":
                    self.queue_match_command(
                        room_id,
                        player_id,
                        {
                            "kind": "build",
                            "owner": game.local_player_id,
                            "unit_id": selected.id,
                            "building_kind": building_kind,
                            "x": game.cursor_x,
                            "y": game.cursor_y,
                        },
                    )
                    game.build_menu_open = False
                continue
            if key == ord("q"):
                self.store.leave_room(player_id)
                return
            movement = movement_delta_for_key(key)
            if movement is not None:
                game.move_cursor(*movement)
            elif key in (ord(" "), 10, 13):
                game.select_at_cursor()
            elif key == 9:
                game.cycle_selection()
            elif key in (ord("x"), 27):
                game.selected_kind = None
                game.selected_id = None
                game.selected_unit_ids = []
                game.build_menu_open = False
            elif key in (ord("a"), curses.ascii.NUL):
                selected = game.get_selected()
                if isinstance(selected, Unit) and selected.owner == game.local_player_id:
                    self.queue_match_command(
                        room_id,
                        player_id,
                        {
                            "kind": "context",
                            "owner": game.local_player_id,
                            "unit_id": selected.id,
                            "x": game.cursor_x,
                            "y": game.cursor_y,
                        },
                    )
            elif key == ord("b"):
                selected = game.get_selected()
                if isinstance(selected, Unit) and selected.owner == game.local_player_id and selected.kind == "villager":
                    game.build_menu_open = True
            elif key == ord("v"):
                selected = game.get_selected()
                if isinstance(selected, Building) and selected.owner == game.local_player_id:
                    self.queue_match_command(
                        room_id,
                        player_id,
                        {"kind": "queue_villager", "owner": game.local_player_id, "building_id": selected.id},
                    )
            elif key == ord("s"):
                selected = game.get_selected()
                if isinstance(selected, Building) and selected.owner == game.local_player_id:
                    self.queue_match_command(
                        room_id,
                        player_id,
                        {"kind": "queue_military", "owner": game.local_player_id, "building_id": selected.id},
                    )
            elif key == ord("n"):
                selected = game.get_selected()
                if isinstance(selected, Building) and selected.owner == game.local_player_id:
                    self.queue_match_command(
                        room_id,
                        player_id,
                        {"kind": "advance_age", "owner": game.local_player_id, "building_id": selected.id},
                    )
            elif key == ord("t"):
                selected = game.get_selected()
                if isinstance(selected, Building) and selected.owner == game.local_player_id:
                    self.queue_match_command(
                        room_id,
                        player_id,
                        {"kind": "research", "owner": game.local_player_id, "building_id": selected.id},
                    )


def main(stdscr: curses.window) -> None:
    app = SSHOfEmpiresApp(stdscr)
    app.run()


if __name__ == "__main__":
    curses.wrapper(main)
