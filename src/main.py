import pygame
import gui


def title_start():
    print("Game start!")


def title_options():
    print("Options screen!")


def title_lang():
    print("Language select!")


def title_quit():
    print("Exit!")


def main():
    clk = pygame.time.Clock()
    pygame.init()
    gui.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    ui = gui.LoaderXML("res/test.xml").get_document()

    ui.set_callbacks({
        "start": title_start,
        "options": title_options,
        "lang": title_lang,
        "exit": title_quit,
    })
    ui.calc_draw(screen.get_clip())
    print(ui.drawables)
    ui.root.tree_print()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            elif e.type == pygame.VIDEORESIZE:
                ui.calc_draw(screen.get_clip())
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    elem = ui.trace_element(e.pos)
                    elem: gui.Element
                    if elem.on_click:
                        ui.call_event(elem.on_click)

        pygame.display.update()
        screen.fill((0, 0, 0, 0))
        ui.draw(screen)

        # Limit framerate so as to not heat up CPU unnecessarily
        clk.tick(20)


if __name__ == "__main__":
    main()
