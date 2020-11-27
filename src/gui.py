import html.parser
import pygame


def draw_box(screen, rect, colour, force=False):
    if force:
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
        pygame.draw.rect(screen, 0x000000, (x + 2, y + 2, w - 4, h - 4), 4)
        pygame.draw.rect(screen, colour, (x + 4, y + 4, w - 8, h - 8), 2, -1)


def fill_rect(screen, rect, colour):
    c = pygame.Color(colour)
    s = pygame.Surface(rect.size)  # the size of your rect
    s.set_alpha(c.a)                # alpha level
    s.fill(c)           # this fills the entire surface
    screen.blit(s, rect.topleft)


class Element:
    def __init__(self, tag, attrs):
        self.tag = tag
        self.children = []
        self.data = ""

        self.attrs = {}
        for key, value in attrs:
            self.attrs[key] = value

        self.length = "auto"
        self.group = "none"
        for k, v in self.attrs.items():
            if k == "length":
                self.length = v
            elif k == "group":
                self.group = v

    def add_child(self, elem):
        self.children.append(elem)

    # Overridable
    def draw(self, screen, rect):
        pass

    # Overridable
    def get_min(self):
        return pygame.Rect(0, 0, 0., 0.)

    # DEBUGGING
    def tree_print(self, level=0):
        def indent(lvl):
            print('  ' * lvl, end='')

        indent(level)
        print("{")
        indent(level + 1)
        print(f"tag: <{self.tag}>,")
        if len(self.attrs) > 0:
            indent(level + 1)
            print(f"attrs: [" + ", ".join([f"{k}='{v}'" for k, v in self.attrs.items()]) + "],")
        if self.data != "":
            indent(level + 1)
            print(f"data: '{self.data}'")
        if len(self.children) > 0:
            indent(level + 1)
            print(f"children: [")
            for c in self.children:
                c.tree_print(level + 2)
            indent(level + 1)
            print("]")
        indent(level)
        print("}")


class Container(Element):
    def __init__(self, tag, attrs):
        super().__init__(tag, attrs)
        self.align = "justify"
        self.colour = 0x00000000
        for k, v in self.attrs.items():
            if k == "align":
                self.align = v
            elif k == "color" or k == "colour":
                if v.startswith("#"):
                    self.colour = int(v[1:], 16)
                else:
                    self.colour = 0x00FFFFFF

    def distribute(self, lengths, space, along_t):
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

    def repart(self, rect, rect2along):
        start_l, start_c, along, across = rect2along(rect)
        lengths = [0. for _ in self.children]
        auto_sized = []
        available_size = along
        for i, c in enumerate(self.children):
            if c.length == "auto":
                auto_sized.append((i, c))
            elif c.length.endswith("%"):
                size = (float(c.length[:-1]) / 100.)
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

    def calc_min(self, rect2along):
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
    def __init__(self, tag, attrs):
        super().__init__(tag, attrs)
        self.colour = 0x00000000
        for k, v in self.attrs.items():
            if k == "color" or k == "colour":
                if v.startswith("#"):
                    self.colour = int(v[1:], 16)
                else:
                    self.colour = 0x00FFFFFF

    def get_min(self):
        return pygame.Rect(0, 0, 0, 0)

    def draw(self, screen, rect):
        fill_rect(screen, rect, self.colour)


class Image(Element):
    def __init__(self, tag, attrs):
        super().__init__(tag, attrs)
        self.source = "missing"
        for k, v in self.attrs.items():
            if k == "source":
                self.source = v
            elif k == "align":
                self.align = v
            elif k == "w":
                self.width = float(v)
            elif k == "h":
                self.height = float(v)

    def draw(self, screen, rect):
        font_surface = pygame.font.SysFont("Comic Sans", 30).render(self.source, True, 0xFFFFFFFF, 0x000000)
        if rect.w / rect.h > self.width / self.height:
            w = self.width * rect.h / self.height
            if self.align == "left":
                r = pygame.Rect(rect.x, rect.y, w, rect.h)
            elif self.align == "right":
                r = pygame.Rect(rect.x + rect.w - w, rect.y, w, rect.h)
            else:
                r = pygame.Rect(rect.x + (rect.w - w) / 2, rect.y, w, rect.h)
        else:
            h = self.height * rect.w / self.width
            if self.align == "up":
                r = pygame.Rect(rect.x, rect.y, rect.w, h)
            elif self.align == "down":
                r = pygame.Rect(rect.x, rect.y + rect.h - h, rect.w, h)
            else:
                r = pygame.Rect(rect.x, rect.y + (rect.h - h) / 2, rect.w, h)
        draw_box(screen, rect, 0x0000FF)
        fill_rect(screen, r, 0xFFFFFF7F)
        draw_box(screen, r, 0xFFFFFF, True)
        screen.blit(font_surface, (r.x + 10, r.y + 10))

    def get_min(self):
        return pygame.Rect(0, 0, 0, 0)


