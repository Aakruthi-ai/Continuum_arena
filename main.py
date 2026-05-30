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

    WINDOW_W, WINDOW_H = 1024, 640
    global WIDTH, HEIGHT, screen
    WIDTH, HEIGHT = WINDOW_W, WINDOW_H
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("CONTINUUM ARENA // ONSLAUGHT SYSTEM")
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
    GRAY = (140, 145, 160)
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

    def get_fonts():
        scale = max(0.75, min(1.4, HEIGHT / 640.0))
        return {
            "main": pygame.font.SysFont("OCR A Extended", int(15 * scale)),
            "small": pygame.font.SysFont("Verdana", int(11 * scale), bold=False),
            "title": pygame.font.SysFont("OCR A Extended", int(17 * scale), bold=True)
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

    # --- Projectile & Drop Classes ---
    class Bullet:
        def __init__(self, x, y, angle, color, owner_name, base_dmg=20):
            self.pos = pygame.Vector2(x, y)
            self.angle = angle 
            self.owner_name = owner_name
            self.active = True
            self.color = color
            self.speed = 12.0
            self.damage_value = base_dmg
            self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.speed

        def update(self, t_scale, min_x):
            self.pos += self.velocity * t_scale
            if self.pos.x < min_x or self.pos.x > WIDTH or self.pos.y < 120 or self.pos.y > HEIGHT:
                self.active = False

        def draw(self, surface):
            w, h = 14, 4
            laser_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            laser_surf.fill(self.color)
            rot_laser = pygame.transform.rotate(laser_surf, -math.degrees(self.angle))
            surface.blit(rot_laser, (self.pos.x - rot_laser.get_width()//2, self.pos.y - rot_laser.get_height()//2))

    class ObstacleBlock:
        def __init__(self, start_x):
            playable_w = WIDTH - start_x
            self.rect = pygame.Rect(
                random.randint(int(start_x + (playable_w * 0.15)), int(start_x + (playable_w * 0.8))),
                random.randint(180, int(HEIGHT - 140)),
                random.randint(35, 70),
                random.randint(35, 70)
            )
            self.pulse = random.random() * 10

        def draw(self, surface):
            self.pulse += 0.05
            glow = int(abs(math.sin(self.pulse)) * 25)
            pygame.draw.rect(surface, (BLOCK_COLOR[0]+glow, BLOCK_COLOR[1], BLOCK_COLOR[2]), self.rect, border_radius=4)
            pygame.draw.rect(surface, NEON_CYAN, self.rect, 1, border_radius=4)

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

    class MysteryBoxDrop:
        def __init__(self, start_x):
            self.rect = pygame.Rect(
                random.randint(int(start_x + 50), int(WIDTH - 80)),
                random.randint(180, int(HEIGHT - 100)),
                24, 24
            )
            self.pulse = 0.0

        def draw(self, surface):
            self.pulse += 0.08
            glow = int(abs(math.sin(self.pulse)) * 40)
            pygame.draw.rect(surface, (20, 10, 40), self.rect, border_radius=4)
            pygame.draw.rect(surface, (150 + glow, 0, 255), self.rect, 2, border_radius=4)
            font_q = pygame.font.SysFont("Courier New", 16, bold=True)
            q_surf = font_q.render("?", True, WHITE)
            surface.blit(q_surf, (self.rect.centerx - q_surf.get_width()//2, self.rect.centery - q_surf.get_height()//2 - 1))

    class FloatingText:
        def __init__(self, text, x, y, color):
            self.text = text
            self.pos = pygame.Vector2(x, y)
            self.color = color
            self.timer = 70 

        def update(self):
            self.pos.y -= 0.6
            self.timer -= 1

        def draw(self, surface):
            if self.timer <= 0: return
            alpha = min(255, self.timer * 4)
            font_f = pygame.font.SysFont("OCR A Extended", 13, bold=True)
            txt_surf = font_f.render(self.text, True, self.color)
            surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
            surf.fill((255, 255, 255, alpha))
            txt_surf.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(txt_surf, (self.pos.x - txt_surf.get_width()//2, self.pos.y))

    class Fighter:
        def __init__(self, x_ratio, y_ratio, color, is_ai=False, name="VEX-9"):
            self.ratio = pygame.Vector2(x_ratio, y_ratio)
            self.color = color
            self.is_ai = is_ai
            self.name = name
            self.max_hp = 1200
            self.hp = self.max_hp
            self.is_alive = True
            self.shoot_cooldown = 0
            self.anim_tick = 0
            self.is_moving = False
            self.facing_angle = 0.0
            
            self.has_mystery_control = False  
            self.shield_hp = 0                
            self.has_overcharge = False      

        def get_actual_pos(self, min_x):
            playable_w = WIDTH - min_x
            return pygame.Vector2(min_x + (self.ratio.x * playable_w), self.ratio.y * HEIGHT)

        def get_hitbox(self, min_x):
            p = self.get_actual_pos(min_x)
            return pygame.Rect(p.x - 15, p.y - 50, 30, 60)

        def handle_input(self, keys, stats_speed, bullets, blocks, min_x, touch_target_pos=None):
            if not self.is_alive: return
            speed = (3.4 + (stats_speed * 0.35))
            old_ratio = pygame.Vector2(self.ratio)
            self.is_moving = False

            p_self = self.get_actual_pos(min_x)

            # Mobile/Mouse Touch Vectors Logic
            if touch_target_pos is not None:
                delta_move = touch_target_pos - p_self
                if delta_move.length() > 6:
                    self.is_moving = True
                    move_vec = delta_move.normalize() * speed
                    new_x = p_self.x + move_vec.x
                    new_y = p_self.y + move_vec.y
                    self.facing_angle = math.atan2(move_vec.y, move_vec.x)
                    self.ratio.x = (new_x - min_x) / (WIDTH - min_x) if (WIDTH - min_x) > 0 else 0
                    self.ratio.y = new_y / HEIGHT
            else:
                # Keyboard Handling Logic
                dx, dy = 0, 0
                if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1; self.is_moving = True
                if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1; self.is_moving = True
                if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1; self.is_moving = True
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1; self.is_moving = True
                
                if self.is_moving:
                    move_vec = pygame.Vector2(dx, dy)
                    if move_vec.length() > 0:
                        move_vec = move_vec.normalize() * speed
                        self.ratio.y += move_vec.y / HEIGHT
                        self.ratio.x += move_vec.x / (WIDTH - min_x) if (WIDTH - min_x) > 0 else 0
                        self.facing_angle = math.atan2(move_vec.y, move_vec.x)

            my_box = self.get_hitbox(min_x)
            for b in blocks:
                if my_box.colliderect(b.rect):
                    self.ratio = old_ratio
                    break

            if self.shoot_cooldown > 0: 
                self.shoot_cooldown -= 1
            else:
                should_fire = False
                if self.has_mystery_control:
                    should_fire = (random.random() < 0.08)
                else:
                    # In mobile touch, tap/hold automatically tracks firing vector streams
                    should_fire = (keys[pygame.K_SPACE] or touch_target_pos is not None)

                if should_fire:
                    p = self.get_actual_pos(min_x)
                    dmg = 60 if self.has_overcharge else 20
                    col = NEON_AMBER if self.has_overcharge else self.color
                    bullets.append(Bullet(p.x, p.y - 18, self.facing_angle, col, self.name, base_dmg=dmg))
                    self.shoot_cooldown = 9 if self.has_mystery_control else 14
                    play_sound(550, 0.06)

        def execute_ai_logic(self, targets, bullets, blocks, min_x, t_scale, frantic_mode=False):
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
            ai_speed = 3.2 if frantic_mode else 2.1

            if dist > 130:
                new_pos = p_self + delta.normalize() * (ai_speed * t_scale)
                self.ratio.x = (new_pos.x - min_x) / (WIDTH - min_x) if (WIDTH - min_x) > 0 else 0
                self.ratio.y = new_pos.y / HEIGHT
            elif dist < 90:
                new_pos = p_self - delta.normalize() * (1.6 * t_scale)
                self.ratio.x = (new_pos.x - min_x) / (WIDTH - min_x) if (WIDTH - min_x) > 0 else 0
                self.ratio.y = new_pos.y / HEIGHT

            my_box = self.get_hitbox(min_x)
            for b in blocks:
                if my_box.colliderect(b.rect):
                    self.ratio = old_ratio
                    break

            if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
            else:
                fire_chance = 0.07 if (frantic_mode or dist < 220) else 0.025
                if random.random() < fire_chance:
                    bullets.append(Bullet(p_self.x, p_self.y - 18, self.facing_angle, self.color, self.name))
                    self.shoot_cooldown = random.randint(20, 45)
                    play_sound(410, 0.07)

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

            if self.shield_hp > 0:
                rad_pulse = int(22 + math.sin(pygame.time.get_ticks() * 0.01) * 3)
                pygame.draw.circle(surface, (0, 230, 255), (int(p.x), int(p.y - 18)), rad_pulse, 2)

            pygame.draw.circle(surface, c, (int(p.x), int(p.y - (h_scale * 3.5) + bounce)), h_scale)
            pygame.draw.rect(surface, c, (p.x - h_scale, p.y - (h_scale * 2.7) + bounce, h_scale * 2, h_scale * 2.5), border_radius=4)

            w_len = h_scale * 2.4
            aim_color = NEON_AMBER if self.has_overcharge else GOLD
            pygame.draw.line(surface, aim_color, (p.x, p.y - h_scale + bounce), (p.x + math.cos(self.facing_angle)*w_len, p.y - h_scale + bounce + math.sin(self.facing_angle)*w_len), 3)

            leg = math.cos(self.anim_tick) * 4 if self.is_moving else 0
            pygame.draw.line(surface, c, (p.x - 3, p.y + bounce), (p.x - h_scale - leg, p.y + (h_scale * 1.8)), 2)
            pygame.draw.line(surface, c, (p.x + 3, p.y + bounce), (p.x + h_scale + leg, p.y + (h_scale * 1.8)), 2)

            lbl = fonts["small"].render(self.name, True, WHITE)
            surface.blit(lbl, (p.x - lbl.get_width()//2, p.y - (h_scale * 5.5) + bounce))

    # --- System Variables Configuration ---
    p1_name = "HERO-X"
    name_active = False
    p1_color = NEON_PURPLE
    color_presets = [NEON_PURPLE, NEON_GREEN, NEON_AMBER, WHITE, (255, 0, 120)]
    
    current_tab = "CREATOR"
    game_mode = "1_BOT"
    arena_unlocked = False
    winning_character = ""
    defeat_reason = ""

    stats = {"STRENGTH": 5, "SPEED": 5, "DEFENSE": 5}
    points = 10
    time_scale = 1.0
    match_timer = 60.0

    ALL_POSSIBLE_MISSIONS = [
        {"id": "orbs_collected", "target_min": 2, "target_max": 4, "desc": "Collect Golden Time Cores"},
        {"id": "laser_hits", "target_min": 6, "target_max": 10, "desc": "Land Tactical Laser Shots"},
        {"id": "damage_inflicted", "target_min": 800, "target_max": 1400, "desc": "Deal Total Matrix Damage"},
        {"id": "distance_traveled", "target_min": 400, "target_max": 800, "desc": "Reposition Chassis Vectors"}
    ]
    
    def generator_shuffle_missions():
        chosen = random.sample(ALL_POSSIBLE_MISSIONS, 4)
        shuffled = {}
        for m in chosen:
            tgt = random.randint(m["target_min"], m["target_max"])
            if m["id"] == "damage_inflicted" or m["id"] == "distance_traveled":
                tgt = (tgt // 100) * 100
            shuffled[m["id"]] = {
                "current": 0,
                "target": tgt,
                "desc": m["desc"],
                "done": False
            }
        return shuffled

    active_missions = generator_shuffle_missions()

    history, bullets, orbs, blocks, active_boxes, floating_texts = [], [], [], [], [], []
    orb_spawn_timer = 0
    box_spawn_timer = 0
    boxes_spawned_count = 0  

    p1 = Fighter(0.2, 0.55, p1_color, name=p1_name)
    enemies = []
    rewind_pressed_last_frame = False

    # --- Tutorial Simulation Attributes ---
    tut_pulse = 0.0
    tut_char_pos = pygame.Vector2(0, 0)
    tut_orb_pos = pygame.Vector2(0, 0)
    tut_box_pos = pygame.Vector2(0, 0)
    tut_orb_active = True
    tut_box_active = True
    tut_state_timer = 0
    tut_float_text = ""
    tut_float_color = WHITE
    tut_float_timer = 0
    tut_float_pos = pygame.Vector2(0,0)

    running = True
    while running:
        m_pos = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()
        screen.fill(BG_DARK)

        left_panel_w = int(WIDTH * 0.28)
        sub_sidebar_w = int(WIDTH * 0.16)
        center_view_x = left_panel_w + sub_sidebar_w
        header_h = 60

        pygame.draw.rect(screen, PANEL_BG, (0, 0, WIDTH, header_h))
        pygame.draw.line(screen, NEON_PURPLE, (0, header_h), (WIDTH, header_h), 2)
        screen.blit(fonts["title"].render("CONTINUUM-ARENA // ONSLAUGHT SYSTEM", True, WHITE), (15, 18))

        fs_btn_rect = pygame.Rect(WIDTH - 190, 12, 175, 34)
        fs_btn_color = NEON_GREEN if is_fullscreen else NEON_CYAN
        pygame.draw.rect(screen, (24, 24, 48), fs_btn_rect, border_radius=4)
        pygame.draw.rect(screen, fs_btn_color, fs_btn_rect, 1, border_radius=4)
        fs_txt = "🖥️ WINDOW MODE" if is_fullscreen else "🖥️ FULLSCREEN MODE"
        screen.blit(fonts["small"].render(fs_txt, True, fs_btn_color), (fs_btn_rect.x + 12, fs_btn_rect.y + 9))

        # --- Side Matrix Log ---
        pygame.draw.rect(screen, (10, 10, 28), (0, header_h, left_panel_w, HEIGHT - header_h))
        pygame.draw.line(screen, NEON_CYAN, (left_panel_w, header_h), (left_panel_w, HEIGHT), 2)

        y_guide = header_h + 15
        screen.blit(fonts["main"].render("MISSION LOG MATRIX", True, GOLD), (15, y_guide))
        y_guide += 25

        box_h = int((HEIGHT - y_guide - 110) / 4)
        box_h = max(38, min(52, box_h))

        for m_key, m_data in active_missions.items():
            box_r = pygame.Rect(10, y_guide, left_panel_w - 20, box_h)
            pygame.draw.rect(screen, (16, 16, 38) if not m_data["done"] else (8, 38, 20), box_r, border_radius=4)
            pygame.draw.rect(screen, NEON_CYAN if not m_data["done"] else NEON_GREEN, box_r, 1, border_radius=4)

            txt_m = f"{m_data['desc']}"
            prog_m = f"[{int(m_data['current'])}/{m_data['target']}]" if not m_data["done"] else "[COMPLETE]"

            screen.blit(fonts["small"].render(txt_m, True, WHITE), (18, y_guide + int(box_h*0.12)))
            screen.blit(fonts["small"].render(prog_m, True, NEON_AMBER if not m_data["done"] else NEON_GREEN), (18, y_guide + int(box_h*0.52)))
            y_guide += box_h + 6

        y_guide += 5
        pygame.draw.line(screen, GRAY, (10, y_guide), (left_panel_w - 10, y_guide))
        y_guide += 10

        screen.blit(fonts["main"].render("VICTORY REQUIREMENT:", True, NEON_RED), (15, y_guide))
        y_guide += 20
        advice_text = [
            "🏆 ALL 5 Missions MUST be completed",
            "🏆 AND ALL Hostile Bots eliminated",
            "📦 Mystery Boxes drop 4 random buffs!",
            "⚠️ Purging bots early without logs = LOSE!"
        ]
        for line in advice_text:
            screen.blit(fonts["small"].render(line, True, WHITE), (15, y_guide))
            y_guide += 18

        # --- Sidebar Nav Matrix ---
        pygame.draw.rect(screen, (16, 16, 36), (left_panel_w, header_h, sub_sidebar_w, HEIGHT - header_h))
        pygame.draw.line(screen, NEON_CYAN, (center_view_x, header_h), (center_view_x, HEIGHT), 1)

        tabs_map = ["CREATOR", "VISUAL TUTORIAL"] if not arena_unlocked else ["CREATOR", "ARENA LOBBY", "VISUAL TUTORIAL"]
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

        touch_vector_pos = None
        if pygame.mouse.get_pressed()[0] and current_tab == "BATTLE_FIELD":
            if m_pos[0] > center_view_x and m_pos[1] > header_h:
                touch_vector_pos = pygame.Vector2(m_pos[0], m_pos[1])

        # --- Event Loop Stream ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

            # FIXES MOBILE ROTATION GLITCH AUTOMATICALLY
            if event.type == pygame.VIDEORESIZE:
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
                btn_enter_arena = pygame.Rect(center_view_x + 30, HEIGHT - 70, 240, 42)

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

                    plus_rects = {"STRENGTH": pygame.Rect(center_view_x + 310, header_h + 205, 30, 30), "SPEED": pygame.Rect(center_view_x + 310, header_h + 255, 30, 30), "DEFENSE": pygame.Rect(center_view_x + 310, header_h + 305, 30, 30)}
                    minus_rects = {"STRENGTH": pygame.Rect(center_view_x + 200, header_h + 205, 30, 30), "SPEED": pygame.Rect(center_view_x + 200, header_h + 255, 30, 30), "DEFENSE": pygame.Rect(center_view_x + 200, header_h + 305, 30, 30)}
                    for s, r in plus_rects.items():
                        if r.collidepoint(m_pos) and points > 0: stats[s] += 1; points -= 1; play_sound(620, 0.03)
                    for s, r in minus_rects.items():
                        if r.collidepoint(m_pos) and stats[s] > 1: stats[s] -= 1; points += 1; play_sound(340, 0.03)

                elif current_tab == "ARENA LOBBY":
                    lobby_box_w = int(WIDTH - center_view_x - 80)
                    lobby_box_w = max(420, min(550, lobby_box_w))
                    
                    for idx in range(4):
                        if pygame.Rect(center_view_x + 30, header_h + 75 + (idx * 85), lobby_box_w, 68).collidepoint(m_pos):
                            game_mode = ["1_BOT", "LOCAL_2P", "2_BOTS", "3_BOTS"][idx]
                            play_sound(800, 0.08)

                            winning_character = ""
                            defeat_reason = ""
                            p1 = Fighter(0.20, 0.55, p1_color, name=p1_name)
                            active_missions = generator_shuffle_missions()

                            enemies.clear(); bullets.clear(); history.clear(); orbs.clear(); blocks.clear(); active_boxes.clear(); floating_texts.clear()
                            for _ in range(random.randint(3, 5)): 
                                blocks.append(ObstacleBlock(center_view_x))
                                
                            match_timer = 60.0; time_scale = 1.0
                            boxes_spawned_count = 0
                            box_spawn_timer = 0

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

        # --- View Routers Rendering ---
        if current_tab == "CREATOR":
            screen.blit(fonts["title"].render("GENETIC CONFIG LAB", True, GOLD), (center_view_x + 30, header_h + 25))
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

            screen.blit(fonts["main"].render(f"ALLOCATIONS REMAINING: {points}", True, NEON_GREEN), (center_view_x + 30, header_h + 175))
            for idx, s_name in enumerate(["STRENGTH", "SPEED", "DEFENSE"]):
                y_p = header_h + 205 + (idx * 50)
                screen.blit(fonts["main"].render(s_name, True, WHITE), (center_view_x + 30, y_p + 4))
                pygame.draw.rect(screen, NEON_CYAN, (center_view_x + 200, y_p, 30, 30), 1, border_radius=4)
                screen.blit(fonts["main"].render("-", True, NEON_CYAN), (center_view_x + 211, y_p + 1))
                screen.blit(fonts["main"].render(str(stats[s_name]), True, WHITE), (center_view_x + 262, y_p + 4))
                pygame.draw.rect(screen, NEON_CYAN, (center_view_x + 310, y_p, 30, 30), 1, border_radius=4)
                screen.blit(fonts["main"].render("+", True, NEON_CYAN), (center_view_x + 319, y_p + 1))

            btn_enter_arena = pygame.Rect(center_view_x + 30, HEIGHT - 70, 240, 42)
            pygame.draw.rect(screen, NEON_GREEN, btn_enter_arena, border_radius=6)
            txt_ent = fonts["main"].render("+ ENTER THE ARENA", True, BG_DARK)
            screen.blit(txt_ent, (btn_enter_arena.centerx - txt_ent.get_width()//2, btn_enter_arena.y + 12))

        elif current_tab == "ARENA LOBBY":
            screen.blit(fonts["title"].render("CHOOSE COMBAT SIMULATION CORE", True, NEON_CYAN), (center_view_x + 30, header_h + 25))
            modes = [
                ("1 BOT CHALLENGE", "Standard target matrix matching versus Kronis-Bot droid. Generates a sequence of 4 clean academic missions."),
                ("LOCAL 2-PLAYER SPLIT", "Mobile Touch Assisted Navigation Mode. Complete designated parameter logs before running down matrix lines."),
                ("2 BOTS CROSSFIRE LAYOUT", "Simulate dodging lines against an aggressive double AI setup under customized tactical configurations."),
                ("3 BOTS EXTREME ONSLAUGHT", "Volatile combat engagement against Alpha, Sigma, and Omni bots. Pure frantic mission clearing challenge.")
            ]
            
            lobby_box_w = int(WIDTH - center_view_x - 80)
            lobby_box_w = max(420, min(550, lobby_box_w))

            for idx, (title, desc) in enumerate(modes):
                m_rect = pygame.Rect(center_view_x + 30, header_h + 75 + (idx * 85), lobby_box_w, 68)
                pygame.draw.rect(screen, (15, 15, 38), m_rect, border_radius=6)
                pygame.draw.rect(screen, NEON_PURPLE if not m_rect.collidepoint(m_pos) else NEON_CYAN, m_rect, 1, border_radius=6)
                screen.blit(fonts["main"].render(title, True, WHITE), (m_rect.x + 15, m_rect.y + 9))
                desc_rect = pygame.Rect(m_rect.x + 15, m_rect.y + 34, m_rect.width - 30, 30)
                render_wrapped_text(screen, desc, fonts["small"], GRAY, desc_rect, line_spacing=2)

        elif current_tab == "VISUAL TUTORIAL":
            tut_pulse += 0.05
            screen.blit(fonts["title"].render("INTELLIGENCE ARCHIVE: CORE MECHANICS", True, GOLD), (center_view_x + 25, header_h + 20))
            
            left_col_w = int((WIDTH - center_view_x) * 0.52)
            right_canvas_w = int((WIDTH - center_view_x) * 0.42)
            card_h = int((HEIGHT - header_h - 110) / 4)
            card_h = max(55, min(80, card_h))

            y_start = header_h + 50
            titles = [
                "1. CHASSIS MOVEMENT CONTROLS",
                "2. TARGET VECTOR ANGLE INDICATORS",
                "3. TIME ORB ACQUISITION",
                "4. MYSTERY POWERUP BUFF MATRIX"
            ]
            descs = [
                "Use the standard W, A, S, D layout keys to steer your chassis directionally inside the arena environment.",
                "Laser projectiles track the golden vector extension line. Tap SPACEBAR manually to fire individual energy beams.",
                "Collect glowing golden Time Orbs during battle loops to gain +200 HP structural repairs and +5s extensions.",
                "Mystery Boxes roll 4 distinct chassis upgrades: AUTO-RAPID LASERS, MATRIX DEFENSIVE SHIELD, OVERCHARGE ATK x3, or REGEN CORE."
            ]
            colors_preset = [NEON_CYAN, GOLD, NEON_AMBER, NEON_PURPLE]

            for idx in range(4):
                c_rect = pygame.Rect(center_view_x + 20, y_start + (idx * (card_h + 8)), left_col_w, card_h)
                pygame.draw.rect(screen, PANEL_BG, c_rect, border_radius=6)
                pygame.draw.rect(screen, colors_preset[idx], c_rect, 1, border_radius=6)
                screen.blit(fonts["main"].render(titles[idx], True, WHITE), (c_rect.x + 12, c_rect.y + 6))
                desc_r = pygame.Rect(c_rect.x + 12, c_rect.y + 24, c_rect.width - 24, card_h - 28)
                render_wrapped_text(screen, descs[idx], fonts["small"], GRAY, desc_r, line_spacing=1)

            canvas_rect = pygame.Rect(center_view_x + 35 + left_col_w, header_h + 50, right_canvas_w, (card_h * 4) + 24)
            pygame.draw.rect(screen, (8, 8, 24), canvas_rect, border_radius=8)
            pygame.draw.rect(screen, NEON_CYAN, canvas_rect, 1, border_radius=8)
            
            cx, cy = canvas_rect.centerx, canvas_rect.centery - 30

            if tut_state_timer == 0:
                tut_char_pos = pygame.Vector2(canvas_rect.x + 40, cy + 30)
                tut_orb_pos = pygame.Vector2(canvas_rect.right - 50, cy - 20)
                tut_box_pos = pygame.Vector2(canvas_rect.right - 60, cy + 60)
                tut_orb_active = True
                tut_box_active = True
                tut_state_timer = 1

            if tut_state_timer == 1:
                target = tut_orb_pos
                dir_v = target - tut_char_pos
                if dir_v.length() > 3:
                    tut_char_pos += dir_v.normalize() * 1.5
                else:
                    tut_orb_active = False
                    tut_float_text = "+200 HP [EXT]"
                    tut_float_color = GOLD
                    tut_float_pos = pygame.Vector2(tut_char_pos.x, tut_char_pos.y - 30)
                    tut_float_timer = 50
                    tut_state_timer = 2
            elif tut_state_timer == 2:
                target = tut_box_pos
                dir_v = target - tut_char_pos
                if dir_v.length() > 3:
                    tut_char_pos += dir_v.normalize() * 1.5
                else:
                    tut_box_active = False
                    tut_float_text = "SHIELD BARRIER!"
                    tut_float_color = NEON_CYAN
                    tut_float_pos = pygame.Vector2(tut_char_pos.x, tut_char_pos.y - 30)
                    tut_float_timer = 50
                    tut_state_timer = 3
            elif tut_state_timer == 3:
                tut_state_timer += 1
            elif tut_state_timer > 3:
                tut_state_timer += 1
                if tut_state_timer > 120:
                    tut_state_timer = 0

            pygame.draw.line(screen, (15, 45, 65), (canvas_rect.x, cy), (canvas_rect.right, cy), 1)
            pygame.draw.circle(screen, (20, 50, 70), (int(tut_char_pos.x), int(tut_char_pos.y)), int(22 + math.sin(tut_pulse)*2), 1)

            if tut_orb_active:
                r_val = int(6 + math.sin(tut_pulse * 2) * 2)
                pygame.draw.circle(screen, GOLD, (int(tut_orb_pos.x), int(tut_orb_pos.y)), r_val)
                pygame.draw.circle(screen, NEON_AMBER, (int(tut_orb_pos.x), int(tut_orb_pos.y)), r_val + 3, 1)

            if tut_box_active:
                b_rect = pygame.Rect(tut_box_pos.x - 10, tut_box_pos.y - 10, 20, 20)
                g_val = int(abs(math.sin(tut_pulse)) * 30)
                pygame.draw.rect(screen, (20, 10, 40), b_rect, border_radius=3)
                pygame.draw.rect(screen, (150 + g_val, 0, 255), b_rect, 2, border_radius=3)
                q_f = pygame.font.SysFont("Courier New", 13, bold=True)
                q_s = q_f.render("?", True, WHITE)
                screen.blit(q_s, (b_rect.centerx - q_s.get_width()//2, b_rect.centery - q_s.get_height()//2))

            pygame.draw.circle(screen, NEON_PURPLE, (int(tut_char_pos.x), int(tut_char_pos.y - 15)), 8)
            pygame.draw.rect(screen, NEON_PURPLE, (tut_char_pos.x - 8, tut_char_pos.y - 10, 16, 18), border_radius=3)
            aim_angle = tut_pulse * 0.5 if tut_state_timer > 2 else math.atan2(5, 5)
            pygame.draw.line(screen, GOLD, (tut_char_pos.x, tut_char_pos.y - 10), (tut_char_pos.x + math.cos(aim_angle)*18, tut_char_pos.y - 10 + math.sin(aim_angle)*18), 3)

            if tut_state_timer == 3:
                pygame.draw.circle(screen, NEON_CYAN, (int(tut_char_pos.x), int(tut_char_pos.y - 8)), 18, 2)

            if tut_float_timer > 0:
                tut_float_pos.y -= 0.4
                tut_float_timer -= 1
                f_font = pygame.font.SysFont("OCR A Extended", 12, bold=True)
                f_surf = f_font.render(tut_float_text, True, tut_float_color)
                screen.blit(f_surf, (tut_float_pos.x - f_surf.get_width()//2, tut_float_pos.y))

            w_box = pygame.Rect(canvas_rect.x + 30, canvas_rect.bottom - 110, 32, 32)
            a_box = pygame.Rect(canvas_rect.x + 30 - 36, canvas_rect.bottom - 74, 32, 32)
            s_box = pygame.Rect(canvas_rect.x + 30, canvas_rect.bottom - 74, 32, 32)
            d_box = pygame.Rect(canvas_rect.x + 30 + 36, canvas_rect.bottom - 74, 32, 32)
            
            for r, char in [(w_box,"W"), (a_box,"A"), (s_box,"S"), (d_box,"D")]:
                pygame.draw.rect(screen, PANEL_BG, r, border_radius=4)
                pygame.draw.rect(screen, NEON_CYAN, r, 1, border_radius=4)
                txt = fonts["main"].render(char, True, WHITE)
                screen.blit(txt, (r.centerx - txt.get_width()//2, r.y + 8))

            instruct_r = pygame.Rect(canvas_rect.x + 115, canvas_rect.bottom - 106, right_canvas_w - 130, 70)
            render_wrapped_text(screen, "EXECUTE VECTOR MANEUVER PROTOCOLS DYNAMICALLY VIA THE ASSIGNED COMPACT W-A-S-D INTERFACE CHASSIS CONNECTOR KEYS.", fonts["small"], GRAY, instruct_r, line_spacing=1)

            lbl_canvas = fonts["small"].render("// VECTOR TRACKING CORE ENGINE DEMO", True, (0, 180, 220))
            screen.blit(lbl_canvas, (canvas_rect.x + 15, canvas_rect.y + 12))

        elif current_tab == "BATTLE_FIELD":
            p1.max_hp = 1000 + (stats["DEFENSE"] * 50)

            old_p1_pos = p1.get_actual_pos(center_view_x)
            is_rewinding = keys[pygame.K_r] or (btn_rev_rect.collidepoint(m_pos) and pygame.mouse.get_pressed()[0] and touch_vector_pos is None)

            if is_rewinding:
                rewind_pressed_last_frame = True
                if history:
                    snap = history.pop()
                    p1.ratio, p1.hp, p1.is_alive, match_timer = snap[0], snap[1], snap[2], snap[3]
                    p1.has_mystery_control, p1.shield_hp, p1.has_overcharge = snap[8], snap[10], snap[11]
                    
                    enemies.clear()
                    for e_d in snap[4]:
                        e_obj = Fighter(e_d[0], e_d[1], e_d[2], is_ai=e_d[3], name=e_d[4])
                        e_obj.hp, e_obj.is_alive, e_obj.facing_angle = e_d[5], e_d[6], e_d[7]
                        enemies.append(e_obj)
                        
                    bullets = [Bullet(b[0], b[1], b[2], b[3], b[4], base_dmg=b[5]) for b in snap[5]]
                    orbs = [TimeOrb(center_view_x) for _ in snap[6]]
                    for idx, o in enumerate(orbs): o.pos = pygame.Vector2(snap[6][idx][0], snap[6][idx][1])

                    for k, m_data in snap[7].items():
                        active_missions[k]["current"] = m_data["current"]
                        active_missions[k]["done"] = m_data["done"]
                    
                    boxes_spawned_count = snap[9]
                    floating_texts.clear()
            else:
                if winning_character == "":
                    match_timer -= (1.0 / 60.0) * time_scale

                rewind_pressed_last_frame = False
                p1.handle_input(keys, stats["SPEED"], bullets, blocks, center_view_x, touch_target_pos=touch_vector_pos)
                p1.restrict_boundaries()

                if p1.is_alive and winning_character == "":
                    new_p1_pos = p1.get_actual_pos(center_view_x)
                    dist_moved = old_p1_pos.distance_to(new_p1_pos)
                    if "distance_traveled" in active_missions and not active_missions["distance_traveled"]["done"]:
                        active_missions["distance_traveled"]["current"] += dist_moved
                        if active_missions["distance_traveled"]["current"] >= active_missions["distance_traveled"]["target"]:
                            active_missions["distance_traveled"]["current"] = active_missions["distance_traveled"]["target"]
                            active_missions["distance_traveled"]["done"] = True
                            play_sound(1200, 0.3)

                for e in enemies:
                    if e.is_ai: e.execute_ai_logic([p1], bullets, blocks, center_view_x, time_scale, frantic_mode=(match_timer <= 20.0))
                    elif not e.is_ai: e.handle_input(keys, 5, bullets, blocks, center_view_x)
                    e.restrict_boundaries()

                if time_scale > 0 and winning_character == "":
                    orb_spawn_timer += 1
                    if orb_spawn_timer > 150: orbs.append(TimeOrb(center_view_x)); orb_spawn_timer = 0

                    if boxes_spawned_count < 2 and len(active_boxes) == 0:
                        box_spawn_timer += 1
                        if box_spawn_timer > 320:
                            active_boxes.append(MysteryBoxDrop(center_view_x))
                            boxes_spawned_count += 1
                            box_spawn_timer = 0

                    p1_box = p1.get_hitbox(center_view_x)

                    for o in orbs:
                        o.update()
                        if o.active and p1.is_alive and p1_box.collidepoint(o.pos):
                            o.active = False; p1.hp = min(p1.max_hp, p1.hp + 200)
                            match_timer = min(60.0, match_timer + 5.0)
                            play_sound(950, 0.12)

                            if "orbs_collected" in active_missions and not active_missions["orbs_collected"]["done"]:
                                active_missions["orbs_collected"]["current"] += 1
                                if active_missions["orbs_collected"]["current"] >= active_missions["orbs_collected"]["target"]:
                                    active_missions["orbs_collected"]["done"] = True
                                    play_sound(1200, 0.3)

                    orbs = [o for o in orbs if o.active]

                    for box in active_boxes[:]:
                        if p1.is_alive and p1_box.colliderect(box.rect):
                            active_boxes.remove(box)
                            play_sound(1100, 0.25)
                            
                            roll = random.random()
                            p_loc = p1.get_actual_pos(center_view_x)
                            
                            if roll < 0.25:
                                p1.has_mystery_control = True
                                floating_texts.append(FloatingText("AUTO-RAPID UNLOCKED!", p_loc.x, p_loc.y - 65, NEON_PURPLE))
                            elif roll < 0.50:
                                p1.shield_hp = 300
                                floating_texts.append(FloatingText("+300 MATRIX SHIELD!", p_loc.x, p_loc.y - 65, NEON_CYAN))
                            elif roll < 0.75:
                                p1.has_overcharge = True
                                floating_texts.append(FloatingText("OVERCHARGE ATK x3!", p_loc.x, p_loc.y - 65, NEON_AMBER))
                            else:
                                p1.hp = min(p1.max_hp, p1.hp + 350)
                                floating_texts.append(FloatingText("+350 REGEN CORE HEAL!", p_loc.x, p_loc.y - 65, NEON_GREEN))

                    for ft in floating_texts: ft.update()
                    floating_texts = [ft for ft in floating_texts if ft.timer > 0]

                    for b in bullets[:]:
                        b.update(time_scale, center_view_x)
                        hit_obstacle = False
                        for blk in blocks:
                            if blk.rect.collidepoint(b.pos):
                                b.active = False; hit_obstacle = True
                                play_sound(220, 0.03, "noise") 
                                break
                        
                        if hit_obstacle or not b.active:
                            if b in bullets: bullets.remove(b)
                            continue

                        if b.active and p1.is_alive and b.owner_name != p1.name:
                            if p1.get_hitbox(center_view_x).collidepoint(b.pos):
                                b.active = False
                                play_sound(160, 0.04, "noise")
                                
                                if p1.shield_hp > 0:
                                    p1.shield_hp = max(0, p1.shield_hp - b.damage_value)
                                else:
                                    p1.hp = max(0, p1.hp - b.damage_value)
                                    
                                if p1.hp <= 0: p1.is_alive = False
                                if b in bullets: bullets.remove(b)
                                continue

                        for e in enemies:
                            if b.active and e.is_alive and b.owner_name != e.name:
                                if e.get_hitbox(center_view_x).collidepoint(b.pos):
                                    dmg_output = b.damage_value
                                    e.hp = max(0, e.hp - dmg_output)
                                    b.active = False
                                    play_sound(160, 0.04, "noise")
                                    if e.hp <= 0: e.is_alive = False

                                    if b.owner_name == p1.name:
                                        if "laser_hits" in active_missions and not active_missions["laser_hits"]["done"]:
                                            active_missions["laser_hits"]["current"] += 1
                                            if active_missions["laser_hits"]["current"] >= active_missions["laser_hits"]["target"]:
                                                active_missions["laser_hits"]["done"] = True
                                                play_sound(1200, 0.3)

                                        if "damage_inflicted" in active_missions and not active_missions["damage_inflicted"]["done"]:
                                            active_missions["damage_inflicted"]["current"] += dmg_output
                                            if active_missions["damage_inflicted"]["current"] >= active_missions["damage_inflicted"]["target"]:
                                                active_missions["damage_inflicted"]["current"] = active_missions["damage_inflicted"]["target"]
                                                active_missions["damage_inflicted"]["done"] = True
                                                play_sound(1200, 0.3)
                                    
                                    if b in bullets: bullets.remove(b)
                                    break

                    bullets = [b for b in bullets if b.active]

                    if p1.is_alive:
                        e_sn = [(e.ratio.x, e.ratio.y, e.color, e.is_ai, e.name, e.hp, e.is_alive, e.facing_angle) for e in enemies]
                        b_sn = [(b.pos.x, b.pos.y, b.angle, b.color, b.owner_name, b.damage_value) for b in bullets]
                        o_sn = [(o.pos.x, o.pos.y) for o in orbs]
                        m_sn = {k: {"current": v["current"], "done": v["done"]} for k, v in active_missions.items()}
                        
                        history.append((pygame.Vector2(p1.ratio), p1.hp, p1.is_alive, match_timer, e_sn, b_sn, o_sn, m_sn, p1.has_mystery_control, boxes_spawned_count, p1.shield_hp, p1.has_overcharge))
                        if len(history) > 400: history.pop(0)

            for j in range(int(HEIGHT*0.25), HEIGHT - 40, int(HEIGHT*0.065)):
                pygame.draw.line(screen, (0, 32, 45), (center_view_x, j), (WIDTH, j), 1)

            for blk in blocks: blk.draw(screen)
            for o in orbs: o.draw(screen)
            for box in active_boxes: box.draw(screen)
            
            p1.draw(screen, center_view_x)
            for e in enemies: e.draw(screen, center_view_x)
            for b in bullets: b.draw(screen)
            for ft in floating_texts: ft.draw(screen)

            if match_timer <= 20.0 and winning_character == "":
                glow_val = int(abs(math.sin(pygame.time.get_ticks() / 150)) * 3) + 1
                pygame.draw.rect(screen, NEON_RED, (center_view_x, 60, WIDTH - center_view_x, HEIGHT - 60), glow_val)

            t_col = NEON_GREEN if match_timer > 20 else NEON_RED
            disp_time = max(0, int(match_timer))
            screen.blit(fonts["title"].render(f"TIMER: {disp_time}s", True, t_col), (center_view_x + 30, header_h + 20))
            
            status_str = "BUFF STATUS: NORMAL UNARMED"
            status_col = GRAY
            if p1.has_overcharge: status_str = "BUFF STATUS: OVERCHARGE ATK (x3)"; status_col = NEON_AMBER
            elif p1.shield_hp > 0: status_str = f"BUFF STATUS: SHIELD BARRIER [{p1.shield_hp}HP]"; status_col = NEON_CYAN
            elif p1.has_mystery_control: status_str = "BUFF STATUS: AUTOMATIC RAPID FIRE"; status_col = NEON_PURPLE
            screen.blit(fonts["small"].render(status_str, True, status_col), (center_view_x + 210, header_h + 25))

            y_g = header_h + 55
            pygame.draw.rect(screen, (24, 24, 48), (center_view_x + 30, y_g, 130, 8))
            if p1.max_hp > 0:
                pygame.draw.rect(screen, p1_color, (center_view_x + 30, y_g, int(130 * (p1.hp/p1.max_hp)), 8))
            screen.blit(fonts["small"].render(f"{p1_name}: {int(p1.hp)}HP", True, WHITE), (center_view_x + 30, y_g + 12))

            for idx, e in enumerate(enemies):
                if not e.is_alive: continue
                x_g = WIDTH - 150 - (idx * 160)
                pygame.draw.rect(screen, (24, 24, 48), (x_g, y_g, 130, 8))
                pygame.draw.rect(screen, e.color, (x_g, y_g, int(130 * (e.hp/1200)), 8))
                screen.blit(fonts["small"].render(f"{e.name}: {int(e.hp)}HP", True, WHITE), (x_g, y_g + 12))

            all_enemies_dead = all(not e.is_alive for e in enemies)
            all_missions_clear = all(m["done"] for m in active_missions.values())

            if winning_character == "":
                if not p1.is_alive:
                    winning_character = "DEFEAT"
                    defeat_reason = "CHASSIS CRITICALLY DESTROYED BY HOSTILE FORCES"
                elif all_enemies_dead or match_timer <= 0:
                    if all_missions_clear and p1.is_alive:
                        winning_character = "VICTORY"
                    else:
                        winning_character = "DEFEAT"
                        defeat_reason = "TACTICAL RECOVERY MATRIX ERROR"

            if winning_character != "":
                banner = pygame.Surface((WIDTH - center_view_x, 125)); banner.fill((5, 5, 12))
                screen.blit(banner, (center_view_x, int(HEIGHT * 0.38)))
                
                if winning_character == "VICTORY":
                    win_text = f"'{p1_name}' WON : SIMULATION SUCCESSFUL"
                    sub_text = "You successfully navigated constraints and cleared the board!"
                    border_c = NEON_GREEN
                    text_c = GOLD
                else:
                    win_text = f"'{p1_name}' LOST : {defeat_reason}"
                    sub_text = "All side metrics must be resolved before executing core terminations."
                    border_c = NEON_RED
                    text_c = NEON_RED
                    
                pygame.draw.rect(screen, border_c, (center_view_x, int(HEIGHT * 0.38), WIDTH - center_view_x, 125), 2)
                screen.blit(fonts["title"].render(win_text.upper(), True, text_c), (center_view_x + 25, int(HEIGHT * 0.42)))
                screen.blit(fonts["small"].render(sub_text, True, WHITE), (center_view_x + 25, int(HEIGHT * 0.51)))

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