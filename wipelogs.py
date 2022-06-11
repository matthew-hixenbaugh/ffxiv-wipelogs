import pandas as pd
from tkinter import *
from tkinter import filedialog
import os
from datetime import datetime
import configparser


class Config:

    def __init__(self):
        config_path = "./config.ini"
        if not os.path.exists(config_path):
            self.default_config()

        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

    @staticmethod
    def default_config():
        default = configparser.ConfigParser()
        default["paths"] = {"wipelogs_dir": "./WIPELOGS",
                            "fight_dir": "./FIGHTS",
                            "roster_dir": "./ROSTERS"}
        default["files"] = {"fight_csv": "",
                            "roster_csv": ""}

        for path in default["paths"].values():
            if not os.path.exists(path):
                os.makedirs(path)

        with open("config.ini", "w") as configfile:
            default.write(configfile)

    def get_fight(self):
        if self.config["files"]["fight_csv"] == "":
            return None
        else:
            return self.config["files"]["fight_csv"]

    def get_roster(self):
        if self.config["files"]["roster_csv"] == "":
            return None
        else:
            return self.config["files"]["roster_csv"]

    # TODO: make fight_path and roster_path instance variables of this class instead of DataModel
    def save_config(self, fight_path, roster_path):
        self.config["files"]["fight_csv"] = fight_path
        self.config["files"]["roster_csv"] = roster_path

        with open("config.ini", "w") as configfile:
            self.config.write(configfile)


# TODO: what i want to do is to draw a blank screen until the fight.csv and roster.csv are loaded either through
#       the popup dialogues or through the config.ini ["files"] fields. Right now im just setting all the variables
#       derived from those files to None until the files are loaded. Regular program execution begins when both
#       derived fight_df and roster_df are not NoneType. Research a better way to do this
class DataModel:

    def __init__(self, interface):
        self.settings = Config()
        self.interface = interface

        now = datetime.now()
        self.timestamp = now.strftime("%Y%m%d%H%M%S")

        # TODO: this
        self.wipelogs_dir = self.settings.config["paths"]["wipelogs_dir"]
        self.fight_path = None
        self.roster_path = None

        # TODO: this
        self.fight_df, self.fight_name = self.load_fight()
        self.roster_df, self.roster_name = self.load_roster()

        # TODO: this
        self.wipe_df = None
        self.fight_mechanics = []
        self.mechanics_per_phase = []
        self.phase_ids = []

    # TODO: this
    def load_fight(self):
        self.fight_path = self.settings.get_fight()
        if self.fight_path is not None:
            fight_df = pd.read_csv(self.fight_path)
            fight_name = os.path.basename(self.fight_path).split(".")[0]
        else:
            fight_df = None
            fight_name = None

        return fight_df, fight_name

    # TODO: this
    def load_fight_from_dialog(self):
        self.fight_path = self.interface.select_path("Fight")
        self.fight_df = pd.read_csv(self.fight_path)
        self.fight_name = os.path.basename(self.fight_path).split(".")[0]
        self.interface.startup_loop()

    # TODO: this
    def load_roster(self):
        self.roster_path = self.settings.get_roster()
        if self.roster_path is not None:
            roster = pd.read_csv(self.roster_path)
            roster_name = os.path.basename(self.roster_path).split(".")[0]
        else:
            roster = None
            roster_name = None
        return roster, roster_name

    # TODO: this
    def load_roster_from_dialog(self):
        self.roster_path = self.interface.select_path("Roster")
        self.roster_df = pd.read_csv(self.roster_path)
        self.roster_name = os.path.basename(self.roster_path).split(".")[0]
        self.interface.startup_loop()

    def create_wipe_df(self):
        for (phase_name, phase_mechanics) in self.fight_df.iteritems():
            for mechanic in phase_mechanics.values:
                if pd.isna(mechanic):
                    pass
                else:
                    self.fight_mechanics.append(mechanic)
            self.mechanics_per_phase.append(phase_mechanics.count())

        for i in range(len(self.mechanics_per_phase)):
            num_of_mechanics_in_phase = self.mechanics_per_phase[i]
            phase_name = self.fight_df.columns[i]
            for _ in range(num_of_mechanics_in_phase):
                self.phase_ids.append(phase_name)

        df = pd.DataFrame(0, index=self.roster_df["player"], columns=self.fight_mechanics)
        add_row = pd.DataFrame([self.phase_ids], columns=self.fight_mechanics)
        df = pd.concat([add_row, df])
        df.index.values[0] = "PHASE ID"
        self.wipe_df = df

    def write_data(self, wiped_player, wiped_mechanic):
        print(f"writing data for {wiped_player} in {wiped_mechanic}")
        self.wipe_df.at[wiped_player, wiped_mechanic] += 1
        self.wipe_df.to_pickle(f"{self.wipelogs_dir}/{self.fight_name}_{self.timestamp}.pkl")
        analysis_df = self.wipe_df.iloc[1:, :].sum(axis=1)
        analysis_df.to_csv(f"{self.wipelogs_dir}/{self.fight_name}_{self.timestamp}_analysis.csv")
        self.settings.save_config(fight_path=self.fight_path, roster_path=self.roster_path)

        self.interface.draw_main_screen()


