from tkinter import *
from tkinter import ttk, messagebox
from os import listdir
from os.path import join as joinpath
from sqlalchemy.orm import sessionmaker
import json
import logging

import db
from timerclasses import *
from options import *

custom_formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("runtime.log")
file_handler.setFormatter(custom_formatter)
log.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(custom_formatter)
log.addHandler(console_handler)

log.info(f"Program launched")

mainwindow = Tk()

# load every .png file from img directory into a dictionary under its filename without extension
imgnames = [filename[:-4] for filename in listdir("img") if filename[-4:] == ".png"]
images = {}
for filename in imgnames:
    try:
        loadedimage = PhotoImage(file=joinpath("img", f"{filename}.png"))
        images[filename] = loadedimage
    except:
        log.warning(f"Failed to load image \"{filename}.png\"")
log.info(f"Successfully loaded {len(images)} images out of {len(imgnames)} files.")

mainwindow.title("To-do list")

if "icon" in images:
    # bool = use icon for all windows?
    mainwindow.iconphoto(True, images["icon"])
else:
    log.warning("Couldn't load \"icon.png\", using default tkinter icon for all windows.")

timers = {}  # ID: [timertype, object]

if "timers.db" in listdir():
    engine = db.create_engine("sqlite:///timers.db")
    Session = sessionmaker(bind=engine)
    db_session = Session()

    for entry in db_session.query(db.Timers).all():
        newobject = globals()[f"{entry.type}Timer"](entry.comment, entry.last_clicked, json.loads(entry.data))
        timers[entry.id] = [entry.type, newobject]

    settings_query = db_session.query(db.Settings).all()

    for entry in settings_query:
        user_settings[entry.name] = entry.value
    
    if len(user_settings) > len(settings_query):
        log.info("Database out of date, adding new settings.")
        for entry in user_settings.keys():
            if entry not in [x.name for x in settings_query]:
                log.debug(f"Adding \"{entry}\" to settings database")
                db_session.add(db.Settings(entry, user_settings[entry]))
        db_session.commit()
    
else:
    log.warning("File \"timers.db\" not found! Initializing new database...")
    engine = db.initialize_db()
    Sessionclass = sessionmaker(bind=engine)
    db_session = Sessionclass()

    for entry in user_settings.items():
        db_session.add(db.Settings(*entry))
    db_session.commit()

log.debug(f"Database currently holds {len(timers)} entries.")

timerwidgets = []

window_height = min(max(100, len(timers)*43), 350)
log.debug(f"Starting window height: {window_height} ({len(timers)} entries)")
mainwindow.geometry(f"300x{window_height}")


