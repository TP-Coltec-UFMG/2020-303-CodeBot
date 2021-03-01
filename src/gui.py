import html.parser
import pygame
from pygame.image import load_extended
import languages

_font: pygame.font.Font


def init(font, size):
    global _font
    _font = pygame.font.Font(font, size)


def debug(func: callable) -> callable:
    def wrapper(*args, **kwargs):
        print(f"Called {func.__name__} with: {args} {kwargs}")
        ret = func(*args, **kwargs)
        print(f"Returned {ret} from {func.__name__}")
        return ret

    return wrapper


def draw_margin(func: callable) -> callable:
    def wrapper(self: "Element", rect: pygame.Rect, document: "DocumentXML"):
        if self.margin.endswith("px"):
            margin = float(self.margin[:-2])
            rect.x += margin
            rect.y += margin
            rect.w -= margin * 2
            rect.h -= margin * 2
        elif self.margin.endswith("%"):
            margin = float(self.margin[:-1]) / 100.
            rect.x += margin * rect.w
            rect.y += margin * rect.h
            rect.w -= margin * rect.w * 2
            rect.h -= margin * rect.h * 2
        return func(self, rect, document)

    return wrapper


def add_margin(func: callable) -> callable:
    def wrapper(self: "Element"):
        rect = func(self)
        if self.margin.endswith("px"):
            margin = float(self.margin[:-2])
            rect.x -= margin
            rect.y -= margin
            rect.w += margin * 2
            rect.h += margin * 2
        elif self.margin.endswith("%"):
            margin = float(self.margin[:-1]) / 100.
            rect.x -= margin * rect.w
            rect.y -= margin * rect.h
            rect.w += margin * rect.w * 2
            rect.h += margin * rect.h * 2
        return rect

    return wrapper


def draw_box(screen: pygame.Surface, rect: pygame.Rect, colour, force: bool = False):
    if force and False:
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
        pygame.draw.rect(screen, 0x000000, (x + 2, y + 2, w - 4, h - 4), 4)
        pygame.draw.rect(screen, colour, (x + 4, y + 4, w - 8, h - 8), 2)


def fill_rect(screen: pygame.Surface, rect: pygame.Rect, colour):
    c = pygame.Color(colour)
    s = pygame.Surface(rect.size)  # the size of your rect
    s.set_alpha(c.a)  # alpha level
    s.fill(c)  # this fills the entire surface
    screen.blit(s, rect.topleft)


def draw_text(screen: pygame.Surface, rect: pygame.Rect, data: str, colour):
    font_surface = _font.render(data, True, colour)
    screen.blit(font_surface, (rect.x + 10, rect.y + 10))


class Element:
    def __init__(self, document: "DocumentXML", tag: str, attrs: dict):
        self.tag = tag
        self.children = []
        self.data = ""

        self.rect: pygame.Rect
        self.rect = None
        self.attrs = attrs

        if "length" in attrs:
            self.length = attrs["length"]
        else:
            self.length = "auto"

        if "margin" in attrs:
            self.margin = attrs["margin"]
        else:
            self.margin = "0px"

        if "id" in attrs:
            self.id = attrs["id"]
            document.ids[attrs["id"]] = self
        else:
            self.id = None

        if "on_click" in attrs:
            self.on_click = attrs["on_click"]
            document.on_click.append(self)
        else:
            self.on_click = None

        if "color" in self.attrs:
            v = self.attrs["color"]
            if v.startswith("#"):
                self.colour = int(v[1:], 16)
            else:
                self.colour = 0x00FFFFFF
        elif "colour" in self.attrs:
            v = self.attrs["colour"]
            if v.startswith("#"):
                self.colour = int(v[1:], 16)
            else:
                self.colour = 0x00FFFFFF
        else:
            self.colour = 0x00000000

    def add_child(self, elem):
        self.children.append(elem)

    # Overridable
    @draw_margin
    def calc_draw(self, rect: pygame.Rect, document: "DocumentXML"):
        document.add_drawable(self)
        self.rect = rect

    # Overridable
    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        pass

    # Overridable
    @add_margin
    def get_min(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 0., 0.)

    # DEBUGGING
    def tree_print(self, level: int = 0):
        def indent(lvl: int):
            print('    ' * lvl, end='')

        indent(level)
        print(
            "<"
            + " ".join((self.tag, *(f"{k}='{v}'" for k, v in self.attrs.items())))
            + (">\n" if len(self.children) > 0 else ">"),
            end=''
        )

        if self.data != "":
            print(self.data, end='')
        if len(self.children) > 0:
            for c in self.children:
                c.tree_print(level + 1)
            indent(level)
        print(f"</{self.tag}>")


