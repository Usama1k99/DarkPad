import os
import re
import sys
import json
import utils
import binary_utils
from tkinter import *
from tkinter import ttk
from datetime import datetime
from tkinter import filedialog as fd
from tkinter import messagebox as msgbox
from tkinter.simpledialog import askinteger,askstring
# Constants
BACKGROUND = '#191919'
SECONDARY_BG = '#2d2d2d'
white = 'white'
highlight_clr = '#e9ff40'
bullet_char = "\u2022"
min_fsize = 2
max_fsize = 100
fonts = ["Arial","Courier","Consolas","Times","Segoe UI"]
fonts.sort()

class DarkPad(Tk):
    """
    The entire application of DarkPad, from its GUI to commands,events,methods all packed in single class
    """
    def __init__(self,geometry,icon) -> None:
        Tk.__init__(self)
        # Initialization
        self.__app_name = "DarkPad"
        self.char_encoding = "UTF-8"
        self.title(f"Untitled - {self.app_name}")
        self.icon_path = icon
        self.iconbitmap(self.icon_path)
        self._curr_file = None
        self.font_tuple = ['Consolas',12]
        self.geometry(geometry)
        self.co_ord = StringVar()
        self.wrap_var = IntVar()
        self.font_rvar = IntVar(value=utils.find_in(fonts,self.font_tuple[0]))
        self.fsize_svar = StringVar(value=f"Current font size : {self.font_tuple[1]}")
        self.nchar_svar = StringVar()
        self.search_window = None

        # Secret feature / Misc menu variables
        self.misc_menu = None
        self.sm_count = 0

        # Menus

        # File menu to create,open,save files
        self.file_menu = Menu(self, background=SECONDARY_BG, fg=white, tearoff=0)
        self.file_menu.add_command(label="New file", command=self.create_file)
        self.file_menu.add_command(label="Open a file", command=self.open_file)
        self.file_menu.add_command(label="Save file", command=self.save_file)
        self.file_menu.add_command(label="Save as..", command=self.save_file_as)

        # Font menu to switch between different fonts and to change font size
        self.font_menu = Menu(self, background=SECONDARY_BG, fg=white, tearoff=0)
        for i, font in enumerate(fonts):
            self.font_menu.add_radiobutton(label=font, font=(font, 10), variable=self.font_rvar, value=i,
                                           command=self.config_font, selectcolor=white)
        self.font_menu.add_separator()
        self.font_menu.add_command(label="Change font size", command=self.change_fsize)

        # Wrap menu to switch between wrap types : char , word, none
        self.wrap_menu = Menu(self, background=SECONDARY_BG, fg=white, tearoff=0)
        self.wrap_menu.add_radiobutton(label="Wrap by words", variable=self.wrap_var, value=0, command=self.config_wrap,
                                       selectcolor=white)
        self.wrap_menu.add_radiobutton(label="Wrap by characters", variable=self.wrap_var, value=1,
                                       command=self.config_wrap, selectcolor=white)
        self.wrap_menu.add_radiobutton(label="No wrap", variable=self.wrap_var, value=2, command=self.config_wrap,
                                       selectcolor=white)

        # Tools menu
        self.tools_menu = Menu(self, background=SECONDARY_BG, fg=white, tearoff=0)
        self.tools_menu.add_command(label="Find & Replace", command=self.open_search_window)
        self.tools_menu.add_command(label="Add today's date/time at cursor", command=self.add_date)
        self.create_custom_menu_bar()

        # creating Text widget and binding events to it
        self.main_frame = Frame(master=self,background=BACKGROUND)
        self.main_frame.pack(side=TOP,fill=BOTH,expand=True)
        self.txtarea = Text(master=self.main_frame,background=BACKGROUND,font=self.font_tuple,width=0,height=0,foreground=white,insertbackground=white,wrap=NONE,undo=True,autoseparators=True,maxundo=-1)
        self.txtarea.pack(side=LEFT,anchor=NW,fill=BOTH,expand=True)
        # ttk Dark Scrollbar
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.Vertical.TScrollbar",
            background=SECONDARY_BG,
            troughcolor=BACKGROUND,
            bordercolor=BACKGROUND,
            arrowcolor=white,
            lightcolor=BACKGROUND,
            darkcolor=BACKGROUND
        )
        style.map(
            "Dark.Vertical.TScrollbar",
            background=[("active", SECONDARY_BG)]
        )

        self.scrollbar = ttk.Scrollbar(
            self.main_frame,
            orient="vertical",
            command=self.txtarea.yview,
            style="Dark.Vertical.TScrollbar"
        )
        self.scrollbar.pack(side=RIGHT,fill=Y,anchor=E)
        self.txtarea.config(yscrollcommand=self.scrollbar.set)
        self.txtarea.tag_configure("search",background=white,foreground='black')
        self.txtarea.tag_configure("current_occurrence",background=highlight_clr,foreground='black')
        self.txtarea.bind("<Tab>",lambda e:self.insert_tab())
        # Have to make two events for lower and upper case letters separately
        self.txtarea.bind("<Control-f>",func=lambda e:self.open_search_window())
        self.txtarea.bind("<Control-F>",func=lambda e:self.open_search_window())
        self.txtarea.bind("<Control-s>",func=lambda e:self.save_file(show_info=False))
        self.txtarea.bind("<Control-S>",func=lambda e:self.save_file(show_info=False))
        self.txtarea.bind("<Control-u>",func=lambda e:self.secret_menu())
        self.txtarea.bind("<Control-U>",func=lambda e:self.secret_menu())
        self.txtarea.bind("<Control-Delete>",func=lambda e:self.ctrl_delete())
        self.txtarea.bind("<Control-BackSpace>",func=lambda e:self.ctrl_backspace())
        self.txtarea.bind("<Control-MouseWheel>",func=lambda e: self.scroll_fsize(e.delta))

        # footer
        self.footer = Frame(master=self,background=SECONDARY_BG)
        self.footer.grid_columnconfigure(1,weight=1)
        self.footer.pack(side=TOP,fill=X,anchor=S)
        self.co_ord_label = Label(master=self.footer,background=SECONDARY_BG,foreground=white,textvariable=self.co_ord)
        self.co_ord_label.pack(side=RIGHT,anchor=E)
        self.fsize_lable = Label(master=self.footer,background=SECONDARY_BG,foreground=white,textvariable=self.fsize_svar)
        self.fsize_lable.pack(side=LEFT,anchor=W)
        self.sep = Label(master=self.footer,background=SECONDARY_BG,foreground=white,text="|",font=('consolas',10,'bold'))
        self.sep.pack(side=LEFT,anchor=W)
        self.nchar_label = Label(master=self.footer,background=SECONDARY_BG,foreground=white,textvariable=self.nchar_svar)
        self.nchar_label.pack(side=LEFT,anchor=W)
        
        # app initialization and configuration / event binding
        self.bind("<Button>",lambda e:self.check_change())
        self.bind("<KeyPress>",lambda e:self.check_change())
        self.protocol("WM_DELETE_WINDOW",self.destroy_event)
        if len(sys.argv)>1:
            self.open_file(sys.argv[-1])
        self.check_change()
        self.config_wrap()
        self.update_footer()
        self.enable_dark_title_bar()
        self.txtarea.focus()

    def enable_dark_title_bar(self):
        try:
            import ctypes
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
        except Exception:
            pass

    def create_custom_menu_bar(self):

        self.menu_bar = Frame(self, bg=SECONDARY_BG)
        self.menu_bar.pack(side=TOP, fill=X)

        def make_menu_button(text, menu):
            lbl = Label(
                self.menu_bar,
                text=text,
                bg=SECONDARY_BG,
                fg=white,
                padx=10,
                pady=4
            )

            def show_menu(event):
                menu.tk_popup(event.x_root, event.y_root)

            def on_enter(e):
                lbl.config(bg=BACKGROUND)

            def on_leave(e):
                lbl.config(bg=SECONDARY_BG)

            lbl.bind("<Button-1>", show_menu)
            lbl.bind("<Enter>", on_enter)
            lbl.bind("<Leave>", on_leave)

            lbl.pack(side=LEFT)
            return lbl

        make_menu_button("File", self.file_menu)
        make_menu_button("Font", self.font_menu)
        make_menu_button("Wrap", self.wrap_menu)
        make_menu_button("Tools", self.tools_menu)

    def open_search_window(self):
        """
        Opens a TopLevel window to use the search/find feature.
        this can be triggered by either using <Control-f> or from Tools menu.
        """
        def find_all(search_entry:Entry,rindex:IntVar,rlist_var:StringVar,total:StringVar,index_reset_flag=True):
            """
            Finds all the occurences of searched word and highlights it using tag "search" and highlights the current occurrence (where cursor is present) with another tag "current_occurrence"
            uses regular expression search and stores the Text.index() values in a list.
            """
            rlist = []
            # if called from replace commands, `index_reset_flag` will be `False`, to keep the cursor on next occurrence of searched word
            if index_reset_flag:
                rindex.set(0)
            # removing all tags before starting a fresh search
            for tag in self.txtarea.tag_names():
                self.txtarea.tag_remove(tag,'1.0','end')
            start = self.txtarea.index('1.0')
            search_word = search_entry.get()
            if search_word:
                matches = re.finditer(search_word, self.content)
                for match in matches:
                    # after finding matches, converting the str indicies to Text indicies and storing in a list
                    match_start = self.txtarea.index(f"{start}+{match.start()}c")
                    match_end = self.txtarea.index(f"{start}+{match.end()}c")
                    rlist.append([match_start, match_end])
                res_list.set(json.dumps(rlist))
                if rlist:
                    for tup in rlist:
                        # adding "search" tags at indicies where search value is found
                        self.txtarea.tag_add("search",tup[0],tup[1])
                    
                    while rindex.get()>len(rlist)-1:
                        # handling index value when called from replace commands
                        rindex.set(rindex.get()-1)
                    # placing cursor at current occurrence and adding "current_occurrence" tag 
                    self.txtarea.mark_set(INSERT,rlist[rindex.get()][0])
                    self.txtarea.tag_add("current_occurrence",rlist[rindex.get()][0],rlist[rindex.get()][1])
                    self.txtarea.see(INSERT)
                    rlist_var.set(json.dumps(rlist))
                    total.set(f"{rindex.get()+1}/{len(json.loads(rlist_var.get()))}")
                    self.check_change()
                else:
                    total.set("0/0")
            else:
                total.set("0/0")

        def next_occurrence(rindex:IntVar,rlist:StringVar,total:StringVar):
            """
            Moves the cursor and focus to next occurrence of searched text
            while doing so, removes "current_occurrence" tag and puts it on next occurence
            """
            rlist = json.loads(rlist.get())
            if len(rlist)!=0 and rindex.get()+1<len(rlist):
                self.txtarea.tag_remove("current_occurrence",'1.0','end')
                rindex.set(rindex.get()+1)
                curr_tup = rlist[rindex.get()]
                self.txtarea.mark_set(INSERT,curr_tup[0])
                self.txtarea.tag_add("current_occurrence",curr_tup[0],curr_tup[1])
                self.txtarea.see(INSERT)
                total.set(f"{rindex.get()+1}/{len(rlist)}")
                self.update_footer()

        def prev_occurrence(rindex:IntVar,rlist:StringVar,total:StringVar):
            """
            Moves the cursor and focus to previous occurrence of searched text
            while doing so, removes "current_occurrence" tag and puts it on previous occurence
            """
            rlist = json.loads(rlist.get())
            if len(rlist)!=0 and rindex.get()-1>=0:
                self.txtarea.tag_remove("current_occurrence",'1.0','end')
                rindex.set(rindex.get()-1) 
                curr_tup = rlist[rindex.get()]
                self.txtarea.mark_set(INSERT,curr_tup[0])
                self.txtarea.tag_add("current_occurrence",curr_tup[0],curr_tup[1])
                self.txtarea.see(INSERT)
                total.set(f"{rindex.get()+1}/{len(rlist)}")
                self.update_footer()

        def replace_current(r_entry:Entry,rindex:IntVar,rlist_var:StringVar,f_entry:Entry,total:StringVar):
            """
            replaces the found text with 'replace' text and updates the List which contains Text.index() values
            """
            ftext = f_entry.get()
            rtext = r_entry.get()
            if ftext==rtext:
                return

            rlist = json.loads(rlist_var.get())
            if rlist:
                curr_tup = rlist[rindex.get()]
                self.txtarea.delete(curr_tup[0],curr_tup[1])
                self.txtarea.insert(curr_tup[0],rtext)
                find_all(f_entry,rindex,rlist_var,total,False)

        def replace_all(r_entry:Entry,rindex:IntVar,rlist_var:StringVar,f_entry:Entry,total:StringVar):
            """
            replaces all occurrences of searched text with 'replace' text using python's str.replace() method and updates the list which contains Text.index() values
            """
            ftext = f_entry.get()
            rtext = r_entry.get()
            if ftext==rtext:
                return

            if json.loads(rlist_var.get()):
                self.content = self.content.replace(ftext,rtext)
                find_all(f_entry,rindex,rlist_var,total,False)
                self.check_change()

        if not isinstance(self.search_window,Toplevel):
            def fr_destroy():
                """
                protocol for window destruction of 'find & replace' window
                removes all kinds of tags from self.txtarea after destroying the TopLevel window.
                """
                self.search_window.destroy()
                self.search_window = None
                for tag in self.txtarea.tag_names():
                    self.txtarea.tag_remove(tag,'1.0','end')

            res_list = StringVar(value="[]")
            total_var = StringVar(value="-/-")
            res_index = IntVar(value=0)

            # search window initialization and configuration
            self.search_window = Toplevel(master=self,background=BACKGROUND)

            def focus_out(event:Event):
                """
                Callback function for when focus is out of Search window
                """
                focus = str(self.search_window.focus_get()) # typecasting widget to string gives the path of widget
                if not focus.startswith(str(self.search_window)):
                    res_list.set("[]")
                    total_var.set("-/-")
                    res_index.set(0)
                    for tag in self.txtarea.tag_names():
                        self.txtarea.tag_remove(tag,'1.0','end')

            self.search_window.geometry("350x150")
            self.search_window.iconbitmap(self.icon_path)
            self.search_window.title(f"Find & Replace - {self.app_name}")
            self.search_window.resizable(width=False,height=False)
            self.search_window.protocol("WM_DELETE_WINDOW",func=fr_destroy)
            self.search_window.bind("<FocusOut>",focus_out)
            self.search_window.focus_set()

            # Creating and adding widgets to search window
            upperFrame = Frame(master=self.search_window,background=BACKGROUND)
            upperFrame.pack(side=TOP,padx=30,anchor=W)
            f_label = Label(master=upperFrame,background=BACKGROUND,foreground=white,text="Find :")
            f_entry = Entry(master=upperFrame,background=BACKGROUND,foreground=white,insertbackground=white,width=25)
            r_label = Label(master=upperFrame,background=BACKGROUND,foreground=white,text="Replace :")
            r_entry = Entry(master=upperFrame,background=BACKGROUND,foreground=white,insertbackground=white,width=25)
            find_btn = Button(master=upperFrame,background=SECONDARY_BG,foreground=white,text="Find all",width=8,command=lambda:find_all(f_entry,res_index,res_list,total_var))
            f_label.grid(row=0,column=0,padx=3,pady=3)
            f_entry.grid(row=0,column=1,padx=3,pady=3)
            r_label.grid(row=1,column=0,padx=3,pady=3)
            r_entry.grid(row=1,column=1,padx=3,pady=3)
            find_btn.grid(row=0,column=2,padx=3,pady=3)
            f_entry.focus()

            midFrame = Frame(master=self.search_window,background=BACKGROUND)
            midFrame.pack(side=TOP,padx=30,anchor=W)
            res_lbl = Label(master=midFrame,background=BACKGROUND,foreground=white,textvariable=total_var)
            res_lbl.pack(padx=100)

            lowerFrame = Frame(master=self.search_window,background=BACKGROUND)
            lowerFrame.pack(side=TOP,padx=30,anchor=W)
            prev_btn = Button(master=lowerFrame,background=SECONDARY_BG,foreground=white,text="Previous",width=15,command=lambda:prev_occurrence(res_index,res_list,total_var))
            next_btn = Button(master=lowerFrame,background=SECONDARY_BG,foreground=white,text="Next",width=15,command=lambda:next_occurrence(res_index,res_list,total_var))
            replace_btn = Button(master=lowerFrame,background=SECONDARY_BG,foreground=white,text="Replace current",width=15,command=lambda:replace_current(r_entry,res_index,res_list,f_entry,total_var))
            replace_all_btn = Button(master=lowerFrame,background=SECONDARY_BG,foreground=white,text="Replace all",width=15,command=lambda:replace_all(r_entry,res_index,res_list,f_entry,total_var))
            prev_btn.grid(row=0,column=0,padx=3,pady=3)
            next_btn.grid(row=0,column=1,padx=3,pady=3)
            replace_btn.grid(row=1,column=0,padx=5,pady=3)
            replace_all_btn.grid(row=1,column=1,padx=5,pady=3)
        else:
            # window is already opened and out of focus. bringing up the window and setting focus on window
            self.search_window.lift()
            self.search_window.focus_set()

    def ctrl_backspace(self):
        """
        Ctrl + BackSpace functionality which deletes the whole word before "insert" mark
        """
        self.txtarea.delete("insert-1c wordstart",INSERT)
        self.check_change()
        return "break" # returning "break" to stop natural behaviour

    def ctrl_delete(self):
        """
        Ctrl + Delete functionality which deletes the whole word after "insert" mark
        """
        self.txtarea.delete(INSERT,"insert+1c wordend")
        self.check_change()
        return "break"

    def add_custom_menu_button(self, text, menu):

        lbl = Label(
            self.menu_bar,
            text=text,
            bg=SECONDARY_BG,
            fg=white,
            padx=10,
            pady=4
        )

        def show_menu(event):
            x = lbl.winfo_rootx()
            y = lbl.winfo_rooty() + lbl.winfo_height()
            menu.tk_popup(x, y)

        def on_enter(e):
            lbl.config(bg=BACKGROUND)

        def on_leave(e):
            lbl.config(bg=SECONDARY_BG)

        lbl.bind("<Button-1>", show_menu)
        lbl.bind("<Enter>", on_enter)
        lbl.bind("<Leave>", on_leave)

        lbl.pack(side=LEFT)
        return lbl

    def secret_menu(self):
        self.sm_count += 1
        if self.sm_count == 99:
            self.misc_menu = Menu(self, background=SECONDARY_BG, fg=white, tearoff=0)

            self.misc_menu.add_command(label="Encrypt", command=self.sm_enc)
            self.misc_menu.add_command(label="Decrypt", command=self.sm_dec)
            self.misc_menu.add_separator()
            self.misc_menu.add_command(label="Text to binary", command=self.sm_t2b)
            self.misc_menu.add_command(label="Binary to text", command=self.sm_b2t)
            self.misc_menu.add_separator()
            self.misc_menu.add_command(label="Destroy!!", command=self.sm_destroy)

            self.misc_button = self.add_custom_menu_button("Misc", self.misc_menu)

    def sm_enc(self):
        """
        secret menu feature
        Encrypts the existing text using key given by user
        best to not use when text is too long
        """
        key = askstring(title="Key",prompt=f"Note: DO NOT USE THIS FEATURE IF THERE IS LOT OF TEXT,\n{' '*10} THIS MIGHT CRASH OR HANG THE APPLICATION\nEnter encryption key:")
        if key:
            key = utils.get_key(key)
            text = utils.ciph(self.content,key)
            self.content = text
            self.wrap_var.set(0)
            self.config_wrap()
            self.check_change()
    
    def sm_dec(self):
        """
        secret menu feature
        Decrypts the existing text using key given by user
        """
        key = askstring(title="Key",prompt="Enter decryption key:\t\t\t")
        if key:
            key = utils.get_key(key)
            text = utils.deciph(self.content,key)
            self.content = text
            self.check_change()

    def sm_t2b(self):
        """
        secret menu feature
        Converts the given text to binary 
        """
        self.content = binary_utils.text_to_binary(self.content)
        self.check_change()

    def sm_b2t(self):
        """
        secret menu feature
        Converts binary to normal text
        """
        try:
            self.content = binary_utils.binary_to_text(self.content)
            self.check_change()
        except TypeError:
            return msgbox.showerror(title="Error",message="Given text is not binary")

    def sm_destroy(self):
        """
        destroys the Misc menu and resets the secret menu trigger counter to 0 (self.ee = 0)
        """
        self.misc_menu.destroy()
        self.misc_button.destroy()
        self.sm_count = 0

    def insert_tab(self):
        """
        Inserts a tab and checks the for change, this is implemented because default <Tab> event binding wasn't working as required.
        """
        self.txtarea.insert(self.txtarea.index(INSERT),"\t")
        self.check_change()
        return "break"

    def add_date(self):
        """
        Adds a Date time string at current position of cursor
        """
        self.txtarea.insert(self.txtarea.index(INSERT),datetime.now().strftime(r"%d/%m/%Y %H:%M:%S"))
        self.check_change()

    def destroy_event(self):
        """
        when user is trying to close the application, then this method will run and ask for confirmation
        """
        def warning_protocol():
            resp = msgbox.askyesnocancel(title="Warning",message="You have unsaved work, do you want to save before exit?")
            if resp is None:
                return
            elif resp:
                self.save_file()
                self.destroy()
            else:
                self.destroy()
        try:
            if self.fs_changed:
                if self.content:
                    warning_protocol()
                else:
                    self.destroy()
            else:
                self.destroy()
        except FileNotFoundError:
            warning_protocol()

    def config_wrap(self):
        """
        wrap configuration, this method is used as command in self.wrap_menu
        """
        wplist = [WORD,CHAR,NONE]
        wp = wplist[self.wrap_var.get()]
        self.txtarea.config(wrap=wp)

    def config_font(self):
        """
        font configuration, this method is used as command in self.font_menu
        """
        font,size = fonts[self.font_rvar.get()], self.font_tuple[1]
        self.font_tuple[0] = font
        self.txtarea.config(font=(font,size))

    def change_fsize(self):
        """
        font size modification, this method is used as command in self.font_menu
        """
        fsize_inp = askinteger(title="Font size",prompt=f"Enter font size:\t\t\t")
        if fsize_inp:
            if fsize_inp<min_fsize:
                fsize_inp = min_fsize
            elif fsize_inp>max_fsize:
                fsize_inp = max_fsize
            else:
                pass
            self.font_tuple[1] = fsize_inp
            self.txtarea.config(font=self.font_tuple)
            self.fsize_svar.set(f"Current font size : {self.font_tuple[1]}")
        
    def check_change(self):
        """
        this method checks if there are any changes in text widget from the saved file, if there is change then '•' will be prefixed and suffixed to the window title
        this method is used as <KeyPress> event handler for application (self) and is used in some other events, methods too.
        """
        self.update_footer()
        try:
            if self.fs_changed:
                if self._curr_file:
                    self.title(f"{bullet_char} {self.curr_file} - {self.app_name} {bullet_char}")
                else:
                    self.title(f"{bullet_char} Untitled - {self.app_name} {bullet_char}")
            else:
                self.title(f"{self.curr_file} - {self.app_name}")
        except FileNotFoundError:
            self.title(f"{bullet_char} Untitled - {self.app_name} {bullet_char}")

    def update_footer(self):
        """
        updates the co-ordinates display of current position of cursor in text widget
        """
        ln,cl  = self.txtarea.index(INSERT).split('.')
        self.co_ord.set(f"Ln {ln}, Col {cl}")
        self.nchar_svar.set(f"Number of characters : {len(self.content)}")

    def update_title(self):
        """
        updates the title of application when opening a file or creating / saving a new file
        """
        if self.curr_file:
            self.title(f"{self.curr_file} - {self.app_name}")
        else:
            self.title(f"Untitled - {self.app_name}")

    def scroll_fsize(self,delta):
        """
        increases and decreases the font size in even numbers (with step of 2), 
        this method is used as <Control-MouseWheel> event handler for text widget
        """
        currval = self.font_tuple[1]
        currval = utils.to_even(currval)
        if delta>0:
            if currval != max_fsize:
                self.font_tuple[1] = currval+2
        else:
            if currval != min_fsize:
                self.font_tuple[1] = currval-2
        self.txtarea.config(font=self.font_tuple)
        self.fsize_svar.set(f"Current font size : {self.font_tuple[1]}")

    @property
    def curr_file(self):
        """
        gives the name of the current file, None if no file is selected
        """
        return self._curr_file

    @curr_file.setter
    def curr_file(self,filename):
        """
        sets the given file as self._curr_file and updates the window title of application
        """
        if filename:
            filename = filename.replace('/','\\')
            self._curr_file = os.path.join(os.getcwd(),filename)
        else:
            self._curr_file = filename
        self.update_title()

    @property
    def app_name(self):
        """
        Returns the __app_name value ("DarkPad")
        """
        return self.__app_name
    
    @app_name.setter
    def app_name(self,v):
        """
        This property cannot be modified
        """
        return

    def create_file(self):
        """
        create a new empty file (unsaved state/Untitled)
        """
        try:
            if self.fs_changed:
                if msgbox.askyesno(title="Confirmation",message="Do you want to proceed without saving the currently opened file?"):
                    pass
                else:
                    return
        except FileNotFoundError:
            pass

        self.curr_file = None
        self.txtarea.delete(1.0,END)
        self.nchar_svar.set(f"Number of characters : {len(self.content)}")

    def open_file(self,filename=""):
        """
        Opens a file and writes its content into text widget
        """
        if not filename: # filename not provided, user is asked to open file
            try:
                if self.curr_file and self.fs_changed:
                    if msgbox.askyesno(title="Confirmation",message="Do you want to proceed without saving the currently opened file?"):
                        pass
                    else:
                        return
                else:
                    pass
            except FileNotFoundError:
                pass

            file = fd.askopenfilename(title="Open a file")
            if file:
                with open(file,'r',encoding=self.char_encoding) as f:
                    print(f'app encoding:{self.char_encoding}, file encoding: {f.encoding}')
                    try:
                        self.content = f.read()
                        self.curr_file = file
                    except UnicodeDecodeError:
                        return msgbox.showerror(title="Error",message="Selected file is not a text file")

        else: # filename provided, opening file directly
            with open(filename,'r',encoding=self.char_encoding) as f:
                print(f'app encoding:{self.char_encoding}, file encoding: {f.encoding}')
                try:
                    self.content = f.read()
                    self.curr_file = filename
                except UnicodeDecodeError:
                    return msgbox.showerror(title="Error",message="Selected file is not a text file")

        self.update_footer()
        self.txtarea.mark_set(INSERT,'1.0')
        self.txtarea.focus()
        self.txtarea.see(INSERT)

    def save_file(self,show_info=True):
        """
        Saves the content of file in file located at self.curr_file 
        """
        try:
            if self.fs_changed :
                if not self.curr_file:
                    file = fd.asksaveasfilename(title="Save this file")
                    if file:
                        self.curr_file = file
                    else:
                        return
                with open(self.curr_file,'w',encoding=self.char_encoding) as f:
                    f.write(self.content)
                if show_info:
                    msgbox.showinfo(title="Success",message=f"Successfully saved file at {self.curr_file}")
                self.check_change()
        except FileNotFoundError:
            self.save_file_as()
    
    def save_file_as(self):
        """
        works similar to popular "Save as" functionality

        asks for a new file name/location and writes the content in the file
        """
        file = fd.asksaveasfilename(title="Save this file as..")
        if file:
            self.curr_file = file
            with open(self.curr_file,'w',encoding=self.char_encoding) as f:
                f.write(self.content)
            msgbox.showinfo(title="Success",message=f"Successfully saved file at {self.curr_file}")

    @property
    def fs_changed(self):
        """
        checks if the current state of text widget is changed from saved file at self.curr_file
        if self.curr_file is None, returns True
        """
        try:
            if self.curr_file:
                f_content = ""
                with open(self.curr_file,'r',encoding=self.char_encoding) as f:
                    f_content = f.read()
                return not f_content == self.content
            else:
                return True
        except FileNotFoundError as err:
            self.curr_file = None
            raise err
    
    @fs_changed.setter
    def fs_changed(self,v):
        """
        This property cannot be modified
        """
        return

    @property
    def content(self):
        """
        gets the entire content of text widget at the moment when this method is called, and returns it
        """
        txt = self.txtarea.get(1.0,END)
        txt = txt[:-1] if txt[-1] == "\n" else txt
        return txt
    
    @content.setter
    def content(self,strval):
        """
        takes strval : string value and writes it in text widget
        """
        self.txtarea.delete(1.0,END)
        self.txtarea.insert(1.0,strval)
	