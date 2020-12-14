import pygame
import gui
import languages


def change_document(name):
    global current_ui
    global ui
    if name in uis:
        current_ui = name
        ui = uis[current_ui]
        ui.calc_draw(screen.get_clip())
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
        button = gui.Button(document, "button", {
            "length": "min",
            "margin": "10px",
            "on_click": "select",
            "id": lang,
        })
        button.data = languages.get_name(lang)
        lang_list.append(button)
    change_document("language")


def title_quit(_: gui.Element):
    print("Exit!")
    pygame.event.post(pygame.event.Event(pygame.QUIT))


def level_select(elem: gui.Element):
    print(elem.id)
    change_document(elem.id)


def lang_select(elem: gui.Element):
    print(elem.id)
    languages.load(elem.id)


def back_title(_: gui.Element):
    print("Back to title screen!")
    change_document("title")


uis = {
    "title": gui.LoaderXML("res/pages/title_screen.xml").get_document(),
    "levels": gui.LoaderXML("res/pages/level_select.xml").get_document(),
    "language": gui.LoaderXML("res/pages/language_select.xml").get_document(),
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
    }
}
current_ui = "title"
ui = uis[current_ui]
for k in ui_callbacks:
    uis[k].set_callbacks(ui_callbacks[k])

pygame.init()
gui.init()
languages.load("res/lang/en-gb.yaml")
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)


def main():
    clk = pygame.time.Clock()

    change_document("title")
    # ui.calc_draw(screen.get_clip())
    # ui.root.tree_print()

    while True:
        ui.hover_element = ui.trace_element(pygame.mouse.get_pos())
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            elif e.type == pygame.VIDEORESIZE:
                ui.calc_draw(screen.get_clip())
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if ui.hover_element and ui.hover_element.on_click:
                        ui.call_event(ui.hover_element)

        screen.fill((0, 0, 0, 0))
        ui.draw(screen)
        pygame.display.update()

        # Limit framerate so as to not heat up CPU unnecessarily
        clk.tick(30)


if __name__ == "__main__":
    main()