class Container(Element):
    def __init__(self, document: "DocumentXML", tag: str, attrs: dict):
        super().__init__(document, tag, attrs)

        if "align" in self.attrs:
            self.align = self.attrs["align"]
        else:
            self.align = "justify"

    def distribute(self, lengths: list, space: float, along_t: tuple) -> list:
        ret = []
        start_l, start_c, along, across = along_t
        if self.align == "before":
            axis_l = start_l
            for i, c in enumerate(self.children):
                sub_rect = (axis_l, start_c, lengths[i], across)
                ret.append((sub_rect, c))
                axis_l += lengths[i]
        elif self.align == "after":
            axis_l = start_l + space
            for i, c in enumerate(self.children):
                sub_rect = (axis_l, start_c, lengths[i], across)
                ret.append((sub_rect, c))
                axis_l += lengths[i]
        elif self.align == "center" or self.align == "centre":
            axis_l = start_l + space / 2
            for i, c in enumerate(self.children):
                sub_rect = (axis_l, start_c, lengths[i], across)
                ret.append((sub_rect, c))
                axis_l += lengths[i]
        elif self.align == "distribute":
            gap = space / (len(self.children) + 1)
            axis_l = start_l + gap
            for i, c in enumerate(self.children):
                sub_rect = (axis_l, start_c, lengths[i], across)
                ret.append((sub_rect, c))
                if space < 0:
                    axis_l += lengths[i]
                elif len(self.children) > 1:
                    axis_l += lengths[i] + gap
        elif self.align == "justify" or self.align == "proportional":
            axis_l = start_l
            for i, c in enumerate(self.children):
                sub_rect = (axis_l, start_c, lengths[i], across)
                ret.append((sub_rect, c))
                if space < 0:
                    axis_l += lengths[i]
                elif len(self.children) > 1:
                    axis_l += lengths[i] + space / (len(self.children) - 1)
        return ret

    def repart(self, rect: pygame.Rect, rect2along: callable) -> list:
        start_l, start_c, along, across = rect2along(rect)
        lengths = [0. for _ in self.children]
        auto_sized = []
        available_size = along
        for i, c in enumerate(self.children):
            if c.length == "auto":
                auto_sized.append((i, c))
            elif c.length.endswith("%"):
                size = float(c.length[:-1]) / 100.
                lengths[i] = along * size
                available_size -= along * size
            elif c.length.endswith("px"):
                size = float(c.length[:-2])
                lengths[i] = size
                available_size -= size
            elif c.length == "min":
                size = rect2along(c.get_min())[2]
                lengths[i] = size
                available_size -= size
            else:
                raise ValueError(c.attrs["len"])
        if len(auto_sized) == 0:
            return self.distribute(lengths, available_size, rect2along(rect))
        elif self.align == "proportional":
            min_sum = 0
            for i, c in auto_sized:
                min_size = rect2along(c.get_min())[2]
                lengths[i] = min_size
                min_sum += min_size
            if min_sum <= available_size:
                for t in auto_sized:
                    i, c = t
                    lengths[i] = lengths[i] * available_size / min_sum
            return self.distribute(lengths, 0, rect2along(rect))
        else:
            divided = 0
            while len(auto_sized) > 0:
                fixed_size = []
                estimate = available_size / len(auto_sized)
                for t in auto_sized:
                    i, c = t
                    min_size = rect2along(c.get_min())[2]
                    if min_size > estimate:
                        fixed_size.append(t)
                        available_size -= min_size
                        lengths[i] = min_size
                if len(fixed_size) == 0:
                    divided = available_size / len(auto_sized)
                    break
                for i in fixed_size:
                    if i in auto_sized:
                        auto_sized.remove(i)
            for i, c in auto_sized:
                lengths[i] = divided
                available_size -= lengths[i]
            return self.distribute(lengths, available_size, rect2along(rect))

    def calc_min(self, rect2along: callable) -> tuple:
        along = 0
        across = 0
        along_percent = 1
        for c in self.children:
            start_along, start_across, this_along, this_across = rect2along(c.get_min())
            if c.length == "auto":
                along += this_along
            elif c.length.endswith("%"):
                along_percent -= float(c.length[:-1]) / 100.
            elif c.length.endswith("px"):
                along += float(c.length[:-2])
            elif c.length == "min":
                along += this_along
            across = max(across, this_across)
        if along_percent > 0:
            along /= along_percent
        return 0, 0, along, across