class NewEntryWindow(Toplevel):
    def __init__(self, parent, timers, editID):
        super().__init__(parent)
        if editID == -1:
            self.title("Add new timer")
        else:
            self.title("Edit existing timer")
        
        self.geometry("360x250")
        self.columnconfigure(1, weight=3)
        self.rowconfigure(1, weight=5)

        confirm = "Add" if editID == -1 else "Change"

        self.currtype = StringVar(self, "Daily")
        self.oldindex = IntVar(self, 0)
        self.descrentry = StringVar(self)
        self.allframes = []
        self.datepicker = StringVar(self, datetime.strftime(now(), "%Y-%m-%d %H:%M"))
        self.intervalpicker = StringVar(self, "1")
        self.measurementpicker = StringVar(self, time_measurements[-1])
        self.weekdaypicker = []
        self.weekpicker = StringVar(self, weekdays[0])
        self.daypicker = StringVar(self, "1")
        self.hourpicker = StringVar(self, "0")
        self.minutepicker = StringVar(self, "0")

        Label(self, text="Timer type").grid(row=0, column=0)
        typepicker = ttk.Combobox(self, textvariable=self.currtype, state="readonly", values=timertypes)
        typepicker.bind('<<ComboboxSelected>>', self.changed_dropdown)
        typepicker.grid(row=0, column=1, sticky=W+E)

        # DYNAMIC FRAMES START
        daily_frame = Frame(self)
        Label(daily_frame, text="Resets every day at specified hour and minute.").grid(row=0, column=0, columnspan=4)
        Label(daily_frame, text="Description").grid(row=1, column=0)
        Entry(daily_frame, textvariable=self.descrentry).grid(row=1, column=1, columnspan=3, sticky=W+E)
        Label(daily_frame, text="Reset hour").grid(row=2, column=0)
        Entry(daily_frame, textvariable=self.hourpicker).grid(row=2, column=1)
        Label(daily_frame, text="Reset mins").grid(row=2, column=2)
        Entry(daily_frame, textvariable=self.minutepicker).grid(row=2, column=3)
        Button(daily_frame, text=confirm, command=lambda: self.add_timer(timers, editID, "Daily"),
               width=15).grid(row=3, column=0, columnspan=4)

        daily_frame.grid(row=1, column=0, columnspan=2, sticky=NSEW)
        self.allframes.append(daily_frame)

        weekly_frame = Frame(self)
        Label(weekly_frame, text="Resets every week at specified day, hour and minute."
              ).grid(row=0, column=0, columnspan=4)
        Label(weekly_frame, text="Description").grid(row=1, column=0)
        Entry(weekly_frame, textvariable=self.descrentry).grid(row=1, column=1, columnspan=3, sticky=W+E)
        Label(weekly_frame, text="Day of week").grid(row=2, column=0)
        ttk.Combobox(weekly_frame, textvariable=self.weekpicker, state="readonly", values=weekdays
                     ).grid(row=2, column=1, columnspan=3, sticky=W+E)
        Label(weekly_frame, text="Reset hour").grid(row=3, column=0)
        Entry(weekly_frame, textvariable=self.hourpicker).grid(row=3, column=1)
        Label(weekly_frame, text="Reset mins").grid(row=3, column=2)
        Entry(weekly_frame, textvariable=self.minutepicker).grid(row=3, column=3)
        Button(weekly_frame, text=confirm, command=lambda: self.add_timer(timers, editID, "Weekly"), width=15
               ).grid(row=4, column=0, columnspan=4)
        self.allframes.append(weekly_frame)

        weekday_frame = Frame(self)
        Label(weekday_frame, text="Resets on specified weekdays at a specific hour and minute."
              ).grid(row=0, column=0, columnspan=4)
        Label(weekday_frame, text="Description").grid(row=1, column=0)
        Entry(weekday_frame, textvariable=self.descrentry).grid(row=1, column=1, columnspan=3, sticky=W+E)
        Label(weekday_frame, text="Reset hour").grid(row=2, column=0)
        Entry(weekday_frame, textvariable=self.hourpicker).grid(row=2, column=1)
        Label(weekday_frame, text="Reset mins").grid(row=3, column=0)
        Entry(weekday_frame, textvariable=self.minutepicker).grid(row=3, column=1)
        Button(weekday_frame, text=confirm, command=lambda: self.add_timer(timers, editID, "Weekday"), width=15
               ).grid(row=4, column=0, columnspan=2)
        
        checkboxframe = Frame(weekday_frame)
        for entry in weekdays:
            tempvar = BooleanVar(weekday_frame)
            check = Checkbutton(checkboxframe, text=entry, variable=tempvar)
            check.pack()
            self.weekdaypicker.append(tempvar)

        checkboxframe.grid(row=2, column=2, rowspan=3, columnspan=2)
        self.allframes.append(weekday_frame)
        
        monthly_frame = Frame(self)
        Label(monthly_frame, text="Resets every month at specified day, hour and minute."
              ).grid(row=0, column=0, columnspan=4)
        Label(monthly_frame, text="NOTE: Will use last day of month if out of bounds (i.e Feb 31st)"
              ).grid(row=1, column=0, columnspan=4)
        Label(monthly_frame, text="Description").grid(row=2, column=0)
        Entry(monthly_frame, textvariable=self.descrentry).grid(row=2, column=1, columnspan=3, sticky=W+E)
        Label(monthly_frame, text="Day of month").grid(row=3, column=0)
        Entry(monthly_frame, textvariable=self.daypicker).grid(row=3, column=1, columnspan=3, sticky=W+E)
        Label(monthly_frame, text="Reset hour").grid(row=4, column=0)
        Entry(monthly_frame, textvariable=self.hourpicker).grid(row=4, column=1)
        Label(monthly_frame, text="Reset mins").grid(row=4, column=2)
        Entry(monthly_frame, textvariable=self.minutepicker).grid(row=4, column=3)
        Button(monthly_frame, text=confirm, command=lambda: self.add_timer(timers, editID, "Monthly"),
               width=15).grid(row=5, column=0, columnspan=4)
        self.allframes.append(monthly_frame)
        
        custom_frame = Frame(self)
        Label(custom_frame, text="Resets at a fixed interval from a specific time.").grid(row=0, column=0, columnspan=3)
        Label(custom_frame, text="Description").grid(row=1, column=0)
        Entry(custom_frame, textvariable=self.descrentry).grid(row=1, column=1, columnspan=2, sticky=W+E)
        Label(custom_frame, text="Start time").grid(row=2, column=0)
        Entry(custom_frame, textvariable=self.datepicker).grid(row=2, column=1, columnspan=2, sticky=W+E)
        Label(custom_frame, text="Resets every").grid(row=3, column=0)
        Entry(custom_frame, textvariable=self.intervalpicker).grid(row=3, column=1)
        ttk.Combobox(custom_frame, textvariable=self.measurementpicker, state="readonly", values=time_measurements
                     ).grid(row=3, column=2)

        Button(custom_frame, text=confirm, command=lambda: self.add_timer(timers, editID, "Custom"), width=15
               ).grid(row=4, column=0, columnspan=3)
        self.allframes.append(custom_frame)

        once_frame = Frame(self)
        Label(once_frame, text="One-time task ending at a specific point in time.").grid(row=0, column=0, columnspan=3)
        Label(once_frame, text="Description").grid(row=1, column=0)
        Entry(once_frame, textvariable=self.descrentry).grid(row=1, column=1, columnspan=2, sticky=W+E)
        Label(once_frame, text="End time").grid(row=2, column=0)
        Entry(once_frame, textvariable=self.datepicker).grid(row=2, column=1, columnspan=2, sticky=W+E)

        Button(once_frame, text=confirm, command=lambda: self.add_timer(timers, editID, "Once"), width=15
               ).grid(row=3, column=0, columnspan=3)
        self.allframes.append(once_frame)
        # DYNAMIC FRAMES END

    def changed_dropdown(self, event):
        currselectionindex = timertypes.index(self.currtype.get())
        
        self.allframes[self.oldindex.get()].grid_forget()

        self.allframes[currselectionindex].grid(row=1, column=0, columnspan=2, sticky=NSEW)
        self.oldindex.set(currselectionindex)

    def add_timer(self, timers, editID, timertype):
        if editID != -1:
            if not db_session.query(db.Timers).get(editID):
                self.destroy()
                err("Attempting to edit a timer that has already been deleted!")

        comment = self.descrentry.get().strip()
        if not user_settings["allow_blank"]:
            if len(comment) == 0:
                err("Task description is empty!\nThis check may be disabled in options.")

        if not timertype in ("Custom","Once"):
            hours = self.hourpicker.get()
            hours = self.handle_number(hours, "hour", 0, 23)
            
            minutes = self.minutepicker.get()
            minutes = self.handle_number(minutes, "minute", 0, 59)

        match timertype:
            case "Daily":
                args = (hours, minutes)
            case "Weekly":
                args = (weekdays.index(self.weekpicker.get()), hours, minutes)
            case "Weekday":
                temp_list = list(filter(lambda x: self.weekdaypicker[x].get(), range(7)))
                if len(temp_list) == 0:
                    err("Not a single weekday was selected.")
                
                args = (temp_list, hours, minutes)
            case "Monthly":
                days = self.daypicker.get()
                days = self.handle_number(days, "day", 1, 31)
                
                args = (days, hours, minutes)
            case "Custom":
                try:
                    newtime = datetime.strptime(self.datepicker.get(), "%Y-%m-%d %H:%M")
                except:
                    err(f"Invalid starting date format\nExample: {datetime.strftime(now(), '%Y-%m-%d %H:%M')}")
                
                interval = self.intervalpicker.get()
                interval = self.handle_number(interval, "interval", 1, -1)

                args = (int(newtime.timestamp()), interval, self.measurementpicker.get())
            case "Once":
                try:
                    newtime = datetime.strptime(self.datepicker.get(), "%Y-%m-%d %H:%M")
                except:
                    err(f"Invalid end date format\nExample: {datetime.strftime(now(), '%Y-%m-%d %H:%M')}")

                args = (int(newtime.timestamp()),)


        if editID == -1:
            newdbentry = db.Timers(timertype, comment, 0, json.dumps(args))
            db_session.add(newdbentry)
            db_session.flush()
            editID = newdbentry.id
        else:
            db_entry = db_session.query(db.Timers).get(editID)
            db_entry.type = timertype
            db_entry.comment = self.descrentry.get()
            db_entry.data = json.dumps(args)
            
        db_session.commit()
        timers[editID] = [timertype, globals()[f"{timertype}Timer"](comment, 0, args)]
        
        populate()
        self.destroy()

    def handle_number(self, value, unit, rangemin, rangemax):
        if len(value) > 0:
            for char in value:
                if char not in "01234356789":
                    err(f"Non-number value in reset {unit} field.")
            
            value = int(value)

            if rangemax == -1:
                if value < rangemin:
                    err(f"Reset {unit} needs to be at least {rangemin}")
            else:
                if value not in range(rangemin, rangemax+1):
                    err(f"Reset {unit} value outside of {rangemin}-{rangemax} range")
        else:
            err(f"No argument for reset {unit}")
        
        return value


