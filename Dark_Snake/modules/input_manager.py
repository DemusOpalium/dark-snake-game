"""Unified keyboard and joystick input with persistent bindings."""

import json
import os
import pygame

from modules.resources import user_data_path


DEFAULT_BINDINGS = {
    "p1_up": {"key": pygame.K_w, "button": None},
    "p1_down": {"key": pygame.K_s, "button": None},
    "p1_left": {"key": pygame.K_a, "button": None},
    "p1_right": {"key": pygame.K_d, "button": None},
    "p1_fire": {"key": pygame.K_SPACE, "button": 0},
    "p2_up": {"key": pygame.K_UP, "button": None},
    "p2_down": {"key": pygame.K_DOWN, "button": None},
    "p2_left": {"key": pygame.K_LEFT, "button": None},
    "p2_right": {"key": pygame.K_RIGHT, "button": None},
    "p2_fire": {"key": pygame.K_RETURN, "button": 0},
    "menu_accept": {"key": pygame.K_RETURN, "button": 0},
}


class InputManager:
    def __init__(self, config_path=None, initialize_joysticks=True):
        self.config_path = config_path or user_data_path("controls.json")
        self.bindings = {name: dict(value) for name, value in DEFAULT_BINDINGS.items()}
        self.joysticks = []
        self.load()
        if initialize_joysticks:
            self.refresh_joysticks()

    def refresh_joysticks(self):
        self.joysticks = []
        try:
            if not pygame.joystick.get_init():
                pygame.joystick.init()
            for index in range(pygame.joystick.get_count()):
                joystick = pygame.joystick.Joystick(index)
                joystick.init()
                self.joysticks.append(joystick)
        except pygame.error as exc:
            print(f"[WARN] Gamepads nicht verfügbar: {exc}")

    def load(self):
        try:
            with open(self.config_path, encoding="utf-8") as file:
                saved = json.load(file)
            for action, binding in saved.items():
                if action in self.bindings and isinstance(binding, dict):
                    self.bindings[action].update(binding)
        except (OSError, ValueError, TypeError):
            pass

    def save(self):
        directory = os.path.dirname(self.config_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(self.bindings, file, ensure_ascii=False, indent=2)

    def reset_defaults(self):
        self.bindings = {name: dict(value) for name, value in DEFAULT_BINDINGS.items()}
        self.save()

    def bind_event(self, action, event):
        if event.type == pygame.KEYDOWN:
            self.bindings[action]["key"] = event.key
        elif event.type == pygame.JOYBUTTONDOWN:
            self.bindings[action]["button"] = event.button
        else:
            return False
        self.save()
        return True

    def actions_for(self, event):
        actions = set()
        for action, binding in self.bindings.items():
            if event.type == pygame.KEYDOWN and event.key == binding.get("key"):
                actions.add(action)
            elif event.type == pygame.JOYBUTTONDOWN and event.button == binding.get("button"):
                player = "p1" if getattr(event, "joy", 0) == 0 else "p2"
                if action.startswith(player) or action == "menu_accept":
                    actions.add(action)

        # Documented alternate fire keys remain available when users remap the primary.
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                actions.add("p1_fire")
            if event.key in (pygame.K_RETURN, pygame.K_PLUS, pygame.K_KP_PLUS):
                actions.add("p2_fire")

        if event.type == pygame.JOYHATMOTION:
            player = "p1" if getattr(event, "joy", 0) == 0 else "p2"
            x, y = event.value
            if x: actions.add(f"{player}_{'right' if x > 0 else 'left'}")
            if y: actions.add(f"{player}_{'up' if y > 0 else 'down'}")
        elif event.type == pygame.JOYAXISMOTION and abs(event.value) >= 0.6:
            player = "p1" if getattr(event, "joy", 0) == 0 else "p2"
            if event.axis == 0: actions.add(f"{player}_{'right' if event.value > 0 else 'left'}")
            elif event.axis == 1: actions.add(f"{player}_{'down' if event.value > 0 else 'up'}")
        return actions

    def label(self, action):
        binding = self.bindings[action]
        key = pygame.key.name(binding["key"]).upper() if binding.get("key") is not None else "–"
        button = binding.get("button")
        return f"{key} / Pad {button}" if button is not None else key