class Space(Element):
    def __init__(self, document: "DocumentXML", tag: str, attrs: dict):
        super().__init__(document, tag, attrs)

    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        if self.colour != 0:
            fill_rect(screen, self.rect, self.colour)


class Image(Element):
    def __init__(self, document: "DocumentXML", tag: str, attrs: dict):
        super().__init__(document, tag, attrs)
        self.image = None
        self.image_scaled = None

        if "hover_colour" in self.attrs:
            self.hover_colour = self.attrs["hover_colour"]
        elif "hover_color" in self.attrs:
            self.hover_colour = self.attrs["hover_color"]
        else:
            self.hover_colour = None

        if "align" in self.attrs:
            self.align = self.attrs["align"]
        else:
            self.align = None

        if "smooth" in self.attrs:
            self.smooth = True
        else:
            self.smooth = False

    @draw_margin
    def calc_draw(self, rect: pygame.Rect, document: "DocumentXML"):
        document.add_drawable(self)
        if not self.image:
            self.image = load_extended(str(self.data))
        img_width, img_height = self.image.get_size()
        if rect.w / rect.h > img_width / img_height:
            w = img_width * rect.h / img_height
            if self.align == "left":
                r = pygame.Rect(rect.x, rect.y, w, rect.h)
            elif self.align == "right":
                r = pygame.Rect(rect.x + rect.w - w, rect.y, w, rect.h)
            else:
                r = pygame.Rect(rect.x + (rect.w - w) / 2, rect.y, w, rect.h)
        else:
            h = img_height * rect.w / img_width
            if self.align == "up":
                r = pygame.Rect(rect.x, rect.y, rect.w, h)
            elif self.align == "down":
                r = pygame.Rect(rect.x, rect.y + rect.h - h, rect.w, h)
            else:
                r = pygame.Rect(rect.x, rect.y + (rect.h - h) / 2, rect.w, h)
        if self.smooth:
            self.image_scaled = pygame.transform.smoothscale(self.image, (r.w, r.h))
        else:
            self.image_scaled = pygame.transform.scale(self.image, (r.w, r.h))
        self.rect = r

    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        # draw_box(screen, self.rect, 0x0000FF)
        # fill_rect(screen, self.rect, 0x0000007F)
        draw_box(screen, self.rect, 0xFFFFFF, True)
        screen.blit(self.image_scaled, self.rect)
        if self.hover_colour:
            if self == document.hover_element:
                fill_rect(screen, self.rect, self.hover_colour)
        # draw_text(screen, self.rect, self.data, 0xFFFFFFFF)


