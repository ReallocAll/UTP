import os
import json

from endstone import ColorFormat, Player


# New keys also provide runtime defaults for existing, customized language files.
CONFIG_TEXT = {
    "zh_CN": {
        "config.title": "配置管理",
        "config.content": "从磁盘重载，或编辑当前生效的配置。",
        "config.button.reload": "从磁盘重载 config.json",
        "config.button.toggles": "编辑功能开关",
        "config.button.global": "编辑全局配置",
        "config.button.save": "保存并应用",
        "config.message.no_permission": "你没有管理 UTP 配置的权限。",
        "config.message.reloaded": "已从磁盘重载并应用配置。",
        "config.message.reload_failed": "重载失败，当前配置保持不变。请查看服务器日志，修复 config.json 后重试。",
        "config.message.saved": "配置已保存并生效。",
        "config.message.save_failed": "保存失败，当前配置保持不变。请查看服务器日志。",
        "config.message.conflict": "配置已被修改。请从磁盘重载，再重新打开编辑表单。此次修改未保存。",
        "config.toggle.home": "私人传送点",
        "config.toggle.warp": "公共传送点",
        "config.toggle.back": "返回上一死亡点",
        "config.toggle.tpa": "请求传送",
        "config.toggle.tpr": "随机传送",
        "config.toggle.death_penalty": "死亡惩罚",
        "config.field.max_home": "每个玩家可创建的私人传送点数量上限",
        "config.field.back_expiry_window": "死亡点记录保留时间（秒）",
        "config.field.death_penalty_rate": "死亡惩罚比率",
        "config.field.tpr_range": "随机传送范围",
        "config.field.tpr_cooldown": "随机传送冷却时间（秒）",
        "config.hint.integer": "输入一个正整数",
        "config.hint.rate": "输入大于 0 且小于 1 的有限小数"
    },
    "en_US": {
        "config.title": "Configuration",
        "config.content": "Reload from disk, or edit the active configuration.",
        "config.button.reload": "Reload config.json from disk",
        "config.button.toggles": "Edit function toggles",
        "config.button.global": "Edit global configuration",
        "config.button.save": "Save and apply",
        "config.message.no_permission": "You do not have permission to manage UTP configuration.",
        "config.message.reloaded": "Configuration reloaded from disk and applied.",
        "config.message.reload_failed": "Reload failed; the active configuration is unchanged. Check the server log, repair config.json and try again.",
        "config.message.saved": "Configuration saved and applied.",
        "config.message.save_failed": "Save failed; the active configuration is unchanged. Check the server log.",
        "config.message.conflict": "Configuration changed. Reload from disk, then reopen the editor. Your changes were not saved.",
        "config.toggle.home": "Home",
        "config.toggle.warp": "Warp",
        "config.toggle.back": "Back",
        "config.toggle.tpa": "Teleport Request",
        "config.toggle.tpr": "TPR",
        "config.toggle.death_penalty": "Death penalty",
        "config.field.max_home": "Maximum homes per player",
        "config.field.back_expiry_window": "Death record lifetime (seconds)",
        "config.field.death_penalty_rate": "Death penalty rate",
        "config.field.tpr_range": "Random teleport range",
        "config.field.tpr_cooldown": "Random teleport cooldown (seconds)",
        "config.hint.integer": "Enter a positive integer",
        "config.hint.rate": "Enter a finite number greater than 0 and less than 1"
    }
}


