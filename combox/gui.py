
#    Copyright (C) 2015 Combox author(s). See AUTHORS.
#
#    This file is part of Combox.
#
#   Combox is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Combox is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Combox (see COPYING).  If not, see
#   <http://www.gnu.org/licenses/>.

import os

import tkFileDialog

from Tkinter import *

#
# Adapted from:
# http://effbot.org/tkinterbook/tkinter-dialog-windows.htm

class ComboxConfigDialog(object):
    """combox configuration dialog for folks that prefer GUI.

    """

    def __init__(self, title=None):
        self.root = Tk()

        if title:
            self.root.title(title)

        self.result = None

        self.body_frame = Frame(self.root)
        self.initial_focus = self.body(self.body_frame)
        self.body_frame.pack(padx=5, pady=5, fill=BOTH)

        self.buttonbox()

        # init. lists to store fields related to "node information".
        self.node_path_labels = []
        self.node_size_labels = []
        self.node_path_entries = []
        self.node_size_entries = []

        self.root.grab_set()

        if not self.initial_focus:
            self.initial_focus = self.root

        self.root.protocol("WM_DELETE_WINDOW", self.cancel)

        self.center_it()

        self.initial_focus.focus_set()

        self.root.wait_window(self.root)


    #
    # construction hooks
    
    # Adapted from:
    # https://bbs.archlinux.org/viewtopic.php?id=149559
    def center_it(self):
        """
        Center combox config dialog.
        """
        self.root.withdraw()
        self.root.update_idletasks()

        x = (self.root.winfo_screenwidth() - self.root.winfo_reqwidth()) / 2
        y = (self.root.winfo_screenheight() - self.root.winfo_reqheight()) / 2

        self.root.geometry("+%d+%d" % (x, y))
        self.root.deiconify()


    def body(self, master):
        """
        Populates the main body of the dialog.
        """
        Label(master, text="name of this combox").grid(row=0, sticky=W)
        Label(master, text="path to combox directory").grid(row=1, sticky=W)
        Label(master, text="passphrase").grid(row=2, sticky=W)
        Label(master, text="no. of nodes").grid(row=3, sticky=W)

        self.cb_name_entry = Entry(master, width=40)
        self.cb_dir_entry = Entry(master, width=40)
        self.cb_pp_entry = Entry(master, width=40, show='*')
        self.cb_no_nodes_entry = Entry(master, width=40)

        self.cb_name_entry.grid(row=0, column=1)
        self.cb_dir_entry.grid(row=1, column=1, padx=5)
        self.cb_pp_entry.grid(row=2, column=1)
        self.cb_no_nodes_entry.grid(row=3, column=1)

        self.cb_no_nodes_entry.bind("<KeyRelease>", self.populate_node_fields)

        self.cb_dir_entry.bind("<FocusIn>",
                     lambda e: self.create_askdirectory_button(
                         e.widget, e.widget.grid_info()['row']))
        self.cb_dir_entry.bind("<FocusOut>",
                    lambda e: self.destroy_askdirectory_button())

        return self.cb_name_entry # initial focus


    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self.root)
        box.pack(fill=BOTH)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)


        self.root.bind("<Return>", self.ok)
        self.root.bind("<Escape>", self.cancel)


    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.root.initial_focus.focus_set() # put focus back
            return

        self.root.withdraw()
        self.root.update_idletasks()

        self.apply()

        self.cancel()


    def cancel(self, event=None):
        #self.parent.focus_set()
        self.root.destroy()


    # command hooks

    def validate(self):
        return 1 # override


    def apply(self):
        combox_name = self.cb_name_entry.get()
        combox_dir = self.cb_dir_entry.get()
        no_nodes = self.cb_no_nodes_entry.get()
        passp = self.cb_pp_entry.get()

        print combox_name, combox_dir, passp, no_nodes

        # get info about nodes.
        for i in xrange(len(self.node_path_entries)):
            print "node %d" % i,
            print self.node_path_entries[i].get(),
            print self.node_size_entries[i].get()


    def create_askdirectory_button(self, entry, row):
        """
        Creates a button that opens askdirectory dialog at row `row'.
        """
        self.ask_dir_btn = Button(self.body_frame, text="select directory",
                   command=lambda: self.askdirectory(entry))
        self.ask_dir_btn.grid(row=row, column=2)


    def destroy_askdirectory_button(self):
        """
        Destroys the button that opens askdirectory dialog.
        """
        self.ask_dir_btn.destroy()


    def askdirectory(self, entry):
        """
        Spawns a file dialog to read a directory for an Entry.
        """
        # first clear the entry
        entry.delete(0, 'end')

        # spawn dialog to choose directory.
        dir_path = tkFileDialog.askdirectory()
        entry.insert(0, dir_path)


    def clear_node_info_fields(self):
        """
        Clears all fields related to "node information".
        """

        for i in xrange(len(self.node_path_labels)):
           self.node_path_labels[i].destroy()
           self.node_path_entries[i].destroy()
           self.node_size_labels[i].destroy()
           self.node_size_entries[i].destroy()
 
        self.node_path_labels = []
        self.node_size_labels = []
        self.node_path_entries = []
        self.node_size_entries = []


    def populate_node_fields(self, event):
        """
        Populate node fields.
        """
        no_nodes_str = self.cb_no_nodes_entry.get()

        if not no_nodes_str:
            # do nothing.
            return

        no_nodes = 0
        try:
            no_nodes = int(no_nodes_str)
        except ValueError:
            print "Oops! You got to enter a number in here."
            return

        # last occupied row number in self.body_frame.
        last_occ_row = 3
        if self.node_path_labels:
            # means, we've already created fields related to "node
            # information" before; get rid of 'em.
            self.clear_node_info_fields()

        for i in xrange(no_nodes):
            node_path_str = 'node %d path' % i
            node_size_str = 'node %d size (in mega bytes)' % i
            
            lp = Label(self.body_frame,text=node_path_str)
            lp.grid(row=last_occ_row + 1, sticky=W)

            ls = Label(self.body_frame, text=node_size_str)
            ls.grid(row=last_occ_row + 2, sticky=W)

            self.node_path_labels.append(lp)
            self.node_size_labels.append(ls)

            ep = Entry(self.body_frame, width=40)
            ep.grid(row=last_occ_row + 1, column=1, padx=5)

            es = Entry(self.body_frame, width=40)
            es.grid(row=last_occ_row + 2, column=1)

            self.node_path_entries.append(ep)
            self.node_size_entries.append(es)

            self.node_path_entries[i].bind("<FocusIn>",
                    lambda e: self.create_askdirectory_button(
                        e.widget,
                        e.widget.grid_info()['row']))
            self.node_path_entries[i].bind("<FocusOut>",
                    lambda e: self.destroy_askdirectory_button())

            last_occ_row = last_occ_row + 2
            
            

#
# It is here for testing purposes only, will be removed in the future.
if __name__ == "__main__":
    dialog = ComboxConfigDialog("combox configuration")
