import json
import os

from endstone import ColorFormat, Player
from endstone.event import PlayerJoinEvent, event_handler
from endstone.form import ActionForm, Dropdown, ModalForm, TextInput


class TPA:
    def __init__(self, main: "Main"):
        self.main = main

        self.__tpa_setting_file_path = os.path.join(
            self.main.first_dir_path,
            "tpa_setting.json"
        )
        self.__tpa_setting_data = self.__load_tpa_setting_data()

    @staticmethod
    def __is_chinese(player: Player) -> bool:
        return str(player.locale).lower().startswith("zh")

    @staticmethod
    def __player_xuid(player: Player) -> str | None:
        xuid = getattr(player, "xuid", None)
        if not isinstance(xuid, str):
            return None

        xuid = xuid.strip()
        return xuid or None

    @staticmethod
    def __default_settings(enabled: bool = True) -> dict:
        return {
            "enabled": enabled,
            "blacklist": [],
            "whitelist": []
        }

    @staticmethod
    def __normalize_name(name: str) -> str:
        return name.casefold()

    def button_text(self, player: Player) -> str:
        return self.__text(player, "request_teleport")

    def settings_button_text(self, player: Player) -> str:
        return self.__text(player, "request_settings")

    def __load_tpa_setting_data(self) -> dict:
        if not os.path.exists(self.__tpa_setting_file_path):
            data = {}
            self.__write_tpa_setting_data(data)
            return data

        try:
            with open(self.__tpa_setting_file_path, "r", encoding="utf-8") as f:
                raw_data = json.loads(f.read())
        except (OSError, json.JSONDecodeError):
            return {}

        if not isinstance(raw_data, dict):
            return {}

        data = {}
        migrated = False

        for player_name, value in raw_data.items():
            if not isinstance(player_name, str):
                migrated = True
                continue

            if isinstance(value, bool):
                data[player_name] = self.__default_settings(value)
                migrated = True
                continue

            if not isinstance(value, dict):
                data[player_name] = self.__default_settings()
                migrated = True
                continue

            enabled = value.get("enabled", True)
            blacklist = value.get("blacklist", [])
            whitelist = value.get("whitelist", [])

            if not isinstance(enabled, bool):
                enabled = True
                migrated = True

            if not isinstance(blacklist, list):
                blacklist = []
                migrated = True

            if not isinstance(whitelist, list):
                whitelist = []
                migrated = True

            blacklist = [
                name.strip()
                for name in blacklist
                if isinstance(name, str) and name.strip()
            ]
            whitelist = [
                name.strip()
                for name in whitelist
                if isinstance(name, str) and name.strip()
            ]

            blacklist_names = {
                self.__normalize_name(name)
                for name in blacklist
            }
            filtered_whitelist = [
                name
                for name in whitelist
                if self.__normalize_name(name) not in blacklist_names
            ]

            if len(filtered_whitelist) != len(whitelist):
                migrated = True

            data[player_name] = {
                "enabled": enabled,
                "blacklist": blacklist,
                "whitelist": filtered_whitelist
            }

        if migrated:
            self.__write_tpa_setting_data(data)

        return data

    def __write_tpa_setting_data(self, data: dict) -> None:
        with open(self.__tpa_setting_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def __save_tpa_setting_data(self) -> None:
        self.__write_tpa_setting_data(self.__tpa_setting_data)

    def __get_settings(self, player_name: str) -> dict:
        settings = self.__tpa_setting_data.get(player_name)

        if not isinstance(settings, dict):
            settings = self.__default_settings()
            self.__tpa_setting_data[player_name] = settings

        return settings

    def __get_real_player(
        self,
        name: str,
        expected_xuid: str | None = None
    ) -> Player | None:
        player = self.main.server.get_player(name)
        if player is None:
            return None

        xuid = self.__player_xuid(player)
        if xuid is None:
            return None

        if expected_xuid is not None and xuid != expected_xuid:
            return None

        return player

    @event_handler
    def on_player_join(self, e: PlayerJoinEvent) -> None:
        if self.__player_xuid(e.player) is None:
            return

        if self.__tpa_setting_data.get(e.player.name) is None:
            self.__tpa_setting_data[e.player.name] = self.__default_settings()
            self.__save_tpa_setting_data()

    def tpa_main(self, player: Player) -> None:
        self.__send_request(player)

    def settings_main(self, player: Player) -> None:
        settings = self.__get_settings(player.name)

        settings_form = ActionForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.__text(player, 'request_settings')}",
            content=f"{ColorFormat.GREEN}"
                    f"{self.__text(player, 'settings_content')}",
            on_close=self.main.back_to_main_form
        )

        if settings["enabled"]:
            status_text = self.__text(player, "requests_enabled")
        else:
            status_text = self.__text(player, "requests_disabled")

        settings_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{status_text}",
            icon="textures/ui/craft_toggle_on"
                 if settings["enabled"]
                 else "textures/ui/craft_toggle_off",
            on_click=self.__toggle_requests
        )

        settings_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.__text(player, 'blacklist').format(len(settings['blacklist']))}",
            icon="textures/ui/cancel",
            on_click=self.__manage_list("blacklist")
        )

        settings_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.__text(player, 'whitelist').format(len(settings['whitelist']))}",
            icon="textures/ui/check",
            on_click=self.__manage_list("whitelist")
        )

        settings_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.__text(player, 'back')}",
            icon="textures/ui/refresh_light",
            on_click=self.main.back_to_main_form
        )

        player.send_form(settings_form)

    def __toggle_requests(self, player: Player) -> None:
        settings = self.__get_settings(player.name)
        settings["enabled"] = not settings["enabled"]
        self.__save_tpa_setting_data()
        self.settings_main(player)

    def __manage_list(self, list_name: str):
        def on_click(player: Player) -> None:
            settings = self.__get_settings(player.name)
            entries = sorted(
                settings[list_name],
                key=str.casefold
            )

            form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.__list_title(player, list_name)}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.__list_content(player, list_name)}",
                on_close=self.settings_main
            )

            form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.__text(player, 'add_online')}",
                icon="textures/ui/dressing_room_customization",
                on_click=self.__add_online_player(list_name)
            )

            form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.__text(player, 'add_offline')}",
                icon="textures/ui/color_plus",
                on_click=self.__add_offline_player(list_name)
            )

            for entry in entries:
                form.add_button(
                    f"{ColorFormat.RED}"
                    f"{self.__text(player, 'remove_entry').format(entry)}",
                    icon="textures/ui/icon_trash",
                    on_click=self.__remove_list_entry(list_name, entry)
                )

            form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.__text(player, 'back')}",
                icon="textures/ui/refresh_light",
                on_click=self.settings_main
            )

            player.send_form(form)

        return on_click

    def __add_online_player(self, list_name: str):
        def on_click(player: Player) -> None:
            settings = self.__get_settings(player.name)
            existing_names = {
                self.__normalize_name(name)
                for name in settings[list_name]
            }

            targets = []

            for online_player in self.main.server.online_players:
                if self.__player_xuid(online_player) is None:
                    continue

                if online_player.name == player.name:
                    continue

                if self.__normalize_name(online_player.name) in existing_names:
                    continue

                targets.append(online_player.name)

            targets.sort(key=str.casefold)

            if len(targets) == 0:
                player.send_message(
                    f"{ColorFormat.RED}"
                    f"{self.__text(player, 'no_list_targets')}"
                )
                return

            form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.__text(player, 'add_online_title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.__text(player, 'add_online_content')}",
                on_close=self.__manage_list(list_name)
            )

            for target_name in targets:
                form.add_button(
                    target_name,
                    icon="textures/ui/dressing_room_customization",
                    on_click=self.__add_list_entry(list_name, target_name)
                )

            form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.__text(player, 'back')}",
                icon="textures/ui/refresh_light",
                on_click=self.__manage_list(list_name)
            )

            player.send_form(form)

        return on_click

    def __add_offline_player(self, list_name: str):
        def on_click(player: Player) -> None:
            name_input = TextInput(
                label=self.__text(player, "offline_name_label"),
                placeholder=self.__text(player, "offline_name_placeholder")
            )

            form = ModalForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.__text(player, 'add_offline_title')}",
                controls=[name_input],
                submit_button=f"{ColorFormat.YELLOW}"
                              f"{self.__text(player, 'add')}",
                on_close=self.__manage_list(list_name)
            )

            def on_submit(p: Player, json_str: str) -> None:
                try:
                    data = json.loads(json_str)
                    target_name = str(data[0]).strip()
                except (TypeError, ValueError, IndexError, json.JSONDecodeError):
                    self.__send_error(p)
                    return

                if (
                    not target_name
                    or self.__normalize_name(target_name)
                    == self.__normalize_name(p.name)
                ):
                    self.__send_error(p)
                    return

                self.__add_name_to_list(p, list_name, target_name)
                self.__manage_list(list_name)(p)

            form.on_submit = on_submit
            player.send_form(form)

        return on_click

    def __add_list_entry(self, list_name: str, target_name: str):
        def on_click(player: Player) -> None:
            self.__add_name_to_list(player, list_name, target_name)
            self.__manage_list(list_name)(player)

        return on_click

    def __add_name_to_list(
        self,
        player: Player,
        list_name: str,
        target_name: str
    ) -> None:
        settings = self.__get_settings(player.name)
        other_list_name = (
            "whitelist"
            if list_name == "blacklist"
            else "blacklist"
        )
        normalized_target = self.__normalize_name(target_name)

        settings[other_list_name] = [
            name
            for name in settings[other_list_name]
            if self.__normalize_name(name) != normalized_target
        ]

        if not any(
            self.__normalize_name(name) == normalized_target
            for name in settings[list_name]
        ):
            settings[list_name].append(target_name)

        self.__save_tpa_setting_data()

    def __remove_list_entry(self, list_name: str, target_name: str):
        def on_click(player: Player) -> None:
            settings = self.__get_settings(player.name)
            normalized_target = self.__normalize_name(target_name)

            settings[list_name] = [
                name
                for name in settings[list_name]
                if self.__normalize_name(name) != normalized_target
            ]

            self.__save_tpa_setting_data()
            self.__manage_list(list_name)(player)

        return on_click

    def __send_request(self, player: Player) -> None:
        sender_xuid = self.__player_xuid(player)
        if sender_xuid is None:
            return

        player_targets: list[tuple[str, str]] = []

        for online_player in self.main.server.online_players:
            acceptor_xuid = self.__player_xuid(online_player)
            if acceptor_xuid is None:
                continue

            if online_player.name == player.name:
                continue

            if not player.is_op and not self.__request_allowed(
                player.name,
                online_player.name
            ):
                continue

            player_targets.append((online_player.name, acceptor_xuid))

        if len(player_targets) == 0:
            player.send_message(
                f"{ColorFormat.RED}"
                f"{self.__text(player, 'no_targets')}"
            )
            return

        player_targets.sort(key=lambda target: target[0].lower())
        player_name_list = [name for name, _ in player_targets]

        player_dropdown = Dropdown(
            label=f"{ColorFormat.GREEN}"
                  f"{self.__text(player, 'select_player')}",
            options=player_name_list,
            default_index=0
        )

        mode_list = [
            "TPA",
            "TPAHere"
        ]

        if player.is_op:
            mode_list.extend([
                "TP",
                "TPHere"
            ])

        mode_dropdown = Dropdown(
            label=f"{ColorFormat.GREEN}"
                  f"{self.__text(player, 'select_mode')}",
            options=mode_list,
            default_index=0
        )

        form = ModalForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.__text(player, 'request_teleport')}",
            controls=[
                player_dropdown,
                mode_dropdown
            ],
            submit_button=f"{ColorFormat.YELLOW}"
                          f"{self.__text(player, 'send')}",
            on_close=self.main.back_to_main_form
        )

        def on_submit(p: Player, json_str: str) -> None:
            try:
                data = json.loads(json_str)
                acceptor_name, acceptor_xuid = player_targets[int(data[0])]
                mode = mode_list[int(data[1])]
            except (TypeError, ValueError, IndexError, json.JSONDecodeError):
                self.__send_error(p)
                return

            if self.__player_xuid(p) != sender_xuid:
                return

            acceptor = self.__get_real_player(acceptor_name, acceptor_xuid)
            if acceptor is None:
                p.send_message(
                    f"{ColorFormat.RED}"
                    f"{self.__text(p, 'target_offline').format(acceptor_name)}"
                )
                return

            if mode in ("TP", "TPHere"):
                if not p.is_op:
                    return

                if mode == "TP":
                    p.teleport(acceptor)
                else:
                    acceptor.teleport(p)

                p.send_message(
                    f"{ColorFormat.YELLOW}"
                    f"{self.__text(p, 'direct_success').format(mode, acceptor_name)}"
                )
                return

            if not self.__request_allowed(p.name, acceptor_name):
                p.send_message(
                    f"{ColorFormat.RED}"
                    f"{self.__text(p, 'request_blocked').format(acceptor_name)}"
                )
                return

            if self.__is_whitelisted(p.name, acceptor_name):
                self.__perform_request_teleport(p, acceptor, mode)
                p.send_message(
                    f"{ColorFormat.YELLOW}"
                    f"{self.__text(p, 'whitelist_success').format(mode, acceptor_name)}"
                )
                return

            request_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.__text(acceptor, 'incoming_title').format(mode)}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.__text(acceptor, 'incoming_content').format(p.name, mode)}",
                on_close=self.__busy(p.name, sender_xuid, mode)
            )

            request_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.__text(acceptor, 'accept')}",
                icon="textures/ui/check",
                on_click=self.__request_handler(
                    p.name,
                    sender_xuid,
                    mode,
                    "accept"
                )
            )

            request_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.__text(acceptor, 'deny')}",
                icon="textures/ui/cancel",
                on_click=self.__request_handler(
                    p.name,
                    sender_xuid,
                    mode,
                    "deny"
                )
            )

            acceptor.send_form(request_form)

            p.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.__text(p, 'request_sent').format(mode, acceptor_name)}"
            )

        form.on_submit = on_submit
        player.send_form(form)

    def __request_allowed(
        self,
        sender_name: str,
        acceptor_name: str
    ) -> bool:
        settings = self.__get_settings(acceptor_name)

        if not settings["enabled"]:
            return False

        normalized_sender = self.__normalize_name(sender_name)

        return not any(
            self.__normalize_name(name) == normalized_sender
            for name in settings["blacklist"]
        )

    def __is_whitelisted(
        self,
        sender_name: str,
        acceptor_name: str
    ) -> bool:
        settings = self.__get_settings(acceptor_name)
        normalized_sender = self.__normalize_name(sender_name)

        return any(
            self.__normalize_name(name) == normalized_sender
            for name in settings["whitelist"]
        )

    @staticmethod
    def __perform_request_teleport(
        sender: Player,
        acceptor: Player,
        mode: str
    ) -> None:
        if mode == "TPA":
            sender.teleport(acceptor)
        else:
            acceptor.teleport(sender)

    def __busy(
        self,
        sender_name: str,
        sender_xuid: str,
        mode: str
    ):
        def on_click(acceptor: Player) -> None:
            sender = self.__get_real_player(sender_name, sender_xuid)
            if sender is not None:
                sender.send_message(
                    f"{ColorFormat.RED}"
                    f"{self.__text(sender, 'busy').format(mode, acceptor.name)}"
                )

        return on_click

    def __request_handler(
        self,
        sender_name: str,
        sender_xuid: str,
        mode: str,
        selection: str
    ):
        def on_click(player: Player) -> None:
            sender = self.__get_real_player(sender_name, sender_xuid)

            if selection == "accept":
                if sender is None:
                    player.send_message(
                        f"{ColorFormat.RED}"
                        f"{self.__text(player, 'sender_offline').format(sender_name)}"
                    )
                    return

                self.__perform_request_teleport(sender, player, mode)
                return

            if sender is not None:
                sender.send_message(
                    f"{ColorFormat.RED}"
                    f"{self.__text(sender, 'denied').format(player.name, mode)}"
                )

        return on_click

    def __list_title(self, player: Player, list_name: str) -> str:
        if list_name == "blacklist":
            return self.__text(player, "blacklist_title")

        return self.__text(player, "whitelist_title")

    def __list_content(self, player: Player, list_name: str) -> str:
        if list_name == "blacklist":
            return self.__text(player, "blacklist_content")

        return self.__text(player, "whitelist_content")

    def __send_error(self, player: Player) -> None:
        player.send_message(
            f"{ColorFormat.RED}"
            f"{self.__text(player, 'error')}"
        )

    def __text(self, player: Player, key: str) -> str:
        if self.__is_chinese(player):
            texts = {
                "request_teleport": "请求传送",
                "request_settings": "请求传送设置",
                "settings_content": "管理请求状态和黑白名单。",
                "requests_enabled": "请求传送：已开启",
                "requests_disabled": "请求传送：已关闭",
                "blacklist": "黑名单 ({0})",
                "whitelist": "白名单 ({0})",
                "blacklist_title": "请求传送黑名单",
                "whitelist_title": "请求传送白名单",
                "blacklist_content": "黑名单中的玩家无法向你请求传送。",
                "whitelist_content": "白名单中的玩家请求传送时无需你确认。",
                "add_online": "添加在线玩家",
                "add_offline": "添加离线玩家",
                "add_online_title": "添加在线玩家",
                "add_online_content": "请选择要添加的在线玩家。",
                "add_offline_title": "添加离线玩家",
                "offline_name_label": "玩家名",
                "offline_name_placeholder": "输入玩家名...",
                "remove_entry": "移除：{0}",
                "no_list_targets": "没有可添加的在线玩家。",
                "add": "添加",
                "back": "返回",
                "select_player": "选择玩家",
                "select_mode": "选择模式",
                "send": "发送",
                "no_targets": "当前没有可请求传送的玩家。",
                "target_offline": "玩家 {0} 已离线。",
                "request_blocked": "无法向玩家 {0} 请求传送。",
                "request_sent": "已向玩家 {1} 发送 {0} 请求。",
                "whitelist_success": "玩家 {1} 已将你加入白名单，{0} 已直接执行。",
                "direct_success": "已对玩家 {1} 直接执行 {0}。",
                "incoming_title": "{0} 请求",
                "incoming_content": "玩家 {0} 向你发送了一个 {1} 请求。",
                "accept": "接受",
                "deny": "拒绝",
                "busy": "{0} 请求失败：玩家 {1} 当前忙碌。",
                "sender_offline": "玩家 {0} 已离线，请求无法接受。",
                "denied": "玩家 {0} 拒绝了你的 {1} 请求。",
                "error": "表单解析错误，请重新操作。"
            }
        else:
            texts = {
                "request_teleport": "Teleport Request",
                "request_settings": "Teleport Request Settings",
                "settings_content": "Manage request status, blacklist and whitelist.",
                "requests_enabled": "Teleport requests: enabled",
                "requests_disabled": "Teleport requests: disabled",
                "blacklist": "Blacklist ({0})",
                "whitelist": "Whitelist ({0})",
                "blacklist_title": "Teleport Request Blacklist",
                "whitelist_title": "Teleport Request Whitelist",
                "blacklist_content": "Blacklisted players cannot send teleport requests to you.",
                "whitelist_content": "Whitelisted players can teleport without your confirmation.",
                "add_online": "Add Online Player",
                "add_offline": "Add Offline Player",
                "add_online_title": "Add Online Player",
                "add_online_content": "Select an online player to add.",
                "add_offline_title": "Add Offline Player",
                "offline_name_label": "Player name",
                "offline_name_placeholder": "Enter player name...",
                "remove_entry": "Remove: {0}",
                "no_list_targets": "There are no online players available to add.",
                "add": "Add",
                "back": "Back",
                "select_player": "Select player",
                "select_mode": "Select mode",
                "send": "Send",
                "no_targets": "There are no players available for teleport requests.",
                "target_offline": "Player {0} is offline.",
                "request_blocked": "Cannot send a teleport request to player {0}.",
                "request_sent": "Sent a {0} request to player {1}.",
                "whitelist_success": "Player {1} whitelisted you; {0} was executed immediately.",
                "direct_success": "Executed {0} directly on player {1}.",
                "incoming_title": "{0} Request",
                "incoming_content": "Player {0} sent you a {1} request.",
                "accept": "Accept",
                "deny": "Deny",
                "busy": "{0} request failed: player {1} is busy.",
                "sender_offline": "Player {0} is offline; the request cannot be accepted.",
                "denied": "Player {0} denied your {1} request.",
                "error": "Failed to parse the form. Please try again."
            }

        return texts[key]