class Lang:
    def __init__(self, main: "Main"):
        self.main = main

        self.__lang_dir_path = os.path.join(self.main.first_dir_path, "lang")

        if not os.path.exists(self.__lang_dir_path):
            os.mkdir(self.__lang_dir_path)

        self.__lang_data = self.__load_lang_data()

    def __load_lang_data(self) -> dict:
        zh_CN_file_path = os.path.join(self.__lang_dir_path, "zh_CN.json")
        en_US_file_path = os.path.join(self.__lang_dir_path, "en_US.json")

        if not os.path.exists(zh_CN_file_path):
            with open(zh_CN_file_path, "w", encoding="utf-8") as f:
                zh_CN = {
                    "message.error": "表单解析错误, 请按提示正确填写...",

                    "dimension": "维度",
                    "overworld": "主世界",
                    "nether": "地狱",
                    "theend": "末地",
                    "location": "坐标",

                    "button.close": "关闭",
                    "button.back": "返回",
                    "button.back_to_previous": "返回",

                    "main_form.title": "UTP - 主表单",
                    "main_form.content": "请选择操作...",
                    "main_form.button.home": "私人传送点",
                    "main_form.button.warp": "公共传送点",
                    "main_form.button.back": "返回上一死亡点",
                    "main_form.button.tpa": "请求传送",
                    "main_form.button.tpr": "随机传送",
                    "main_form.button.reload_config": "重载配置文件",

                    "home_form.title": "私人传送点",
                    "home_form.content": "请选择操作...",
                    "home_form.button.add_home": "添加新私人传送点",

                    "add_home_form.textinput.label": "输入新私人传送点的名称...",
                    "add_home_form.textinput.placeholder": "输入任意字符串但不能留空...",
                    "add_home_form.title": "添加新私人传送点",
                    "add_home_form.submit_button": "添加",
                    "add_home.message.fail": "添加新私人传送点失败",
                    "add_home.message.fail.reason1": "你已经拥有 {0} 个私人传送点了, 已达服务器分配给每个玩家的上限...",
                    "add_home.message.fail.reason2": "你已经拥有一个名为: {0} 的私人传送点了...",
                    "add_home.message.success": "添加新私人传送点成功...",

                    "home_info_form.title": "私人传送点",
                    "home_info_form.content": "你正在对私人传送点: {0} 进行操作...\n\n请选择操作...",
                    "home_info_form.button.teleport": "传送",
                    "home_info_form.button.edit_home": "编辑私人传送点",

                    "home_teleport.message.success": "传送至私人传送点: {0} 成功...",

                    "edit_home_form.title": "编辑私人传送点",
                    "edit_home_form.content": "你正在对私人传送点: {0} 进行操作...\n\n请选择操作...",
                    "edit_home_form.button.update_home": "更新私人传送点",
                    "edit_home_form.button.delete_home": "删除私人传送点",

                    "update_home_form.title": "更新私人传送点",
                    "update_home_form.content": "你正在对私人传送点: {0} 进行操作...\n\n请选择操作...",
                    "update_home_form.button.update_home_name": "更新私人传送点的名称",
                    "update_home_form.button.update_home_loc": "更新私人传送点的坐标",

                    "update_home_name_form.textinput.label": "你正在对私人传送点: {0} 进行操作...\n\n输入该私人传送点的新名称...",
                    "update_home_name_form.textinput.placeholder": "输入任意字符串但不能留空...",
                    "update_home_name.form.title": "更新私人传送点的名称",
                    "update_home_name_form.submit_button": "更新",
                    "update_home_name.message.fail1": "更新私人传送点: {0} 的名称失败",
                    "update_home_name.message.fail1.reason": "未发生改变...",
                    "update_home_name.message.fail2": "更新私人传送点: {0} 的名称为 {1} 失败",
                    "update_home_name.message.fail2.reason": "你已经有一个名为: {0} 的私人传送点了...",
                    "update_home_name.message.success": "更新私人传送点: {0} 的名称为 {1} 成功...",

                    "update_home_loc_form.title": "更新私人传送点的坐标",
                    "update_home_loc_form.content": "你正在对私人传送点: {0} 进行操作...\n\n你确定将该私人传送点的坐标更新为 {1} 吗?",
                    "update_home_loc_form.confirm": "确认",
                    "update_home_loc.message.fail": "更新私人传送点: {0} 的坐标失败",
                    "update_home_loc.message.fail.reason": "维度不匹配...",
                    "update_home_loc.message.success": "更新私人传送点: {0} 的坐标成功...",

                    "delete_home_form.title": "删除私人传送点",
                    "delete_home_form.content": "你正在对私人传送点: {0} 进行操作...\n\n你确定删除该私人传送点吗?",
                    "delete_home_form.button.confirm": "确认",
                    "delete_home.message.success": "删除私人传送点: {0} 成功...",

                    "warp_form.title": "公共传送点",
                    "warp_form.content": "请选择操作...",
                    "warp_form.button.add_warp": "添加新公共传送点",

                    "add_warp_form.textinput.label": "输入新公共传送点的名称...",
                    "add_warp_form.textinput.placeholder": "输入任意字符串但不能留空...",
                    "add_warp_form.title": "添加新公共传送点",
                    "add_warp_form.submit_button": "添加",
                    "add_warp.message.fail": "添加新公共传送点失败",
                    "add_warp.message.reason": "已经有一个名为: {0} 的公共传送点了...",
                    "add_warp.message.success": "添加新公共传送点成功...",

                    "warp_info_form.title": "公共传送点",
                    "warp_info_form.content": "你正在对公共传送点: {0} 进行操作...\n\n请选择操作...",
                    "warp_info_form.button.teleport": "传送",
                    "warp_info_form.button.edit_warp": "编辑公共传送点",

                    "warp_teleport.message.success": "传送至公共传送点: {0} 成功...",

                    "edit_warp_form.title": "编辑公共传送点",
                    "edit_warp_form.content": "你正在对公共传送点: {0} 进行操作...\n\n请选择操作...",
                    "edit_warp_form.button.update_warp": "更新公共传送点",
                    "edit_warp_form.button.delete_warp": "删除公共传送点",

                    "update_warp_form.title": "更新公共传送点",
                    "update_warp_form.content": "你正在对公共传送点: {0} 进行操作...\n\n请选择操作...",
                    "update_warp_form.button.update_warp_name": "更新公共传送点的名称",
                    "update_warp_form.button.update_warp_loc": "更新公共传送点的坐标",

                    "update_warp_name_form.textinput.label": "你正在对公共传送点: {0} 进行操作...\n\n输入该公共传送点的新名称...",
                    "update_warp_name_form.textinput.placeholder": "输入任意字符串但不能留空...",
                    "update_warp_name.form.title": "更新公共传送点的名称",
                    "update_warp_name_form.submit_button": "更新",
                    "update_warp_name.message.fail1": "更新公共传送点: {0} 的名称失败",
                    "update_warp_name.message.fail.reason": "未发生改变...",
                    "update_warp_name.message.fail2": "更新公共传送点: {0} 的名称为 {1} 失败",
                    "update_warp_name.message.fail2.reason": "已经有一个名为: {0} 的公共传送点了...",
                    "update_warp_name.message.success": "更新公共传送点: {0} 的名称为 {1} 成功...",

                    "update_warp_loc_form.title": "更新公共传送点的坐标成功...",
                    "update_warp_loc_form.content": "你正在对公共传送点: {0} 进行操作...\n\n你确定更新该公共传送点的名称为 {1} 吗?",
                    "update_warp_loc_form.button.confirm": "确认",
                    "update_warp_loc.message.fail": "更新公共传送点: {0} 的坐标失败",
                    "update_warp_loc.message.fail.reason": "维度不匹配...",
                    "update_warp_loc.message.success": "更新公共传送点: {0} 的坐标成功...",

                    "delete_warp_form.title": "删除公共传送点",
                    "delete_warp_form.content": "你正在对公共传送点: {0} 进行操作...\n\n你确定删除该公共传送点吗?",
                    "delete_warp_form.button.confirm": "确认",
                    "delete_warp.message.success": "删除公共传送点: {0} 成功...",

                    "back.message.fail": "返回上一死亡点失败",
                    "back.message.fail.reason": "你近 {0}s 内没有死亡记录...",
                    "back.message.success": "返回上一死亡点成功...",

                    "death_penalty.message": "死亡惩罚!!!",

                    "tpa_form.title": "请求传送",
                    "tpa_form.content": "请选择操作...",
                    "tpa_form.button.tpa_setting": "请求传送设置",
                    "tpa_form.button.send_request": "发送新请求",

                    "tpa_setting_form.toggle.label": "其他玩家能否向你发送 TPA/TPAHere 请求?",
                    "tpa_setting_form.title": "请求传送设置",
                    "tpa_setting_form.submit_button": "更新",
                    "tpa_setting.message.success": "更新 TPA & TPAHere 设置成功...",

                    "send_request_form.dropdown1.label": "选择玩家...",
                    "send_request_form.dropdown2.label": "选择模式...",
                    "send_request_form.title": "发送新请求",
                    "send_request_form.submit_button": "发送",
                    "send_request.message.fail1": "发送新 TPA/TPAHere 请求失败",
                    "send_request.message.fail2": "发送新 {0} 请求失败",
                    "send_request.message.fail1.reason": "没有可用于发送新 TPA/TPAHere 请求的玩家...",
                    "send_request.message.fail2.reason1": "玩家: {0} 已经离线...",
                    "send_request.message.fail2.reason2": "玩家: {0} 忙碌中...",
                    "send_request.message.success": "向玩家: {1} 发送新 {0} 请求成功...",

                    "request_form.title": "{0} 请求",
                    "request_form.content": "玩家: {0} 向你发送了一个 {1} 请求...",
                    "request_form.button.accept": "接受",
                    "request_form.button.deny": "拒绝",

                    "accept.message.fail": "接受该 {0} 请求失败",
                    "accept.message.fail.reason": "玩家: {0} 已经离线...",
                    "deny.message": "玩家: {0} 拒绝了你的 {1} 请求...",

                    "tpr.message.fail": "随机传送失败",
                    "tpr.message.fail.reason1": "只允许在主世界进行随机传送...",
                    "tpr.message.fail.reason2": "随机传送冷却中, 请再等待 {0}s...",
                    "tpr.message.broadcast": "玩家: {0} 正在进行随机传送, 这可能会造成服务器卡顿...",

                    **CONFIG_TEXT["zh_CN"],
                }
                json_str = json.dumps(zh_CN, indent=4, ensure_ascii=False)
                f.write(json_str)

        if not os.path.exists(en_US_file_path):
            with open(en_US_file_path, "w", encoding="utf-8") as f:
                en_US = {
                    "message.error": "error",

                    "dimension": "Dimension",
                    "overworld": "Overworld",
                    "nether": "Nether",
                    "theend": "The End",
                    "location": "Location",

                    "button.close": "Close",
                    "button.back": "Back",
                    "button.back_to_previous": "Back to previous",

                    "main_form.title": "UTP - main form",
                    "main_form.content": "Please select a function...",
                    "main_form.button.home": "Home",
                    "main_form.button.warp": "Warp",
                    "main_form.button.back": "Back",
                    "main_form.button.tpa": "Teleport Request",
                    "main_form.button.tpr": "TPR",
                    "main_form.button.reload_config": "Reload configurations",

                    "home_form.title": "Home",
                    "home_form.content": "Please select a function...",
                    "home_form.button.add_home": "Add a new home",

                    "add_home_form.textinput.label": "Input a name for this new home...",
                    "add_home_form.textinput.placeholder": "Input any string but cannot left blank...",
                    "add_home_form.title": "Add a new home",
                    "add_home_form.submit_button": "Add",
                    "add_home.message.fail": "Failed to add a new home",
                    "add_home.message.fail.reason1": "you already have {0} homes, at or above the current limit...",
                    "add_home.message.fail.reason2": "you already have a home named: {0}...",
                    "add_home.message.success": "Successfully added a new home...",

                    "home_info_form.title": "Home",
                    "home_info_form.content": "You are operating on home: {0}...\n\nPlease select a function...",
                    "home_info_form.button.teleport": "Teleport",
                    "home_info_form.button.edit_home": "Edit this home",

                    "home_teleport.message.success": "Successfully teleported to home: {0}...",

                    "edit_home_form.title": "Edit this home",
                    "edit_home_form.content": "You are operating on home: {0}...\n\nPlease select a function...",
                    "edit_home_form.button.update_home": "Update this home",
                    "edit_home_form.button.delete_home": "Delete this home",

                    "update_home_form.title": "Update this home",
                    "update_home_form.content": "You are operating on home: {0}...\n\nPlease select a function...",
                    "update_home_form.button.update_home_name": "Update this home's name",
                    "update_home_form.button.update_home_loc": "Update this home's location",

                    "update_home_name_form.textinput.label": "You are operating on home: {0}...\n\nInput new name for this home...",
                    "update_home_name_form.textinput.placeholder": "Input any string but cannot left blank...",
                    "update_home_name.form.title": "Update this home's name",
                    "update_home_name_form.submit_button": "Update",
                    "update_home_name.message.fail1": "Failed to update home: {0}'s name",
                    "update_home_name.message.fail1.reason": "nothing changed...",
                    "update_home_name.message.fail2": "Failed to update home: {0}'s name to {1}",
                    "update_home_name.message.fail2.reason": "you already have a home named {0}...",
                    "update_home_name.message.success": "Successfully updated home: {0}'s name to {1}...",

                    "update_home_loc_form.title": "Update this home's location",
                    "update_home_loc_form.content": "You are operating on home: {0}...\n\nAre you sure to update this home's location to {1} ?",
                    "update_home_loc_form.confirm": "Confirm",
                    "update_home_loc.message.fail": "Failed to update home: {0}'s location",
                    "update_home_loc.message.fail.reason": "dimension mismatched...",
                    "update_home_loc.message.success": "Successfully updated home: {0}'s location...",

                    "delete_home_form.title": "Delete this home",
                    "delete_home_form.content": "You are operating on home: {0}...\n\nAre you sure to delete this home?",
                    "delete_home_form.button.confirm": "Confirm",
                    "delete_home.message.success": "Successfully deleted home: {0}...",

                    "warp_form.title": "Warp",
                    "warp_form.content": "Please select a function...",
                    "warp_form.button.add_warp": "Add a new warp",

                    "add_warp_form.textinput.label": "Input a name for this new warp...",
                    "add_warp_form.textinput.placeholder": "Input any string but cannot be blank...",
                    "add_warp_form.title": "Add a new warp",
                    "add_warp_form.submit_button": "Add",
                    "add_warp.message.fail": "Failed to add a new warp",
                    "add_warp.message.reason": "there already exists a warp named {0}...",
                    "add_warp.message.success": "Successfully added a new warp...",

                    "warp_info_form.title": "Warp",
                    "warp_info_form.content": "You are operating on warp: {0}...\n\nPlease select a function...",
                    "warp_info_form.button.teleport": "Teleport",
                    "warp_info_form.button.edit_warp": "Edit this warp",

                    "warp_teleport.message.success": "Successfully teleported to warp: {0}...",

                    "edit_warp_form.title": "Edit this warp",
                    "edit_warp_form.content": "You are operating on warp: {0}...\n\nPlease select a function...",
                    "edit_warp_form.button.update_warp": "Update this warp",
                    "edit_warp_form.button.delete_warp": "Delete this warp",

                    "update_warp_form.title": "Update this warp",
                    "update_warp_form.content": "You are operating on warp: {0}...\n\nPlease select a function...",
                    "update_warp_form.button.update_warp_name": "Update this warp's name",
                    "update_warp_form.button.update_warp_loc": "Update this warp's location",

                    "update_warp_name_form.textinput.label": "You are operating on warp: {0}...\n\nInput new name for this warp...",
                    "update_warp_name_form.textinput.placeholder": "Input any string but cannot left blank...",
                    "update_warp_name.form.title": "Update this warp's name",
                    "update_warp_name_form.submit_button": "Update",
                    "update_warp_name.message.fail1": "Failed to update warp: {0}'s name",
                    "update_warp_name.message.fail.reason": "nothing changed...",
                    "update_warp_name.message.fail2": "Failed to update warp: {0}'s name to {1}",
                    "update_warp_name.message.fail2.reason": "there already exists a warp named {0}...",
                    "update_warp_name.message.success": "Successfully updated warp: {0}'s name to {1}...",

                    "update_warp_loc_form.title": "Update this warp's location",
                    "update_warp_loc_form.content": "You are operating on warp: {0}...\n\nAre you sure to update this warp's location to {1} ?",
                    "update_warp_loc_form.button.confirm": "Confirm",
                    "update_warp_loc.message.fail": "Failed to update update warp: {0}'s location",
                    "update_warp_loc.message.fail.reason": "dimension mismatched...",
                    "update_warp_loc.message.success": "Successfully updated warp: {0}'s location...",

                    "delete_warp_form.title": "Delete this warp",
                    "delete_warp_form.content": "You are operating on warp: {0}...\n\nAre you sure to delete this warp?",
                    "delete_warp_form.button.confirm": "Confirm",
                    "delete_warp.message.success": "Successfully deleted warp: {0}...",

                    "back.message.fail": "Failed to back",
                    "back.message.fail.reason": "you have no death records in the last {0}s...",
                    "back.message.success": "Successfully backed...",

                    "death_penalty.message": "Death penalty!!!",

                    "tpa_form.title": "Teleport Request",
                    "tpa_form.content": "Please select a function...",
                    "tpa_form.button.tpa_setting": "Teleport Request Settings",
                    "tpa_form.button.send_request": "Send a new request",

                    "tpa_setting_form.toggle.label": "Can other players send TPA/TPAHere requests to you?",
                    "tpa_setting_form.title": "Teleport Request Settings",
                    "tpa_setting_form.submit_button": "Update",
                    "tpa_setting.message.success": "Successfully updated tpa setting...",

                    "send_request_form.dropdown1.label": "Select a player...",
                    "send_request_form.dropdown2.label": "Select a mode...",
                    "send_request_form.title": "Send a new request",
                    "send_request_form.submit_button": "Send",
                    "send_request.message.fail1": "Failed to send a new TPA/TPAHere request",
                    "send_request.message.fail2": "Failed to send a new {0} request",
                    "send_request.message.fail1.reason": "there are no players available to send a new TPA/TPAHere request...",
                    "send_request.message.fail2.reason1": "player: {0} is offline...",
                    "send_request.message.fail2.reason2": "player: {0} is busy now...",
                    "send_request.message.success": "Successfully sent a new {0} request to player: {1}...",

                    "request_form.title": "{0} request",
                    "request_form.content": "Player: {0} has sent a {1} request to you...",
                    "request_form.button.accept": "Accept",
                    "request_form.button.deny": "Deny",

                    "accept.message.fail": "Failed to accept this {0} request",
                    "accept.message.fail.reason": "player: {0} is offline...",
                    "deny.message": "Player: {0} denied your {1} request...",

                    "tpr.message.fail": "Failed to TPR",
                    "tpr.message.fail.reason1": "TPR is only allowed in Overworld...",
                    "tpr.message.fail.reason2": "TPR is on cooldown, please wait {0} more seconds...",
                    "tpr.message.broadcast": "player: {0} is undergoing random teleportation, which may cause server lag...",

                    **CONFIG_TEXT["en_US"],
                }
                json_str = json.dumps(en_US, indent=4, ensure_ascii=False)
                f.write(json_str)

        lang_data = {}

        for lang in os.listdir(self.__lang_dir_path):
            lang_name = lang.strip(".json")

            lang_file_path = os.path.join(self.__lang_dir_path, lang)

            with open(lang_file_path, "r", encoding="utf-8") as f:
                lang_data[lang_name] = json.loads(f.read())

        for locale, defaults in CONFIG_TEXT.items():
            loaded = lang_data.setdefault(locale, {})
            for key, value in defaults.items():
                loaded.setdefault(key, value)

        return lang_data

    def get_text(self, player: Player, text_key: str) -> str:
        player_lang = player.locale

        try:
            if self.__lang_data.get(player_lang) is None:
                text_value = self.__lang_data["en_US"][text_key]
            else:
                if self.__lang_data[player_lang].get(text_key) is None:
                    text_value = self.__lang_data["en_US"][text_key]
                else:
                    text_value = self.__lang_data[player_lang][text_key]

            return text_value
        except Exception as e:
            self.main.logger.error(
                f"{ColorFormat.RED}"
                f"{e}"
            )

            return text_key
