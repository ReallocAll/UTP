import os

from endstone import ColorFormat, Player
from endstone.plugin import Plugin
from endstone.command import Command, CommandSender, CommandSenderWrapper
from endstone.form import ActionForm

from endstone_utp.lang import Lang
from endstone_utp.config import Config

from endstone_utp.functions.home import Home
from endstone_utp.functions.warp import Warp
from endstone_utp.functions.back import Back
from endstone_utp.functions.tpa import TPA
from endstone_utp.functions.tpr import TPR
from endstone_utp.functions.admin_teleport import AdminTeleport


class Main(Plugin):
    api_version = "0.10"

    def __init__(self):
        super().__init__()

        self.first_dir_path = os.path.join(os.getcwd(), "plugins", "utp")

        if not os.path.exists(self.first_dir_path):
            os.mkdir(self.first_dir_path)

        self.lang_funct = Lang(self)
        self.config_funct = Config(self)

        self.command_sender = ""

        self.home_funct = Home(self)
        self.warp_funct = Warp(self)
        self.back_funct = Back(self)
        self.tpa_funct = TPA(self)
        self.tpr_funct = TPR(self)
        self.admin_teleport_funct = AdminTeleport(self)

    commands = {
        "utp": {
            "description": "Call out the main form of UTP...",
            "usages": ["/utp"],
            "permissions": ["Main.command.utp"]
        }
    }

    permissions = {
        "Main.command.utp": {
            "description": "Call out the main form of UTP...",
            "default": True
        }
    }

    def on_enable(self) -> None:
        self.register_events(self.home_funct)
        self.register_events(self.back_funct)
        self.register_events(self.tpa_funct)

        self.command_sender = CommandSenderWrapper(
            self.server.command_sender,
            on_message=None
        )

        self.logger.info(
            f"{ColorFormat.YELLOW}"
            f"UTP is enabled..."
        )

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> None:
        if command.name == "utp":
            if not isinstance(sender, Player):
                self.logger.error(
                    f"{ColorFormat.RED}"
                    f"This command can only be executed by a player..."
                )

                return

            main_form = ActionForm(
                title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                      f"{self.lang_funct.get_text(sender, 'main_form.title')}",
                content=f"{ColorFormat.GREEN}"
                        f"{self.lang_funct.get_text(sender, 'main_form.content')}"
            )

            if self.config_funct.config_data["is_enabled"]["home"]:
                main_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(sender, 'main_form.button.home')}",
                    icon="textures/items/ender_pearl",
                    on_click=self.home_funct.home_main
                )

            if self.config_funct.config_data["is_enabled"]["warp"]:
                main_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(sender, 'main_form.button.warp')}",
                    icon="textures/items/ender_eye",
                    on_click=self.warp_funct.warp_main
                )

            if self.config_funct.config_data["is_enabled"]["back"]:
                main_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(sender, 'main_form.button.back')}",
                    icon="textures/ui/friend_glyph_desaturated",
                    on_click=self.back_funct.back_main
                )

            if self.config_funct.config_data["is_enabled"]["tpa"]:
                main_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(sender, 'main_form.button.tpa')}",
                    icon="textures/ui/dressing_room_customization",
                    on_click=self.tpa_funct.tpa_main
                )

            if self.config_funct.config_data["is_enabled"]["tpr"]:
                main_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(sender, 'main_form.button.tpr')}",
                    icon="textures/ui/icon_random",
                    on_click=self.tpr_funct.tpr_main
                )

            if sender.is_op:
                main_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.admin_teleport_funct.button_text(sender)}",
                    icon="textures/ui/realmsIcon",
                    on_click=self.admin_teleport_funct.admin_teleport_main
                )

            main_form.add_button(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(sender, 'main_form.button.reload_config')}",
                icon="textures/ui/icon_setting",
                on_click=self.config_funct.reload_config_main
            )

            if self.server.plugin_manager.get_plugin("zx_ui") is None:
                main_form.on_close = None

                main_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(sender, 'button.close')}",
                    icon="textures/ui/cancel",
                    on_click=None
                )
            else:
                main_form.on_close = Main.back_to_zx_ui

                main_form.add_button(
                    f"{ColorFormat.YELLOW}"
                    f"{self.lang_funct.get_text(sender, 'button.back')}",
                    icon="textures/ui/refresh_light",
                    on_click=Main.back_to_zx_ui
                )

            sender.send_form(main_form)

    @staticmethod
    def back_to_zx_ui(player: Player):
        player.perform_command("cd")

    @staticmethod
    def back_to_main_form(player: Player):
        player.perform_command("utp")
