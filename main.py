#!/usr/bin/env python
# coding: utf-8

import pygame
import random
import sys
import math
import asyncio

async def run_game():
    # --- Engine Setup ---
    pygame.init()
    pygame.mixer.init()

    # Clean, native HD resolution that scales perfectly in Pygbag
    WINDOW_W, WINDOW_H = 1024, 640
    global WIDTH, HEIGHT, screen
    WIDTH, HEIGHT = WINDOW_W, WINDOW_H
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("CONTINUUM ARENA")
    clock = pygame.time.Clock()

    is_fullscreen = False

    # --- Cyberpunk Palette ---
    BG_DARK = (5, 5, 15)
    PANEL_BG = (12, 12, 32)
    NEON_PURPLE = (180, 0, 255)
    NEON_CYAN = (0, 255, 255)
    NEON_AMBER = (255, 170, 0)
    NEON_GREEN = (0, 255, 102)
    NEON_RED = (255, 50, 50)
    WHITE = (240, 240, 240)
    GRAY = (80, 80, 105)
    GOLD = (255, 215, 0)
    BLOCK_COLOR = (40, 50, 75)

    def play_sound(freq, duration, wave_type="square"):
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = bytearray()
        for i in range(n_samples):
            t = float(i) / sample_rate
            if wave_type == "noise":
                val = random.randint(-127, 127)
            else:
                val = 127 if math.sin(2.0 * math.pi * freq * t) > 0 else -127
            buf.append(int(val + 128))
        try:
            sound = pygame.mixer.Sound(buffer=buf)
            sound.set_volume(0.02)
            sound.play()
        except: pass

    # --- Fixed Dynamic Font Scaling Engine ---
    def get_fonts():
        scale = max(0.7, min(1.5, HEIGHT / 640.0))
        return {
            "main": pygame.font.SysFont("OCR A Extended", int(14 * scale)),
            "small": pygame.font.SysFont("Verdana", int(10 * scale), bold=True),
            "title": pygame.font.SysFont("OCR A Extended", int(18 * scale), bold=True)
        }
    fonts = get_fonts()

    def render_wrapped_text(surface, text, font, color, rect, line_spacing=4):
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] < rect.width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line: lines.append(current_line)

        y_offset = rect.y
        for line in lines:
            text_surf = font.render(line, True, color)
            surface.blit(text_surf, (rect.x, y_offset))
            y_offset += font.get_linesize() + line_spacing

    # --- Projectile Vector Class ---
    class Bullet:
        def __init__(self, x, y, angle, color, owner_name, is_plasma=False):
            self.pos = pygame.Vector2(x, y)
            self.angle = angle 
            self.speed = 14.0 if is_plasma else 10.0
            self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.speed
            self.color = color
            self.owner_name = owner_name
            self.active = True
            self.is_plasma = is_plasma

        def update(self, t_scale, min_x):
            self.pos += self.velocity * t_scale
            if self.pos.x < min_x or self.pos.x > WIDTH or self.pos.y < 120 or self.pos.y > HEIGHT:
                self.active = False

        def draw(self, surface):
            w = 18 if self.is_plasma else 12
            h = 6 if self.is_plasma else 4
            laser_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            laser_surf.fill(self.color)
            rot_laser = pygame.transform.rotate(laser_surf, -math.degrees(self.angle))
            surface.blit(rot_laser, (self.pos.x - rot_laser.get_width()//2, self.pos.y - rot_laser.get_height()//2))

    # --- Random Obstacle Block Class ---
    class ObstacleBlock:
        def __init__(self, start_x):
            self.rect = pygame.Rect(
                random.randint(int(start_x + 60), int(WIDTH - 100)),
                random.randint(180, int(HEIGHT - 120)),
                random.randint(35, 55),
                random.randint(35, 55)
            )
            self.pulse = random.random() * 10

        def draw(self, surface):
            self.pulse += 0.05
            glow = int(abs(math.sin(self.pulse)) * 25)
            pygame.draw.rect(surface, (BLOCK_COLOR[0]+glow, BLOCK_COLOR[1], BLOCK_COLOR[2]), self.rect, border_radius=4)
            pygame.draw.rect(surface, NEON_CYAN, self.rect, 1, border_radius=4)

    # --- Golden Time Orb Class ---
    class TimeOrb:
        def __init__(self, start_x):
            self.pos = pygame.Vector2(
                random.randint(int(start_x + 40), int(WIDTH - 60)),
                random.randint(180, int(HEIGHT - 90))
            )
            self.pulse = random.random() * 5
            self.active = True

        def update(self): self.pulse += 0.1

        def draw(self, surface):
            if not self.active: return
            radius = int(7 + math.sin(self.pulse) * 2)
            pygame.draw.circle(surface, GOLD, (int(self.pos.x), int(self.pos.y)), radius)
            pygame.draw.circle(surface, NEON_AMBER, (int(self.pos.x), int(self.pos.y)), radius + 3, 2)

    # --- Entity Fighter Class ---
    class Fighter:
        def __init__(self, x_ratio, y_ratio, color, is_ai=False, name="VEX-9"):
            self.ratio = pygame.Vector2(x_ratio, y_ratio)
            self.color = color
            self.is_ai = is_ai
            self.name = name
            self.max_hp = 1200
            self.hp = self.max_hp
            self.atk_mult = 1.0
            self.weapon_type = "STANDARD LASER"
            self.has_plasma = False
            self.is_alive = True
            self.shoot_cooldown = 0
            self.anim_tick = 0
            self.is_moving = False
            self.facing_angle = 0.0

        def get_actual_pos(self, min_x):
            playable_w = WIDTH - min_x
            return pygame.Vector2(min_x + (self.ratio.x * playable_w), self.ratio.y * HEIGHT)

        def get_hitbox(self, min_x):
            p = self.get_actual_pos(min_x)
            return pygame.Rect(p.x - 15, p.y - 50, 30, 60)

        def handle_input(self, keys, stats_speed, bullets, blocks, min_x, is_p2=False):
            if not self.is_alive: return
            speed = (3.0 + (stats_speed * 0.35))
            old_ratio = pygame.Vector2(self.ratio)
            self.is_moving = False

            if not is_p2:
                if keys[pygame.K_w]: self.ratio.y -= speed / HEIGHT; self.is_moving = True
                if keys[pygame.K_s]: self.ratio.y += speed / HEIGHT; self.is_moving = True
                if keys[pygame.K_a]: self.ratio.x -= speed / (WIDTH - min_x); self.is_moving = True; self.facing_angle = math.pi
                if keys[pygame.K_d]: self.ratio.x += speed / (WIDTH - min_x); self.is_moving = True; self.facing_angle = 0.0
            else:
                if keys[pygame.K_UP]: self.ratio.y -= speed / HEIGHT; self.is_moving = True
                if keys[pygame.K_DOWN]: self.ratio.y += speed / HEIGHT; self.is_moving = True
                if keys[pygame.K_LEFT]: self.ratio.x -= speed / (WIDTH - min_x); self.is_moving = True; self.facing_angle = math.pi
                if keys[pygame.K_RIGHT]: self.ratio.x += speed / (WIDTH - min_x); self.is_moving = True; self.facing_angle = 0.0

            my_box = self.get_hitbox(min_x)
            for b in blocks:
                if my_box.colliderect(b.rect):
                    self.ratio = old_ratio
                    break

            if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
            else:
                trigger = keys[pygame.K_SPACE] if not is_p2 else keys[pygame.K_RCTRL]
                if trigger:
                    p = self.get_actual_pos(min_x)
                    bullets.append(Bullet(p.x, p.y - 18, self.facing_angle, self.color, self.name, self.has_plasma))
                    self.shoot_cooldown = 10 if self.has_plasma else 16
                    play_sound(680 if self.has_plasma else 550, 0.06)

        def execute_ai_logic(self, targets, bullets, blocks, min_x, t_scale, sudden_death=False):
            if not self.is_alive or not self.is_ai or t_scale == 0: return
            alive_targets = [t for t in targets if t.is_alive]
            if not alive_targets: return

            p_self = self.get_actual_pos(min_x)
            target_obj = min(alive_targets, key=lambda t: p_self.distance_to(t.get_actual_pos(min_x)))
            p_target = target_obj.get_actual_pos(min_x)

            self.anim_tick += 0.1
            self.is_moving = True

            delta = (p_target - pygame.Vector2(0, 18)) - p_self
            self.facing_angle = math.atan2(delta.y, delta.x)

            dist = p_self.distance_to(p_target)
            old_ratio = pygame.Vector2(self.ratio)

            ai_speed = 3.2 if sudden_death else 2.1

            if dist > 130:
                new_pos = p_self + delta.normalize() * (ai_speed * t_scale)
                self.ratio.x = (new_pos.x - min_x) / (WIDTH - min_x)
                self.ratio.y = new_pos.y / HEIGHT
            elif dist < 90:
                new_pos = p_self - delta.normalize() * (1.6 * t_scale)
                self.ratio.x = (new_pos.x - min_x) / (WIDTH - min_x)
                self.ratio.y = new_pos.y / HEIGHT

            my_box = self.get_hitbox(min_x)
            for b in blocks:
                if my_box.colliderect(b.rect):
                    self.ratio = old_ratio
                    break

            if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
            else:
                fire_chance = 0.07 if (sudden_death or dist < 220) else 0.025
                if random.random() < fire_chance:
                    bullets.append(Bullet(p_self.x, p_self.y - 18, self.facing_angle, self.color, self.name, sudden_death))
                    self.shoot_cooldown = random.randint(12, 26) if sudden_death else random.randint(25, 45)
                    play_sound(410 if not sudden_death else 490, 0.07)

        def restrict_boundaries(self):
            self.ratio.x = max(0.05, min(0.95, self.ratio.x))
            self.ratio.y = max(160 / HEIGHT, min((HEIGHT - 60) / HEIGHT, self.ratio.y))

        def draw(self, surface, min_x):
            if not self.is_alive: return
            p = self.get_actual_pos(min_x)
            c = self.color
            if self.is_moving: self.anim_tick += 0.15

            bounce = math.sin(self.anim_tick) * 2
            h_scale = 10

            pygame.draw.circle(surface, c, (int(p.x), int(p.y - (h_scale * 3.5) + bounce)), h_scale)
            pygame.draw.rect(surface, c, (p.x - h_scale, p.y - (h_scale * 2.7) + bounce, h_scale * 2, h_scale * 2.5), border_radius=4)

            w_len = h_scale * 2.4
            pygame.draw.line(surface, GOLD if not self.has_plasma else NEON_GREEN, (p.x, p.y - h_scale + bounce), (p.x + math.cos(self.facing_angle)*w_len, p.y - h_scale + bounce + math.sin(self.facing_angle)*w_len), 3)

            leg = math.cos(self.anim_tick) * 4 if self.is_moving else 0
            pygame.draw.line(surface, c, (p.x - 3, p.y + bounce), (p.x - h_scale - leg, p.y + (h_scale * 1.8)), 2)
            pygame.draw.line(surface, c, (p.x + 3, p.y + bounce), (p.x + h_scale + leg, p.y + (h_scale * 1.8)), 2)

            lbl = fonts["small"].render(self.name, True, WHITE)
            surface.blit(lbl, (p.x - lbl.get_width()//2, p.y - (h_scale * 5.5) + bounce))

    # --- Setup Core Structures ---
    p1_name = "HERO-X"
    name_active = False
    p1_color = NEON_PURPLE
    color_presets = [NEON_PURPLE, NEON_GREEN, NEON_AMBER, WHITE, (255, 0, 120)]

    current_tab = "CREATOR"
    game_mode = "1_BOT"
    arena_unlocked = False
    winning_character = ""

    stats = {"STRENGTH": 5, "SPEED": 5, "DEFENSE": 5}
    points = 10
    time_scale = 1.0
    match_timer = 60.0

    missions = {
        "orbs_collected": {"current": 0, "target": 3, "desc": "Collect Golden Time Cores", "done": False},
        "laser_hits": {"current": 0, "target": 8, "desc": "Land Tactical Laser Shots", "done": False},
        "damage_inflicted": {"current": 0, "target": 1200, "desc": "Deal Total Matrix Damage", "done": False},
        "rewinds_used": {"current": 0, "target": 1, "desc": "Activate Temporal Chrono-Rewind", "done": False},
        "survive_sudden_death": {"current": 0, "target": 1, "desc": "Trigger & Enter Sudden Death", "done": False}
    }

    box_rewards = [
        {"name": "PLASMA CANNON", "perk": "plasma"},
        {"name": "SHIELD PACK (+400 HP)", "perk": "hp"},
        {"name": "DAMAGE BOOSTER (2X)", "perk": "dmg"}
    ]
    box_state = "IDLE"
    roll_timer, roll_speed, current_roll_idx = 0, 0, 0
    box_unlocked_reward = None

    history, bullets, orbs, blocks = [], [], [], []
    orb_spawn_timer = 0
    p1 = Fighter(0.2, 0.55, p1_color, name=p1_name)
    enemies = []
    rewind_pressed_last_frame = False

    running = True
    while running:
        m_pos = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()
        screen.fill(BG_DARK)

        # Dynamic Grid and Panel Calculations
        left_panel_w = int(WIDTH * 0.28)
        sub_sidebar_w = int(WIDTH * 0.16)
        center_view_x = left_panel_w + sub_sidebar_w
        header_h = 60

        # Draw Global Header Elements
        pygame.draw.rect(screen, PANEL_BG, (0, 0, WIDTH, header_h))
        pygame.draw.line(screen, NEON_PURPLE, (0, header_h), (WIDTH, header_h), 2)
        screen.blit(fonts["title"].render("CONTINUUM-ARENA // ONSLAUGHT SYSTEM", True, WHITE), (15, 18))

        fs_btn_rect = pygame.Rect(WIDTH - 190, 12, 175, 34)
        fs_btn_color = NEON_GREEN if is_fullscreen else NEON_CYAN
        pygame.draw.rect(screen, (20, 30, 55), fs_btn_rect, border_radius=4)
        pygame.draw.rect(screen, fs_btn_color, fs_btn_rect, 1, border_radius=4)
        fs_txt = "🖥️ WINDOW MODE" if is_fullscreen else "🖥️ FULLSCREEN MODE"
        screen.blit(fonts["small"].render(fs_txt, True, fs_btn_color), (fs_btn_rect.x + 12, fs_btn_rect.y + 9))

        is_sudden_death = (current_tab == "BATTLE_FIELD" and match_timer <= 20.0 and match_timer > 0)
        if is_sudden_death and not missions["survive_sudden_death"]["done"]:
            missions["survive_sudden_death"]["current"] = 1
            missions["survive_sudden_death"]["done"] = True
            play_sound(1100, 0.2)

        # --- Progress Tracker Panel ---
        pygame.draw.rect(screen, (10, 10, 28), (0, header_h, left_panel_w, HEIGHT - header_h))
        pygame.draw.line(screen, NEON_CYAN, (left_panel_w, header_h), (left_panel_w, HEIGHT), 2)

        y_guide = header_h + 15
        screen.blit(fonts["main"].render("MISSION LOG MATRIX", True, GOLD), (15, y_guide))
        y_guide += 25

        # Responsive calculation for mission list items to prevent crushing
        box_h = int((HEIGHT - y_guide - 110) / 5)
        box_h = max(38, min(52, box_h))

        for m_key, m_data in missions.items():
            box_r = pygame.Rect(10, y_guide, left_panel_w - 20, box_h)
            pygame.draw.rect(screen, (16, 16, 38) if not m_data["done"] else (8, 38, 20), box_r, border_radius=4)
            pygame.draw.rect(screen, NEON_CYAN if not m_data["done"] else NEON_GREEN, box_r, 1, border_radius=4)

            txt_m = f"{m_data['desc']}"
            prog_m = f"[{m_data['current']}/{m_data['target']}]" if not m_data["done"] else "[COMPLETE]"

            screen.blit(fonts["small"].render(txt_m, True, WHITE), (18, y_guide + int(box_h*0.12)))
            screen.blit(fonts["small"].render(prog_m, True, NEON_AMBER if not m_data["done"] else NEON_GREEN), (18, y_guide + int(box_h*0.52)))
            y_guide += box_h + 6

        y_guide += 5
        pygame.draw.line(screen, GRAY, (10, y_guide), (left_panel_w - 10, y_guide))
        y_guide += 10

        screen.blit(fonts["main"].render("MODIFIER ATTRIBUTES:", True, NEON_RED), (15, y_guide))
        y_guide += 20
        advice_text = [
            "- Boss units speed up in proximity",
            "- Under 20s environment goes Red",
            "- Chrono-rewind restores variables"
        ]
        for line in advice_text:
            screen.blit(fonts["small"].render(line, True, WHITE), (15, y_guide))
            y_guide += 18

        # --- Sidebar Nav Router Panel ---
        pygame.draw.rect(screen, (16, 16, 36), (left_panel_w, header_h, sub_sidebar_w, HEIGHT - header_h))
        pygame.draw.line(screen, NEON_CYAN, (center_view_x, header_h), (center_view_x, HEIGHT), 1)

        tabs_map = ["CREATOR", "VISUAL TUTORIAL", "MYSTERY BOX"] if not arena_unlocked else ["CREATOR", "ARENA LOBBY", "VISUAL TUTORIAL", "MYSTERY BOX"]
        if current_tab == "BATTLE_FIELD": tabs_map = ["ARENA LOBBY"] + tabs_map

        nav_rects = {}
        for idx, tab_name in enumerate(tabs_map):
            r_tab = pygame.Rect(left_panel_w + 8, header_h + 15 + (idx * 48), sub_sidebar_w - 16, 36)
            nav_rects[tab_name] = r_tab
            is_active_tab = (current_tab == tab_name or (current_tab == "BATTLE_FIELD" and tab_name == "ARENA LOBBY"))
            pygame.draw.rect(screen, (35, 25, 55) if is_active_tab else (22, 22, 45), r_tab, border_radius=4)
            screen.blit(fonts["small"].render(tab_name, True, WHITE if is_active_tab else GRAY), (r_tab.x + 8, r_tab.y + 11))

        btn_rev_rect = pygame.Rect(left_panel_w + 8, HEIGHT - 140, sub_sidebar_w - 16, 32)
        btn_frz_rect = pygame.Rect(left_panel_w + 8, HEIGHT - 102, sub_sidebar_w - 16, 32)
        btn_slw_rect = pygame.Rect(left_panel_w + 8, HEIGHT - 64, sub_sidebar_w - 16, 32)

        if current_tab == "BATTLE_FIELD":
            for r, col, txt in [(btn_rev_rect, NEON_PURPLE, "HOLD R / REV"), (btn_frz_rect, NEON_CYAN, "FREEZE" if time_scale > 0 else "RESUME"), (btn_slw_rect, NEON_AMBER, "SLOWMO" if time_scale==1.0 else "NORMAL")]:
                pygame.draw.rect(screen, (12, 12, 30), r, border_radius=4)
                pygame.draw.rect(screen, col, r, 1, border_radius=4)
                screen.blit(fonts["small"].render(txt, True, WHITE), (r.centerx - fonts["small"].size(txt)[0]//2, r.y + 9))

        # --- Global Clock Tick Engine Processing ---
        is_match_active = (current_tab == "BATTLE_FIELD" and time_scale > 0 and match_timer > 0 and p1.is_alive and any(e.is_alive for e in enemies))
        if is_match_active:
            match_timer -= (1.0 / 60.0) * time_scale

        if box_state == "ROLLING":
            roll_timer += 1
            if roll_timer % roll_speed == 0:
                current_roll_idx = (current_roll_idx + 1) % len(box_rewards)
                play_sound(350 + (current_roll_idx * 80), 0.04)
                if roll_speed < 18: roll_speed += 2
                else:
                    box_state = "CLAIMED"
                    box_unlocked_reward = box_rewards[current_roll_idx]
                    play_sound(880, 0.25)
                    if box_unlocked_reward["perk"] == "plasma": p1.has_plasma = True; p1.weapon_type = "PLASMA RIFLE"
                    elif box_unlocked_reward["perk"] == "hp": p1.max_hp += 400; p1.hp += 400
                    elif box_unlocked_reward["perk"] == "dmg": p1.atk_mult = 2.0

        # --- Event Matrix Loop ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

            if event.type == pygame.VIDEORESIZE and not is_fullscreen:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                fonts = get_fonts()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        WIDTH, HEIGHT = screen.get_size()
                    else:
                        WIDTH, HEIGHT = WINDOW_W, WINDOW_H
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    fonts = get_fonts()
                    play_sound(520, 0.15)

                if name_active:
                    if event.key == pygame.K_BACKSPACE: p1_name = p1_name[:-1]
                    elif event.key == pygame.K_RETURN: name_active = False
                    elif len(p1_name) < 14: p1_name += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                name_input_rect = pygame.Rect(center_view_x + 200, header_h + 75, 180, 32)
                btn_enter_arena = pygame.Rect(center_view_x + 30, HEIGHT - 80, 240, 42)
                btn_box_rect = pygame.Rect(center_view_x + 50, header_h + 80, 130, 130)

                if fs_btn_rect.collidepoint(m_pos):
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        WIDTH, HEIGHT = screen.get_size()
                    else:
                        WIDTH, HEIGHT = WINDOW_W, WINDOW_H
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    fonts = get_fonts()
                    play_sound(520, 0.15)

                name_active = name_input_rect.collidepoint(m_pos) if current_tab == "CREATOR" else False

                for tab_name, r_btn in nav_rects.items():
                    if r_btn.collidepoint(m_pos): current_tab = tab_name; play_sound(440, 0.04)

                if current_tab == "BATTLE_FIELD":
                    if btn_frz_rect.collidepoint(m_pos): time_scale = 0.0 if time_scale > 0 else 1.0; play_sound(490, 0.05)
                    if btn_slw_rect.collidepoint(m_pos): time_scale = 0.2 if time_scale == 1.0 else 1.0; play_sound(310, 0.05)

                if current_tab == "CREATOR":
                    if btn_enter_arena.collidepoint(m_pos):
                        arena_unlocked = True; current_tab = "ARENA LOBBY"; play_sound(680, 0.1)

                    for idx, color in enumerate(color_presets):
                        if pygame.Rect(center_view_x + 200 + (idx*38), header_h + 130, 28, 28).collidepoint(m_pos):
                            p1_color = color; play_sound(500, 0.04)

                    plus_rects = {"STRENGTH": pygame.Rect(center_view_x + 310, header_h + 245, 30, 30), "SPEED": pygame.Rect(center_view_x + 310, header_h + 295, 30, 30), "DEFENSE": pygame.Rect(center_view_x + 310, header_h + 345, 30, 30)}
                    minus_rects = {"STRENGTH": pygame.Rect(center_view_x + 200, header_h + 245, 30, 30), "SPEED": pygame.Rect(center_view_x + 200, header_h + 295, 30, 30), "DEFENSE": pygame.Rect(center_view_x + 200, header_h + 345, 30, 30)}
                    for s, r in plus_rects.items():
                        if r.collidepoint(m_pos) and points > 0: stats[s] += 1; points -= 1; play_sound(620, 0.03)
                    for s, r in minus_rects.items():
                        if r.collidepoint(m_pos) and stats[s] > 1: stats[s] -= 1; points += 1; play_sound(340, 0.03)

                elif current_tab == "ARENA LOBBY":
                    for idx in range(4):
                        if pygame.Rect(center_view_x + 30, header_h + 75 + (idx * 75), 420, 58).collidepoint(m_pos):
                            game_mode = ["1_BOT", "LOCAL_2P", "2_BOTS", "3_BOTS"][idx]
                            play_sound(800, 0.08)

                            winning_character = ""
                            p1 = Fighter(0.20, 0.55, p1_color, name=p1_name)
                            if p1.has_plasma: p1.weapon_type = "PLASMA RIFLE"

                            for m in missions.values(): m["current"] = 0; m["done"] = False

                            enemies.clear(); bullets.clear(); history.clear(); orbs.clear(); blocks.clear()
                            for _ in range(random.randint(2, 4)): blocks.append(ObstacleBlock(center_view_x))
                            match_timer = 60.0; time_scale = 1.0

                            if game_mode == "1_BOT":
                                enemies.append(Fighter(0.75, 0.55, NEON_CYAN, is_ai=True, name="KRONIS-BOT"))
                            elif game_mode == "LOCAL_2P":
                                enemies.append(Fighter(0.75, 0.55, NEON_RED, is_ai=False, name="PLAYER-2"))
                            elif game_mode == "2_BOTS":
                                enemies.append(Fighter(0.75, 0.35, NEON_CYAN, is_ai=True, name="KRONIS-BOT"))
                                enemies.append(Fighter(0.80, 0.65, NEON_RED, is_ai=True, name="VEX-BOT"))
                            elif game_mode == "3_BOTS":
                                enemies.append(Fighter(0.75, 0.30, NEON_CYAN, is_ai=True, name="ALPHA-BOT"))
                                enemies.append(Fighter(0.80, 0.55, NEON_RED, is_ai=True, name="SIGMA-BOT"))
                                enemies.append(Fighter(0.75, 0.75, NEON_AMBER, is_ai=True, name="OMNI-BOT"))

                            current_tab = "BATTLE_FIELD"

                if current_tab == "MYSTERY BOX" and btn_box_rect.collidepoint(m_pos) and box_state != "ROLLING":
                    box_state = "ROLLING"; roll_timer, roll_speed = 0, 2; play_sound(150, 0.1)

        # --- Active Dashboard Window View Core Router ---
        if current_tab == "CREATOR":
            screen.blit(fonts["title"].render("GENETIC LOADOUT LAB", True, GOLD), (center_view_x + 30, header_h + 25))
            
            # Repositioned Layout Blocks using explicit spacing offsets
            screen.blit(fonts["main"].render("CHASSIS IDENTIFIER:", True, WHITE), (center_view_x + 30, header_h + 81))
            name_input_rect = pygame.Rect(center_view_x + 200, header_h + 75, 180, 32)
            pygame.draw.rect(screen, (24, 24, 48) if name_active else (14, 14, 28), name_input_rect, border_radius=4)
            pygame.draw.rect(screen, NEON_CYAN if name_active else GRAY, name_input_rect, 1, border_radius=4)
            screen.blit(fonts["main"].render(p1_name + ("|" if name_active and pygame.time.get_ticks()//400 % 2 == 0 else ""), True, NEON_GREEN), (name_input_rect.x + 8, name_input_rect.y + 6))

            screen.blit(fonts["main"].render("CORE ENERGY COLOR:", True, WHITE), (center_view_x + 30, header_h + 135))
            for idx, color in enumerate(color_presets):
                c_box = pygame.Rect(center_view_x + 200 + (idx * 38), header_h + 130, 28, 28)
                pygame.draw.rect(screen, color, c_box, border_radius=14)
                if p1_color == color: pygame.draw.rect(screen, WHITE, c_box, 2, border_radius=14)

            screen.blit(fonts["main"].render(f"ALLOCATIONS REMAINING: {points}", True, NEON_GREEN), (center_view_x + 30, header_h + 195))
            for idx, s_name in enumerate(["STRENGTH", "SPEED", "DEFENSE"]):
                y_p = header_h + 245 + (idx * 50)
                screen.blit(fonts["main"].render(s_name, True, WHITE), (center_view_x + 30, y_p + 4))
                
                pygame.draw.rect(screen, NEON_CYAN, (center_view_x + 200, y_p, 30, 30), 1, border_radius=4)
                screen.blit(fonts["main"].render("-", True, NEON_CYAN), (center_view_x + 211, y_p + 1))
                
                screen.blit(fonts["main"].render(str(stats[s_name]), True, WHITE), (center_view_x + 262, y_p + 4))
                
                pygame.draw.rect(screen, NEON_CYAN, (center_view_x + 310, y_p, 30, 30), 1, border_radius=4)
                screen.blit(fonts["main"].render("+", True, NEON_CYAN), (center_view_x + 319, y_p + 1))

            btn_enter_arena = pygame.Rect(center_view_x + 30, HEIGHT - 80, 240, 42)
            pygame.draw.rect(screen, NEON_GREEN, btn_enter_arena, border_radius=6)
            txt_ent = fonts["main"].render("+ ENTER THE ARENA", True, BG_DARK)
            screen.blit(txt_ent, (btn_enter_arena.centerx - txt_ent.get_width()//2, btn_enter_arena.y + 12))

        elif current_tab == "ARENA LOBBY":
            screen.blit(fonts["title"].render("CHOOSE COMBAT SIMULATION CORE", True, NEON_CYAN), (center_view_x + 30, header_h + 25))
            modes = [
                ("1 BOT CHALLENGE", "Standard target matrix matching versus Kronis-Bot droid."),
                ("LOCAL 2-PLAYER SPLIT", "P1 controls with [WASD+SPACE] | P2 maps onto [ARROWS+RCTRL]."),
                ("2 BOTS CROSSFIRE LAYOUT", "Simulate dodging lines against an aggressive double AI setup."),
                ("3 BOTS EXTREME ONSLAUGHT", "Volatile combat engagement against Alpha, Sigma, and Omni bots.")
            ]
            for idx, (title, desc) in enumerate(modes):
                m_rect = pygame.Rect(center_view_x + 30, header_h + 75 + (idx * 75), 420, 58)
                pygame.draw.rect(screen, (15, 15, 38), m_rect, border_radius=6)
                pygame.draw.rect(screen, NEON_PURPLE if not m_rect.collidepoint(m_pos) else NEON_CYAN, m_rect, 1, border_radius=6)
                screen.blit(fonts["main"].render(title, True, WHITE), (m_rect.x + 15, m_rect.y + 9))
                screen.blit(fonts["small"].render(desc, True, GRAY), (m_rect.x + 15, m_rect.y + 32))

        elif current_tab == "VISUAL TUTORIAL":
            screen.blit(fonts["title"].render("INTELLIGENCE ARCHIVE: HOW TO PLAY", True, GOLD), (center_view_x + 30, header_h + 25))

            card_w = int((WIDTH - center_view_x - 80) / 2)
            card_h = int((HEIGHT - header_h - 90) / 2)

            x1, y1 = center_view_x + 25, header_h + 70
            b1 = pygame.Rect(x1, y1, card_w, card_h)
            pygame.draw.rect(screen, PANEL_BG, b1, border_radius=6)
            pygame.draw.rect(screen, NEON_CYAN, b1, 1, border_radius=6)
            screen.blit(fonts["main"].render("1. LOCOMOTION VECTOR", True, WHITE), (b1.x + 15, b1.y + 15))
            render_wrapped_text(screen, "Maneuver your unit across space using standard WASD layout parameters.", fonts["small"], GRAY, pygame.Rect(b1.x + 15, b1.y + 45, card_w - 30, card_h - 55))

            x2, y2 = x1 + card_w + 25, y1
            b2 = pygame.Rect(x2, y2, card_w, card_h)
            pygame.draw.rect(screen, PANEL_BG, b2, border_radius=6)
            pygame.draw.rect(screen, NEON_PURPLE, b2, 1, border_radius=6)
            screen.blit(fonts["main"].render("2. LASER INTERCEPT", True, WHITE), (b2.x + 15, b2.y + 15))
            render_wrapped_text(screen, "Press SPACEBAR to unleash active plasma rounds toward incoming configurations.", fonts["small"], GRAY, pygame.Rect(b2.x + 15, b2.y + 45, card_w - 30, card_h - 55))

            x3, y3 = x1, y1 + card_h + 20
            b3 = pygame.Rect(x3, y3, card_w, card_h)
            pygame.draw.rect(screen, PANEL_BG, b3, border_radius=6)
            pygame.draw.rect(screen, NEON_AMBER, b3, 1, border_radius=6)
            screen.blit(fonts["main"].render("3. CHRONO REVERSAL", True, WHITE), (b3.x + 15, b3.y + 15))
            render_wrapped_text(screen, "Hold key [R] at any crunch frame to rewind health, position, and vectors.", fonts["small"], GRAY, pygame.Rect(b3.x + 15, b3.y + 45, card_w - 30, card_h - 55))

            x4, y4 = x2, y3
            b4 = pygame.Rect(x4, y4, card_w, card_h)
            pygame.draw.rect(screen, PANEL_BG, b4, border_radius=6)
            pygame.draw.rect(screen, NEON_GREEN, b4, 1, border_radius=6)
            screen.blit(fonts["main"].render("4. TIME CORE MATRIX", True, WHITE), (b4.x + 15, b4.y + 15))
            render_wrapped_text(screen, "Intercept spawned golden spheres directly to gain critical timeline extensions.", fonts["small"], GRAY, pygame.Rect(b4.x + 15, b4.y + 45, card_w - 30, card_h - 55))

        elif current_tab == "BATTLE_FIELD":
            p1.max_hp = 1000 + (stats["DEFENSE"] * 50)
            p1_calc_atk = (15 + (stats["STRENGTH"] * 2)) * p1.atk_mult

            is_rewinding = keys[pygame.K_r] or (btn_rev_rect.collidepoint(m_pos) and pygame.mouse.get_pressed()[0])

            if is_rewinding:
                if not rewind_pressed_last_frame and not missions["rewinds_used"]["done"]:
                    missions["rewinds_used"]["current"] = 1
                    missions["rewinds_used"]["done"] = True
                    play_sound(1000, 0.15)
                rewind_pressed_last_frame = True

                if history:
                    snap = history.pop()
                    p1.ratio, p1.hp, p1.is_alive = pygame.Vector2(snap[0]), snap[1], snap[2]
                    match_timer = snap[3]
                    enemies.clear()
                    for e_d in snap[4]:
                        e_obj = Fighter(e_d[0], e_d[1], e_d[2], is_ai=e_d[3], name=e_d[4])
                        e_obj.hp, e_obj.is_alive, e_obj.facing_angle = e_d[5], e_d[6], e_d[7]
                        enemies.append(e_obj)
                    bullets = [Bullet(b[0], b[1], b[2], b[3], b[4], b[5]) for b in snap[5]]
                    orbs = [TimeOrb(center_view_x) for _ in snap[6]]
                    for idx, o in enumerate(orbs): o.pos = pygame.Vector2(snap[6][idx][0], snap[6][idx][1])
                    for k, m_data in snap[7].items():
                        missions[k]["current"] = m_data["current"]
                        missions[k]["done"] = m_data["done"]
            else:
                rewind_pressed_last_frame = False
                p1.handle_input(keys, stats["SPEED"], bullets, blocks, center_view_x, is_p2=False)
                p1.restrict_boundaries()

                for e in enemies:
                    if e.is_ai: e.execute_ai_logic([p1], bullets, blocks, center_view_x, time_scale, sudden_death=is_sudden_death)
                    elif not e.is_ai: e.handle_input(keys, 5, bullets, blocks, center_view_x, is_p2=True)
                    e.restrict_boundaries()

                if time_scale > 0:
                    orb_spawn_timer += 1
                    if orb_spawn_timer > 150: orbs.append(TimeOrb(center_view_x)); orb_spawn_timer = 0

                    p1_box = p1.get_hitbox(center_view_x)
                    for o in orbs:
                        o.update()
                        if o.active and p1.is_alive and p1_box.collidepoint(o.pos):
                            o.active = False; p1.hp = min(p1.max_hp, p1.hp + 200)
                            match_timer = min(60.0, match_timer + 5.0)
                            play_sound(950, 0.12)

                            if not missions["orbs_collected"]["done"]:
                                missions["orbs_collected"]["current"] += 1
                                if missions["orbs_collected"]["current"] >= missions["orbs_collected"]["target"]:
                                    missions["orbs_collected"]["done"] = True
                                    play_sound(1200, 0.3)

                    orbs = [o for o in orbs if o.active]

                    for b in bullets[:]:
                        b.update(time_scale, center_view_x)
                        for blk in blocks:
                            if blk.rect.collidepoint(b.pos): b.active = False; break
                        if not b.active: continue

                        base_dmg = 30 if is_sudden_death else 20

                        if b.active and p1.is_alive and b.owner_name != p1.name and p1.get_hitbox(center_view_x).collidepoint(b.pos):
                            p1.hp = max(0, p1.hp - base_dmg); b.active = False; play_sound(160, 0.04, "noise")
                            if p1.hp <= 0: p1.is_alive = False

                        for e in enemies:
                            if b.active and e.is_alive and b.owner_name != e.name and e.get_hitbox(center_view_x).collidepoint(b.pos):
                                final_p1_atk = int(p1_calc_atk * 1.5) if is_sudden_death else int(p1_calc_atk)
                                e.hp = max(0, e.hp - (final_p1_atk if b.owner_name == p1.name else base_dmg))
                                b.active = False; play_sound(160, 0.04, "noise")
                                if e.hp <= 0: e.is_alive = False

                                if b.owner_name == p1.name:
                                    if not missions["laser_hits"]["done"]:
                                        missions["laser_hits"]["current"] += 1
                                        if missions["laser_hits"]["current"] >= missions["laser_hits"]["target"]:
                                            missions["laser_hits"]["done"] = True
                                            play_sound(1200, 0.3)

                                    if not missions["damage_inflicted"]["done"]:
                                        missions["damage_inflicted"]["current"] += final_p1_atk
                                        if missions["damage_inflicted"]["current"] >= missions["damage_inflicted"]["target"]:
                                            missions["damage_inflicted"]["current"] = missions["damage_inflicted"]["target"]
                                            missions["damage_inflicted"]["done"] = True
                                            play_sound(1200, 0.3)

                    bullets = [b for b in bullets if b.active]

                    if p1.is_alive and any(e.is_alive for e in enemies) and match_timer > 0:
                        e_sn = [(e.ratio.x, e.ratio.y, e.color, e.is_ai, e.name, e.hp, e.is_alive, e.facing_angle) for e in enemies]
                        m_sn = {k: {"current": v["current"], "done": v["done"]} for k, v in missions.items()}
                        history.append(((p1.ratio.x, p1.ratio.y), p1.hp, p1.is_alive, match_timer, e_sn, [(b.pos.x, b.pos.y, b.angle, b.color, b.owner_name, b.is_plasma) for b in bullets], [(o.pos.x, o.pos.y) for o in orbs], m_sn))
                        if len(history) > 400: history.pop(0)

            for j in range(int(HEIGHT*0.25), HEIGHT - 40, int(HEIGHT*0.065)):
                pygame.draw.line(screen, (0, 32, 45), (center_view_x, j), (WIDTH, j), 1)

            for blk in blocks: blk.draw(screen)
            for o in orbs: o.draw(screen)
            p1.draw(screen, center_view_x)
            for e in enemies: e.draw(screen, center_view_x)
            for b in bullets: b.draw(screen)

            if is_sudden_death:
                glow_val = int(abs(math.sin(pygame.time.get_ticks() / 150)) * 3) + 1
                pygame.draw.rect(screen, NEON_RED, (center_view_x, 60, WIDTH - center_view_x, HEIGHT - 60), glow_val)

            t_col = NEON_GREEN if match_timer > 20 else NEON_RED
            screen.blit(fonts["title"].render(f"TIMER: {int(match_timer)}s", True, t_col), (center_view_x + 30, header_h + 20))

            y_g = header_h + 55
            pygame.draw.rect(screen, (24, 24, 48), (center_view_x + 30, y_g, 130, 8))
            pygame.draw.rect(screen, p1_color, (center_view_x + 30, y_g, int(130 * (p1.hp/p1.max_hp)), 8))
            screen.blit(fonts["small"].render(f"{p1_name}: {int(p1.hp)}HP", True, WHITE), (center_view_x + 30, y_g + 12))

            for idx, e in enumerate(enemies):
                x_g = WIDTH - 150 - (idx * 160)
                pygame.draw.rect(screen, (24, 24, 48), (x_g, y_g, 130, 8))
                pygame.draw.rect(screen, e.color, (x_g, y_g, int(130 * (e.hp/1200)), 8))
                screen.blit(fonts["small"].render(f"{e.name}: {int(e.hp)}HP", True, WHITE), (x_g, y_g + 12))

            if not p1.is_alive or all(not e.is_alive for e in enemies) or match_timer <= 0:
                if winning_character == "":
                    if not p1.is_alive:
                        alive_enemies = [e.name for e in enemies if e.is_alive]
                        winning_character = alive_enemies[0] if alive_enemies else "THE ARCHIVE VECTOR"
                    elif all(not e.is_alive for e in enemies):
                        winning_character = p1.name
                    else:
                        winning_character = "TIMELINE EXPIRED OVERRIDE"

                banner = pygame.Surface((WIDTH - center_view_x, 90)); banner.fill((5, 5, 10))
                screen.blit(banner, (center_view_x, int(HEIGHT * 0.40)))
                win_text = f"GAME WON BY {winning_character}"
                screen.blit(fonts["title"].render(win_text.upper(), True, NEON_AMBER), (center_view_x + 30, int(HEIGHT * 0.45)))

        elif current_tab == "MYSTERY BOX":
            screen.blit(fonts["title"].render("QUANTUM MATRIX CACHE", True, NEON_AMBER), (center_view_x + 30, header_h + 25))
            btn_box_rect = pygame.Rect(center_view_x + 50, header_h + 80, 130, 130)
            is_h = btn_box_rect.collidepoint(m_pos) and box_state != "ROLLING"
            pygame.draw.rect(screen, (45, 30, 15) if is_h else (24, 18, 42) if box_state=="ROLLING" else (14, 14, 28), btn_box_rect, border_radius=12)
            pygame.draw.rect(screen, NEON_AMBER, btn_box_rect, 2, border_radius=12)
            screen.blit(fonts["title"].render("BOX", True, GOLD), (btn_box_rect.centerx - 16, btn_box_rect.centery - 12))

            strip = pygame.Rect(center_view_x + 30, header_h + 250, WIDTH - center_view_x - 60, 55)
            pygame.draw.rect(screen, (10, 10, 26), strip, border_radius=6)
            if box_state == "ROLLING": txt = box_rewards[current_roll_idx]["name"]; c = NEON_AMBER
            elif box_state == "CLAIMED": txt = f"UNLOCKED: {box_unlocked_reward['name']}"; c = NEON_GREEN
            else: txt = "AWAITING QUANTUM KEY INPUT MODIFIER..."; c = GRAY
            surf = fonts["main"].render(txt, True, c)
            screen.blit(surf, (strip.centerx - surf.get_width()//2, strip.centery - surf.get_height()//2))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    try:
        import asyncio
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        task = loop.create_task(run_game())
    else:
        asyncio.run(run_game())