class Button(Element):
    def __init__(self, document: "DocumentXML", tag: str, attrs: dict):
        super().__init__(document, tag, attrs)

        if "align" in self.attrs:
            self.align = self.attrs["align"]
        else:
            self.align = "left"

    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        font_size = _font.size(languages.get_str(self.data))
        gap_x = self.rect.w - font_size[0] - 20
        gap_y = self.rect.h - font_size[1] - 20
        if self.colour:
            if self == document.hover_element:
                fill_rect(screen, self.rect, (self.colour & 0xFFFFFF00) | 0x000000FF)
            else:
                fill_rect(screen, self.rect, (self.colour & 0xFFFFFF00) | 0x0000007F)
        else:
            if self == document.hover_element:
                fill_rect(screen, self.rect, 0xFFFFFF7F)
            else:
                fill_rect(screen, self.rect, 0x0000007F)
        draw_box(screen, self.rect, 0x000000FF, True)
        if self.align == "left":
            draw_text(screen, self.rect, languages.get_str(self.data), 0xFFFFFFFF)
        elif self.align == "rigth":
            r = pygame.Rect(self.rect.x + gap_x, self.rect.y, 0, 0)
            draw_text(screen, r, languages.get_str(self.data), 0xFFFFFFFF)
        elif self.align == "centre" or self.align == "center":
            r = pygame.Rect(self.rect.x + gap_x / 2, self.rect.y + gap_y / 2, 0, 0)
            draw_text(screen, r, languages.get_str(self.data), 0xFFFFFFFF)

    @add_margin
    def get_min(self) -> pygame.Rect:
        font_size = _font.size(languages.get_str(self.data))
        return pygame.Rect(0, 0, font_size[0] + 20, font_size[1] + 20)


class Text(Element):
    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        draw_box(screen, self.rect, 0xFF00FF, True)
        draw_text(screen, self.rect, languages.get_str(self.data), self.colour)

    @add_margin
    def get_min(self) -> pygame.Rect:
        font_size = _font.size(languages.get_str(self.data))
        return pygame.Rect(0, 0, font_size[0] + 20, font_size[1] + 20)


class Horizontal(Container):
    def __init__(self, document: "DocumentXML", tag: str, attrs: dict):
        super().__init__(document, tag, attrs)
        # Generalise horizontal-specific values to container-compatible ones
        if self.align == "left":
            self.align = "before"
        if self.align == "right":
            self.align = "after"

    @draw_margin
    def calc_draw(self, rect: pygame.Rect, document: "DocumentXML"):
        document.add_drawable(self)
        self.rect = rect
        items = self.repart(rect, lambda r: (r.x, r.y, r.w, r.h))
        for along_t, c in items:
            c.calc_draw(pygame.Rect(*along_t), document)

    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        if self.colour != 0:
            fill_rect(screen, self.rect, self.colour)
        draw_box(screen, self.rect, 0xFF0000)

    @add_margin
    def get_min(self) -> pygame.Rect:
        along_t = self.calc_min(lambda r: (r.x, r.y, r.w, r.h))
        return pygame.Rect(*along_t)


class Vertical(Container):
    def __init__(self, document: "DocumentXML", tag: str, attrs: dict):
        super().__init__(document, tag, attrs)
        # Generalise vertical-specific values to container-compatible ones
        if self.align == "up":
            self.align = "before"
        if self.align == "down":
            self.align = "after"

    @draw_margin
    def calc_draw(self, rect: pygame.Rect, document: "DocumentXML"):
        document.add_drawable(self)
        self.rect = rect
        items = self.repart(rect, lambda r: (r.y, r.x, r.h, r.w))
        for along_t, c in items:
            c.calc_draw(pygame.Rect(along_t[1], along_t[0], along_t[3], along_t[2]), document)

    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        if self.colour != 0:
            fill_rect(screen, self.rect, self.colour)
        draw_box(screen, self.rect, 0x00FF00)

    @add_margin
    def get_min(self) -> pygame.Rect:
        along_t = self.calc_min(lambda r: (r.y, r.x, r.h, r.w))
        return pygame.Rect(0, 0, along_t[3], along_t[2])