def err(description):
    log.warning(description)
    messagebox.showerror("Error", description)
    raise ValueError(description)


def exc(description):
    log.error(description)
    messagebox.showerror("Error", description)
    raise Exception(description)


def addnew():
    NewEntryWindow(mainwindow, timers, -1)


def task_finished(objid):
    log.debug(f"Task finished, id {objid}")
    if timers[objid][0] == "Once":
        delete_timer(objid)
    else:
        timers[objid][1].lastclicked = time_int()

        db_entry = db_session.query(db.Timers).get(objid)
        db_entry.value = time_int()
        db_session.commit()

        populate()


def uncheck_task(objid):
    log.debug(f"Task restarted manually, id {objid}")
    timers[objid][1].lastclicked = 0
    
    db_entry = db_session.query(db.Timers).get(objid)
    db_entry.value = 0
    db_session.commit()
    
    populate()


def edit_timer(objid):
    log.debug(f"Task edit called on id {objid}")
    # no populate on initial call!
    subwindow = NewEntryWindow(mainwindow, timers, objid)
    
    subwindow.currtype.set(timers[objid][0])
    subwindow.descrentry.set(timers[objid][1].comment)
    args = timers[objid][1].extraargs

    match timers[objid][0]:
        case "Daily":
            subwindow.hourpicker.set(args[0])
            subwindow.minutepicker.set(args[1])
        case "Weekly":
            subwindow.weekpicker.set(weekdays[args[0]])
            subwindow.hourpicker.set(args[1])
            subwindow.minutepicker.set(args[2])
        case "Weekday":
            for value in args[0]:
                subwindow.weekdaypicker[value].set(True)
            subwindow.hourpicker.set(args[1])
            subwindow.minutepicker.set(args[2])
        case "Monthly":
            subwindow.daypicker.set(args[0])
            subwindow.hourpicker.set(args[1])
            subwindow.minutepicker.set(args[2])
        case "Custom":
            oldtime = datetime.fromtimestamp(args[0]).strftime("%Y-%m-%d %H:%M")
            subwindow.datepicker.set(oldtime)
            subwindow.intervalpicker.set(args[1])
            subwindow.measurementpicker.set(args[2])
        case "Once":
            oldtime = datetime.fromtimestamp(args[0]).strftime("%Y-%m-%d %H:%M")
            subwindow.datepicker.set(oldtime)
    
    subwindow.changed_dropdown(None)


