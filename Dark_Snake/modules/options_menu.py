#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Modul: options_menu.py
# Zweck: Erzeugt ein modernes Optionsmenü, das als ein einziges Menü die gesamte 
#        Spielereinstellung ermöglicht. Es zeigt in Spalte 1 alle klassischen 
#        Einstellungen (Gameplay und Audio), in Spalte 2 das Image Inventory – hier
#        können per Tab (Heads / Bodies) alle Bilder (in kleineren Thumbnails) angezeigt 
#        und den Spielern zugewiesen werden –, und in Spalte 3 eine finale Vorschau 
#        der zugewiesenen Images in Spielgröße (Head und Body) separat für Spieler 1 
#        (oben) und Spieler 2 (unten).
#
# Design:
#   - Dark Art Style: Schwarzer Hintergrund, grüne Rahmen, purple Akzente und orange Highlights.
#   - Das Inventory zeigt Thumbnails in ca. 60×60 Pixel, innerhalb eines fest definierten und
#     scrollbaren Grid-Bereichs (4 pro Zeile).
#   - Ein separates globales Control-Panel (ganz oben) enthält die Buttons Speichern, 
#     Zurück, Set for P1 und Set for P2, die immer anklickbar bleiben.
#   - Die Final Preview (Spalte 3) zeigt in zwei Containern, jeweils für Spieler 1 und Spieler 2,
#     in Spielgröße (GRID_SIZE) die aktuell zugewiesenen Bilder an.
#
# Hinweis:
#   Die UI-Klassen (Button, Slider, Dropdown etc.) befinden sich in ui.py, und alle 
#   Konstanten werden aus config.py geladen.
#

import os
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, DARK_GREY, WHITE, PURPLE, ORANGE, FONT_MEDIUM, FONT_SMALL, GRID_SIZE

# -----------------------------------------------------------------------------
# Bild anhand des Dateinamens laden (aus "assets/graphics")
# -----------------------------------------------------------------------------
def load_image(filename):
    base_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "graphics")
    path = os.path.join(base_dir, filename)
    try:
        image = pygame.image.load(path).convert_alpha()
        return image
    except Exception as e:
        print(f"Bild {filename} konnte nicht geladen werden: {e}")
        return None

# -----------------------------------------------------------------------------
# Zeichnet einen Container im gewünschten Stil.
# -----------------------------------------------------------------------------
def draw_container(surface, rect, title, padding=10):
    pygame.draw.rect(surface, (0, 0, 0), rect, border_radius=8)
    pygame.draw.rect(surface, (0, 255, 0), rect, 2, border_radius=8)
    if title:
        title_surf = FONT_MEDIUM.render(title, True, PURPLE)
        surface.blit(title_surf, (rect.x + padding, rect.y + padding))

# -----------------------------------------------------------------------------
# Basis-Container-Klasse (verschachtelbar)
# -----------------------------------------------------------------------------
class Container:
    def __init__(self, x, y, width, height, title="", padding=10):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.padding = padding
        self.elements = []  # Unterelemente

    def add_element(self, element):
        self.elements.append(element)

    def draw(self, surface):
        draw_container(surface, self.rect, self.title, self.padding)
        for element in self.elements:
            element.draw(surface)

    def handle_event(self, event):
        pos = pygame.mouse.get_pos()
        # Aktualisiere den Hover-Status für alle untergeordneten Elemente, sofern vorhanden
        for element in self.elements:
            if hasattr(element, "check_hover"):
                element.check_hover(pos)
            element.handle_event(event)

