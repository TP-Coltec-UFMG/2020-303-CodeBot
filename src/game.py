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
    _font = pygame.font.Font("res/font/JetBrainsMono-Bold.ttf", 25)


def draw_text(screen: pygame.Surface, rect: pygame.Rect, data: str, colour):
    font_surface = _font.render(data, True, colour)
    screen.blit(font_surface, rect)


def fill_rect(screen: pygame.Surface, rect: pygame.Rect, colour):
    c = pygame.Color(colour)
    s = pygame.Surface(rect.size)  # the size of your rect
    s.set_alpha(c.a)  # alpha level
    s.fill(c)  # this fills the entire surface
    screen.blit(s, rect.topleft)


class SlicedSprite:
    def __init__(self, image: pygame.Surface, corner_size: int = 16):
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
click_threshold = 150
step_delay = 500

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

        player = data["player"]
        self.start_x = player["start-x"]
        self.start_y = player["start-y"]
        self.start_dir = player["start-dir"]

        for i in range(self.height):
            for j in range(self.width):
                tile = self.map[i][j]
                area = pygame.Rect(tile * texture_res, 0, texture_res, texture_res)
                dest = (j * texture_res, i * texture_res)
                self.level_map.blit(texture_atlas, dest, area)

    def get_block(self, x: int, y: int) -> int:
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return 0
        return self.map[y][x]


