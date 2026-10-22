import os
import json
import math
from copy import deepcopy

from endstone_utp.storage import atomic_write_json
from endstone_utp.destinations import load_destinations, guard_callback

from endstone import ColorFormat, Player
from endstone.level import Location
from endstone.form import ActionForm, ModalForm, TextInput


class Warp:
    def __init__(self, main: "Main"):
        self.main = main

        self.__warp_data_file_path = os.path.join(self.main.first_dir_path, "warp.json")
        self.__warp_data, self._content = load_destinations(self.__warp_data_file_path, homes=False)
        self._revision = 0

        self.lang_funct = main.lang_funct

    def _allowed(self, player, *, admin=False):
        if not self.main.is_enabled or getattr(self.main, "warp_funct", self) is not self:
            return False
        enabled = self.main.config_funct.config_data.get("is_enabled", {}).get("warp", True)
        return enabled and player.has_permission("Main.command.utp") and (not admin or player.is_op)

    def __save_warp_data(self, candidate, player=None) -> bool:
        try:
            content = atomic_write_json(self.__warp_data_file_path, candidate, expected_content=self._content)
        except (OSError, ValueError, TypeError) as exc:
            self.main.logger.error(f"Unable to save warp destinations: {exc}")
            if player is not None:
                player.send_message("保存失败，原有数据未更改。请联系管理员。")
            return False
        self.__warp_data = candidate
        self._content = content
        self._revision += 1
        return True

    def warp_main(self, player: Player) -> None:
        if not self._allowed(player):
            return
        warp_form = ActionForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'warp_form.title')}",
            content=f"{ColorFormat.GREEN}"
                    f"{self.lang_funct.get_text(player, 'warp_form.content')}",
            on_close=self.main.back_to_main_form
        )

        if player.is_op:
            warp_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'warp_form.button.add_warp')}",
                icon="textures/ui/color_plus",
                on_click=self.__add_warp
            )

        for key, value in self.__warp_data.items():
            dim: str = value["dim"]
            loc: list = value["loc"]

            warp_form.add_button(
                key,
                icon="textures/items/ender_eye",
                on_click=self.__warp_info(key, dim, loc)
            )

        warp_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
            icon="textures/ui/refresh_light",
            on_click=self.main.back_to_main_form
        )

        player.send_form(warp_form)

    def __add_warp(self, player: Player) -> None:
        if not self._allowed(player, admin=True):
            return
        dim = player.dimension.name

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
            f"{self.lang_funct.get_text(player, 'add_warp_form.textinput.label')}"
        )

        textinput = TextInput(
            label=label,
            placeholder=self.lang_funct.get_text(player, 'add_warp_form.textinput.placeholder')
        )

        add_warp_form = ModalForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'add_warp_form.title')}",
            controls=[textinput],
            submit_button=f"{ColorFormat.YELLOW}"
                          f"{self.lang_funct.get_text(player, 'add_warp_form.submit_button')}",
            on_close=self.warp_main
        )

        def on_submit(p: Player, json_str: str) -> None:
            data = json.loads(json_str)

            warp_name = data[0]

            if len(warp_name) == 0:
                p.send_message(
                    f"{ColorFormat.RED}"
                    f"{self.lang_funct.get_text(p, 'message.error')}"
                )

                return

            if self.__warp_data.get(warp_name) is not None:
                p.send_message(
                    f"{ColorFormat.RED}"
                    f"[{self.lang_funct.get_text(p, 'add_warp.message.fail')}] "
                    f"{ColorFormat.WHITE}"
                    f"{self.lang_funct.get_text(p, 'add_warp.message.reason').format(warp_name)}"
                )

                return

            candidate = deepcopy(self.__warp_data)
            candidate[warp_name] = {"dim": dim, "loc": loc}
            if not self.__save_warp_data(candidate, p):
                return

            p.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(p, 'add_warp.message.success')}"
            )

        add_warp_form.on_submit = guard_callback(self, on_submit, admin=True, player=player)

        player.send_form(add_warp_form)

    def __warp_info(self, warp_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            warp_info_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'warp_info_form.title')}",
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
                        f"{self.lang_funct.get_text(player, 'warp_info_form.content').format(warp_name)}",
                on_close=self.warp_main
            )

            warp_info_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'warp_info_form.button.teleport')}",
                icon="textures/ui/realmsIcon",
                on_click=self.__warp_teleport(warp_name, dim, loc)
            )

            if player.is_op:
                warp_info_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(player, 'warp_info_form.button.edit_warp')}",
                    icon="textures/ui/hammer_l",
                    on_click=self.__edit_warp(warp_name, dim, loc)
                )

            warp_info_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.warp_main
            )

            player.send_form(warp_info_form)

        return guard_callback(self, on_click, admin=False)

    def __warp_teleport(self, warp_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            target_dim = self.main.server.level.get_dimension(dim.upper())

            target_loc = Location(
                target_dim,
                x=float(loc[0]),
                y=float(loc[1]),
                z=float(loc[2])
            )

            if player.teleport(target_loc) is False:
                player.send_message("传送被取消。")
                return

            player.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'warp_teleport.message.success').format(warp_name)}"
            )

        return guard_callback(self, on_click, admin=False)

    def __edit_warp(self, warp_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            edit_warp_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'edit_warp_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'edit_warp_form.content').format(warp_name)}",
                on_close=self.__warp_info(warp_name, dim, loc)
            )

            edit_warp_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'edit_warp_form.button.update_warp')}",
                icon="textures/ui/refresh",
                on_click=self.__update_warp(warp_name, dim, loc)
            )

            edit_warp_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'edit_warp_form.button.delete_warp')}",
                icon="textures/ui/icon_trash",
                on_click=self.__delete_warp(warp_name, dim, loc)
            )

            edit_warp_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.__warp_info(warp_name, dim, loc)
            )

            player.send_form(edit_warp_form)

        return guard_callback(self, on_click, admin=True)

    def __update_warp(self, warp_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            update_warp_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'update_warp_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'update_warp_form.content').format(warp_name)}",
                on_close=self.__edit_warp(warp_name, dim, loc)

            )

            update_warp_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'update_warp_form.button.update_warp_name')}",
                icon="textures/ui/refresh",
                on_click=self.__update_warp_name(warp_name, dim, loc)
            )

            update_warp_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'update_warp_form.button.update_warp_loc')}",
                icon="textures/ui/refresh",
                on_click=self.__update_warp_loc(warp_name, dim, loc)
            )

            update_warp_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.__edit_warp(warp_name, dim, loc)
            )

            player.send_form(update_warp_form)

        return guard_callback(self, on_click, admin=True)

    def __update_warp_name(self, warp_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            textinput = TextInput(
                label=f"{ColorFormat.GREEN}"
                      f"{self.lang_funct.get_text(player, 'update_warp_name_form.textinput.label').format(warp_name)}",
                placeholder=self.lang_funct.get_text(player, 'update_warp_name_form.textinput.placeholder'),
                default_value=warp_name
            )

            update_warp_name_form = ModalForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'update_warp_name.form.title')}",
                controls=[textinput],
                submit_button=f"{ColorFormat.YELLOW}"
                              f"{self.lang_funct.get_text(player, 'update_warp_name_form.submit_button')}",
                on_close=self.__update_warp(warp_name, dim, loc)
            )

            def on_submit(p: Player, json_str: str) -> None:
                data = json.loads(json_str)

                new_warp_name = data[0]

                if len(new_warp_name) == 0:
                    p.send_message(
                        f"{ColorFormat.YELLOW}"
                        f"{self.lang_funct.get_text(p, 'message.error')}"
                    )

                    return

                if self.__warp_data.get(new_warp_name) is not None:
                    if new_warp_name == warp_name:
                        p.send_message(
                            f"{ColorFormat.RED}"
                            f"[{self.lang_funct.get_text(p, 'update_warp_name.message.fail1').format(warp_name)}] "
                            f"{ColorFormat.WHITE}"
                            f"{self.lang_funct.get_text(p, 'update_warp_name.message.fail.reason')}"
                        )
                    else:
                        p.send_message(
                            f"{ColorFormat.RED}"
                            f"[{self.lang_funct.get_text(p, 'update_warp_name.message.fail2').format(warp_name, new_warp_name)}] "
                            f"{ColorFormat.WHITE}"
                            f"{self.lang_funct.get_text(p, 'update_warp_name.message.fail2.reason').format(new_warp_name)}"
                        )

                    return

                candidate = deepcopy(self.__warp_data)
                candidate[new_warp_name] = candidate.pop(warp_name)
                if not self.__save_warp_data(candidate, p):
                    return

                p.send_message(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(p, 'update_warp_name.message.success').format(warp_name, new_warp_name)}"
                )

            update_warp_name_form.on_submit = guard_callback(self, on_submit, admin=True, player=player)

            player.send_form(update_warp_name_form)

        return guard_callback(self, on_click, admin=True)

    def __update_warp_loc(self, warp_name: str, dim: str, loc: list):
        def on_click(player: Player) -> None:
            if player.dimension.name != dim:
                player.send_message(
                    f"{ColorFormat.RED}"
                    f"[{self.lang_funct.get_text(player, 'update_warp_loc.message.fail').format(warp_name)}] "
                    f"{ColorFormat.WHITE}"
                    f"{self.lang_funct.get_text(player, 'update_warp_loc.message.fail.reason')}"
                )

                return

            new_loc = [
                math.floor(player.location.x),
                math.floor(player.location.y),
                math.floor(player.location.z)
            ]

            update_warp_loc_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'update_warp_loc_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'update_warp_loc_form.content').format(warp_name, new_loc)}",
                on_close=self.__update_warp(warp_name, dim, loc)
            )

            update_warp_loc_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'update_warp_loc_form.button.confirm')}",
                icon="textures/ui/check",
                on_click=self.__update_warp_loc_c(warp_name, new_loc)
            )

            update_warp_loc_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.__update_warp(warp_name, dim, loc)
            )

            player.send_form(update_warp_loc_form)

        return guard_callback(self, on_click, admin=True)

    def __update_warp_loc_c(self, warp_name: str, new_loc: list):
        def on_click(player: Player) -> None:
            candidate = deepcopy(self.__warp_data)
            candidate[warp_name]["loc"] = new_loc
            if not self.__save_warp_data(candidate, player):
                return

            player.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'update_warp_loc.message.success').format(warp_name)}"
            )

        return guard_callback(self, on_click, admin=True)

    def __delete_warp(self, warp_name, dim: str, loc: list):
        def on_click(player: Player) -> None:
            delete_warp_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(player, 'delete_warp_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(player, 'delete_warp_form.content').format(warp_name)}",
                on_close=self.__edit_warp(warp_name, dim, loc)
            )

            delete_warp_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'delete_warp_form.button.confirm')}",
                icon="textures/ui/check",
                on_click=self.__delete_warp_c(warp_name)
            )

            delete_warp_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'button.back_to_previous')}",
                icon="textures/ui/refresh_light",
                on_click=self.__edit_warp(warp_name, dim, loc)
            )

            player.send_form(delete_warp_form)

        return guard_callback(self, on_click, admin=True)

    def __delete_warp_c(self, warp_name: str):
        def on_click(player: Player) -> None:
            candidate = deepcopy(self.__warp_data)
            candidate.pop(warp_name)
            if not self.__save_warp_data(candidate, player):
                return

            player.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(player, 'delete_warp.message.success').format(warp_name)}"
            )

        return guard_callback(self, on_click, admin=True)