# -----------------------------------------------------------------------------
# Hauptklasse OptionsMenu
# -----------------------------------------------------------------------------
class OptionsMenu:
    def __init__(self, game):
        self.game = game

        # --- Globales Control-Panel (ganz oben)
        control_height = 40
        self.control_panel = Container(0, 0, WINDOW_WIDTH, control_height, "", padding=5)
        from modules.ui import Button
        btn_width = (WINDOW_WIDTH - 5 * 10) // 4  # 4 Buttons, 5 Abstände zu je 10 px
        btn_height = control_height - 10
        self.save_btn = Button(10, 5, btn_width, btn_height, "Speichern", color=PURPLE, action=self.save)
        self.back_btn = Button(20 + btn_width, 5, btn_width, btn_height, "Zurück", color=PURPLE, action=self.back)
        self.assign_p1_btn = Button(30 + 2 * btn_width, 5, btn_width, btn_height, "Set for P1", color=ORANGE, action=lambda: self.assign_image(1))
        self.assign_p2_btn = Button(40 + 3 * btn_width, 5, btn_width, btn_height, "Set for P2", color=ORANGE, action=lambda: self.assign_image(2))
        self.control_panel.add_element(self.save_btn)
        self.control_panel.add_element(self.back_btn)
        self.control_panel.add_element(self.assign_p1_btn)
        self.control_panel.add_element(self.assign_p2_btn)

        # --- Weitere Panels beginnen unterhalb des Control-Panels
        top_margin = self.control_panel.rect.bottom + 10
        col1_width = int(WINDOW_WIDTH * 0.35)   # Settings
        col2_width = int(WINDOW_WIDTH * 0.35)   # Image Inventory
        col3_width = WINDOW_WIDTH - col1_width - col2_width - 40  # Final Preview
        panel_height = WINDOW_HEIGHT - top_margin - 10  # Abstand unten
        padding = 10

        # ----- Spalte 1: Settings Panel (Gameplay und Audio)
        self.settings_panel = Container(10, top_margin, col1_width, panel_height, "Settings", padding)
        settings_inner_pad = 8
        gameplay_height = int(panel_height * 0.55)
        audio_height = panel_height - gameplay_height - settings_inner_pad
        self.gameplay_container = Container(self.settings_panel.rect.x + padding,
                                            self.settings_panel.rect.y + padding,
                                            col1_width - 2 * padding, gameplay_height,
                                            "Gameplay", padding)
        self.audio_container = Container(self.settings_panel.rect.x + padding,
                                         self.settings_panel.rect.y + padding + gameplay_height + settings_inner_pad,
                                         col1_width - 2 * padding, audio_height,
                                         "Audio", padding)
        self.settings_panel.add_element(self.gameplay_container)
        self.settings_panel.add_element(self.audio_container)
        from modules.ui import Slider, Dropdown
        self.speed_slider = Slider(self.gameplay_container.rect.x + 10, self.gameplay_container.rect.y + 30,
                                   self.gameplay_container.rect.width - 20, 25, 1, 15, self.game.settings['initial_speed'], "Speed")
        self.difficulty_slider = Slider(self.gameplay_container.rect.x + 10, self.gameplay_container.rect.y + 70,
                                        self.gameplay_container.rect.width - 20, 25, 0.5, 2.0, self.game.settings['difficulty'], "Difficulty")
        self.projectile_slider = Slider(self.gameplay_container.rect.x + 10, self.gameplay_container.rect.y + 110,
                                        self.gameplay_container.rect.width - 20, 25, 0.5, 2.0, self.game.settings.get('projectile_speed_factor', 1.0), "Projectile")
        self.spawnrate_slider = Slider(self.gameplay_container.rect.x + 10, self.gameplay_container.rect.y + 150,
                                       self.gameplay_container.rect.width - 20, 25, 0.001, 0.005, self.game.settings.get('enemy_spawn_rate', 0.002), "Spawnrate")
        self.boss_health_slider = Slider(self.gameplay_container.rect.x + 10, self.gameplay_container.rect.y + 190,
                                         self.gameplay_container.rect.width - 20, 25, 1.0, 3.0, self.game.settings.get('boss_health_multiplier', 1.0), "Boss HP")
        self.gameplay_container.add_element(self.speed_slider)
        self.gameplay_container.add_element(self.difficulty_slider)
        self.gameplay_container.add_element(self.projectile_slider)
        self.gameplay_container.add_element(self.spawnrate_slider)
        self.gameplay_container.add_element(self.boss_health_slider)
        self.music_slider = Slider(self.audio_container.rect.x + 10, self.audio_container.rect.y + 30,
                                   self.audio_container.rect.width - 20, 25, 0, 1, self.game.settings['music_volume'], "Music")
        self.sfx_slider = Slider(self.audio_container.rect.x + 10, self.audio_container.rect.y + 70,
                                 self.audio_container.rect.width - 20, 25, 0, 1, self.game.settings['sfx_volume'], "SFX")
        music_options = self.game.get_music_library() or ["Default"]
        self.music_dropdown = Dropdown(self.audio_container.rect.x + 10, self.audio_container.rect.y + 110,
                                       self.audio_container.rect.width - 20, 35, music_options, music_options[0], FONT_SMALL, self.change_music)
        self.audio_container.add_element(self.music_slider)
        self.audio_container.add_element(self.sfx_slider)
        self.audio_container.add_element(self.music_dropdown)

        # ----- Spalte 2: Image Inventory (Scroll-Container)
        self.inventory_panel = Container(col1_width + 20, top_margin, col2_width, panel_height, "Image Inventory", padding)
        tab_height = 30
        tab_pad = 5
        tab_width = (self.inventory_panel.rect.width - 3 * tab_pad) // 2
        # ACHTUNG: Den exakten Ordnernamen beachten – hier "SnakeHeadsbibliothek" (d.h. "bibliothek" klein)
        self.head_tab_button = Button(self.inventory_panel.rect.x + tab_pad,
                                      self.inventory_panel.rect.y + tab_pad,
                                      tab_width, tab_height, "Heads", color=PURPLE)
        self.body_tab_button = Button(self.inventory_panel.rect.x + 2 * tab_pad + tab_width,
                                      self.inventory_panel.rect.y + tab_pad,
                                      tab_width, tab_height, "Bodies", color=PURPLE)
        self.current_tab = "Heads"
        self.inventory_panel.add_element(self.head_tab_button)
        self.inventory_panel.add_element(self.body_tab_button)
        grid_y = self.inventory_panel.rect.y + tab_height + 2 * tab_pad
        grid_height = int(self.inventory_panel.rect.height * 0.55)
        self.inventory_grid_rect = pygame.Rect(self.inventory_panel.rect.x + tab_pad,
                                               grid_y,
                                               self.inventory_panel.rect.width - 2 * tab_pad,
                                               grid_height)
        self.inventory_scroll_offset = 0
        self.head_options = self.load_options("assets/graphics/SnakeHeadsbibliothek")
        self.body_options = self.load_options("assets/graphics/SnakeBodysBibliothek")
        self.current_selected_img = None

        # ----- Spalte 3: Final Preview
        self.preview_panel = Container(col1_width + col2_width + 30, top_margin, col3_width, panel_height, "Final Preview", padding)
        preview_pad = 8
        half_preview = (self.preview_panel.rect.height - 3 * preview_pad) // 2
        self.final_preview_p1 = Container(self.preview_panel.rect.x + preview_pad,
                                          self.preview_panel.rect.y + preview_pad,
                                          self.preview_panel.rect.width - 2 * preview_pad,
                                          half_preview,
                                          "Player 1 Final", preview_pad)
        self.final_preview_p2 = Container(self.preview_panel.rect.x + preview_pad,
                                          self.preview_panel.rect.y + preview_pad + half_preview + preview_pad,
                                          self.preview_panel.rect.width - 2 * preview_pad,
                                          half_preview,
                                          "Player 2 Final", preview_pad)
        self.preview_panel.add_element(self.final_preview_p1)
        self.preview_panel.add_element(self.final_preview_p2)

        # ----- Spalte 4: (Globale Buttons werden im Control-Panel geführt)
        self.selected_head_p1 = self.game.settings.get('custom_head_p1', None)
        self.selected_body_p1 = self.game.settings.get('custom_body_p1', None)
        self.selected_head_p2 = self.game.settings.get('custom_head_p2', None)
        self.selected_body_p2 = self.game.settings.get('custom_body_p2', None)

    # Lädt Bildoptionen und skaliert Thumbnails auf 60×60.
    def load_options(self, folder_path):
        base_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "graphics")
        rel_folder = folder_path.split("assets/graphics/")[-1]
        full_folder_path = os.path.join(base_dir, rel_folder)
        options = []
        if os.path.exists(full_folder_path):
            for fname in os.listdir(full_folder_path):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    full_path = os.path.join(full_folder_path, fname)
                    try:
                        img = pygame.image.load(full_path).convert_alpha()
                        thumb = pygame.transform.scale(img, (60, 60))
                        options.append((fname, thumb, img))
                    except Exception as e:
                        print(f"Fehler beim Laden von {full_path}: {e}")
        else:
            print(f"Ordner {full_folder_path} existiert nicht.")
        return options

    def change_music(self, selected_option):
        self.game.settings['bg_music_volume'] = self.music_slider.current_val
        from modules.audio import play_background_music
        play_background_music(selected_option, self.game.settings['bg_music_volume'])
        print(f"Hintergrundmusik geändert: {selected_option}")

    def save(self):
        self.game.settings['initial_speed'] = self.speed_slider.current_val
        self.game.settings['difficulty'] = self.difficulty_slider.current_val
        self.game.settings['projectile_speed_factor'] = self.projectile_slider.current_val
        self.game.settings['enemy_spawn_rate'] = self.spawnrate_slider.current_val
        self.game.settings['boss_health_multiplier'] = self.boss_health_slider.current_val
        self.game.settings['music_volume'] = self.music_slider.current_val
        self.game.settings['sfx_volume'] = self.sfx_slider.current_val
        self.game.settings['custom_head_p1'] = self.selected_head_p1
        self.game.settings['custom_body_p1'] = self.selected_body_p1
        self.game.settings['custom_head_p2'] = self.selected_head_p2
        self.game.settings['custom_body_p2'] = self.selected_body_p2

        with open("settings.txt", "w") as f:
            for key, value in self.game.settings.items():
                f.write(f"{key}={value}\n")
        print("Einstellungen wurden gespeichert! Snake Profil gespeichert.")

    def back(self):
        self.game.set_state(self.game.intro_state())

    def handle_event(self, event):
        pos = pygame.mouse.get_pos()
        # Zuerst: Wenn der Mauszeiger im Control-Panel liegt, nur dieses behandeln.
        if self.control_panel.rect.collidepoint(pos):
            self.control_panel.handle_event(event)
            return
        self.settings_panel.handle_event(event)
        self.inventory_panel.handle_event(event)
        self.preview_panel.handle_event(event)
        if event.type == pygame.MOUSEWHEEL:
            if self.inventory_grid_rect.collidepoint(pos):
                self.inventory_scroll_offset += event.y * 20
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.head_tab_button.rect.collidepoint(pos):
                self.current_tab = "Heads"
                print("Tab Heads ausgewählt.")
            elif self.body_tab_button.rect.collidepoint(pos):
                self.current_tab = "Bodies"
                print("Tab Bodies ausgewählt.")
            else:
                self.check_inventory_click()

    def check_inventory_click(self):
        pos = pygame.mouse.get_pos()
        spacing = 10
        cols = 4  # 4 Thumbnails pro Zeile
        avail_width = self.inventory_grid_rect.width
        thumb_size = (avail_width - (cols + 1) * spacing) // cols
        options = self.head_options if self.current_tab == "Heads" else self.body_options
        for i, (fname, thumb, original) in enumerate(options):
            row = i // cols
            col = i % cols
            x = self.inventory_grid_rect.x + spacing + col * (thumb_size + spacing)
            y = self.inventory_grid_rect.y + spacing + row * (thumb_size + spacing) + self.inventory_scroll_offset
            thumb_rect = pygame.Rect(x, y, thumb_size, thumb_size)
            if thumb_rect.collidepoint(pos):
                self.current_selected_img = (fname, thumb, original)
                print(f"Inventar: {fname} ausgewählt im Tab {self.current_tab}.")
                break

    def assign_image(self, player):
        if not self.current_selected_img:
            print("Kein Bild ausgewählt.")
            return
        fname, _, _ = self.current_selected_img
        if self.current_tab == "Heads":
            if player == 1:
                self.selected_head_p1 = fname
                print(f"Player 1 Head zugewiesen: {fname}")
            else:
                self.selected_head_p2 = fname
                print(f"Player 2 Head zugewiesen: {fname}")
        elif self.current_tab == "Bodies":
            if player == 1:
                self.selected_body_p1 = fname
                print(f"Player 1 Body zugewiesen: {fname}")
            else:
                self.selected_body_p2 = fname
                print(f"Player 2 Body zugewiesen: {fname}")

    def draw(self, surface):
        self.settings_panel.draw(surface)
        self.inventory_panel.draw(surface)
        self.preview_panel.draw(surface)
        self.draw_inventory_grid(surface)
        self.draw_final_preview(surface)
        # Schließlich das Control-Panel (sorgt dafür, dass die Buttons immer oben sind)
        self.control_panel.draw(surface)

    def draw_inventory_grid(self, surface):
        spacing = 10
        cols = 4  # 4 Thumbnails pro Zeile
        avail_width = self.inventory_grid_rect.width
        thumb_size = (avail_width - (cols + 1) * spacing) // cols
        pygame.draw.rect(surface, DARK_GREY, self.inventory_grid_rect)
        options = self.head_options if self.current_tab == "Heads" else self.body_options
        for i, (fname, thumb, original) in enumerate(options):
            row = i // cols
            col = i % cols
            x = self.inventory_grid_rect.x + spacing + col * (thumb_size + spacing)
            y = self.inventory_grid_rect.y + spacing + row * (thumb_size + spacing) + self.inventory_scroll_offset
            thumb_rect = pygame.Rect(x, y, thumb_size, thumb_size)
            scaled_thumb = pygame.transform.scale(thumb, (thumb_size, thumb_size))
            surface.blit(scaled_thumb, thumb_rect)
            if self.current_selected_img and self.current_selected_img[0] == fname:
                color = (0, 255, 0) if self.current_tab == "Heads" else (255, 255, 0)
                pygame.draw.rect(surface, color, thumb_rect, 3)
            if thumb_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surface, WHITE, thumb_rect, 1)

    def draw_final_preview(self, surface):
        preview_padding = 10
        inner_rect = self.preview_panel.rect.inflate(-2 * preview_padding, -2 * preview_padding)
        half_height = (inner_rect.height - preview_padding) // 2
        p1_area = pygame.Rect(inner_rect.x, inner_rect.y, inner_rect.width, half_height)
        p2_area = pygame.Rect(inner_rect.x, inner_rect.y + half_height + preview_padding, inner_rect.width, half_height)

        def draw_player_preview(head_fname, body_fname, area):
            images = []
            if head_fname:
                img = load_image(head_fname)
                if img:
                    images.append(img)
            if body_fname:
                img = load_image(body_fname)
                if img:
                    images.append(img)
            if not images:
                txt = FONT_SMALL.render("Kein Bild", True, WHITE)
                surface.blit(txt, txt.get_rect(center=area.center))
                return
            total_width = len(images) * GRID_SIZE + (len(images) - 1) * 5
            start_x = area.x + (area.width - total_width) // 2
            y = area.y + (area.height - GRID_SIZE) // 2
            for img in images:
                scaled = pygame.transform.scale(img, (GRID_SIZE, GRID_SIZE))
                surface.blit(scaled, (start_x, y))
                start_x += GRID_SIZE + 5

        draw_player_preview(self.selected_head_p1, self.selected_body_p1, p1_area)
        draw_player_preview(self.selected_head_p2, self.selected_body_p2, p2_area)

# -----------------------------------------------------------------------------
# Erweiterte OptionsMenu-Klasse (für eventuelle weitere Anpassungen)
# -----------------------------------------------------------------------------
class ExtendedOptionsMenu(OptionsMenu):
    def __init__(self, game):
        super().__init__(game)
        self.display_panel = self.inventory_panel

    def handle_event(self, event):
        OptionsMenu.handle_event(self, event)

    def draw(self, surface):
        OptionsMenu.draw(self, surface)
