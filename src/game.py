import pygame
from pygame.image import load_extended
import ticks
import gui
import yaml
import math

texture_atlas: pygame.Surface = load_extended("res/textures/atlas.png")
texture_res = 32
robot_atlas: pygame.Surface = load_extended("res/textures/robot.png")
robot_res = 64
robot_ground = 48


class Level:
    def __init__(self, filename: str):
        text: str
        with open(filename, encoding='utf-8') as file:
            text = file.read()
        data = yaml.safe_load(text)
        # Available blocks
        self.blocks = data["blocks"]
        # Map data
        self.map = data["map"]
        # Map surface
        self.height = len(self.map)
        self.width = 0
        if self.height > 0:
            for row in self.map:
                if len(row) != len(self.map[0]):
                    raise ValueError("Invalid map, inconsistent row lengths.")
            self.width = len(self.map[0])
        self.level_map = pygame.Surface((self.width * texture_res, self.height * texture_res), pygame.SRCALPHA)

        for i in range(self.height):
            for j in range(self.width):
                tile = self.map[i][j]
                area = pygame.Rect(tile * texture_res, 0, texture_res, texture_res)
                dest = (j * texture_res, i * texture_res)
                self.level_map.blit(texture_atlas, dest, area)


class Game:
    def __init__(self):
        # UI interactions
        self.block_dragged = None
        self.click_start = -1
        self.click_start_pos = None
        self.click_type = 0
        self.old_view = (0, 0)
        # 3D angles
        self.yaw = math.pi / 4
        self.pitch = math.pi / 6
        self.zoom = 1
        # UI integrations
        self.elem = None
        self.level = None
        self.enabled = False
        # Game
        self.robot_x = 0
        self.robot_y = -1

    def enable(self, elem: gui.Element, level: Level):
        self.elem = elem
        self.level = level
        self.enabled = True
        lvl_size = max(self.level.width, self.level.height) * texture_res
        self.zoom = min(self.elem.rect.w / 2, self.elem.rect.h / 2) / lvl_size

    def disable(self):
        self.elem = None
        self.level = None
        self.enabled = False

    def handle_event(self, _: pygame.Surface, event: pygame.event.Event):
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.click_start = ticks.get_time()
            mpos = pygame.mouse.get_pos()
            self.click_start_pos = mpos
            if self.elem.rect.collidepoint(mpos):
                self.click_type = 1  # drag/pan
                self.old_view = (self.yaw, self.pitch)
        elif event.type == pygame.MOUSEBUTTONUP:
            click_duration = ticks.get_time() - self.click_start
            self.click_type = 0
            self.click_start = -1
            print(click_duration)
        elif event.type == pygame.VIDEORESIZE:
            lvl_size = max(self.level.width, self.level.height) * texture_res
            self.zoom = min(self.elem.rect.w / 2, self.elem.rect.h / 2) / lvl_size

    def update(self):
        mpos = pygame.mouse.get_pos()
        if self.click_start > -1:
            if self.click_type == 1:
                # print("Dragging")
                n_yaw = (mpos[0] - self.click_start_pos[0]) / 100 + self.old_view[0]
                n_pitch = (mpos[1] - self.click_start_pos[1]) / 100 + self.old_view[1]
                self.update_position(n_yaw, n_pitch, None)

    def update_position(self, yaw=None, pitch=None, zoom=None):
        if yaw:
            self.yaw = yaw
        if pitch:
            self.pitch = min(max(pitch, math.pi / 6), math.pi / 3)
        if zoom:
            self.zoom = zoom

    def render(self, screen: pygame.Surface):
        if not self.enabled:
            return
        # Transform axis vectors
        x_axis = pygame.math.Vector2(texture_res * self.zoom, 0)
        y_axis = pygame.math.Vector2(0, texture_res * self.zoom)
        x_axis = x_axis.rotate(math.degrees(-self.yaw))
        y_axis = y_axis.rotate(math.degrees(-self.yaw))
        x_axis.y *= math.sin(self.pitch)
        y_axis.y *= math.sin(self.pitch)
        # Transform rendered map
        map_render = pygame.transform.rotozoom(self.level.level_map, math.degrees(self.yaw), self.zoom)
        map_render = pygame.transform.scale(
            map_render,
            (int(map_render.get_width()),
             int(map_render.get_height() * math.sin(self.pitch)))
        )
        pos_x = self.elem.rect.x + (self.elem.rect.w / 2)
        pos_y = self.elem.rect.y + (self.elem.rect.h / 2)
        # Scale robot sprite
        robot_pos = x_axis * self.robot_x + y_axis * self.robot_y + pygame.math.Vector2(pos_x, pos_y)
        angle = ((self.yaw + math.pi * 9 / 8) % (math.pi * 2)) * 8 / (math.pi * 2)
        bot_render = pygame.Surface((robot_res, robot_res), pygame.SRCALPHA)
        bot_render.blit(
            robot_atlas,
            (0, 0),
            pygame.Rect(int(angle) * robot_res, 0, robot_res, robot_res)
        )
        bot_render = pygame.transform.rotozoom(bot_render, 0, self.zoom / 2)
        # Rendering
        screen.blit(map_render, (pos_x - map_render.get_width() / 2, pos_y - map_render.get_height() / 2))
        screen.blit(
            bot_render,
            (robot_pos.x - (robot_res * self.zoom) / 4, robot_pos.y - (robot_ground * self.zoom) / 2)
        )


class Blocklist:
    def __init__(self):
        pass

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            print("click! " + self.__str__())


class Codeblock:
    pass
