import pygame
from pygame.image import load_extended
import ticks
import gui
import yaml
import math
import languages

_font_code: pygame.font.Font
_font_victory: pygame.font.Font


def init():
    global _font_code, _font_victory
    _font_code = pygame.font.Font("res/font/JetBrainsMono-Bold.ttf", 25)
    _font_victory = pygame.font.Font("res/font/JetBrainsMono-Bold.ttf", 60)


def draw_text(screen: pygame.Surface, rect: pygame.Rect, data: str, colour, font: pygame.font.Font):
    font_surface = font.render(data, True, colour)
    screen.blit(font_surface, rect)


def fill_rect(screen: pygame.Surface, rect: pygame.Rect, colour):
    c = pygame.Color(colour)
    s = pygame.Surface(rect.size)  # the size of your rect
    s.set_alpha(c.a)  # alpha level
    s.fill(c)  # this fills the entire surface
    screen.blit(s, rect.topleft)


class SlicedSprite:
    def __init__(self, image: pygame.Surface, corner_size: int = 32):
        self.image = image
        self.corner = corner_size
        self.size = image.get_size()

    def draw(self, screen: pygame.Surface, rect: pygame.Rect, sizes: tuple, gap: int = 0):
        sizes = (max(sizes[0], 0), max(sizes[1], 1))
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
        if gap == 0:
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
        else:
            # Centre
            centre = pygame.transform.scale(
                self.image.subsurface(
                    pygame.Rect(
                        self.corner, self.corner, self.size[0] - 2 * self.corner, self.size[1] - 2 * self.corner
                    )
                ).copy(),
                (sizes[0], sizes[1] - gap)
            )
            screen.blit(centre, (rect.x + self.corner, rect.y + self.corner))
            # Right
            right = pygame.transform.scale(
                self.image.subsurface(
                    pygame.Rect(
                        self.size[0] - self.corner, self.corner, self.corner, self.size[1] - 2 * self.corner
                    )
                ).copy(),
                (self.corner, sizes[1] - gap)
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
coin_atlas: pygame.Surface = load_extended("res/textures/coin.png")
entity_res = 64
entity_ground = 48
click_threshold = 150
step_delay = 200
cursor_h = 16
win_rot_speed = 0.03

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

# container_block_textures: list = [
#     SlicedSprite(load_extended("res/textures/blocks/block_red.png")),
# ]


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

        stars = data["stars"]
        self.min_coins = stars["coins"]
        self.min_blocks = stars["blocks"]

        # Level number
        self.number = data["number"]

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
        self.coins = []
        # Game
        self.robot_x = 0
        self.robot_y = 0
        self.robot_dir = 0
        # Levels
        self.won = False
        self.coin_counter = 0
        # Level stats
        self.unlocked_level = 1
        self.levels = []

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

        self.coins = []
        for i, row in enumerate(self.level.map):
            for j, col in enumerate(row):
                if col == 4:
                    self.coins.append((j, i))

        for i, b in enumerate(level.blocks):
            block = defined_blocks[b]
            self.blocks.append(Blocklist(document, *block))
        document.calc_draw(screen.get_clip())
        for b in self.blocks:
            b.update()
        document.calc_draw(screen.get_clip())
        document.hover_element = document.trace_element(pygame.mouse.get_pos())

    def disable(self):
        self.elem = None
        self.level = None
        self.enabled = False
        self.won = False
        self.gen = None
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
                    ret = self.code.trace_block(mpos)
                    rect: pygame.Rect = self.code.elem.rect
                    if ret is not None:
                        self.click_type = 3
                        self.block_dragged = ret[1]
                        self.block_offset = (mpos[0] - ret[1].pos.x - rect.x, mpos[1] - ret[1].pos.y - rect.y)
                        self.code.remove_block(ret[0])

                    # for i, b in enumerate(self.code.blocks):
                    #     b: Codeblock
                    #     rect: pygame.Rect = self.code.elem.rect
                    #     if b.get_box(rect.topleft).collidepoint(mpos):
                    #         self.click_type = 3
                    #         self.block_dragged = b
                    #         self.block_offset = (mpos[0] - b.pos.x - rect.x, mpos[1] - b.pos.y - rect.y)
                    #         self.code.remove_block(i)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            click_duration = ticks.get_time() - self.click_start
            if self.click_type == 2:
                if self.code.elem.rect.collidepoint(mpos):
                    print("Block placed")
                    self.code.place_block(self.block_dragged)
                elif click_duration < click_threshold:
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

    def win(self):
        self.unlocked_level = max(self.unlocked_level, self.level.number + 1)
        self.gen = None
        self.won = True

        level_stats = (
            True,
            self.code.get_block_count() <= self.level.min_blocks,
            self.coin_counter >= self.level.min_coins
        ).count(True)
        level_idx = self.level.number - 1
        if level_idx < len(self.levels):
            self.levels[level_idx] = max(level_stats, self.levels[level_idx])
        elif level_idx == len(self.levels):
            self.levels.append(level_stats)

        print(f"{self.code.get_block_count()} <> {self.level.min_blocks}")
        print(f"{self.coin_counter} <> {self.level.min_coins}")

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
        if self.won:
            self.update_position(self.yaw + win_rot_speed)
        if self.click_start > -1:
            click_duration = ticks.get_time() - self.click_start
            if self.click_type == 1:
                # print("Dragging")
                n_yaw = (mpos[0] - self.click_start_pos[0]) / 100 + self.old_view[0]
                n_pitch = (mpos[1] - self.click_start_pos[1]) / 400 + self.old_view[1]
                self.update_position(n_yaw, n_pitch, None)
                self.won = False
            elif self.click_type == 2:
                if click_duration >= click_threshold:
                    self.block_dragged: Codeblock
                    self.block_dragged.pos = pygame.Rect(
                        mpos[0] - self.block_offset[0],
                        mpos[1] - self.block_offset[1],
                        0, 0
                    )
                    self.block_dragged.update(None, self.block_dragged.pos.topleft)
                    if self.code.elem.rect.collidepoint(mpos):
                        self.code.cursor_closest(mpos)
            elif self.click_type == 3:
                self.block_dragged: Codeblock
                self.block_dragged.pos = pygame.Rect(
                    mpos[0] - self.block_offset[0],
                    mpos[1] - self.block_offset[1],
                    0, 0
                )
                self.block_dragged.update(None, self.block_dragged.pos.topleft)
                if self.code.elem.rect.collidepoint(mpos):
                    self.code.cursor_closest(mpos)

    def update_position(self, yaw=None, pitch=None, zoom=None):
        if yaw:
            self.yaw = yaw % (math.pi * 2)
        if pitch:
            self.pitch = min(max(pitch, math.pi / 12), math.pi / 4)
        if zoom:
            self.zoom = zoom

    def run_code(self):
        self.code_start = ticks.get_time()
        self.gen = self.code.exec()
        self.steps = 1

        self.robot_x = self.level.start_x
        self.robot_y = self.level.start_y
        self.robot_dir = self.level.start_dir

        self.won = False
        self.coins = []
        self.coin_counter = 0
        for i, row in enumerate(self.level.map):
            for j, col in enumerate(row):
                if col == 4:
                    self.coins.append((j, i))

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

        collected = None
        for c in self.coins:
            if (self.robot_x, self.robot_y) == c:
                collected = c
        if collected is not None:
            self.coins.remove(collected)
            self.coin_counter += 1

        if block == 0:
            self.robot_x, self.robot_y = old_pos
        elif block == 1:
            print("Died!")
            self.gen = None
        elif block == 3:
            print(f"Win!")
            self.win()

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
        if self.won:
            text = languages.get_str("level.win")
            text_width = _font_victory.size(text)[0]
            pos = pygame.Rect(self.elem.rect.x + (self.elem.rect.w - text_width) / 2, 10, 0, 0)
            draw_text(screen, pos, text, 0xFF00FFFF, _font_victory)

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
        angle = ((self.yaw + self.robot_dir * math.pi / 2 + math.pi * 9 / 8) % (math.pi * 2)) * 8 / (math.pi * 2)
        bot_render = robot_atlas.subsurface(
            pygame.Rect(
                int(angle) * entity_res,
                0,
                entity_res,
                entity_res
            )
        ).copy()
        coin_state = int(ticks.get_time() / 250) % 4
        coin_render = coin_atlas.subsurface(
            pygame.Rect(
                coin_state * entity_res,
                0,
                entity_res,
                entity_res
            )
        ).copy()
        # Entities
        entities = []
        for c in self.coins:
            entities.append(
                (pygame.transform.rotozoom(coin_render, 0, self.zoom / 2), *c)
            )
        entities.append((
            pygame.transform.rotozoom(bot_render, 0, self.zoom / 2),
            self.robot_x,
            self.robot_y,
        ))
        to_render = []
        for e in entities:
            ent_pos_real = (e[1] - self.level.width / 2 + .5, e[2] - self.level.height / 2 + .5)
            ent_pos = x_axis * ent_pos_real[0] + y_axis * ent_pos_real[1] + pygame.math.Vector2(pos_x, pos_y)
            to_render.append((e[0], ent_pos.x, ent_pos.y))
        to_render.sort(key=lambda x: x[2])
        # Rendering
        screen.blit(map_render, (pos_x - map_render.get_width() / 2, pos_y - map_render.get_height() / 2))
        # screen.blit(
        #     bot_render,
        #     (robot_pos.x - (robot_res * self.zoom) / 4, robot_pos.y - (robot_ground * self.zoom) / 2)
        # )
        for e in to_render:
            # print(e)
            screen.blit(
                e[0],
                (e[1] - (entity_res * self.zoom) / 4, e[2] - (entity_ground * self.zoom) / 2)
            )


# Source of blocks, from which they spawn and get dragged out of
class Blocklist:
    def __init__(self, document: gui.DocumentXML, block_name: str, colour: int = 0, container: bool = False, times=4):
        btnlist: gui.Element = document.ids["blocklist"]
        self.elem = gui.Space(document, "space", {"margin": "10px"})
        btnlist.add_child(self.elem)
        self.name = block_name
        self.colour = colour
        self.container = container
        self.times = times
        if container:
            # self.sprite = container_block_textures[colour]
            # self.block = CodeContainer(container_block_textures[colour], block_name, pygame.Rect(0, 0, 0, 0))
            self.sprite = code_block_textures[colour]
            self.block = CodeContainer(code_block_textures[colour], block_name, pygame.Rect(0, 0, 0, 0), times)
        else:
            self.sprite = code_block_textures[colour]
            self.block = Codeblock(code_block_textures[colour], block_name, pygame.Rect(0, 0, 0, 0))

    def get_new_block(self, rect: pygame.Rect):
        if self.container:
            return CodeContainer(self.sprite, self.name, rect, self.times)
        else:
            return Codeblock(self.sprite, self.name, rect)

    def update(self):
        self.block.pos = self.elem.rect
        self.elem.length = f"{self.block.get_box().w}px"

    def draw(self, screen: pygame.Surface):
        self.block.draw(screen)


defined_blocks = {
    "left": ("left", 0, False),
    "forward": ("forward", 1, False),
    "right": ("right", 2, False),
    "repeat4": ("repeat4", 3, True, 4),
    "repeat8": ("repeat8", 4, True, 8),
}


class Codeblock:
    def __init__(self, sprite: SlicedSprite, name: str, pos: pygame.Rect):
        self.sprite = sprite
        self.name = name
        self.pos = pos

    def draw(self, screen: pygame.Surface):
        text = languages.get_str("level.blocks." + self.name)
        size = _font_code.size(text)
        size = (size[0] - 32, size[1] - 32)
        self.sprite.draw(screen, self.pos, size)
        draw_text(
            screen,
            pygame.Rect(self.pos.x + 16, self.pos.y + 16, 0, 0),
            text,
            0xFFFFFFFF,
            _font_code
        )

    def get_box(self, off: tuple = (0, 0)) -> pygame.Rect:
        size = _font_code.size(languages.get_str("level.blocks." + self.name))
        return pygame.Rect(
            self.pos.x + off[0],
            self.pos.y + off[1],
            size[0] + 32,
            size[1] + 32
        )

    def update(self, cursors, off: tuple):
        pass


class CodeContainer(Codeblock):
    def __init__(self, sprite: SlicedSprite, name: str, pos: pygame.Rect, times):
        super().__init__(sprite, name, pos)
        self.children = []
        self.height = 0
        self.times = times

    def draw(self, screen: pygame.Surface):
        for i, b in enumerate(self.children):
            b: Codeblock
            b.draw(screen)

        text = languages.get_str("level.blocks." + self.name)
        size = _font_code.size(text)
        size = (size[0] - 32, size[1] + self.height)
        self.sprite.draw(screen, self.pos, size, self.height)
        draw_text(
            screen,
            pygame.Rect(self.pos.x + 16, self.pos.y + 16, 0, 0),
            text,
            0xFFFFFFFF,
            _font_code
        )

    def get_block_count(self):
        count = 0
        for b in self.children:
            if type(b) is CodeContainer:
                b: CodeContainer
                count += b.get_block_count()
            count += 1
        return count

    def update(self, cursors, off: tuple):
        current_y = 0
        size = _font_code.size(languages.get_str("level.blocks." + self.name))
        off = (off[0] + 32, off[1] + 32 + size[1])
        for i, b in enumerate(self.children):
            b: Codeblock
            if cursors is not None and len(cursors) > 0 and cursors[0] == i:
                if len(cursors) == 1:
                    current_y += cursor_h
                n_off = (off[0], off[1] + current_y)
                b.update(cursors[1:], n_off)
            else:
                n_off = (off[0], off[1] + current_y)
                b.update(None, n_off)
            b.pos = pygame.Rect(n_off[0], n_off[1], 0, 0)
            current_y += b.get_box().h
        if cursors is not None and len(cursors) > 0 and cursors[0] == len(self.children):
            current_y += cursor_h
        self.height = current_y

    def draw_cursor(self, screen: pygame.Surface, cursors, off: tuple):
        current_y = 0
        size = _font_code.size(languages.get_str("level.blocks." + self.name))
        off = (off[0] + 32, off[1] + 32 + size[1])
        for i, b in enumerate(self.children):
            b: Codeblock
            if cursors is not None and len(cursors) > 0 and cursors[0] == i:
                if len(cursors) == 1:
                    fill_rect(screen, pygame.Rect(off[0], off[1] + current_y, 1000, cursor_h), 0xFFFFFF3F)
                    current_y += cursor_h
                n_off = (off[0], off[1] + current_y)
                if type(b) is CodeContainer:
                    b: CodeContainer
                    b.draw_cursor(screen, cursors[1:], n_off)
            current_y += b.get_box().h
        if cursors is not None and len(cursors) > 0 and cursors[0] == len(self.children):
            fill_rect(screen, pygame.Rect(off[0], off[1] + current_y, 1000, cursor_h), 0xFFFFFF3F)
            current_y += cursor_h

    def trace_block(self, pos: tuple, off: tuple):
        for i, b in enumerate(self.children):
            b: Codeblock
            if b.get_box(off).collidepoint(pos):
                if type(b) is CodeContainer:
                    b: CodeContainer
                    ret = b.trace_block(pos, off)
                    if ret is None:
                        return [i], b
                    else:
                        return [i, *ret[0]], ret[1]
                else:
                    return [i], b
        return None

    def cursor_closest(self, pos: tuple, off: pygame.Rect, stack: list):
        vpos = pygame.Vector2(pos)
        size = _font_code.size(languages.get_str("level.blocks." + self.name))
        closest = [*stack, 0]
        closest_dis = pygame.Vector2(
            self.pos.x + off.x,
            self.pos.y + 32 + size[1] + off.y
        ).distance_squared_to(vpos)
        print("== nested CLOSEST ==")
        print(f"root{stack}.dis = {closest_dis}")
        for i, b in enumerate(self.children):
            b: Codeblock
            block_pos = (b.pos.x + off.x, b.pos.y + off.y)
            this_dis = pygame.Vector2(block_pos).distance_squared_to(vpos)
            if closest_dis is None or this_dis < closest_dis:
                closest = [*stack, i]
                closest_dis = this_dis
            if type(b) is CodeContainer:
                b: CodeContainer
                this_cur, this_dis = b.cursor_closest(pos, off, [*stack, i])
                if this_dis < closest_dis:
                    closest = this_cur
                    closest_dis = this_dis
            print(f"block{[*stack, i]}.dis = {this_dis}")
        if len(self.children) > 0:
            last_b = self.children[-1]
            block_pos = (last_b.pos.x + off.x, last_b.pos.y + off.y + last_b.get_box().h)
            last_dis = pygame.Vector2(block_pos).distance_squared_to(vpos)
            if last_dis < closest_dis:
                closest = [*stack, len(self.children)]
                closest_dis = last_dis

        # self.set_cursor(closest)
        print(f"closest = {closest}")
        return closest, closest_dis

    def get_box(self, off: tuple = (0, 0)) -> pygame.Rect:
        size = _font_code.size(languages.get_str("level.blocks." + self.name))
        return pygame.Rect(
            self.pos.x + off[0],
            self.pos.y + off[1],
            size[0] + 32,
            size[1] + 64 + self.height
        )

    def exec(self):
        for b in self.children:
            b: Codeblock
            if type(b) is CodeContainer:
                b: CodeContainer
                for i in range(b.times):
                    yield from b.exec()
            else:
                yield b.name


class Code:
    def __init__(self, document: gui.DocumentXML):
        self.elem: gui.Element = document.ids["code"]
        self.blocks = []
        self.cursors = [0]  # For nested blocks

    def get_block_count(self):
        count = 0
        for b in self.blocks:
            if type(b) is CodeContainer:
                b: CodeContainer
                count += b.get_block_count()
            count += 1
        return count

    def place_block(self, block: Codeblock):
        context = self.blocks
        for c in self.cursors[:-1]:
            context = context[c].children
        context.insert(self.cursors[-1], block)
        self.cursors[-1] += 1

    def remove_block(self, index: list):
        context = self.blocks
        for c in index[:-1]:
            context = context[c].children
        if index[-1] < self.cursors[-1]:
            self.cursors[-1] -= 1
        print(index)
        context.pop(index[-1])

    def trace_block(self, pos: tuple):
        for i, b in enumerate(self.blocks):
            b: Codeblock
            rect: pygame.Rect = self.elem.rect
            if b.get_box(rect.topleft).collidepoint(pos):
                if type(b) is CodeContainer:
                    b: CodeContainer
                    ret = b.trace_block(pos, rect.topleft)
                    if ret is None:
                        return [i], b
                    else:
                        return [i, *ret[0]], ret[1]
                else:
                    return [i], b
        return None

    def cursor_closest(self, pos: tuple):
        vpos = pygame.Vector2(pos)
        closest = [0]
        closest_dis = None
        print(" == CLOSEST ==")
        for i, b in enumerate(self.blocks):
            b: Codeblock
            block_pos = (b.pos.x + self.elem.rect.x, b.pos.y + self.elem.rect.y)
            this_dis = pygame.Vector2(block_pos).distance_squared_to(vpos)
            if closest_dis is None or this_dis < closest_dis:
                closest = [i]
                closest_dis = this_dis
            print(f"block{[i]}.dis = {this_dis}")
            if type(b) is CodeContainer:
                b: CodeContainer
                this_cur, this_dis = b.cursor_closest(pos, self.elem.rect, [i])
                if this_dis < closest_dis:
                    closest = this_cur
                    closest_dis = this_dis
        if len(self.blocks) > 0:
            last_b = self.blocks[-1]
            block_pos = (last_b.pos.x + self.elem.rect.x, last_b.pos.y + self.elem.rect.y + last_b.get_box().h)
            last_dis = pygame.Vector2(block_pos).distance_squared_to(vpos)
            if last_dis < closest_dis:
                closest = [len(self.blocks)]
                closest_dis = last_dis

        self.set_cursor(closest)
        print(f"closest = {closest}")
        return closest, closest_dis

    def update(self):
        current_y = 0
        # print(self.cursors)
        for i, b in enumerate(self.blocks):
            b: Codeblock
            if i == self.cursors[0]:
                if len(self.cursors) == 1:
                    current_y += cursor_h
                b.update(self.cursors[1:], (0, current_y))
            else:
                b.update(None, (0, current_y))
            b.pos = pygame.Rect(0, current_y, 0, 0)
            current_y += b.get_box().h

    def draw_cursor(self, screen: pygame.Surface):
        # dest = screen.subsurface(self.elem.rect)
        current_y = 0
        for i, b in enumerate(self.blocks):
            b: Codeblock
            if i == self.cursors[0]:
                if len(self.cursors) == 1:
                    fill_rect(screen, pygame.Rect(0, current_y, 1000, cursor_h), 0xFFFFFF3F)
                    current_y += cursor_h
                if type(b) is CodeContainer:
                    b: CodeContainer
                    b.draw_cursor(screen, self.cursors[1:], (0, current_y))
            current_y += b.get_box().h
        if self.cursors is not None and len(self.cursors) > 0 and self.cursors[0] == len(self.blocks):
            fill_rect(screen, pygame.Rect(0, current_y, 1000, cursor_h), 0xFFFFFF3F)
            current_y += cursor_h

    def set_cursor(self, path: list):
        self.cursors = path
        self.update()

    def render(self, screen: pygame.Surface):
        dest = screen.subsurface(self.elem.rect)
        # current_y = 0
        for i, b in enumerate(self.blocks):
            b: Codeblock
            b.draw(dest)
        self.draw_cursor(dest)
        #     if i == self.cursors[-1]:
        #         fill_rect(dest, pygame.Rect(0, current_y, 1000, cursor_h), 0xFFFFFF3F)
        #         current_y += cursor_h
        #     current_y += b.get_box().h
        # if self.cursors[-1] == len(self.blocks):
        #     pass
        #     fill_rect(dest, pygame.Rect(0, current_y, 1000, cursor_h), 0xFFFFFF3F)

    def exec(self):
        for b in self.blocks:
            b: Codeblock
            if type(b) is CodeContainer:
                b: CodeContainer
                for i in range(b.times):
                    yield from b.exec()
            else:
                yield b.name

    # def reset(self):
    #     pass
    #
    # def step(self):
    #     pass
