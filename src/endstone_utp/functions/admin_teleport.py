import json
import math

from endstone import ColorFormat, Player
from endstone.form import ActionForm, Dropdown, ModalForm, TextInput
from endstone.level import Location


class AdminTeleport:
    def __init__(self, main: "Main"):
        self.main = main

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

    def button_text(self, player: Player) -> str:
        return self.__text(player, "title")

    def admin_teleport_main(self, player: Player) -> None:
        if not player.is_op:
            return

        form = ActionForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.__text(player, 'title')}",
            content=f"{ColorFormat.GREEN}"
                    f"{self.__text(player, 'content')}",
            on_close=self.main.back_to_main_form
        )

        form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.__text(player, 'teleport_self')}",
            icon="textures/ui/realmsIcon",
            on_click=self.__teleport_self
        )

        form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.__text(player, 'teleport_player')}",
            icon="textures/ui/dressing_room_customization",
            on_click=self.__select_player
        )

        form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.__text(player, 'back')}",
            icon="textures/ui/refresh_light",
            on_click=self.main.back_to_main_form
        )

        player.send_form(form)

    def __teleport_self(self, player: Player) -> None:
        if not player.is_op:
            return

        self.__send_coordinate_form(player, player)

    def __select_player(self, player: Player) -> None:
        if not player.is_op:
            return

        player_targets = []

        for online_player in self.main.server.online_players:
            xuid = self.__player_xuid(online_player)
            if xuid is None:
                continue

            if online_player.name == player.name:
                continue

            player_targets.append((online_player.name, xuid))

        player_targets.sort(key=lambda target: target[0].lower())

        if len(player_targets) == 0:
            player.send_message(
                f"{ColorFormat.RED}"
                f"{self.__text(player, 'no_players')}"
            )
            return

        form = ActionForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.__text(player, 'select_player_title')}",
            content=f"{ColorFormat.GREEN}"
                    f"{self.__text(player, 'select_player_content')}",
            on_close=self.admin_teleport_main
        )

        for player_name, player_xuid in player_targets:
            form.add_button(
                player_name,
                icon="textures/ui/dressing_room_customization",
                on_click=self.__select_player_handler(player_name, player_xuid)
            )

        form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.__text(player, 'back')}",
            icon="textures/ui/refresh_light",
            on_click=self.admin_teleport_main
        )

        player.send_form(form)

    def __select_player_handler(self, player_name: str, player_xuid: str):
        def on_click(admin: Player) -> None:
            if not admin.is_op:
                return

            target = self.__get_real_player(player_name, player_xuid)
            if target is None:
                self.__send_target_unavailable(admin, player_name)
                return

            self.__send_coordinate_form(
                admin,
                target,
                player_name=player_name,
                player_xuid=player_xuid
            )

        return on_click

    def __send_coordinate_form(
        self,
        admin: Player,
        target: Player,
        player_name: str | None = None,
        player_xuid: str | None = None
    ) -> None:
        if not admin.is_op:
            return

        dimensions = list(self.main.server.level.dimensions)
        if len(dimensions) == 0:
            self.__send_error(admin)
            return

        dimension_options = [
            self.__dimension_name(admin, dimension)
            for dimension in dimensions
        ]

        current_dimension_index = 0

        for index, dimension in enumerate(dimensions):
            if dimension.name == target.dimension.name:
                current_dimension_index = index
                break

        location = target.location

        dimension_dropdown = Dropdown(
            label=self.__text(admin, "dimension"),
            options=dimension_options,
            default_index=current_dimension_index
        )

        x_input = TextInput(
            label="X",
            placeholder=self.__text(admin, "coordinate_placeholder"),
            default_value=self.__format_coordinate(location.x)
        )

        y_input = TextInput(
            label="Y",
            placeholder=self.__text(admin, "coordinate_placeholder"),
            default_value=self.__format_coordinate(location.y)
        )

        z_input = TextInput(
            label="Z",
            placeholder=self.__text(admin, "coordinate_placeholder"),
            default_value=self.__format_coordinate(location.z)
        )

        if player_name is None:
            title = self.__text(admin, "self_title")
            on_close = self.admin_teleport_main
        else:
            title = self.__text(admin, "player_title").format(player_name)
            on_close = self.__select_player

        form = ModalForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{title}",
            controls=[
                dimension_dropdown,
                x_input,
                y_input,
                z_input
            ],
            submit_button=f"{ColorFormat.YELLOW}"
                          f"{self.__text(admin, 'submit')}",
            on_close=on_close
        )

        def on_submit(p: Player, json_str: str) -> None:
            if not p.is_op:
                return

            try:
                data = json.loads(json_str)

                dimension_index = int(data[0])
                if dimension_index < 0 or dimension_index >= len(dimensions):
                    raise ValueError

                x = float(data[1])
                y = float(data[2])
                z = float(data[3])

                if not all(math.isfinite(value) for value in (x, y, z)):
                    raise ValueError
            except (TypeError, ValueError, IndexError, json.JSONDecodeError):
                self.__send_error(p)
                return

            if player_name is None:
                teleport_target = p
            else:
                teleport_target = self.__get_real_player(player_name, player_xuid)
                if teleport_target is None:
                    self.__send_target_unavailable(p, player_name)
                    return

            target_dimension = dimensions[dimension_index]
            target_location = Location(
                target_dimension,
                x=x,
                y=y,
                z=z,
                pitch=teleport_target.location.pitch,
                yaw=teleport_target.location.yaw
            )

            teleport_target.teleport(target_location)

            if player_name is None:
                message = self.__text(p, "self_success").format(
                    self.__dimension_name(p, target_dimension),
                    self.__format_coordinate(x),
                    self.__format_coordinate(y),
                    self.__format_coordinate(z)
                )
            else:
                message = self.__text(p, "player_success").format(
                    player_name,
                    self.__dimension_name(p, target_dimension),
                    self.__format_coordinate(x),
                    self.__format_coordinate(y),
                    self.__format_coordinate(z)
                )

            p.send_message(
                f"{ColorFormat.YELLOW}"
                f"{message}"
            )

        form.on_submit = on_submit

        admin.send_form(form)

    def __get_real_player(self, player_name: str, player_xuid: str | None) -> Player | None:
        player = self.main.server.get_player(player_name)
        if player is None:
            return None

        current_xuid = self.__player_xuid(player)
        if current_xuid is None:
            return None

        if player_xuid is not None and current_xuid != player_xuid:
            return None

        return player

    def __dimension_name(self, player: Player, dimension) -> str:
        dimension_type = dimension.type.value

        if dimension_type == 0:
            return self.__text(player, "overworld")

        if dimension_type == 1:
            return self.__text(player, "nether")

        if dimension_type == 2:
            return self.__text(player, "the_end")

        return dimension.name

    def __send_error(self, player: Player) -> None:
        player.send_message(
            f"{ColorFormat.RED}"
            f"{self.__text(player, 'error')}"
        )

    def __send_target_unavailable(self, player: Player, player_name: str) -> None:
        player.send_message(
            f"{ColorFormat.RED}"
            f"{self.__text(player, 'target_unavailable').format(player_name)}"
        )

    @staticmethod
    def __format_coordinate(value: float) -> str:
        return f"{value:.6f}".rstrip("0").rstrip(".")

    def __text(self, player: Player, key: str) -> str:
        if self.__is_chinese(player):
            texts = {
                "title": "管理员直传",
                "content": "请选择传送目标...",
                "teleport_self": "传送自己",
                "teleport_player": "传送玩家",
                "select_player_title": "选择玩家",
                "select_player_content": "请选择要直接传送的在线玩家...",
                "self_title": "传送自己",
                "player_title": "传送玩家: {0}",
                "dimension": "目标维度",
                "coordinate_placeholder": "输入坐标...",
                "submit": "传送",
                "back": "返回",
                "overworld": "主世界",
                "nether": "下界",
                "the_end": "末地",
                "self_success": "已传送至 {0} ({1}, {2}, {3})",
                "player_success": "已将玩家 {0} 传送至 {1} ({2}, {3}, {4})",
                "no_players": "当前没有可直接传送的在线玩家...",
                "target_unavailable": "玩家 {0} 已离线或不再可用...",
                "error": "传送失败，请检查维度和坐标..."
            }
        else:
            texts = {
                "title": "Admin Teleport",
                "content": "Select a teleport target...",
                "teleport_self": "Teleport Self",
                "teleport_player": "Teleport Player",
                "select_player_title": "Select Player",
                "select_player_content": "Select an online player to teleport...",
                "self_title": "Teleport Self",
                "player_title": "Teleport Player: {0}",
                "dimension": "Target dimension",
                "coordinate_placeholder": "Enter coordinate...",
                "submit": "Teleport",
                "back": "Back",
                "overworld": "Overworld",
                "nether": "Nether",
                "the_end": "The End",
                "self_success": "Teleported to {0} ({1}, {2}, {3})",
                "player_success": "Teleported player {0} to {1} ({2}, {3}, {4})",
                "no_players": "There are no online players available to teleport.",
                "target_unavailable": "Player {0} is offline or no longer available.",
                "error": "Teleport failed. Check the dimension and coordinates."
            }

        return texts[key]