class WipeLogs(Tk):

    def __init__(self):
        super(WipeLogs, self).__init__()

        self.data_model = DataModel(interface=self)

        self.title("FFXIV Wipelogs Tool")
        self.config(padx=30, pady=30)
        self.minsize(width=500, height=300)
        self.create_menu_bar()

        self.widgets_to_hide = []
        self.widgets_to_destroy = []

        self.static_player_labels = []
        self.static_phase_buttons = []
        self.load_label = Label(text="No fight or roster loaded, use the dropdown menu to load these.")

        self.startup_loop()

    # TODO: there HAS to be a better way to do what i want here, see DataModel todo
    def startup_loop(self):
        # TODO: this is downright horrendous
        if isinstance(self.data_model.fight_df, type(None)) or isinstance(self.data_model.roster_df, type(None)):
            self.load_label.grid(row=0, column=0)
        else:
            # TODO: probably just refactor the whole save_config() method to not use args
            # self.data_model.settings.save_config()
            self.data_model.create_wipe_df()
            self.load_label.grid_forget()
            self.create_static_buttons()
            self.draw_main_screen()

    def create_static_buttons(self):
        for player in self.data_model.roster_df["player"]:
            new_name_label = Label(text=player)
            self.static_player_labels.append(new_name_label)

            p = []
            for phase in self.data_model.fight_df.columns:
                new_phase_button = Button(text=phase, command=lambda selected_player=player, selected_phase=phase:
                                          self.draw_sub_screen(selected_player, selected_phase))
                p.append(new_phase_button)
            self.static_phase_buttons.append(p)

    def create_menu_bar(self):
        menu_bar = Menu(self)
        self.config(menu=menu_bar)

        file_menu = Menu(menu_bar)
        file_menu.add_command(label="Import Roster", command=self.data_model.load_roster_from_dialog)
        file_menu.add_command(label="Import Fight", command=self.data_model.load_fight_from_dialog)

        menu_bar.add_cascade(label="File", menu=file_menu)

    def draw_main_screen(self):
        self.destroy_widgets()

        player_label_row_pos = 1
        for label in self.static_player_labels:
            label.grid(row=player_label_row_pos, column=0, padx=10, pady=10)
            player_label_row_pos += 1
            self.widgets_to_hide.append(label)

        phase_button_row_pos = 1
        for row in self.static_phase_buttons:
            phase_button_col_pos = 2
            for button in row:
                button.grid(row=phase_button_row_pos, column=phase_button_col_pos, padx=10, pady=10)
                self.widgets_to_hide.append(button)
                phase_button_col_pos += 1
            phase_button_row_pos += 1

    def draw_sub_screen(self, selected_player, selected_phase):
        self.clear_main_screen_widgets()
        player_label = Label(text=selected_player)
        player_label.grid(row=0, column=0, padx=20, pady=20)
        self.widgets_to_destroy.append(player_label)

        sub_screen_button_col_number = 1
        for mechanic_name in self.data_model.fight_df[selected_phase].values:
            if pd.isna(mechanic_name):
                break

            new_button = Button(text=mechanic_name,
                                command=lambda wiped_player=selected_player, wiped_mechanic=mechanic_name:
                                self.data_model.write_data(wiped_player, wiped_mechanic))
            new_button.grid(row=0, column=sub_screen_button_col_number, padx=20, pady=20)
            self.widgets_to_destroy.append(new_button)
            sub_screen_button_col_number += 1

        back = Button(text="Back", command=self.draw_main_screen)
        back.grid(row=2, column=sub_screen_button_col_number+1, padx=20, pady=20)
        self.widgets_to_destroy.append(back)

    def clear_main_screen_widgets(self):
        for widget in self.widgets_to_hide:
            widget.grid_forget()
        self.widgets_to_hide = []

    def destroy_widgets(self):
        for widget in self.widgets_to_destroy:
            widget.destroy()
        self.widgets_to_destroy = []

    @staticmethod
    def select_path(file_type):
        popup = Tk()
        popup.withdraw()
        path = filedialog.askopenfilename(title=f"Select {file_type} CSV",
                                                filetypes=[('csv files', '*.csv')],
                                                initialdir=os.getcwd())
        return path


def main():
    root = WipeLogs()
    root.mainloop()


if __name__ == '__main__':
    main()
