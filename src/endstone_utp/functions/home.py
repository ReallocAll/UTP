import os
import json
import math

from endstone import ColorFormat, Player
from endstone.level import Location
from endstone.form import ActionForm, ModalForm, TextInput
from endstone.event import event_handler, PlayerJoinEvent


class Home:
    def __init__(self, main: "Main"):
        self.main = main

        self.__home_data_file_path = os.path.join(self.main.first_dir_path, "home.json")
        self.__home_data = self.__load_home_data()

        self.lang_funct = main.lang_funct
        self.config_funct = main.config_funct

    def __load_home_data(self) -> dict:
        if not os.path.exists(self.__home_data_file_path):
            with open(self.__home_data_file_path, "w", encoding="utf-8") as f:
                home_data = {}
                json_str = json.dumps(home_data, indent=4, ensure_ascii=False)
                f.write(json_str)
        else:
            with open(self.__home_data_file_path, "r", encoding="utf-8") as f:
                home_data: dict = json.loads(f.read())

        return home_data

    def __save_home_data(self) -> None:
        with open(self.__home_data_file_path, "w+", encoding="utf-8") as f:
            json_str = json.dumps(self.__home_data, indent=4, ensure_ascii=False)
            f.write(json_str)

    @event_handler
    def __on_player_join(self, e: PlayerJoinEvent) -> None:
        if self.__home_data.get(e.player.name) is None:
            self.__home_data[e.player.name] = {}

            self.__save_home_data()

    def home_main(self, player: Player) -> None:
        home_form = ActionForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'home_form.title')}",
            content=f"{ColorFormat.GREEN}"
                    f"{self.lang_funct.get_text(player, 'home_form.content')}",
            on_close=self.main.back_to_main_form
        )

        home_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.lang_funct.get_text(player, 'home_form.button.add_home')}",
            icon="textures/ui/color_plus",
            on_click=self.__add_home
        )

        for key, value in self.__home_data[player.name].items():
            dim: str = value["dim"]
            loc: list = value["loc"]

            home_form.add_button(
                key,
                icon="textures/items/ender_pearl",
                on_click=self.__home_info(key, dim, loc)
            )

        home_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
            icon="textures/ui/refresh_light",
            on_click=self.main.back_to_main_form
        )

        player.send_form(home_form)

    def __add_home(self, player: Player) -> None:
        home_count = len(self.__home_data[player.name])

        if home_count == self.config_funct.config_data["max_home"]:
            player.send_message(
                f"{ColorFormat.RED}"
                f"[{self.lang_funct.get_text(player, 'add_home.message.fail')}] "
                f"{ColorFormat.WHITE}"
                f"{self.lang_funct.get_text(player, 'add_home.message.fail.reason1').format(home_count)}"
            )

            return

        dim = player.location.dimension.name

        loc = [
            math.floor(player.location.x),
            math.floor(player.location.y),
            math.floor(player.location.z)
        ]

        label = (
            f"{ColorFormat.GREEN}"
            f"{self.lang_funct.get_text(player, 'dimension')}: "
            f"{ColorFormat.WHITE}"
            f"{dim}\n"
            f"{ColorFormat.GREEN}"
            f"{self.lang_funct.get_text(player, 'location')}: "
            f"{ColorFormat.WHITE}"
            f"{loc}\n"
            f"\n"
            f"{ColorFormat.GREEN}"
            f"{self.lang_funct.get_text(player, 'add_home_form.textinput.label')}"
        )

        textinput = TextInput(
            label=label,
            placeholder=self.lang_funct.get_text(player, 'add_home_form.textinput.placeholder')
        )

        add_home_form = ModalForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'add_home_form.title')}",
            controls=[textinput],
            submit_button=f"{ColorFormat.YELLOW}"
                          f"{self.lang_funct.get_text(player, 'add_home_form.submit_button')}",
            on_close=self.home_main
        )

        def on_submit(p: Player, json_str: str) -> None:
            data = json.loads(json_str)

            home_name = data[0]

            if len(home_name) == 0:
                p.send_message(
                    f"{ColorFormat.RED}"
                    f"{self.lang_funct.get_text(p, 'message.error')}"
                )

                return

            if self.__home_data[p.name].get(home_name) is not None:
                p.send_message(
                    f"{ColorFormat.RED}"
                    f"[{self.lang_funct.get_text(p, 'add_home.message.fail')}] "
                    f"{ColorFormat.WHITE}"
                    f"{self.lang_funct.get_text(p, 'add_home.message.fail.reason2').format(home_name)}"
                )

                return

            self.__home_data[p.name][home_name] = {
                "dim": dim,
                "loc": loc
            }

            self.__save_home_data()

            p.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(p, 'add_home.message.success')}"
            )

        add_home_form.on_submit = on_submit

        player.send_form(add_home_form)

    def __home_info(self, home_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            home_info_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'home_info_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'dimension')}: "
                        f"{ColorFormat.WHITE}"
                        f"{dim}\n"
                        f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'location')}: "
                        f"{ColorFormat.WHITE}"
                        f"{loc}\n"
                        f"\n"
                        f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'home_info_form.content').format(home_name)}",
                on_close=self.home_main
            )

            home_info_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'home_info_form.button.teleport')}",
                icon="textures/ui/realmsIcon",
                on_click=self.__home_teleport(home_name, dim, loc)
            )

            home_info_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'home_info_form.button.edit_home')}",
                icon="textures/ui/hammer_l",
                on_click=self.__edit_home(home_name, dim, loc)
            )

            home_info_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.home_main
            )

            player.send_form(home_info_form)

        return on_click

    def __home_teleport(self, home_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            target_dim = self.main.server.level.get_dimension(dim.upper())

            target_loc = Location(
                target_dim,
                x=float(loc[0]),
                y=float(loc[1]),
                z=float(loc[2])
            )

            player.teleport(target_loc)

            player.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'home_teleport.message.success').format(home_name)}"
            )

        return on_click

    def __edit_home(self, home_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            edit_home_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'edit_home_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'edit_home_form.content').format(home_name)}",
                on_close=self.__home_info(home_name, dim, loc)
            )

            edit_home_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'edit_home_form.button.update_home')}",
                icon="textures/ui/refresh",
                on_click=self.__update_home(home_name, dim, loc)
            )

            edit_home_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'edit_home_form.button.delete_home')}",
                icon="textures/ui/icon_trash",
                on_click=self.__delete_home(home_name, dim, loc)
            )

            edit_home_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.__home_info(home_name, dim, loc)
            )

            player.send_form(edit_home_form)

        return on_click

    def __update_home(self, home_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            update_home_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'update_home_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'update_home_form.content').format(home_name)}",
                on_close=self.__edit_home(home_name, dim, loc)
            )

            update_home_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'update_home_form.button.update_home_name')}",
                icon="textures/ui/refresh",
                on_click=self.__update_home_name(home_name, dim, loc)
            )

            update_home_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'update_home_form.button.update_home_loc')}",
                icon="textures/ui/refresh",
                on_click=self.__update_home_loc(home_name, dim, loc)
            )

            update_home_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.__edit_home(home_name, dim, loc)
            )

            player.send_form(update_home_form)

        return on_click

    def __update_home_name(self, home_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            textinput = TextInput(
                label=f"{ColorFormat.GREEN}"
                      f"{self.lang_funct.get_text(player, 'update_home_name_form.textinput.label').format(home_name)}",
                placeholder=self.lang_funct.get_text(player, 'update_home_name_form.textinput.placeholder'),
                default_value=home_name
            )

            update_home_name_form = ModalForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'update_home_name.form.title')}",
                controls=[textinput],
                submit_button=f"{ColorFormat.YELLOW}"
                              f"{self.lang_funct.get_text(player, 'update_home_name_form.submit_button')}",
                on_close=self.__update_home(home_name, dim, loc)
            )

            def on_submit(p: Player, json_str: str) -> None:
                data = json.loads(json_str)

                new_home_name = data[0]

                if len(new_home_name) == 0:
                    p.send_message(
                        f"{ColorFormat.RED}"
                        f"{self.lang_funct.get_text(p, 'message.error')}"
                    )

                    return

                if self.__home_data[p.name].get(new_home_name) is not None:
                    # Nothing changed
                    if new_home_name == home_name:
                        p.send_message(
                            f"{ColorFormat.RED}"
                            f"[{self.lang_funct.get_text(p, 'update_home_name.message.fail1').format(home_name)}] "
                            f"{ColorFormat.WHITE}"
                            f"{self.lang_funct.get_text(p, 'update_home_name.message.fail1.reason')}"
                        )
                    else:
                        p.send_message(
                            f"{ColorFormat.RED}"
                            f"[{self.lang_funct.get_text(p, 'update_home_name.message.fail2').format(home_name, new_home_name)}] "
                            f"{ColorFormat.WHITE}"
                            f"{self.lang_funct.get_text(p, 'update_home_name.message.fail2.reason').format(new_home_name)}"
                        )

                    return

                self.__home_data[p.name].pop(home_name)

                self.__home_data[p.name][new_home_name] = {
                    "dim": dim,
                    "loc": loc
                }

                self.__save_home_data()

                p.send_message(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(p, 'update_home_name.message.success').format(home_name, new_home_name)}"
                )

            update_home_name_form.on_submit = on_submit

            player.send_form(update_home_name_form)

        return on_click

    def __update_home_loc(self, home_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            if player.dimension.name != dim:
                player.send_message(
                    f"{ColorFormat.RED}"
                    f"[{self.lang_funct.get_text(player, 'update_home_loc.message.fail').format(home_name)}] "
                    f"{ColorFormat.WHITE}"
                    f"{self.lang_funct.get_text(player, 'update_home_loc.message.fail.reason')}"
                )

                return

            new_loc = [
                math.floor(player.location.x),
                math.floor(player.location.y),
                math.floor(player.location.z)
            ]

            update_home_loc_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'update_home_loc_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'update_home_loc_form.content').format(home_name, new_loc)}",
                on_close=self.__update_home(home_name, dim, loc)
            )

            update_home_loc_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'update_home_loc_form.confirm')}",
                icon="textures/ui/check",
                on_click=self.__update_home_loc_c(home_name, new_loc)
            )

            update_home_loc_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.__update_home(home_name, dim, loc)
            )

            player.send_form(update_home_loc_form)

        return on_click

    def __update_home_loc_c(self, home_name: str, new_loc: list):
        def on_click(player: Player) -> None:
            self.__home_data[player.name][home_name]["loc"] = new_loc

            self.__save_home_data()

            player.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'update_home_loc.message.success').format(home_name)}"
            )

        return on_click

    def __delete_home(self, home_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            delete_home_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'delete_home_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'delete_home_form.content').format(home_name)}",
                on_close=self.__edit_home(home_name, dim, loc)
            )

            delete_home_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'delete_home_form.button.confirm')}",
                icon="textures/ui/check",
                on_click=self.__delete_home_c(home_name)
            )

            delete_home_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.__edit_home(home_name, dim, loc)
            )

            player.send_form(delete_home_form)

        return on_click

    def __delete_home_c(self, home_name: str):
        def on_click(player: Player) -> None:
            self.__home_data[player.name].pop(home_name)

            self.__save_home_data()

            player.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'delete_home.message.success').format(home_name)}"
            )

        return on_click