class Lengthwise(Container):
    def __init__(self, document: "DocumentXML", tag: str, attrs: dict):
        super().__init__(document, tag, attrs)

    @draw_margin
    def calc_draw(self, rect: pygame.Rect, document: "DocumentXML"):
        document.add_drawable(self)
        self.rect = rect
        if rect.w > rect.h:
            items = self.repart(rect, lambda r: (r.x, r.y, r.w, r.h))
            for along_t, c in items:
                c.calc_draw(pygame.Rect(*along_t), document)
        else:
            items = self.repart(rect, lambda r: (r.y, r.x, r.h, r.w))
            for along_t, c in items:
                c.calc_draw(pygame.Rect(along_t[1], along_t[0], along_t[3], along_t[2]), document)

    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        if self.colour != 0:
            fill_rect(screen, self.rect, self.colour)
        draw_box(screen, self.rect, 0x00FF00)

    @add_margin
    def get_min(self) -> pygame.Rect:
        along_t = self.calc_min(lambda r: (r.x, r.y, r.w, r.h))
        greater = max(along_t[3], along_t[2])
        return pygame.Rect(0, 0, greater)


class Crosswise(Container):
    def __init__(self, document: "DocumentXML", tag: str, attrs: dict):
        super().__init__(document, tag, attrs)

    @draw_margin
    def calc_draw(self, rect: pygame.Rect, document: "DocumentXML"):
        document.add_drawable(self)
        self.rect = rect
        if rect.w > rect.h:
            items = self.repart(rect, lambda r: (r.y, r.x, r.h, r.w))
            for along_t, c in items:
                c.calc_draw(pygame.Rect(along_t[1], along_t[0], along_t[3], along_t[2]), document)
        else:
            items = self.repart(rect, lambda r: (r.x, r.y, r.w, r.h))
            for along_t, c in items:
                c.calc_draw(pygame.Rect(*along_t), document)

    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        if self.colour != 0:
            fill_rect(screen, self.rect, self.colour)
        draw_box(screen, self.rect, 0x00FF00)

    @add_margin
    def get_min(self) -> pygame.Rect:
        along_t = self.calc_min(lambda r: (r.y, r.x, r.h, r.w))
        greater = max(along_t[3], along_t[2])
        return pygame.Rect(0, 0, greater)


class Overlap(Element):
    @draw_margin
    def calc_draw(self, rect: pygame.Rect, document: "DocumentXML"):
        document.add_drawable(self)
        self.rect = rect
        for c in self.children:
            c.calc_draw(rect, document)

    def draw(self, screen: pygame.Surface, document: "DocumentXML"):
        draw_box(screen, self.rect, 0xFFFF00)

    @add_margin
    def get_min(self) -> pygame.Rect:
        w, h = 0, 0
        for c in self.children:
            r = c.get_min()
            w = max(w, r.w)
            h = max(h, r.h)
        return pygame.Rect(0, 0, w, h)


class DocumentXML:
    def __init__(self):
        self.root = None
        self.ids = dict()
        self.on_click = list()
        self.on_hover = list()
        self.drawables = list()
        self.callbacks = None
        self.hover_element = None

    def set_callbacks(self, callbacks: dict):
        self.callbacks = callbacks

    def set_root(self, root: Element):
        self.root = root

    def call_event(self, elem: Element):
        self.callbacks[elem.on_click](elem)

    def add_drawable(self, elem: Element):
        self.drawables.append(elem)

    def calc_draw(self, rect: pygame.Rect):
        self.root: Element
        self.drawables.clear()
        self.root.calc_draw(rect, self)

    def draw(self, screen: pygame.Surface):
        for d in self.drawables:
            d: Element
            d.draw(screen, self)

    def trace_element(self, pos: tuple):
        # Find element that collides with a certain pos (x, y) (useful for mouse clicks)
        for elem in reversed(self.drawables):
            elem: Element
            if elem.rect.collidepoint(pos):
                return elem
        return None

    def handle_event(self, screen: pygame.Surface, event: pygame.event.Event):
        if event.type == pygame.VIDEORESIZE:
            self.calc_draw(screen.get_clip())
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.hover_element and self.hover_element.on_click:
                    self.call_event(self.hover_element)