class Button(Element):
    def draw(self, screen, rect):
        font_surface = pygame.font.SysFont("Comic Sans", 30).render(self.data, True, 0xFFFFFFFF, 0x000000)
        fill_rect(screen, rect, 0xFF00FF7F)
        draw_box(screen, rect, 0xFF00FF, True)
        screen.blit(font_surface, (rect.x + 10, rect.y + 10))

    def get_min(self):
        font_size = pygame.font.SysFont("Comic Sans", 30).size(self.data)
        return pygame.Rect(0, 0, font_size[0] + 20, font_size[1] + 20)


class Horizontal(Container):
    def __init__(self, tag, attrs):
        super().__init__(tag, attrs)
        # Generalise horizontal-specific values to container-compatible ones
        if self.align == "left":
            self.align = "before"
        if self.align == "right":
            self.align = "after"

    def draw(self, screen, rect):
        fill_rect(screen, rect, self.colour)
        draw_box(screen, rect, 0xFF0000)
        items = self.repart(rect, lambda r: (r.x, r.y, r.w, r.h))
        for along_t, c in items:
            c.draw(screen, pygame.Rect(*along_t))

    def get_min(self):
        along_t = self.calc_min(lambda r: (r.x, r.y, r.w, r.h))
        return pygame.Rect(*along_t)


class Vertical(Container):
    def __init__(self, tag, attrs):
        super().__init__(tag, attrs)
        # Generalise vertical-specific values to container-compatible ones
        if self.align == "up":
            self.align = "before"
        if self.align == "down":
            self.align = "after"

    def draw(self, screen, rect):
        fill_rect(screen, rect, self.colour)
        draw_box(screen, rect, 0x00FF00)
        items = self.repart(rect, lambda r: (r.y, r.x, r.h, r.w))
        for along_t, c in items:
            c.draw(screen, pygame.Rect(along_t[1], along_t[0], along_t[3], along_t[2]))

    def get_min(self):
        along_t = self.calc_min(lambda r: (r.y, r.x, r.h, r.w))
        return pygame.Rect(along_t[1], along_t[0], along_t[3], along_t[2])


class Overlap(Element):
    def draw(self, screen, rect):
        for c in self.children:
            c.draw(screen, rect)
        draw_box(screen, rect, 0xFFFF00)

    def get_min(self):
        w, h = 0, 0
        for c in self.children:
            r = c.get_min()
            w = max(w, r.w)
            h = max(h, r.h)
        return pygame.Rect(0, 0, w, h)


class LoaderXML(html.parser.HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.tree = None
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
        if not self.tree:
            self.error("Unexpected EOF")

    def get_tree(self):
        return self.tree

    def tree_builder(self, elem=None):
        while True:
            args = yield
            if args.call == "start":
                new_tag = None
                if args.tag in LoaderXML.tags:
                    new_tag = LoaderXML.tags[args.tag](args.tag, args.attrs)
                    yield from self.tree_builder(new_tag)
                elif args.tag in LoaderXML.elements:
                    new_tag = LoaderXML.elements[args.tag](args.tag, args.attrs)
                else:
                    self.error(f"Unrecognised element '{args.tag}'")
                if elem:
                    elem.add_child(new_tag)
                else:
                    self.tree = new_tag
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

    def error(self, message):
        ln, cl = self.getpos()
        txt_line = self.text.split('\n')[ln - 1]
        raise SyntaxError(message, (self.filename, ln, cl, txt_line))

    # Handler argument passing helper classes
    class HandlerArgs:
        def __init__(self, call):
            self.call = call

    class StartTag(HandlerArgs):
        def __init__(self, tag, attrs):
            super().__init__("start")
            self.tag = tag
            self.attrs = attrs

        def __str__(self):
            return f"StartTag({self.tag}, {self.attrs})"

    class EndTag(HandlerArgs):
        def __init__(self, tag):
            super().__init__("end")
            self.tag = tag

        def __str__(self):
            return f"EndTag({self.tag})"

    class TagData(HandlerArgs):
        def __init__(self, data):
            super().__init__("data")
            self.data = data

        def __str__(self):
            return f"TagData({self.data})"

    # Handlers
    def handle_starttag(self, tag, attrs):
        self.gen.send(LoaderXML.StartTag(tag, attrs))

    def handle_endtag(self, tag):
        self.gen.send(LoaderXML.EndTag(tag))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        text = data.strip()
        if text != "":
            self.gen.send(LoaderXML.TagData(text))

    # Tag tables
    tags = {
        "horizontal": Horizontal,
        "vertical": Vertical,
        "lengthwise": None,
        "crosswise": None,
        "overlap": Overlap,
        "button": Button
    }

    elements = {
        "image": Image,
        "text": Element,
        "space": Space
    }


if __name__ == '__main__':
    xml = LoaderXML("res/test.xml")
    xml.get_tree().tree_print()
