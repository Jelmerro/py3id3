#!/usr/bin/env python3

__author__ = "Jelmerro"
# See README.md for more details
__license__ = "MIT"
# See LICENSE for more details
__version__ = "0.2.1"
# See Jelmerro/py3id3 on github for updates

import os
import stagger
import tkinter as tk
import webbrowser

from tkinter import messagebox
from tkinter import filedialog
from tkinter import Menu

# The ID3 fields
ID3_FIELDS = (
    "title",
    "artist",
    "date",
    "album_artist",
    "album",
    "track",
    "track_total",
    "disc",
    "disc_total",
    "composer",
    "genre",
    "comment",
    "grouping")
# Picture and version are special fields
# They are implemented differently

# A dictionary of Field objects
# Field class is found at the end of this file
FIELDS = {}

# A list of opened files
FILES = []


def close_window_callback(root):
    """
    Close the window if that's requested
    Ask for a confirmation if files have been opened
    """
    if not FILES:
        root.destroy()
    elif messagebox.askokcancel("Quit", "Do you really wish to quit?"):
        root.destroy()


class Application:
    """
    Main application class
    """
    def __init__(self, root):
        # Init
        self.frame = tk.Frame(root)
        self.frame.pack()
        # Menu bar
        menubar = Menu(root)
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.browse_files_popup)
        file_menu.add_command(label="List", command=self.list_files_popup)
        file_menu.add_command(label="About", command=self.about_popup)
        file_menu.add_command(
            label="Exit",
            command=lambda: close_window_callback(root))
        menubar.add_cascade(label="File", menu=file_menu)
        # Convert menu
        write_menu = Menu(menubar, tearoff=0)
        write_menu.add_command(
            label="As v2.2",
            command=lambda: self.write_tags(2))
        write_menu.add_command(
            label="As v2.3",
            command=lambda: self.write_tags(3))
        write_menu.add_command(
            label="As v2.4",
            command=lambda: self.write_tags(4))
        write_menu.add_command(
            label="As original",
            command=lambda: self.write_tags(0))
        menubar.add_cascade(label="Write", menu=write_menu)
        root.config(menu=menubar)
        # Add the fields to the frame
        self.create_fields()
        root.bind("<Control-q>", lambda e: close_window_callback(root))
        root.bind("<Control-Q>", lambda e: close_window_callback(root))

    def browse_files_popup(self):
        """
        Show a file browser and expand the list of files
        Duplicates won't be added
        Menu: File > Open
        """
        self.files_opened = []
        # Limit the selection to mp3 only
        self.files_opened = filedialog.askopenfilenames(
            filetypes=(("Mp3 files", "*.mp3"),))
        # If any files were opened, add them to files
        if self.files_opened:
            for file in self.files_opened:
                # Only add new files, to prevent duplicates
                if file not in FILES:
                    FILES.append(file)
            # Update the list of old values
            self.update_fields()

    def list_files_popup(self):
        """
        Show a popup with the list of opened files
        Menu: File > List
        """
        file_list = ""
        for file in FILES:
            file_list += f"{file}\n"
        if file_list:
            Popup(self.frame, "Files", file_list)
        else:
            Popup(self.frame, "Files", "No files have been opened yet\n")

    def about_popup(self):
        """
        Show a popup with details about the program
        Menu: File > About
        """
        Popup(
            self.frame,
            "About",
            "Py3ID3 {}\n"
            "Created by Jelmerro\n"
            "MIT License\n".format(__version__),
            15,
            "Github",
            "https://github.com/Jelmerro/py3id3",
            13)

    def write_tags(self, requested_version):
        """
        Read the tags and write them to each file
        A list of failed files will be shown afterwards
        Menu: All options in "Write"
        """
        skipped = {}
        for file in FILES:
            tag = ""
            try:
                tag = stagger.read_tag(file)
            except FileNotFoundError:
                skipped[file] = f"missing file: {file}"
            except stagger.errors.NoTagError:
                skipped[file] = f"missing id3 tag: {file}"
            if tag:
                version = self.file_version(tag.version, requested_version)
                error = self.write_tag_to_file(tag, file, version)
                if error:
                    skipped[file] = error
        self.show_results(skipped)

    def show_results(self, skipped):
        """
        Show a popup with the list of failed files (if any)
        Also shows the number of processed files
        """
        success_number = len(FILES) - len(skipped)
        if FILES:
            if success_number == 0:
                message = f"All {len(FILES)} files failed:\n"
                for file, error in skipped.items():
                    message += f"{file} - {error}\n"
            elif skipped:
                message = f"{success_number} of the {len(FILES)} succeeded, but some failed:\n"
                for file, error in skipped.items():
                    message += f"{file} - {error}\n"
            else:
                message = f"Replaced tags for all {len(FILES)} files " \
                          "with success\n"
        else:
            message = "No files have been opened yet\n"
        Popup(self.frame, "Done", message)
        # Update the fields afterwards
        self.update_fields()

    def write_tag_to_file(self, old_tag, file, version):
        """
        Write the fields to the file as part of a tag
        Returns the error message (if any)
        """
        # Create a tag with the correct version
        if version not in [0, 2, 3, 4]:
            return f"Invalid version {version}"
        if version == 0:
            new_tag = old_tag
        if version == 2:
            new_tag = stagger.tags.Tag22()
        if version == 3:
            new_tag = stagger.tags.Tag23()
        if version == 4:
            new_tag = stagger.tags.Tag24()
        # Set the regular fields
        for field in ID3_FIELDS:
            if field not in ["track", "track_total"]:
                if FIELDS[field].checked():
                    try:
                        setattr(
                            new_tag,
                            field,
                            FIELDS[field].text())
                    except ValueError or KeyError:
                        return "Invalid tag error"
                else:
                    try:
                        setattr(
                            new_tag,
                            field,
                            getattr(old_tag, field))
                    except ValueError or KeyError:
                        return "Invalid tag error"
        # Set the numbering if enabled
        if FIELDS["track"].checked():
            track_total = len(FILES)
            track = str(FILES.index(file) + 1)
            if FIELDS["track_total"].checked():
                track = track.zfill(len(str(track_total)))
        else:
            track_total = getattr(old_tag, "track_total")
            track = getattr(old_tag, "track")
        try:
            setattr(
                new_tag,
                "track_total",
                track_total)
        except ValueError or KeyError:
            return "Invalid tag error"
        try:
            setattr(
                new_tag,
                "track",
                track)
        except ValueError or KeyError:
            return "Invalid tag error"
        # Picture
        if self.picture_enabled_var.get():
            if self.picture_var.get():
                new_tag.picture = self.picture_var.get()
            else:
                new_tag.picture = ""
        else:
            picture_data = ""
            if "PIC" in old_tag:
                picture_data = old_tag["PIC"][0].data
            elif "APIC" in old_tag:
                picture_data = old_tag["APIC"][0].data
            if picture_data:
                # This is required, for details see:
                # https://github.com/lorentey/stagger/issues/48
                with open("temp_image_file_for_stagger.png", "wb") as f:
                    f.write(picture_data)
                new_tag.picture = "temp_image_file_for_stagger.png"
            else:
                new_tag.picture = ""
            try:
                os.remove("temp_image_file_for_stagger.png")
            except OSError:
                pass
        # Write to file
        try:
            new_tag.write(file)
        except FileNotFoundError:
            return "Write error"
        return ""

    def file_version(self, tag_version, requested_version):
        """
        Calculates the required version for the new tag
        """
        # If the versions match and the obscure tags should be kept, return 0
        if tag_version == requested_version:
            if self.keep_obscure.get():
                return 0
        # If the requested version is not set, keep the original version
        if requested_version == 0:
            return tag_version
        # Else set the version to the requested version
        return requested_version

    def create_fields(self):
        """
        Creates a label, checkbox and textfields
        Every field in the tag will have them
        """
        # regular fields
        row = 1
        for field in ID3_FIELDS:
            FIELDS[field] = Field(field, row, self.frame)
            row += 1
        # special fields
        version_frame = tk.Frame(self.frame)
        version_frame.grid(column=1, row=row)
        # version field
        self.version_label = tk.Label(self.frame, text="ID3 Version")
        self.version_label.grid(column=0, row=row)
        self.version_var = tk.StringVar()
        self.version = tk.Entry(
            version_frame,
            width=50,
            state=tk.DISABLED,
            textvariable=self.version_var)
        self.version.grid(column=0, row=0)
        # version settings
        keep_obscure_frame = tk.Frame(version_frame)
        keep_obscure_frame.grid(column=0, row=1)
        self.keep_obscure = tk.IntVar()
        check = tk.Checkbutton(
            keep_obscure_frame,
            variable=self.keep_obscure)
        check.grid(column=0, row=0)
        label = tk.Label(
            keep_obscure_frame,
            text="Keep obscure tags for files with unchanged ID3 versions")
        label.grid(column=1, row=0)
        # picture settings
        self.picture_enabled_var = tk.IntVar()
        self.picture_enabled = tk.Checkbutton(
            self.frame,
            variable=self.picture_enabled_var)
        self.picture_enabled.grid(column=2, row=row)
        self.picture_enabled.bind("<Button-1>", self.update_picture)
        self.picture_enabled.bind("<Return>", self.update_picture)
        self.picture_enabled.bind("<space>", self.update_picture)
        picture_settings_frame = tk.Frame(self.frame)
        picture_settings_frame.grid(column=3, row=row)
        browse_button = tk.Button(picture_settings_frame, text="Browse")
        browse_button.grid(column=0, row=0)
        browse_button.bind("<Button-1>", self.open_picture)
        browse_button.bind("<Return>", self.open_picture)
        browse_button.bind("<space>", self.open_picture)
        self.picture_var = tk.StringVar()
        self.picture = tk.Entry(
            picture_settings_frame,
            width=30,
            state=tk.DISABLED,
            textvariable=self.picture_var)
        self.picture.grid(column=1, row=0)
        self.picture_status_var = tk.StringVar()
        self.picture_status_var.set("All files will keep the current picture")
        picture_status = tk.Label(
            picture_settings_frame,
            textvariable=self.picture_status_var)
        picture_status.grid(column=1, row=1)
        clear_button = tk.Button(picture_settings_frame, text="Clear")
        clear_button.grid(column=2, row=0)
        clear_button.bind("<Button-1>", self.clear_picture)
        clear_button.bind("<Return>", self.clear_picture)
        clear_button.bind("<space>", self.clear_picture)

    def clear_picture(self, event=None):
        """
        Clears the picture field
        """
        self.picture_var.set("")
        self.update_picture()

    def open_picture(self, event=None):
        if event:
            event.widget.after_idle(self.open_picture_callback)
        else:
            self.open_picture_callback()

    def open_picture_callback(self, e=None):
        """
        Show a file browser and set the new picture
        """
        # Limit the selection to png and jpg only
        self.file_opened = filedialog.askopenfilename(
            filetypes=(("PNG files", "*.png"),))
        # If any files were opened, add them to files
        if self.file_opened:
            self.picture_var.set(self.file_opened)
            self.update_picture()

    def update_picture(self, event=None):
        if event:
            event.widget.after_idle(self.update_picture_callback)
        else:
            self.update_picture_callback()

    def update_picture_callback(self, e=None):
        """
        Update the picture status label to match new the settings
        """
        if self.picture_enabled_var.get():
            if self.picture_var.get():
                self.picture_status_var.set(
                    "All files will have this picture added")
            else:
                self.picture_status_var.set(
                    "All files will have the picture removed")
        else:
            self.picture_status_var.set(
                "All files will keep the current picture")

    def update_fields(self):
        """
        Update the original values for each field
        """
        separator = ""
        last_value = {}
        all_the_same = {"version": True}
        self.version_var.set("")
        for field in ID3_FIELDS:
            FIELDS[field].clear_original()
            all_the_same[field] = True
        remove_list = []
        for file in FILES:
            tag = ""
            try:
                tag = stagger.read_tag(file)
            except FileNotFoundError:
                Popup(
                    self.frame,
                    "Warning",
                    f"missing file: {file}")
                remove_list.append(file)
            except stagger.errors.NoTagError:
                Popup(
                    self.frame,
                    "Warning",
                    f"missing id3 tag: {file}")
                remove_list.append(file)
            if tag:
                for field in ID3_FIELDS:
                    value = getattr(tag, field)
                    FIELDS[field].set_original(f"{FIELDS[field].original()}{separator}{value}")
                    if field in last_value:
                        if last_value[field] != value:
                            all_the_same[field] = False
                    last_value[field] = value
                value = getattr(tag, "version")
                self.version_var.set(f"{self.version_var.get()}{separator}{value}")
                if "version" in last_value:
                    if last_value["version"] != value:
                        all_the_same["version"] = False
                last_value["version"] = value
                separator = ";"
        for file in remove_list:
            FILES.remove(file)
        if FILES:
            for field in ID3_FIELDS:
                if all_the_same[field]:
                    FIELDS[field].set_original(last_value[field])
                FIELDS[field].update_output()
            if all_the_same["version"]:
                self.version_var.set(last_value["version"])


