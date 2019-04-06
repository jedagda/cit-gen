import logging
import gi; gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from src.gui_constants import BOX_SPACING, PADDING, STATIC_DIRECTORY


# This class is the widget inside of vmWidget if an more adapters are added.
class NetworkAdapterWidget(Gtk.EventBox):
    
    def __init__(self):
        logging.debug("Creating NetworkAdapterWidget")
        super(NetworkAdapterWidget, self).__init__()

        self.outerHorBox = Gtk.Box(spacing=BOX_SPACING)
        #self.label = Gtk.Label("Internalnet Basename:") # This is changed to Radio buttons
        self.internalnetButton = Gtk.RadioButton.new_with_label_from_widget(None, "Internalnet")
        self.udpTunnelButton = Gtk.RadioButton.new_with_label_from_widget(self.internalnetButton, "UDPTunnel")
        self.entry = Gtk.Entry()
        self.removeInetButton = Gtk.Button()
        self.removeInetButton.set_image(Gtk.Image.new_from_file(STATIC_DIRECTORY + "/delete-icon.png"))
        self.removeInetButtonHandlerID = 0

        self.initialize()

    #TODO: is this needed?
    def initialize(self):
        self.add(self.outerHorBox)

        #self.outerHorBox.pack_start(self.label, False, False, PADDING) # This is the radio buttons
        self.outerHorBox.pack_start(self.internalnetButton, False, False, PADDING)
        self.outerHorBox.pack_start(self.udpTunnelButton, False, False, PADDING)
        self.outerHorBox.pack_end(self.removeInetButton, False, False, PADDING)
        self.outerHorBox.pack_end(self.entry, True, True, PADDING)

