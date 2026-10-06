import json
import math

from endstone import ColorFormat, Player
from endstone.form import Dropdown, ModalForm, TextInput
from endstone.level import Location


class AdminTeleport:
    def __init__(self, main: "Main"):
        self.main = main

    @staticmethod
    def __is_chinese(player: Player) -> bool:
        return player.locale.lower().startswith("zh")

    def button_text(self, player: Player) -> str:
        if self.__is_chinese(player):
            return "管理员直传"

        return "Admin Teleport"

    def admin_teleport_main(self, player: Player) -> None:
        if not player.is_op:
            return

        dimensions = list(self.main.server.level.dimensions)
        if len(dimensions) == 0:
            self.__send_error(player)
            return

        dimension_options = [
            self.__dimension_name(player, dimension)
            for dimension in dimensions
        ]

        current_dimension_index = 0

        for index, dimension in enumerate(dimensions):
            if dimension.name == player.dimension.name:
                current_dimension_index = index
                break

        location = player.location

        dimension_dropdown = Dropdown(
            label=self.__text(player, "dimension"),
            options=dimension_options,
            default_index=current_dimension_index
        )

        x_input = TextInput(
            label="X",
            placeholder=self.__text(player, "coordinate_placeholder"),
            default_value=self.__format_coordinate(location.x)
        )

        y_input = TextInput(
            label="Y",
            placeholder=self.__text(player, "coordinate_placeholder"),
            default_value=self.__format_coordinate(location.y)
        )

        z_input = TextInput(
            label="Z",
            placeholder=self.__text(player, "coordinate_placeholder"),
            default_value=self.__format_coordinate(location.z)
        )

        form = ModalForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.__text(player, 'title')}",
            controls=[
                dimension_dropdown,
                x_input,
                y_input,
                z_input
            ],
            submit_button=f"{ColorFormat.YELLOW}"
                          f"{self.__text(player, 'submit')}",
            on_close=self.main.back_to_main_form
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

            target_dimension = dimensions[dimension_index]
            target_location = Location(
                target_dimension,
                x=x,
                y=y,
                z=z,
                pitch=p.location.pitch,
                yaw=p.location.yaw
            )

            p.teleport(target_location)

            p.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.__text(p, 'success').format(
                    self.__dimension_name(p, target_dimension),
                    self.__format_coordinate(x),
                    self.__format_coordinate(y),
                    self.__format_coordinate(z)
                )}"
            )

        form.on_submit = on_submit

        player.send_form(form)

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

    @staticmethod
    def __format_coordinate(value: float) -> str:
        return f"{value:.6f}".rstrip("0").rstrip(".")

    def __text(self, player: Player, key: str) -> str:
        if self.__is_chinese(player):
            texts = {
                "title": "管理员直传",
                "dimension": "目标维度",
                "coordinate_placeholder": "输入坐标...",
                "submit": "传送",
                "overworld": "主世界",
                "nether": "下界",
                "the_end": "末地",
                "success": "已传送至 {0} ({1}, {2}, {3})",
                "error": "传送失败，请检查维度和坐标..."
            }
        else:
            texts = {
                "title": "Admin Teleport",
                "dimension": "Target dimension",
                "coordinate_placeholder": "Enter coordinate...",
                "submit": "Teleport",
                "overworld": "Overworld",
                "nether": "Nether",
                "the_end": "The End",
                "success": "Teleported to {0} ({1}, {2}, {3})",
                "error": "Teleport failed. Check the dimension and coordinates."
            }

        return texts[key]