class Game:
    def __init__(self):
        # Code
        self.code = None
        self.gen = None
        self.steps = 1
        self.code_start = 0
        # Blocks (source)
        self.blocks = []
        # UI interactions
        self.block_dragged = None
        self.block_offset = (0, 0)
        self.click_start = -1
        self.click_start_pos = None
        self.click_type = 0  # 1 = pan, 2 = drag block
        # 3D angles
        self.yaw = math.pi / 4
        self.pitch = math.pi / 6
        self.zoom = 1
        self.old_view = (0, 0)  # (yaw, pitch)
        # UI integrations
        self.elem = None  # Container for rendering game scene
        self.level = None  # Current level object
        self.enabled = False  # false = in title screen
        # Game
        self.robot_x = 0
        self.robot_y = 0
        self.robot_dir = 0

    def enable(self, document: gui.DocumentXML, level: Level, screen: pygame.Surface):
        self.elem = document.ids["game"]
        self.level = level
        self.enabled = True
        lvl_size = max(self.level.width, self.level.height) * texture_res

        self.zoom = min(self.elem.rect.w / 2, self.elem.rect.h / 2) / lvl_size
        self.yaw = math.pi / 4
        self.pitch = math.pi / 6

        self.code = Code(document)

        self.robot_x = level.start_x
        self.robot_y = level.start_y
        self.robot_dir = level.start_dir

        btnlist: gui.Element = document.ids["blocklist"]
        btnlist.children.clear()
        self.blocks = []
        for i, b in enumerate(level.blocks):
            blocklist = Blocklist(document, b, i)
            self.blocks.append(blocklist)
        document.calc_draw(screen.get_clip())
        for b in self.blocks:
            b.update()
        document.calc_draw(screen.get_clip())
        document.hover_element = document.trace_element(pygame.mouse.get_pos())

    def disable(self):
        self.elem = None
        self.level = None
        self.enabled = False
        self.blocks = []

    def handle_event(self, _: pygame.Surface, event: pygame.event.Event):
        if not self.enabled:
            return
        mpos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click_start = ticks.get_time()
            self.click_start_pos = mpos
            if self.elem.rect.collidepoint(mpos):
                self.click_type = 1  # drag/pan
                self.old_view = (self.yaw, self.pitch)
            else:
                for b in self.blocks:
                    b: Blocklist
                    if b.block.get_box().collidepoint(mpos):
                        self.click_type = 2
                        self.block_dragged = b.get_new_block(pygame.Rect(mpos[0], mpos[1], 0, 0))
                        self.block_offset = (mpos[0] - b.block.pos.x, mpos[1] - b.block.pos.y)
                        break
                else:
                    for i, b in enumerate(self.code.blocks):
                        b: Codeblock
                        rect: pygame.Rect = self.code.elem.rect
                        if b.get_box(rect.topleft).collidepoint(mpos):
                            self.click_type = 3
                            self.block_dragged = b
                            self.block_offset = (mpos[0] - b.pos.x - rect.x, mpos[1] - b.pos.y - rect.y)
                            self.code.remove_block(i)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            click_duration = ticks.get_time() - self.click_start
            if self.click_type == 2:
                if self.code.elem.rect.collidepoint(mpos):
                    print("Block placed")
                    self.code.place_block(self.block_dragged)
                if click_duration < click_threshold:
                    print("Clicked")
                    self.code.place_block(self.block_dragged)
                    # self.move_bot(self.block_dragged.name)
                else:
                    print(f"Dropped ({click_duration})")
            elif self.click_type == 3:
                if self.code.elem.rect.collidepoint(mpos):
                    print("Block placed")
                    self.code.place_block(self.block_dragged)
                print(f"Dropped ({click_duration})")
            self.click_type = 0
            self.click_start = -1
        elif event.type == pygame.VIDEORESIZE:
            lvl_size = max(self.level.width, self.level.height) * texture_res
            self.zoom = min(self.elem.rect.w / 2, self.elem.rect.h / 2) / lvl_size

    def update(self):
        if not self.enabled:
            return
        mpos = pygame.mouse.get_pos()
        now = ticks.get_time()
        for b in self.blocks:
            b.update()
        self.code.update()
        if self.gen is not None:
            if self.steps * step_delay < now - self.code_start:
                try:
                    move = next(self.gen)
                    self.move_bot(move)
                    self.steps += 1
                except StopIteration:
                    self.gen = None

        if self.click_start > -1:
            click_duration = ticks.get_time() - self.click_start
            if self.click_type == 1:
                # print("Dragging")
                n_yaw = (mpos[0] - self.click_start_pos[0]) / 100 + self.old_view[0]
                n_pitch = (mpos[1] - self.click_start_pos[1]) / 400 + self.old_view[1]
                self.update_position(n_yaw, n_pitch, None)
            elif self.click_type == 2:
                if click_duration >= click_threshold:
                    self.block_dragged: Codeblock
                    self.block_dragged.pos = pygame.Rect(
                        mpos[0] - self.block_offset[0],
                        mpos[1] - self.block_offset[1],
                        0, 0
                    )
                    if self.code.elem.rect.collidepoint(mpos):
                        self.code.cursor_closest(mpos)
            elif self.click_type == 3:
                self.block_dragged: Codeblock
                self.block_dragged.pos = pygame.Rect(
                    mpos[0] - self.block_offset[0],
                    mpos[1] - self.block_offset[1],
                    0, 0
                )
                if self.code.elem.rect.collidepoint(mpos):
                    self.code.cursor_closest(mpos)

    def update_position(self, yaw=None, pitch=None, zoom=None):
        if yaw:
            self.yaw = yaw
        if pitch:
            self.pitch = min(max(pitch, math.pi / 6), math.pi / 4)
        if zoom:
            self.zoom = zoom

    def run_code(self):
        self.code_start = ticks.get_time()
        self.gen = self.code.exec()
        self.steps = 1

        self.robot_x = self.level.start_x
        self.robot_y = self.level.start_y
        self.robot_dir = self.level.start_dir

    def move_bot(self, move):
        old_pos = self.robot_x, self.robot_y
        if move == "forward":
            pos_offset = (
                (0, -1),
                (-1, 0),
                (0, 1),
                (1, 0),
            )[self.robot_dir]
            self.robot_x += pos_offset[0]
            self.robot_y += pos_offset[1]
        elif move == "left":
            self.robot_dir = (self.robot_dir + 1) % 4
        elif move == "right":
            self.robot_dir = (self.robot_dir - 1) % 4

        block = self.level.get_block(self.robot_x, self.robot_y)
        if block == 0:
            self.robot_x, self.robot_y = old_pos
        elif block == 1:
            print("Died!")
            self.gen = None
        elif block == 3:
            print("Win!")

    def draw(self, screen: pygame.Surface):
        if not self.enabled:
            return
        self.code.render(screen)
        self.render_scene(screen)
        for b in self.blocks:
            b: Blocklist
            b.draw(screen)
        if self.click_start > -1:
            # mpos = pygame.mouse.get_pos()
            click_duration = ticks.get_time() - self.click_start
            if self.click_type == 2:
                if click_duration >= click_threshold:
                    self.block_dragged: Codeblock
                    self.block_dragged.draw(screen)
            elif self.click_type == 3:
                self.block_dragged: Codeblock
                self.block_dragged.draw(screen)

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
        robot_pos_real = (self.robot_x - self.level.width / 2 + .5, self.robot_y - self.level.height / 2 + .5)
        robot_pos = x_axis * robot_pos_real[0] + y_axis * robot_pos_real[1] + pygame.math.Vector2(pos_x, pos_y)
        angle = ((self.yaw + self.robot_dir * math.pi / 2 + math.pi * 9 / 8) % (math.pi * 2)) * 8 / (math.pi * 2)
        bot_render = robot_atlas.subsurface(
            pygame.Rect(
                int(angle) * robot_res,
                0,
                robot_res,
                robot_res
            )
        ).copy()
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
        self.elem = gui.Space(document, "space", {"margin": "10px"})
        btnlist.add_child(self.elem)
        self.name = block_name
        self.colour = colour
        self.block = Codeblock(code_block_textures[colour], block_name, pygame.Rect(0, 0, 0, 0))

    def get_new_block(self, rect: pygame.Rect):
        return Codeblock(code_block_textures[self.colour], self.name, rect)

    def update(self):
        self.block.pos = self.elem.rect
        self.elem.length = f"{self.block.get_box().w}px"

    def draw(self, screen: pygame.Surface):
        self.block.draw(screen)


