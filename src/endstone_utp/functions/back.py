import math
import time

from endstone import ColorFormat, Player
from endstone.level import Location
from endstone.event import event_handler, PlayerDeathEvent


class Back:
    def __init__(self, main: "Main"):
        self.main = main

        self.lang_funct = main.lang_funct
        self.config_funct = main.config_funct

        self.__death_recorder = {}

    def back_main(self, player: Player) -> None:
        back_expiry_window = self.config_funct.config_data["back_expiry_window"]

        if self.__death_recorder.get(player.name) is None:
            player.send_message(
                f"{ColorFormat.RED}"
                f"[{self.lang_funct.get_text(player, 'back.message.fail')}] "
                f"{ColorFormat.WHITE}"
                f"{self.lang_funct.get_text(player, 'back.message.fail.reason').format(back_expiry_window)}"
            )
        else:
            current_time = time.time()

            death_time = self.__death_recorder[player.name]["death_time"]

            if int(current_time - death_time) > back_expiry_window:
                player.send_message(
                    f"{ColorFormat.RED}"
                    f"[{self.lang_funct.get_text(player, 'back.message.fail')}] "
                    f"{ColorFormat.WHITE}"
                    f"{self.lang_funct.get_text(player, 'back.message.fail.reason').format(back_expiry_window)}"
                )
            else:
                death_dim: str = self.__death_recorder[player.name]["death_dim"]

                death_loc: list = self.__death_recorder[player.name]["death_loc"]

                target_dim = self.main.server.level.get_dimension(death_dim.upper())

                target_loc = Location(
                    target_dim,
                    x=float(death_loc[0]),
                    y=float(death_loc[1]),
                    z=float(death_loc[2])
                )

                player.teleport(target_loc)

                player.send_message(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(player, 'back.message.success')}"
                )

            self.__death_recorder.pop(player.name)

    @event_handler
    def on_player_death(self, e: PlayerDeathEvent):
        # Always up to date
        if self.config_funct.config_data["is_enabled"]["back"]:
            death_dim = e.player.dimension.name

            death_loc = [
                math.floor(e.player.location.x),
                math.floor(e.player.location.y),
                math.floor(e.player.location.z)
            ]

            death_time = time.time()

            self.__death_recorder[e.player.name] = {
                "death_dim": death_dim,
                "death_loc": death_loc,
                "death_time": death_time
            }

        if self.config_funct.config_data["is_enabled"]["death_penalty"]:
            if self.main.server.plugin_manager.get_plugin("umoney") is not None:
                umoney = self.main.server.plugin_manager.get_plugin("umoney")

                death_penalty_rate = self.config_funct.config_data["death_penalty_rate"]

                player_money = umoney.api_get_player_money(e.player.name)

                death_penalty = int(player_money * death_penalty_rate)

                if death_penalty != 0:
                    e.player.send_message(
                        f"{ColorFormat.RED}"
                        f"{self.lang_funct.get_text(e.player, 'death_penalty.message')}"
                    )

                    umoney.api_change_player_money(e.player.name, -death_penalty)
