import os
import json

from endstone import ColorFormat, Player
from endstone.form import ActionForm, ModalForm, Toggle, TextInput


class Config:
    def __init__(self, main: "Main"):
        self.main = main

        self.__config_data_file_path = os.path.join(self.main.first_dir_path, "config.json")
        self.config_data = self.__load_config_data()

        self.lang_funct = main.lang_funct

    def __load_config_data(self) -> dict:
        if not os.path.exists(self.__config_data_file_path):
            with open(self.__config_data_file_path, "w") as f:
                config_data = {
                    "max_home": 5,
                    "back_expiry_window": 30,   # In seconds
                    "death_penalty_rate": 0.01,
                    "tpr_range": 2000,
                    "tpr_cooldown": 60,     # In seconds
                    "is_enabled": {
                        "home": True,
                        "warp": True,
                        "back": True,
                        "tpa": True,
                        "tpr": True,
                        "death_penalty": False,
                    }
                }
                json_str = json.dumps(config_data, indent=4, ensure_ascii=False)
                f.write(json_str)
        else:
            with open(self.__config_data_file_path, "r") as f:
                config_data = json.loads(f.read())

        return config_data

    def __save_config_data(self) -> None:
        with open(self.__config_data_file_path, "w+") as f:
            json_str = json.dumps(self.config_data, indent=4, ensure_ascii=False)
            f.write(json_str)

    def reload_config_main(self, player: Player):
        reload_config_form = ActionForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'reload_config_form.title')}",
            content=f"{ColorFormat.GREEN}"
                    f"{self.lang_funct.get_text(player, 'reload_config_form.content')}",
            on_close=self.main.back_to_main_form
        )

        reload_config_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.lang_funct.get_text(player, 'reload_config_form.button.reload_function_toggles')}",
            icon="textures/ui/craft_toggle_off",
            on_click=self.__reload_function_toggles
        )

        reload_config_form.add_button(
            f"{ColorFormat.YELLOW}"
            f"{self.lang_funct.get_text(player, 'reload_config_form.button.reload_global_config')}",
            icon="textures/ui/icon_setting",
            on_click=self.__reload_global_config
        )

        player.send_form(reload_config_form)

    def __reload_function_toggles(self, player: Player) -> None:
        controls_list = []

        for key, value in self.config_data["is_enabled"].items():
            text_key = "reload_function_toggles." + key

            if key == "tpa":
                label = self.main.tpa_funct.button_text(player)
            else:
                label = self.lang_funct.get_text(player, text_key)

            toggle = Toggle(
                label=f"{ColorFormat.GREEN}"
                      f"{label}"
            )

            if value:
                toggle.default_value = True
            else:
                toggle.default_value = False

            controls_list.append(toggle)

        reload_function_toggles_form = ModalForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'reload_function_toggles_form.title')}",
            controls=controls_list,
            submit_button=f"{ColorFormat.YELLOW}"
                          f"{self.lang_funct.get_text(player, 'reload_function_toggles_form.submit_button')}",
            on_close=self.reload_config_main
        )

        def on_submit(p: Player, json_str: str) -> None:
            data = json.loads(json_str)

            data_index = 0

            for key1 in self.config_data["is_enabled"].keys():
                self.config_data["is_enabled"][key1] = data[data_index]

                data_index += 1

            self.__save_config_data()

            p.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(p, 'reload_function_toggles.message.success')}"
            )

        reload_function_toggles_form.on_submit = on_submit

        player.send_form(reload_function_toggles_form)

    def __reload_global_config(self, player: Player) -> None:
        controls_list = []

        index = 1

        for key, value in self.config_data.items():
            if key == "is_enabled":
                continue

            label_text_key = "reload_global_config_form.textinput" + str(index) + ".label"
            placeholder_text_key = "reload_global_config_form.textinput" + str(index) + ".placeholder"

            textinput = TextInput(
                label=f"{ColorFormat.GREEN}"
                      f"{self.lang_funct.get_text(player, label_text_key)}: "
                      f"{ColorFormat.WHITE}"
                      f"{value}",
                placeholder=self.lang_funct.get_text(player, placeholder_text_key),
                default_value=f"{value}"
            )

            controls_list.append(textinput)

            index += 1

        reload_global_config_form = ModalForm(
            title=f"{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}"
                  f"{self.lang_funct.get_text(player, 'reload_global_config_form.title')}",
            controls=controls_list,
            submit_button=f"{ColorFormat.YELLOW}"
                          f"{self.lang_funct.get_text(player, 'reload_global_config_form.submit_button')}",
            on_close=self.reload_config_main
        )

        def on_submit(p: Player, json_str: str) -> None:
            pre_data: list = json.loads(json_str)

            data = []

            for pre_data_value in pre_data:
                if pre_data.index(pre_data_value) == 2:
                    try:
                        data_value = float(pre_data_value)
                    except:
                        p.send_message(
                            f"{ColorFormat.RED}"
                            f"{self.lang_funct.get_text(p, 'message.error')}"
                        )

                        return
                else:
                    try:
                        data_value = int(pre_data_value)
                    except:
                        p.send_message(
                            f"{ColorFormat.RED}"
                            f"{self.lang_funct.get_text(p, 'message.error')}"
                        )

                        return

                data.append(data_value)

            for data_value in data:
                if data.index(data_value) == 2:
                    if data_value <= 0 or data_value >= 1:
                        p.send_message(
                            f"{ColorFormat.RED}"
                            f"{self.lang_funct.get_text(p, 'message.error')}"
                        )

                        return
                else:
                    if data_value <= 0:
                        p.send_message(
                            f"{ColorFormat.RED}"
                            f"{self.lang_funct.get_text(p, 'message.error')}"
                        )

                        return

            data_index = 0

            for key1 in self.config_data.keys():
                if key1 == "is_enabled":
                    continue

                self.config_data[key1] = data[data_index]

                data_index += 1

            self.__save_config_data()

            p.send_message(
                f"{ColorFormat.YELLOW}"
                f"{self.lang_funct.get_text(p, 'reload_global_config.message.success')}"
            )

        reload_global_config_form.on_submit = on_submit

        player.send_form(reload_global_config_form)
