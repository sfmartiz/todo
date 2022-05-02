master_settings_config = [
    #FORMAT:
    #[internal name,    GUI display name,           default value]
    ["show_remain",     "Show remaining time",      True],
    ["show_edit",       "Show edit buttons",        True],
    ["show_delete",     "Show delete buttons",      True],
    ["show_complete",   "Show completed tasks",     False],
    ["show_border",     "Show borders",             False],
    ["allow_blank",     "Allow blank entries",      False]
    ]

default_settings = {}
for entry in master_settings_config:
    default_settings[entry[0]] = entry[2]

settings_names = {}
for entry in master_settings_config:
    settings_names[entry[0]] = entry[1]

user_settings = default_settings.copy()