class Codeblock:
    def __init__(self, sprite: SlicedSprite, name: str, pos: pygame.Rect):
        self.sprite = sprite
        self.name = name
        self.pos = pos
        self.children = []

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

    def get_box(self, off: tuple = (0, 0)) -> pygame.Rect:
        size = _font.size(languages.get_str("level.blocks." + self.name))
        return pygame.Rect(
            self.pos.x + off[0],
            self.pos.y + off[1],
            size[0] + self.sprite.corner * 2,
            size[1] + self.sprite.corner * 2
        )


class Code:
    def __init__(self, document: gui.DocumentXML):
        self.elem: gui.Element = document.ids["code"]
        self.blocks = []
        self.cursors = []  # For nested blocks
        self.cursor = 0

    def place_block(self, block: Codeblock):
        context = self.blocks
        for c in self.cursors:
            context = context[c].children
        self.blocks.insert(self.cursor, block)
        self.cursor += 1

    def remove_block(self, index: int):
        if index < self.cursor:
            self.cursor -= 1
        self.blocks.pop(index)

    def cursor_closest(self, pos: tuple):
        vpos = pygame.Vector2(pos)
        closest = 0
        closest_dis = None
        print(" == CLOSEST ==")
        for i, b in enumerate(self.blocks):
            b: Codeblock
            block_pos = (b.pos.x + self.elem.rect.x, b.pos.y + self.elem.rect.y)
            # fill_rect(
            #     pygame.display.get_surface(),
            #     pygame.Rect(b.pos.x - self.elem.rect.x, b.pos.y - self.elem.rect.y, 10, 10),
            #     0xFF0000FF
            # )
            this_dis = pygame.Vector2(block_pos).distance_squared_to(vpos)
            if closest_dis is None or this_dis < closest_dis:
                closest = i
                closest_dis = this_dis
            print(f"block[{i}].dis = {this_dis}")
        if len(self.blocks) > 0:
            last_b = self.blocks[-1]
            block_pos = (last_b.pos.x + self.elem.rect.x, last_b.pos.y + self.elem.rect.y + last_b.get_box().h)
            last_dis = pygame.Vector2(block_pos).distance_squared_to(vpos)
            if last_dis < closest_dis:
                closest = len(self.blocks)
                # closest_dis = last_dis

        self.set_cursor([closest])
        print(f"closest = {closest}")
        return closest

    def update(self):
        current_y = 0
        for i, b in enumerate(self.blocks):
            b: Codeblock
            if i == self.cursor:
                current_y += 10
            b.pos = pygame.Rect(0, current_y, 0, 0)
            current_y += b.get_box().h

    def set_cursor(self, path: list):
        self.cursors = path[:-1]
        self.cursor = path[-1]
        self.update()

    def render(self, screen: pygame.Surface):
        dest = screen.subsurface(self.elem.rect)
        current_y = 0
        for i, b in enumerate(self.blocks):
            b: Codeblock
            b.draw(dest)
            if i == self.cursor:
                fill_rect(dest, pygame.Rect(0, current_y, 1000, 10), 0xFFFFFF3F)
                current_y += 10
            current_y += b.get_box().h
        if self.cursor == len(self.blocks):
            fill_rect(dest, pygame.Rect(0, current_y, 1000, 10), 0xFFFFFF3F)
        pass

    def exec(self):
        for b in self.blocks:
            b: Codeblock
            yield b.name

    # def reset(self):
    #     pass
    #
    # def step(self):
    #     pass
