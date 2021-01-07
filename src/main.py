import pygame
import ticks
import gui
import languages
import game
import math


def change_document(name):
    global current_ui
    global ui
    if name in uis:
        current_ui = name
        ui = uis[current_ui]
        ui.calc_draw(screen.get_clip())
        ui.hover_element = ui.trace_element(pygame.mouse.get_pos())
    else:
        print("404 page not found.")


# Callbacks:
def title_start(_: gui.Element):
    print("Game start!")
    change_document("levels")


def title_options(_: gui.Element):
    print("Options screen (not implemented)!")
    change_document("options")


def title_lang(_: gui.Element):
    print("Language select!")
    document = uis["language"]
    lang_list: list = document.ids["lang_list"].children
    lang_list.clear()
    for lang in languages.refresh():
        print(lang)
        name: str
        try:
            name = languages.get_name(lang)
        except ValueError as err:
            print("Invalid language file! " + str(err))
            continue
        except KeyError as err:
            print("Invalid language YAML! " + str(err))
            continue
        button = gui.Button(document, "button", {
            "length": "min",
            "margin": "10px",
            "on_click": "select",
            "id": lang,
        })
        button.data = name
        lang_list.append(button)
    change_document("language")


def title_quit(_: gui.Element):
    print("Exit!")
    pygame.event.post(pygame.event.Event(pygame.QUIT))


def level_select(elem: gui.Element):
    print(elem.id)
    change_document("level")


def lang_select(elem: gui.Element):
    print(elem.id)
    languages.load(elem.id)
    ui.calc_draw(screen.get_clip())
    ui.hover_element = ui.trace_element(pygame.mouse.get_pos())


def back_title(_: gui.Element):
    print("Back to title screen!")
    change_document("title")


uis = {
    "title": gui.LoaderXML("res/pages/title_screen.xml").get_document(),
    "levels": gui.LoaderXML("res/pages/level_select.xml").get_document(),
    "language": gui.LoaderXML("res/pages/language_select.xml").get_document(),
    "level": gui.LoaderXML("res/pages/level_layout.xml").get_document(),
}
ui_callbacks = {
    "title": {
        "start": title_start,
        "options": title_options,
        "lang": title_lang,
        "exit": title_quit,
    },
    "levels": {
        "back": back_title,
        "level": level_select,
    },
    "language": {
        "back": back_title,
        "select": lang_select
    },
    "level": {
        "back": title_start,
    },
}
for k in ui_callbacks:
    uis[k].set_callbacks(ui_callbacks[k])
current_ui = "title"
ui = uis[current_ui]

pygame.init()
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)


def main():
    clk = pygame.time.Clock()
    gui.init()
    languages.load("res/lang/none.yaml")
    change_document("title")
    main_game = game.Game()

    while True:
        ticks.update()
        ui.hover_element = ui.trace_element(pygame.mouse.get_pos())
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            ui.handle_event(screen, e)
            main_game.handle_event(screen, e)

        # screen.fill((0, 0, 0, 0))
        ui.draw(screen)
        render_x, render_y = (ticks.get_time() / 1000), math.pi / 8
        main_game.render(screen, render_x, render_y)
        # print((render_x, render_y))
        pygame.display.update()

        # Limit framerate so as to not heat up CPU unnecessarily
        clk.tick(30)


if __name__ == "__main__":
    main()
