import gi.repository

gi.require_version('Budgie', '1.0')
from gi.repository import Budgie, GObject, Gtk, Gio
from threading import Thread
import time

import bluetooth_battery

"""
BluetoothBatteryApplet
Author: Konstantin Köhring
Copyright © 2021 Konstantin Köhring
Website=https://github.com/GaLaXy102/budgie-bluetooth-battery-applet
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or any later version. This
program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details. You
should have received a copy of the GNU General Public License along with this
program.  If not, see <https://www.gnu.org/licenses/>.

battery icon
Icons made by Matthieu James for the Faenza Theme is licensed under GPL3
"""

SCHEMA = "de.galaxy102.budgie.bluetooth-battery"
MAC_ADDR_KEY = "device"
POLL_INTERVAL = 30


class BudgieBluetoothBattery(GObject.GObject, Budgie.Plugin):
    """ This is simply an entry point into your Budgie Applet implementation.
        Note you must always override Object, and implement Plugin.
    """

    # Good manners, make sure we have unique name in GObject type system
    __gtype_name__ = "BudgieBluetoothBattery"

    def __init__(self):
        """ Initialisation is important.
        """
        GObject.Object.__init__(self)

    def do_get_panel_widget(self, uuid):
        """ This is where the real fun happens. Return a new Budgie.Applet
            instance with the given UUID. The UUID is determined by the
            BudgiePanelManager, and is used for lifetime tracking.
        """
        return BudgieBluetoothBatteryApplet(uuid)


class BudgieBluetoothBatterySettings(Gtk.Grid):

    def __init__(self, setting):

        super().__init__()

        self.setting = setting
        # grid & layout
        grid = Gtk.Grid()
        self.add(grid)
        self.settings = Gio.Settings(schema=SCHEMA)
        currvalue = self.settings.get_string(MAC_ADDR_KEY)
        entry = Gtk.Entry()
        entry.set_width_chars(17)
        entry.set_text(currvalue)
        entry.connect("changed", self.update_value)
        label = Gtk.Label("MAC address ")
        grid.attach(label, 1, 1, 1, 1)
        grid.attach(entry, 2, 1, 1, 1)
        self.show_all()

    def update_value(self, e: Gtk.Entry):
        newval = e.get_text()
        self.settings.set_string(MAC_ADDR_KEY, newval)


class BudgieBluetoothBatteryApplet(Budgie.Applet):
    """ Budgie.Applet is in fact a Gtk.Bin """
    manager = None

    def __init__(self, uuid):
        Budgie.Applet.__init__(self)
        self.uuid = uuid
        self.settings = Gio.Settings.new(schema_id=SCHEMA)

        self.box = Gtk.EventBox()

        self.icon = Gtk.Image.new_from_icon_name(
            "bluetooth-battery-applet-symbolic",
            Gtk.IconSize.MENU,
        )

        self.label = Gtk.Label()

        self.box.add(self.icon)
        self.box.add(self.label)
        self.add(self.box)
        self.box.show_all()
        self.show_all()

        GObject.threads_init()
        # thread
        self.update = Thread(target=self.loop)
        # daemonize the thread to make the indicator stopable
        self.update.setDaemon(True)
        self.update.start()

    def loop(self):
        while True:
            self.query()
            time.sleep(POLL_INTERVAL)

    def query(self):
        device = self.settings.get_string(MAC_ADDR_KEY)
        if device != self.settings.get_default_value(MAC_ADDR_KEY):
            try:
                self.label.set_label(str(bluetooth_battery.BatteryStateQuerier(device)))
            except:
                self.label.set_label("NC")

    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return BudgieBluetoothBatterySettings(self.get_applet_settings(self.uuid))

    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise.
        """
        return True
