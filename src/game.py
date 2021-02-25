import pygame
from pygame.image import load_extended
import ticks
import gui
import yaml
import math
import languages

_font: pygame.font.Font


def init():
    global _font
    _font = pygame.font.Font("res/font/JetBrainsMono-Bold.ttf", 20)


def draw_text(screen: pygame.Surface, rect: pygame.Rect, data: str, colour):
    font_surface = _font.render(data, True, colour)
    screen.blit(font_surface, rect)


class SlicedSprite:
    def __init__(self, image: pygame.Surface, corner_size: int = 32):
        self.image = image
        self.corner = corner_size
        self.size = image.get_size()

    def draw(self, screen: pygame.Surface, rect: pygame.Rect, sizes: tuple):
        # Top left
        screen.blit(
            self.image, rect,
            pygame.Rect(0, 0, self.corner, self.corner)
        )
        # Top
        top = pygame.transform.scale(
            self.image.subsurface(
                pygame.Rect(
                    self.corner, 0, self.size[0] - 2 * self.corner, self.corner
                )
            ).copy(),
            (sizes[0], self.corner)
        )
        screen.blit(top, (rect.x + self.corner, rect.y))
        # Top right
        screen.blit(
            self.image, (rect.x + sizes[0] + self.corner, rect.y),
            pygame.Rect(self.size[0] - self.corner, 0, self.corner, self.corner)
        )
        # Left
        left = pygame.transform.scale(
            self.image.subsurface(
                pygame.Rect(
                    0, self.corner, self.corner, self.size[1] - 2 * self.corner
                )
            ).copy(),
            (self.corner, sizes[1])
        )
        screen.blit(left, (rect.x, rect.y + self.corner))
        # Centre
        centre = pygame.transform.scale(
            self.image.subsurface(
                pygame.Rect(
                    self.corner, self.corner, self.size[0] - 2 * self.corner, self.size[1] - 2 * self.corner
                )
            ).copy(),
            (sizes[0], sizes[1])
        )
        screen.blit(centre, (rect.x + self.corner, rect.y + self.corner))
        # Right
        right = pygame.transform.scale(
            self.image.subsurface(
                pygame.Rect(
                    self.size[0] - self.corner, self.corner, self.corner, self.size[1] - 2 * self.corner
                )
            ).copy(),
            (self.corner, sizes[1])
        )
        screen.blit(right, (rect.x + sizes[0] + self.corner, rect.y + self.corner))
        # Bottom left
        screen.blit(
            self.image, (rect.x, rect.y + sizes[1] + self.corner),
            pygame.Rect(0, self.size[1] - self.corner, self.corner, self.corner)
        )
        # Bottom
        bottom = pygame.transform.scale(
            self.image.subsurface(
                pygame.Rect(
                    self.corner, self.size[1] - self.corner, self.size[0] - 2 * self.corner, self.corner
                )
            ).copy(),
            (sizes[0], self.corner)
        )
        screen.blit(bottom, (rect.x + self.corner, rect.y + sizes[1] + self.corner))
        # Bottom right
        screen.blit(
            self.image, (rect.x + sizes[0] + self.corner, rect.y + sizes[1] + self.corner),
            pygame.Rect(self.size[0] - self.corner, self.size[1] - self.corner, self.corner, self.corner)
        )


texture_atlas: pygame.Surface = load_extended("res/textures/atlas.png")
texture_res = 32
robot_atlas: pygame.Surface = load_extended("res/textures/robot.png")
robot_res = 64
robot_ground = 48

