import os
import json

from endstone import ColorFormat, Player
from endstone.form import ActionForm, Toggle, Dropdown, ModalForm
from endstone.event import event_handler, PlayerJoinEvent


class TPA:
    def __init__(self, main: "Main"):
        self.main = main

        self.__tpa_setting_file_path = os.path.join(self.main.first_dir_path, "tpa_setting.json")
        self.__tpa_setting_data = self.__load_tpa_setting_data()

        self.lang_funct = main.lang_funct

    def __load_tpa_setting_data(self) -> dict:
        if not os.path.exists(self.__tpa_setting_file_path):
            with open(self.__tpa_setting_file_path, "w") as f:
                tpa_setting_data = {}
                json_str = json.dumps(tpa_setting_data, indent=4, ensure_ascii=False)
                f.write(json_str)
        else:
            with open(self.__tpa_setting_file_path, "r") as f:
                tpa_setting_data: dict = json.loads(f.read())

        return tpa_setting_data

    def __save_tpa_setting_data(self) -> None:
        with open(self.__tpa_setting_file_path, "w+") as f:
            json_str = json.dumps(self.__tpa_setting_data, indent=4, ensure_ascii=False)
            f.write(json_str)

    @event_handler
    def on_player_join(self, e: PlayerJoinEvent) -> None:
        if self.__tpa_setting_data.get(e.player.name) is None:
            self.__tpa_setting_data[e.player.name] = True

            self.__save_tpa_setting_data()

    def tpa_main(self, player: Player) -> None:
        tpa_form = ActionForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'tpa_form.title')}",
            content=f"{ColorFormat.GREEN}"
                    f"{self.lang_funct.get_text(player, 'tpa_form.content')}",
            on_close=self.main.back_to_main_form
        )

        tpa_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.lang_funct.get_text(player, 'tpa_form.button.tpa_setting')}",
            icon="textures/ui/icon_setting",
            on_click=self.__tpa_setting
        )

        tpa_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.lang_funct.get_text(player, 'tpa_form.button.send_request')}",
            icon="textures/ui/dressing_room_customization",
            on_click=self.__send_request
        )

        player.send_form(tpa_form)

    def __tpa_setting(self, player: Player) -> None:
        toggle = Toggle(
            label=f"{ColorFormat.GREEN}"
                  f"{self.lang_funct.get_text(player, 'tpa_setting_form.toggle.label')}",
        )

        if self.__tpa_setting_data[player.name]:
            toggle.default_value = True
        else:
            toggle.default_value = False

        tpa_setting_form = ModalForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'tpa_setting_form.title')}",
            controls=[toggle],
            submit_button=f"{ColorFormat.YELLOW}"
                          f"{self.lang_funct.get_text(player, 'tpa_setting_form.submit_button')}",
            on_close=self.tpa_main
        )

        def on_submit(p: Player, json_str: str) -> None:
            data = json.loads(json_str)

            self.__tpa_setting_data[p.name] = data[0]

            self.__save_tpa_setting_data()

            p.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(p, 'tpa_setting.message.success')}"
            )

        tpa_setting_form.on_submit = on_submit

        player.send_form(tpa_setting_form)

    def __send_request(self, player: Player) -> None:
        player_name_list = []

        for online_player in self.main.server.online_players:
            if (
                online_player.name != player.name
                and
                self.__tpa_setting_data[online_player.name]
            ):
                player_name_list.append(online_player.name)

        if len(player_name_list) == 0:
            player.send_message(
                f"{ColorFormat.RED}"
                f"[{self.lang_funct.get_text(player, 'send_request.message.fail1')}] "
                f"{ColorFormat.WHITE}"
                f"{self.lang_funct.get_text(player, 'send_request.message.fail1.reason')}"
            )

            return

        player_name_list.sort(key=lambda x:x[0].lower(), reverse=False)

        dropdown1 = Dropdown(
            label=f"{ColorFormat.GREEN}"
                  f"{self.lang_funct.get_text(player, 'send_request_form.dropdown1.label')}",
            options=player_name_list,
            default_index=0
        )

        mode_list = [
            "TPA",
            "TPAHere"
        ]

        dropdown2 = Dropdown(
            label=f"{ColorFormat.GREEN}"
                  f"{self.lang_funct.get_text(player, 'send_request_form.dropdown2.label')}",
            options=mode_list,
            default_index=0
        )

        send_request_form = ModalForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'send_request_form.title')}",
            controls=[
                dropdown1,
                dropdown2
            ],
            submit_button=f"{ColorFormat.YELLOW}"
                          f"{self.lang_funct.get_text(player, 'send_request_form.submit_button')}",
            on_close=self.tpa_main
        )

        def on_submit(p: Player, json_str: str) -> None:
            data = json.loads(json_str)

            acceptor_name = player_name_list[data[0]]

            mode = mode_list[data[1]]

            # Ensure that the target acceptor is still online!
            if self.main.server.get_player(acceptor_name) is not None:
                acceptor: Player = self.main.server.get_player(acceptor_name)

                request_form = ActionForm(
                    title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                          f"{self.lang_funct.get_text(acceptor, 'request_form.title').format(mode)}",
                    content=f"{ColorFormat.GREEN}"
                            f"{self.lang_funct.get_text(acceptor, 'request_form.content').format(p.name, mode)}",
                    on_close=self.__busy(p.name, mode)
                )

                request_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(acceptor, 'request_form.button.accept')}",
                    icon="textures/ui/check",
                    on_click=self.__request_handler(p.name, mode, "accept")
                )

                request_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(acceptor, 'request_form.button.deny')}",
                    icon="textures/ui/cancel",
                    on_click=self.__request_handler(p.name, mode, "deny")
                )

                acceptor.send_form(request_form)

                p.send_message(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(p, 'send_request.message.success').format(mode, acceptor_name)}"
                )
            else:
                p.send_message(
                    f"{ColorFormat.RED}"
                    f"[{self.lang_funct.get_text(p, 'send_request.message.fail2').format(mode)}] "
                    f"{ColorFormat.WHITE}"
                    f"{self.lang_funct.get_text(p, 'send_request.message.fail2.reason1').format(acceptor_name)}"
                )

        send_request_form.on_submit = on_submit

        player.send_form(send_request_form)

    def __busy(self, sender_name: str, mode: str):
        def on_click(acceptor: Player) -> None:
            if self.main.server.get_player(sender_name) is not None:
                sender: Player = self.main.server.get_player(sender_name)

                sender.send_message(
                    f"{ColorFormat.RED}"
                    f"[{self.lang_funct.get_text(sender, 'send_request.message.fail2').format(mode)}] "
                    f"{ColorFormat.WHITE}"
                    f"{self.lang_funct.get_text(sender, 'send_request.message.fail2.reason2').format(acceptor.name)}"
                )

        return on_click

    def __request_handler(self, sender_name: str, mode: str, selection: str):
        def on_click(player: Player) -> None:
            if selection == "accept":
                if self.main.server.get_player(sender_name) is not None:
                    sender: Player = self.main.server.get_player(sender_name)

                    if mode == "TPA":
                        sender.teleport(player)
                    else:
                        player.teleport(sender)
                else:
                    player.send_message(
                        f"{ColorFormat.RED}"
                        f"[{self.lang_funct.get_text(player, 'accept.message.fail').format(mode)}] "
                        f"{ColorFormat.WHITE}"
                        f"{self.lang_funct.get_text(player, 'accept.message.fail.reason').format(sender_name)}"
                    )
            else:
                if self.main.server.get_player(sender_name) is not None:
                    sender: Player = self.main.server.get_player(sender_name)

                    sender.send_message(
                        f"{ColorFormat.RED}"
                        f"{self.lang_funct.get_text(sender, 'deny.message').format(player.name, mode)}"
                    )

        return on_click
