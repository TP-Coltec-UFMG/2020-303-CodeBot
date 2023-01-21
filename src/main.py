import pygame
import ticks
import gui
import languages
import options
import game
import os


# import math


def change_document(name):
    global current_ui
    global ui
    if name in uis:
        current_ui = name
        ui = uis[current_ui]
        ui.calc_draw(screen.get_clip())
        ui.hover_element = ui.trace_element(pygame.mouse.get_pos())
    else:
        raise KeyError(f"{name} page does not exist.")


# Callbacks:
def title_start(_: gui.Element):
    main_game.disable()
    document = uis["levels"]
    lvl_list: gui.Element = document.ids["level_list"]
    lvl_list.children.clear()
    for i in range(main_game.unlocked_level):
        if i >= len(levels):
            break
        if len(main_game.levels) <= i:
            stars = 0
        else:
            stars = main_game.levels[i]

        button = gui.Button(ui, "button", {
            "id": levels[i],
            "on_click": "level",
        })
        button.data = f"levels.{levels[i]}"

        horiz = gui.Horizontal(ui, "horizontal", {
            "id": "level1_stars",
            "length": "min",
            "margin": "5px"
        })
        horiz.add_child(button)
        for j in range(3):
            if stars > j:
                filled_star = gui.Image(ui, "image", {
                    "align": "centre",
                    "smooth": "True",
                    "margin": "5px",
                    "length": "10%",
                    "id": f"star{j + 1}"
                })
                filled_star.data = "res/textures/star_full.png"
                horiz.add_child(filled_star)
            else:
                empty_star = gui.Image(ui, "image", {
                    "align": "centre",
                    "smooth": "True",
                    "margin": "5px",
                    "length": "10%",
                    "id": f"star{j + 1}"
                })
                empty_star.data = "res/textures/star_empty.png"
                horiz.add_child(empty_star)
        lvl_list.add_child(horiz)
    change_document("levels")


def title_options(_: gui.Element):
    change_document("options")


def font_size_select(_: gui.Element):
    change_document("font_size")

def title_lang(_: gui.Element):
    document = uis["language"]
    lang_list: gui.Element = document.ids["lang_list"]
    lang_list.children.clear()
    for lang in languages.refresh():
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
        lang_list.add_child(button)
    change_document("language")


def title_quit(_: gui.Element):
    # pygame.event.post(pygame.event.Event(pygame.QUIT))
    change_document("quit")


def game_quit(_: gui.Element):
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    # change_document("quit")


def level_select(elem: gui.Element):
    change_document("level")
    main_game.enable(ui, game.Level(f"res/levels/{elem.id}.yaml"), screen)
    # main_game.update_position(None, None, 2)


def lang_select(elem: gui.Element):
    languages.load(elem.id)
    ui.calc_draw(screen.get_clip())
    ui.hover_element = ui.trace_element(pygame.mouse.get_pos())


def back_title(_: gui.Element):
    change_document("title")


def back_level_select(_: gui.Element):
    change_document("levels")
    main_game.disable()


def exec_code(_: gui.Element):
    main_game.run_code()

def select_ft_max(_: gui.Element):
    gui.init("res/font/JetBrainsMono-Regular.ttf",45)

def select_ft_medium(_: gui.Element):
    gui.init("res/font/JetBrainsMono-Regular.ttf",40)

def select_ft_min(_: gui.Element):
    gui.init("res/font/JetBrainsMono-Regular.ttf",30)


levels = sorted([
    lvl[:-5] for lvl in os.listdir("res/levels")
])

uis = {
    "title": gui.LoaderXML("res/pages/title_screen.xml").get_document(),
    "options": gui.LoaderXML("res/pages/options_select.xml").get_document(),
    "font_size": gui.LoaderXML("res/pages/font_size_select.xml").get_document(),
    "levels": gui.LoaderXML("res/pages/level_select.xml").get_document(),
    "language": gui.LoaderXML("res/pages/language_select.xml").get_document(),
    "level": gui.LoaderXML("res/pages/level_layout.xml").get_document(),
    "quit": gui.LoaderXML("res/pages/quit_confirm.xml").get_document(),
}
ui_callbacks = {
    "title": {
        "start": title_start,
        "options": title_options,
        "lang": title_lang,
        "exit": title_quit,
    },
    "options":{
        "languages": title_lang,
        "font_size": font_size_select,
        "back": back_title,
    },
    "font_size": {
        "font_size_min": select_ft_min,
        "font_size_medium": select_ft_medium,
        "font_size_max": select_ft_max,
        "back": title_options
    },

   
    "levels": {
        "back": back_title,
        "level": level_select,
    },
    "language": {
        "select": lang_select,
        "back": title_options,
    },
    "level": {
        "back": title_start,
        "play": exec_code,
    },
    "quit": {
        "quit": game_quit,
        "cancel_quit": back_title,
    }
}

for k in ui_callbacks:
    uis[k].set_callbacks(ui_callbacks[k])
current_ui = "title"
ui = uis[current_ui]

pygame.init()
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)

main_game = game.Game()


def main():
    pygame.display.set_caption('Code Bot')
    clk = pygame.time.Clock()
    gui.init("res/font/JetBrainsMono-Regular.ttf", 30)
    game.init()
    languages.load("res/lang/en-gb.yaml")
    change_document("title")

    while True:
        ticks.update()
        ui.hover_element = ui.trace_element(pygame.mouse.get_pos())
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            ui.handle_event(screen, e)
            main_game.handle_event(screen, e)

        main_game.update()

        ui.draw(screen)
        main_game.draw(screen)
        pygame.display.update()

        # Limit framerate so as to not heat up CPU unnecessarily
        clk.tick(20)


if __name__ == "__main__":
    main()