class Popup:
    """
    Popup class creates a toplevel with labels
    It's not resizable, grabs the focus and stays on top
    Optionally adds a link to it
    """
    def __init__(self,
                 frame,
                 title,
                 message,
                 size=12,
                 link_title=None,
                 link=None,
                 link_size=None):
        popup = tk.Toplevel(frame, padx="40", pady="40")
        # Add a link if provided
        if link_title:
            label = tk.Label(popup, text=message, font=f"-size {size}")
            label.grid(row=0)
            link_label = tk.Label(
                popup,
                text=link_title,
                fg="blue",
                cursor="hand2",
                font=f"-size {link_size}")
            link_label.bind(
                "<Button-1>",
                lambda e: webbrowser.open_new(link))
            link_label.grid(row=1)
        else:
            tk.Label(popup, text=message, font=f"-size {size}").pack()
        popup.grab_set()
        popup.title(title)
        popup.resizable(False, False)
        popup.wm_attributes("-topmost", True)
        popup.bind("<Escape>", lambda e: popup.destroy())


class Field(tk.Frame):
    """
    Field class consists of a label, checkbox and three entry fields
    A field will occupy a single row in the application
    For every id3 field, a Field object will be created
    (except for the picture and version)
    """
    def __init__(self, name, row, master):
        self.name = name
        self.master = master
        super(Field, self).__init__(master=master)
        # label - title Label
        self.label = tk.Label(self.master, text=self.title(name))
        self.label.grid(column=0, row=row)
        # original - old Entry
        self.old_var = tk.StringVar()
        self.old = tk.Entry(
            self.master,
            width=50,
            state=tk.DISABLED,
            textvariable=self.old_var)
        self.old.grid(column=1, row=row)
        # checkbox - enabled Checkbutton
        self.checkbox_var = tk.IntVar()
        self.checkbox = tk.Checkbutton(
            self.master,
            variable=self.checkbox_var)
        self.checkbox.grid(column=2, row=row)
        self.checkbox.bind("<Button-1>", self.update_output)
        self.checkbox.bind("<Return>", self.update_output)
        self.checkbox.bind("<space>", self.update_output)
        # entry - input Entry
        if name not in ["track", "track_total"]:
            self.input_var = tk.StringVar()
            self.input = tk.Entry(
                self.master,
                width=50,
                textvariable=self.input_var)
            self.input.grid(column=3, row=row)
            self.input.bind("<Any-KeyPress>", self.update_output)
        elif name == "track":
            self.input = tk.Label(
                self.master,
                text="Automatically number the tracks")
            self.input.grid(column=3, row=row)
        elif name == "track_total":
            self.input = tk.Label(
                self.master,
                text="Pad zeros to match the total number of tracks")
            self.input.grid(column=3, row=row)
        # output - new Entry
        self.output_var = tk.StringVar()
        self.output = tk.Entry(
            self.master,
            width=50,
            state=tk.DISABLED,
            textvariable=self.output_var)
        self.output.grid(column=4, row=row)

    def title(self, text):
        return text.title().replace("_", " ")

    def set_original(self, text):
        self.old_var.set(text)

    def clear_original(self):
        self.old_var.set("")

    def original(self):
        return self.old_var.get()

    def checked(self):
        return bool(self.checkbox_var.get())

    def text(self):
        return self.input_var.get()

    def set_output(self, text):
        self.output_var.set(text)

    def update_output(self, event=None):
        if event:
            event.widget.after_idle(self.update_output_callback)
        else:
            self.update_output_callback()

    def update_output_callback(self):
        """
        Update the output fields to match the new settings
        """
        if self.name in ["track", "track_total"]:
            if FIELDS["track"].checked():
                padding = FIELDS["track_total"].checked()
                track, track_total = self.get_numbering(padding)
                FIELDS["track"].set_output(track)
                FIELDS["track_total"].set_output(track_total)
            else:
                FIELDS["track"].set_output(FIELDS["track"].original())
                FIELDS["track_total"].set_output(
                    FIELDS["track_total"].original())
        else:
            if not self.checked():
                self.set_output(self.original())
            else:
                self.set_output(self.text())

    def get_numbering(self, padding):
        """
        Returns a formatted string version of the numbering
        """
        if not FILES:
            return "", ""
        track = ""
        track_total = str(len(FILES))
        id = 1
        for file in FILES:
            if padding:
                track += f"{str(id).zfill(len(track_total))};"
            else:
                track += f"{id};"
            id += 1
        track = track[:-1]
        return track, track_total


if __name__ == "__main__":
    # Create a root Tk object and start the application with it
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", lambda: close_window_callback(root))
    root.resizable(False, False)
    root.title("Py3ID3")
    Application(root)
    root.mainloop()