class LoaderXML(html.parser.HTMLParser):
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename
        self.document = DocumentXML()
        with open(filename) as file:
            self.file = file
            text = file.read()
        self.text = text
        self.gen = self.tree_builder()
        next(self.gen)
        try:
            self.feed(text)
        except StopIteration:
            self.error("Unexpected tokens after root tag")
        if not self.document.root:
            self.error("Unexpected EOF")

        del self.text
        del self.gen

    def get_document(self) -> DocumentXML:
        return self.document

    def tree_builder(self, elem: Element = None) -> iter:
        while True:
            args = yield
            if args.call == "start":
                new_tag = None

                if args.tag in LoaderXML.tags:
                    new_tag = LoaderXML.tags[args.tag](self.document, args.tag, args.attrs)
                    yield from self.tree_builder(new_tag)
                elif args.tag in LoaderXML.elements:
                    new_tag = LoaderXML.elements[args.tag](self.document, args.tag, args.attrs)
                else:
                    self.error(f"Unrecognised element '{args.tag}'")

                if elem:
                    elem.add_child(new_tag)
                else:
                    self.document.set_root(new_tag)
                    yield
                    return
            elif args.call == "data":
                if not elem:
                    self.error("Unexpected data")
                elem.data += args.data
            elif args.call == "end":
                if not elem:
                    self.error("Unexpected end of tag")
                elif args.tag in LoaderXML.elements:
                    self.error(f"Element '{args.tag}' cannot have a closing tag (single element)")
                elif elem.tag != args.tag:
                    self.error(f"Closing tags do not match ({elem.tag} != {args.tag})")
                return

    def error(self, message: str):
        ln, cl = self.getpos()
        txt_line = self.text.split('\n')[ln - 1]
        raise SyntaxError(message, (self.filename, ln, cl, txt_line))

    # Handler argument passing helper classes
    class HandlerArgs:
        def __init__(self, call: str):
            self.call = call

    class StartTag(HandlerArgs):
        def __init__(self, tag: str, attrs: list):
            super().__init__("start")
            self.tag = tag
            self.attrs = dict()

            # Convert list of tuples [(name, value), ...] to dictionary
            for k, v in attrs:
                self.attrs[k] = v

        def __str__(self) -> str:
            return f"StartTag({self.tag}, {self.attrs})"

    class EndTag(HandlerArgs):
        def __init__(self, tag: str):
            super().__init__("end")
            self.tag = tag

        def __str__(self) -> str:
            return f"EndTag({self.tag})"

    class TagData(HandlerArgs):
        def __init__(self, data: str):
            super().__init__("data")
            self.data = data

        def __str__(self) -> str:
            return f"TagData({self.data})"

    # Handlers
    def handle_starttag(self, tag: str, attrs: list):
        self.gen.send(LoaderXML.StartTag(tag, attrs))

    def handle_endtag(self, tag: str):
        self.gen.send(LoaderXML.EndTag(tag))

    def handle_startendtag(self, tag: str, attrs: list):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str):
        text = data.strip()
        if text != "":
            self.gen.send(LoaderXML.TagData(text))

    # Tag tables
    tags: dict = {
        "horizontal": Horizontal,
        "vertical": Vertical,
        "lengthwise": Lengthwise,
        "crosswise": Crosswise,
        "overlap": Overlap,
        "text": Text,
        "button": Button,
        "image": Image,
    }

    elements: dict = {
        "space": Space,
    }