def delete_timer(objid):
    log.debug(f"Deleting task with id {objid}")
    db_session.delete(db_session.query(db.Timers).get(objid))
    db_session.commit()
    del timers[objid]
    populate()


def autopopulate():
    populate()
    mainwindow.after(60000, autopopulate)


def populate():
    while len(timerwidgets) > 0:
        item = timerwidgets[0]
        
        timerwidgets.remove(item)
        item.destroy()
        del item
    
    sortedtimers = sorted(timers.items(), key=lambda x: x[1][1].remaining_delta())

    size = "32" if user_settings["show_remain"] else "" 

    if not user_settings["show_complete"]:
        sortedtimers = list(filter(lambda x: x[1][1].lastclicked < x[1][1].lastdeadline(), sortedtimers))

    if len(timers) == 0:
        line1 = Label(mainwindow, text="No timers added!")
        line1.pack()

        line2 = Label(mainwindow, text="Click \"New Entry\" to begin.")
        line2.pack()
        
        timerwidgets.append(line1)
        timerwidgets.append(line2)
    
    elif len(sortedtimers) == 0:
        line1 = Label(mainwindow, text="All tasks finished. Good job!")
        line1.pack()
        
        timerwidgets.append(line1)
    
    else:
        for entry in sortedtimers:
            itemframe = Frame(mainwindow)
            if user_settings["show_border"]:
                itemframe.config(highlightbackground="black", highlightthickness=1)
            
            labelframe = Frame(itemframe)

            if user_settings["show_complete"] and entry[1][1].lastclicked > entry[1][1].lastdeadline():
                Button(itemframe, image=images[f"cross{size}"], command=lambda objid=entry[0]: uncheck_task(objid)
                       ).pack(side=LEFT)
            else:
                Button(itemframe, image=images[f"check{size}"], command=lambda objid=entry[0]: task_finished(objid)
                       ).pack(side=LEFT)

            if user_settings["show_delete"]:
                Button(itemframe, image=images[f"trash{size}"], command=lambda objid=entry[0]: delete_timer(objid)
                       ).pack(side=RIGHT)
            if user_settings["show_edit"]:
                Button(itemframe, image=images[f"edit{size}"], command=lambda objid=entry[0]: edit_timer(objid)
                       ).pack(side=RIGHT)

            Label(labelframe, text=entry[1][1].comment).pack(anchor=W)
            if user_settings["show_remain"]:
                if user_settings["show_complete"] and entry[1][1].lastclicked > entry[1][1].lastdeadline():
                    Label(labelframe, text="Completed!").pack(anchor=W)
                else:
                    Label(labelframe, text=entry[1][1].remaining_str()).pack(anchor=W)
            labelframe.pack(side=LEFT, expand=True, fill=X)

            timerwidgets.append(itemframe)
            itemframe.pack(fill=X)


mainmenu = Menu(mainwindow)
uioptions_menu = Menu(mainwindow, tearoff=0)
mainwindow.config(menu=mainmenu)

mainmenu.add_command(label="New entry", command=addnew)
mainmenu.add_cascade(label="UI options", menu=uioptions_menu)


def update_settings():
    for key, value in settingswidgets.items():
        if value.get() != user_settings[key]:
            log.debug(f"Changing setting \"{key}\", new value: {value.get()}")
            user_settings[key] = value.get()

            db_entry = db_session.query(db.Settings).get(key)
            db_entry.value = user_settings[key]
            db_session.commit()

    populate()


settingswidgets = {}

for key, value in settings_names.items():
    tempvar = BooleanVar(mainwindow, user_settings[key])
    settingswidgets[key] = tempvar
    uioptions_menu.add_checkbutton(label=value, variable=tempvar, command=update_settings)

autopopulate()
mainwindow.mainloop()
