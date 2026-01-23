import math
import time

from endstone import ColorFormat, Player
from endstone.command import CommandSenderWrapper


class TPR:
    def __init__(self, main: "Main"):
        self.main = main

        self.lang_funct = main.lang_funct
        self.config_funct = main.config_funct

        self.__tpr_recorder = {}

    def tpr_main(self, player: Player):
        if player.dimension.type.value != 0:
            player.send_message(
                f"{ColorFormat.RED}"
                f"[{self.lang_funct.get_text(player, 'tpr.message.fail')}] "
                f"{ColorFormat.WHITE}"
                f"{self.lang_funct.get_text(player, 'tpr.message.fail.reason1')}"
            )

            return

        if self.__tpr_recorder.get(player.name) is not None:
            last_tpr_time = self.__tpr_recorder[player.name]

            current_time = time.time()

            interval = int(current_time - last_tpr_time)

            tpr_cooldown = self.config_funct.config_data["tpr_cooldown"]

            if interval < tpr_cooldown:
                wait_time = tpr_cooldown - interval

                player.send_message(
                    f"{ColorFormat.RED}"
                    f"[{self.lang_funct.get_text(player, 'tpr.message.fail')}] "
                    f"{ColorFormat.WHITE}"
                    f"{self.lang_funct.get_text(player, 'tpr.message.fail.reason2').format(wait_time)}"
                )

                return

        loc = [
            math.floor(player.location.x),
            math.floor(player.location.z)
        ]

        tpr_time = time.time()

        tpr_range = self.config_funct.config_data["tpr_range"]

        print(tpr_range)

        if player.name.find(" ") != -1:
            player_name = f'"{player.name}"'
        else:
            player_name = player.name

        command_sender = CommandSenderWrapper(
            self.main.server.command_sender,
            on_message=None
        )

        self.main.server.dispatch_command(
            command_sender,
            f'spreadplayers {loc[0]} {loc[1]} 0 {tpr_range} {player_name}'
        )

        self.main.server.dispatch_command(
            command_sender,
            f'effect {player_name} resistance 20 255 true'
        )

        self.__tpr_recorder[player.name] = tpr_time

        for online_player in self.main.server.online_players:
            online_player.send_message(
                f"{ColorFormat.YELLOW}"
                f"[TPR] "
                f"{ColorFormat.WHITE}"
                f"{self.lang_funct.get_text(player, 'tpr.message.broadcast').format(player.name)}"
            )