# Each sprite uses a different dark colour against white bold text, and
# two adjacent sprites have very distinct colours. This was made with
# colour blindness in mind, to help create greater contrast between the
# code blocks.
code_block_textures: list = [
    SlicedSprite(load_extended("res/textures/blocks/block_red.png")),
    SlicedSprite(load_extended("res/textures/blocks/block_blue.png")),
    SlicedSprite(load_extended("res/textures/blocks/block_yellow.png")),
    SlicedSprite(load_extended("res/textures/blocks/block_green.png")),
    SlicedSprite(load_extended("res/textures/blocks/block_orange.png")),
    SlicedSprite(load_extended("res/textures/blocks/block_pink.png")),
]


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
        # Blocks
        self.blocks = []
        # UI interactions
        self.block_dragged = None
        self.click_start = -1
        self.click_start_pos = None
        self.click_type = 0
        # 3D angles
        self.yaw = math.pi / 4
        self.pitch = math.pi / 6
        self.zoom = 1
        self.old_view = (0, 0)
        # UI integrations
        self.elem = None
        self.level = None
        self.enabled = False
        # Game
        self.robot_x = 0
        self.robot_y = -1

    def enable(self, document: gui.DocumentXML, level: Level):
        self.elem = document.ids["game"]
        self.level = level
        self.enabled = True
        lvl_size = max(self.level.width, self.level.height) * texture_res
        self.zoom = min(self.elem.rect.w / 2, self.elem.rect.h / 2) / lvl_size

        btnlist: gui.Element = document.ids["blocklist"]
        btnlist.children.clear()
        self.blocks = []
        for i, b in enumerate(level.blocks):
            self.blocks.append(Blocklist(document, b, i))

    def disable(self):
        self.elem = None
        self.level = None
        self.enabled = False
        self.blocks = []

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
            else:
                for b in self.blocks:
                    b: Blocklist
                    b.block.get_box()
        elif event.type == pygame.MOUSEBUTTONUP:
            # click_duration = ticks.get_time() - self.click_start
            self.click_type = 0
            self.click_start = -1
            # print(click_duration)
        elif event.type == pygame.VIDEORESIZE:
            lvl_size = max(self.level.width, self.level.height) * texture_res
            self.zoom = min(self.elem.rect.w / 2, self.elem.rect.h / 2) / lvl_size

    def update(self):
        mpos = pygame.mouse.get_pos()
        if self.click_start > -1:
            if self.click_type == 1:
                # print("Dragging")
                n_yaw = (mpos[0] - self.click_start_pos[0]) / 100 + self.old_view[0]
                n_pitch = (mpos[1] - self.click_start_pos[1]) / 400 + self.old_view[1]
                self.update_position(n_yaw, n_pitch, None)

    def update_position(self, yaw=None, pitch=None, zoom=None):
        if yaw:
            self.yaw = yaw
        if pitch:
            self.pitch = min(max(pitch, math.pi / 6), math.pi / 4)
        if zoom:
            self.zoom = zoom

    def draw(self, screen: pygame.Surface):
        if not self.enabled:
            return
        self.render_scene(screen)
        for b in self.blocks:
            b: Blocklist
            b.draw(screen)

    def render_scene(self, screen: pygame.Surface):
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


# Source of blocks, from which they spawn and get dragged out of
class Blocklist:
    def __init__(self, document: gui.DocumentXML, block_name: str, colour: int = 0):
        btnlist: gui.Element = document.ids["blocklist"]
        self.elem = gui.Space(document, "space", {})
        btnlist.add_child(self.elem)
        self.name = block_name
        self.colour = colour
        self.block = Codeblock(code_block_textures[colour], block_name, pygame.Rect(0, 0, 0, 0))

    def draw(self, screen: pygame.Surface):
        self.block.pos = self.elem.rect
        self.block.draw(screen)


class Codeblock:
    def __init__(self, sprite: SlicedSprite, name: str, pos: pygame.Rect):
        self.sprite = sprite
        self.name = name
        self.pos = pos

    def draw(self, screen: pygame.Surface):
        text = languages.get_str("level.blocks." + self.name)
        size = _font.size(text)
        self.sprite.draw(screen, self.pos, size)
        draw_text(
            screen,
            pygame.Rect(self.pos.x + self.sprite.corner, self.pos.y + self.sprite.corner, 0, 0),
            text,
            0xFFFFFFFF
            # 0x000000FF
        )

    def get_box(self) -> pygame.Rect:
        size = _font.size(languages.get_str("level.blocks." + self.name))
        return pygame.Rect(
            self.pos.x,
            self.pos.y,
            size[0] + self.sprite.corner * 2,
            size[1] + self.sprite.corner * 2
        )
