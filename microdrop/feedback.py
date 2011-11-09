"""
Copyright 2011 Ryan Fobel

This file is part of dmf_control_board.

dmf_control_board is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

dmf_control_board is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with dmf_control_board.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import math
from cPickle import dumps, loads

import gtk
import numpy as np
import matplotlib
if os.name=='nt':
    matplotlib.rc('font', **{'family':'sans-serif','sans-serif':['Arial']})
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvasGTK
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

from utility import *


class RetryAction():
    capacitance_threshold = 0
    def __init__(self,
                 capacitance_threshold=None,
                 increase_voltage=None,
                 max_repeats=None):
        if capacitance_threshold:
            self.capacitance_threshold = capacitance_threshold
        else:
            self.capacitance_threshold = self.__class__.capacitance_threshold
        if increase_voltage:
            self.increase_voltage = increase_voltage
        else:
            self.increase_voltage = 0
        if max_repeats:
            self.max_repeats = max_repeats
        else:
            self.max_repeats = 3


class SweepFrequencyAction():
    def __init__(self,
                 start_frequency=None,
                 end_frequency=None,
                 n_frequency_steps=None):
        if start_frequency:
            self.start_frequency = start_frequency
        else:
            self.start_frequency = 1e2
        if end_frequency:
            self.end_frequency = end_frequency
        else:
            self.end_frequency = 30e3
        if n_frequency_steps:
            self.n_frequency_steps = n_frequency_steps
        else:
            self.n_frequency_steps = 30


class SweepVoltageAction():
    def __init__(self,
                 start_voltage=None,
                 end_voltage=None,
                 n_voltage_steps=None):
        if start_voltage:
            self.start_voltage = start_voltage
        else:
            self.start_voltage = 5
        if end_voltage:
            self.end_voltage = end_voltage
        else:
            self.end_voltage = 100
        if n_voltage_steps:
            self.n_voltage_steps = n_voltage_steps
        else:
            self.n_voltage_steps = 20


class FeedbackOptions():
    """
    This class stores the feedback options for a single step in the protocol.
    """
    def __init__(self, feedback_enabled=None,
                 sampling_time_ms=None,
                 n_samples=None,
                 delay_between_samples_ms=None,
                 action=None):
        if feedback_enabled:
            self.feedback_enabled = feedback_enabled
        else:
            self.feedback_enabled = False
        if sampling_time_ms:
            self.sampling_time_ms = sampling_time_ms
        else:
            self.sampling_time_ms = 10
        if n_samples:
            self.n_samples = n_samples
        else:
            self.n_samples = 10
        if delay_between_samples_ms:
            self.delay_between_samples_ms = delay_between_samples_ms
        else:
            self.delay_between_samples_ms = 0
        if action:
            self.action = action
        else:
            self.action = RetryAction()


class FeedbackOptionsController():
    def __init__(self, plugin):
        self.plugin = plugin
        self.builder = gtk.Builder()
        self.builder.add_from_file("plugins/dmf_control_board/microdrop/glade/feedback_options.glade")
        self.window = self.builder.get_object("window")
        self.builder.connect_signals(self)
        self.window.set_title("Feedback Options")
        menu_item = gtk.MenuItem("Feedback Options")
        plugin.app.main_window_controller.menu_tools.append(menu_item)
        menu_item.connect("activate", self.on_window_show)
        menu_item.show()
        
        menu_item = gtk.MenuItem("Calibrate feedback")
        plugin.app.dmf_device_controller.popup.append(menu_item)
        menu_item.connect("activate", self.on_calibrate_feedback)
        menu_item.show()

    def update(self):
        options = self.plugin.current_step_options()

        # update the state of the "Feedback enabled" check button        
        button = self.builder.get_object("button_feedback_enabled")
        if options.feedback_enabled != button.get_active():
            button.set_active(options.feedback_enabled)
        else:
            # if the "Feedback enabled" check button state has not changed, we need to
            # call the handler explicitly
            self.on_button_feedback_enabled_toggled(button)

        # update the sampling time value
        self.builder.get_object("textentry_sampling_time_ms").set_text(
            str(options.sampling_time_ms))

        # update the number of samples value
        self.builder.get_object("textentry_n_samples").set_text(
            str(options.n_samples))

        # update the delay between samples value
        self.builder.get_object("textentry_delay_between_samples_ms").set_text(
            str(options.delay_between_samples_ms))

        # update the state of the "Retry until capacitance..." radio button
        button = self.builder.get_object("radiobutton_retry")
        if (options.action.__class__==RetryAction) != button.get_active():
            button.set_active(options.action.__class__==RetryAction)
        else:
            # if the "Retry until capacitance..." radio button state has not
            # changed, we need to call the handler explicitly
            self.on_radiobutton_retry_toggled(button)

        # update the state of the "Sweep Frequency..." radio button
        button = self.builder.get_object("radiobutton_sweep_frequency")
        if (options.action.__class__==SweepFrequencyAction) != button.get_active():
            button.set_active(options.action.__class__==SweepFrequencyAction)
        else:
            # if the "Sweep Frequency..." radio button state has not
            # changed, we need to call the handler explicitly
            self.on_radiobutton_sweep_frequency_toggled(button)

        # update the state of the "Sweep Voltage..." radio button
        button = self.builder.get_object("radiobutton_sweep_voltage")
        if (options.action.__class__==SweepVoltageAction) != button.get_active():
            button.set_active(options.action.__class__==SweepVoltageAction)
        else:
            # if the "Sweep Voltage..." radio button state has not
            # changed, we need to call the handler explicitly
            self.on_radiobutton_sweep_voltage_toggled(button)

    def on_window_show(self, widget, data=None):
        """
        Handler called when the user clicks on "Feedback Options" in the "Tools"
        menu.
        """
        self.window.show()

    def on_window_delete_event(self, widget, data=None):
        """
        Handler called when the user closes the "Feedback Options" window. 
        """
        self.window.hide()
        return True

    def on_calibrate_feedback(self, widget, data=None):
        print "Calibrate feedback"
        if self.plugin.control_board.connected():
            electrode = \
                self.plugin.app.dmf_device_controller.last_electrode_clicked
            area = electrode.area()*self.plugin.app.dmf_device.scale
            current_state = self.plugin.control_board.state_of_all_channels()
            state = np.zeros(len(current_state))

            if self.plugin.control_board.number_of_channels() < \
                max(electrode.channels):
                self.plugin.app.main_window_controller.warning("Error: "
                    "currently connected board does not have enough channels "
                    "to perform calibration on this electrode.")
                return

            state[electrode.channels]=1
            options = FeedbackOptions(feedback_enabled=True,
                                      sampling_time_ms=10,
                                      n_samples=1,
                                      delay_between_samples_ms=0,
                                      action=RetryAction())
            impedance = self.plugin.measure_impedance(state, options)
            results = FeedbackResults(options,
                                      impedance,
                                      area,
                                      self.app.protocol.current_step().voltage)
            self.plugin.control_board.set_state_of_all_channels(current_state)
            RetryAction.capacitance_threshold = results.max_capacitance/area*0.95
            print "%.1e F/mm2" % results.max_capacitance/area

    def on_button_feedback_enabled_toggled(self, widget, data=None):
        """
        Handler called when the "Feedback enabled" check box is toggled. 
        """
        options = self.plugin.current_step_options()
        options.feedback_enabled = widget.get_active()
        
        self.builder.get_object("textentry_sampling_time_ms").set_sensitive(
            options.feedback_enabled)
        self.builder.get_object("textentry_n_samples").set_sensitive(
            options.feedback_enabled)
        self.builder.get_object("textentry_delay_between_samples_ms"). \
            set_sensitive(options.feedback_enabled)
        self.builder.get_object("radiobutton_retry"). \
            set_sensitive(options.feedback_enabled)
        self.builder.get_object("radiobutton_sweep_frequency"). \
            set_sensitive(options.feedback_enabled)
        self.builder.get_object("radiobutton_sweep_voltage"). \
            set_sensitive(options.feedback_enabled)

        retry = options.action.__class__==RetryAction
        self.builder.get_object("textentry_capacitance_threshold"). \
            set_sensitive(options.feedback_enabled and retry)
        self.builder.get_object("textentry_increase_voltage"). \
            set_sensitive(options.feedback_enabled and retry)
        self.builder.get_object("textentry_max_repeats"). \
            set_sensitive(options.feedback_enabled and retry)

        sweep_frequency = options.action.__class__==SweepFrequencyAction
        self.builder.get_object("textentry_start_frequency"). \
            set_sensitive(options.feedback_enabled and sweep_frequency)
        self.builder.get_object("textentry_end_frequency"). \
            set_sensitive(options.feedback_enabled and sweep_frequency)
        self.builder.get_object("textentry_n_frequency_steps"). \
            set_sensitive(options.feedback_enabled and sweep_frequency)

        sweep_voltage = options.action.__class__==SweepVoltageAction
        self.builder.get_object("textentry_start_voltage"). \
            set_sensitive(options.feedback_enabled and sweep_voltage)
        self.builder.get_object("textentry_end_voltage"). \
            set_sensitive(options.feedback_enabled and sweep_voltage)
        self.builder.get_object("textentry_n_voltage_steps"). \
            set_sensitive(options.feedback_enabled and sweep_voltage)

    def on_radiobutton_retry_toggled(self, widget, data=None):
        """
        Handler called when the "Retry until capacitance..." radio button is
        toggled. 
        """
        options = self.plugin.current_step_options()
        retry = widget.get_active()
        if retry and options.action.__class__!=RetryAction:
            options.action = RetryAction()
        
        # update the retry action parameters
        if retry:
            self.builder.get_object("textentry_capacitance_threshold"). \
                set_text(str(options.action.capacitance_threshold))
            self.builder.get_object("textentry_increase_voltage"). \
                set_text(str(options.action.increase_voltage))
            self.builder.get_object("textentry_max_repeats").set_text(
                str(options.action.max_repeats))
        else:
            self.builder.get_object("textentry_capacitance_threshold"). \
                set_text("")
            self.builder.get_object("textentry_increase_voltage").set_text("")
            self.builder.get_object("textentry_max_repeats").set_text("")

        # update sensitivity
        self.builder.get_object("textentry_capacitance_threshold"). \
            set_sensitive(options.feedback_enabled and retry)
        self.builder.get_object("textentry_increase_voltage"). \
            set_sensitive(options.feedback_enabled and retry)
        self.builder.get_object("textentry_max_repeats"). \
            set_sensitive(options.feedback_enabled and retry)

    def on_radiobutton_sweep_frequency_toggled(self, widget, data=None):
        """
        Handler called when the "Sweep Frequency..." radio button is
        toggled. 
        """
        options = self.plugin.current_step_options()
        sweep_frequency = widget.get_active()
        if sweep_frequency and options.action.__class__!=SweepFrequencyAction:
            options.action = SweepFrequencyAction()
        
        # update the sweep frequency action parameters
        if sweep_frequency:
            self.builder.get_object("textentry_start_frequency"). \
                set_text(str(options.action.start_frequency/1000.0))
            self.builder.get_object("textentry_end_frequency").set_text(
                str(options.action.end_frequency/1000.0))
            self.builder.get_object("textentry_n_frequency_steps").set_text(
                str(str(options.action.n_frequency_steps)))
        else:
            self.builder.get_object("textentry_start_frequency").set_text("")
            self.builder.get_object("textentry_end_frequency").set_text("")
            self.builder.get_object("textentry_n_frequency_steps").set_text("")

        # update sensitivity 
        self.builder.get_object("textentry_start_frequency"). \
            set_sensitive(options.feedback_enabled and sweep_frequency)
        self.builder.get_object("textentry_end_frequency"). \
            set_sensitive(options.feedback_enabled and sweep_frequency)
        self.builder.get_object("textentry_n_frequency_steps"). \
            set_sensitive(options.feedback_enabled and sweep_frequency)

    def on_radiobutton_sweep_voltage_toggled(self, widget, data=None):
        """
        Handler called when the "Sweep Voltage..." radio button is
        toggled. 
        """
        options = self.plugin.current_step_options()
        sweep_voltage = widget.get_active() 
        if sweep_voltage and options.action.__class__!=SweepVoltageAction:
            options.action = SweepVoltageAction()
            
        # update the sweep voltage action parameters
        if sweep_voltage:
            self.builder.get_object("textentry_start_voltage"). \
                set_text(str(options.action.start_voltage))
            self.builder.get_object("textentry_end_voltage").set_text(
                str(options.action.end_voltage))
            self.builder.get_object("textentry_n_voltage_steps").set_text(
                str(str(options.action.n_voltage_steps)))
        else:
            self.builder.get_object("textentry_start_voltage").set_text("")
            self.builder.get_object("textentry_end_voltage").set_text("")
            self.builder.get_object("textentry_n_voltage_steps").set_text("")

        # update sensitivity 
        self.builder.get_object("textentry_start_voltage"). \
            set_sensitive(options.feedback_enabled and sweep_voltage)
        self.builder.get_object("textentry_end_voltage"). \
            set_sensitive(options.feedback_enabled and sweep_voltage)
        self.builder.get_object("textentry_n_voltage_steps"). \
            set_sensitive(options.feedback_enabled and sweep_voltage)

    def on_textentry_sampling_time_ms_focus_out_event(self, widget, event):
        """
        Handler called when the "sampling time" text box loses focus. 
        """
        self.on_textentry_sampling_time_ms_changed(widget)
    
    def on_textentry_sampling_time_ms_key_press_event(self, widget, event):
        """
        Handler called when the user presses a key within the "sampling time" text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_sampling_time_ms_changed(widget)
    
    def on_textentry_sampling_time_ms_changed(self, widget):
        """
        Update the sampling time value for the current step. 
        """
        self.plugin.current_step_options().sampling_time_ms = \
            check_textentry(widget,
                            self.plugin.current_step_options().sampling_time_ms,
                            int)

    def on_textentry_n_samples_focus_out_event(self, widget, event):
        """
        Handler called when the "number of samples" text box loses focus. 
        """
        self.on_textentry_n_samples_changed(widget)
    
    def on_textentry_n_samples_key_press_event(self, widget, event):
        """
        
        Handler called when the user presses a key within the "number of
        samples" text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_n_samples_changed(widget)
    
    def on_textentry_n_samples_changed(self, widget):
        """
        Update the number of samples value for the current step. 
        """
        self.plugin.current_step_options().n_samples = \
            check_textentry(widget,
                            self.plugin.current_step_options().n_samples,
                            int)

    def on_textentry_delay_between_samples_ms_focus_out_event(self,
                                                              widget,
                                                              event):
        """
        Handler called when the "delay between samples" text box loses focus. 
        """
        self.on_textentry_delay_between_samples_ms_changed(widget)
    
    def on_textentry_delay_between_samples_ms_key_press_event(self,
                                                              widget,
                                                              event):
        """
        Handler called when the user presses a key within the "delay between
        samples" text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_delay_between_samples_ms_changed(widget)
    
    def on_textentry_delay_between_samples_ms_changed(self, widget):
        """
        Update the delay between samples value for the current step. 
        """
        self.plugin.current_step_options().delay_between_samples_ms = \
            check_textentry(widget,
                            self.plugin.current_step_options().delay_between_samples_ms,
                            int)
    
    def on_textentry_capacitance_threshold_focus_out_event(self,
                                                           widget,
                                                           event):
        """
        Handler called when the "capacitance threshold" text box loses focus. 
        """
        self.on_textentry_capacitance_threshold_changed(widget)
    
    def on_textentry_capacitance_threshold_key_press_event(self,
                                                           widget,
                                                           event):
        """
        Handler called when the user presses a key within the "capacitance
        threshold" text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_capacitance_threshold_changed(widget)
    
    def on_textentry_capacitance_threshold_changed(self, widget):
        """
        Update the capacitance threshold value for the current step. 
        """
        self.plugin.current_step_options().action.capacitance_threshold = \
            check_textentry(widget,
                            self.plugin.current_step_options(). \
                            action.capacitance_threshold,
                            float)



    def on_textentry_increase_voltage_focus_out_event(self, widget, event):
        """
        Handler called when the "increase voltage" text box loses focus. 
        """
        self.on_textentry_increase_voltage_changed(widget)
    
    def on_textentry_increase_voltage_key_press_event(self, widget, event):
        """
        Handler called when the user presses a key within the "increase
        voltage" text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_increase_voltage_changed(widget)
    
    def on_textentry_increase_voltage_changed(self, widget):
        """
        Update the increase voltage value for the current step. 
        """
        self.plugin.current_step_options().action.increase_voltage = \
            check_textentry(widget,
                            self.plugin.current_step_options().action. \
                            increase_voltage,
                            float)
    
    def on_textentry_max_repeats_focus_out_event(self, widget, event):
        """
        Handler called when the "max repeats" text box loses focus. 
        """
        self.on_textentry_max_repeats_changed(widget)
    
    def on_textentry_max_repeats_key_press_event(self, widget, event):
        """
        Handler called when the user presses a key within the "max repeats"
        text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_max_repeats_changed(widget)
    
    def on_textentry_max_repeats_changed(self, widget):
        """
        Update the max repeats value for the current step. 
        """
        self.plugin.current_step_options().action.max_repeats = \
            check_textentry(widget,
                            self.plugin.current_step_options().action. \
                            max_repeats,
                            int)
            
    def on_textentry_start_frequency_focus_out_event(self, widget, event):
        """
        Handler called when the "start frequency" text box loses focus. 
        """
        self.on_textentry_start_frequency_changed(widget)
    
    def on_textentry_start_frequency_key_press_event(self, widget, event):
        """
        Handler called when the user presses a key within the "start frequency"
        text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_start_frequency_changed(widget)
    
    def on_textentry_start_frequency_changed(self, widget):
        """
        Update the start frequency value for the current step. 
        """
        self.plugin.current_step_options().action.start_frequency = \
            check_textentry(widget,
                            self.plugin.current_step_options().action. \
                            start_frequency/1e3,
                            float)*1e3

    def on_textentry_end_frequency_focus_out_event(self, widget, event):
        """
        Handler called when the "end frequency" text box loses focus. 
        """
        self.on_textentry_end_frequency_changed(widget)
    
    def on_textentry_end_frequency_key_press_event(self, widget, event):
        """
        Handler called when the user presses a key within the "end frequency"
        text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_end_frequency_changed(widget)
    
    def on_textentry_end_frequency_changed(self, widget):
        """
        Update the end frequency value for the current step. 
        """
        self.plugin.current_step_options().action.end_frequency = \
            check_textentry(widget,
                            self.plugin.current_step_options().action. \
                            end_frequency/1e3,
                            float)*1e3

    def on_textentry_n_frequency_steps_focus_out_event(self, widget, event):
        """
        Handler called when the "number of frequency steps" text box loses focus. 
        """
        self.on_textentry_n_frequency_steps_changed(widget)
    
    def on_textentry_n_frequency_steps_key_press_event(self, widget, event):
        """
        Handler called when the user presses a key within the "number of
        frequency steps" text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_n_frequency_steps_changed(widget)
    
    def on_textentry_n_frequency_steps_changed(self, widget):
        """
        Update the number of frequency steps value for the current step. 
        """
        self.plugin.current_step_options().action.n_frequency_steps = \
            check_textentry(widget,
                            self.plugin.current_step_options().action. \
                            n_frequency_steps,
                            float)

    def on_textentry_start_voltage_focus_out_event(self, widget, event):
        """
        Handler called when the "start voltage" text box loses focus. 
        """
        self.on_textentry_start_voltage_changed(widget)
    
    def on_textentry_start_voltage_key_press_event(self, widget, event):
        """
        Handler called when the user presses a key within the "start voltage"
        text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_start_voltage_changed(widget)
    
    def on_textentry_start_voltage_changed(self, widget):
        """
        Update the start voltage value for the current step. 
        """
        self.plugin.current_step_options().action.start_voltage = \
            check_textentry(widget,
                            self.plugin.current_step_options().action. \
                            start_voltage/1e3,
                            float)*1e3

    def on_textentry_end_voltage_focus_out_event(self, widget, event):
        """
        Handler called when the "end voltage" text box loses focus. 
        """
        self.on_textentry_end_voltage_changed(widget)
    
    def on_textentry_end_voltage_key_press_event(self, widget, event):
        """
        Handler called when the user presses a key within the "end voltage"
        text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_end_voltage_changed(widget)
    
    def on_textentry_end_voltage_changed(self, widget):
        """
        Update the end voltage value for the current step. 
        """
        self.plugin.current_step_options().action.end_voltage = \
            check_textentry(widget,
                            self.plugin.current_step_options().action. \
                            end_voltage/1e3,
                            float)*1e3

    def on_textentry_n_voltage_steps_focus_out_event(self, widget, event):
        """
        Handler called when the "number of voltage steps" text box loses focus. 
        """
        self.on_textentry_n_voltage_steps_changed(widget)
    
    def on_textentry_n_voltage_steps_key_press_event(self, widget, event):
        """
        Handler called when the user presses a key within the "number of
        voltage steps" text box. 
        """
        if event.keyval == 65293: # user pressed enter
            self.on_textentry_n_voltage_steps_changed(widget)
    
    def on_textentry_n_voltage_steps_changed(self, widget):
        """
        Update the number of voltage steps value for the current step. 
        """
        self.plugin.current_step_options().action.n_voltage_steps = \
            check_textentry(widget,
                            self.plugin.current_step_options().action. \
                            n_voltage_steps,
                            float)


class FeedbackResults():
    """
    This class stores the impedance results for a single step in the protocol.
    """
    def __init__(self, options, impedance, area, V_total):
        self.options = options
        self.area = area
        self.time = np.array(range(0,self.options.n_samples)) * \
            (self.options.sampling_time_ms + \
            self.options.delay_between_samples_ms)
        self.V_fb = impedance[0::2]
        self.Z_fb = impedance[1::2]
        self.V_total = V_total
        self.Z_device = self.Z_fb*(self.V_total/self.V_fb-1)

    def min_impedance(self):
        return min(self.Z_device)
    
    def max_capacitance(self, frequency):
        return 1.0/(2*math.pi*frequency*self.min_impedance())

    def plot(self, axis):
        axis.plot(t, self.Z_device)


class SweepFrequencyResults():
    """
    This class stores the results for a frequency sweep.
    """
    def __init__(self, options, area, V_total):
        self.options = options
        self.area = area
        self.V_total = V_total
        self.frequency = []
        self.V_fb = []
        self.Z_fb = []
        self.Z_device = []

    def add_frequency_step(self, frequency, impedance):
        V_fb = impedance[0::2]
        Z_fb = impedance[1::2]
        self.frequency.append(frequency)
        self.V_fb.append(V_fb)
        self.Z_fb.append(Z_fb)
        self.Z_device.append(Z_fb*(self.V_total/V_fb-1))

    def plot(self, axis):
        """
        axis.plot(t, self.Z_device)
        """


class SweepVoltageResults():
    """
    This class stores the results for a frequency sweep.
    """
    def __init__(self, options, area):
        self.options = options
        self.area = area
        self.voltage = []
        self.V_fb = []
        self.Z_fb = []
        self.Z_device = []

    def add_voltage_step(self, voltage, impedance):
        V_fb = impedance[0::2]
        Z_fb = impedance[1::2]
        self.voltage.append(voltage)        
        self.V_fb.append(V_fb)
        self.Z_fb.append(Z_fb)
        self.Z_device.append(Z_fb*(voltage/V_fb-1))

    def plot(self, axis):
        """
        axis.plot(t, self.Z_device)
        """


class FeedbackResultsController():
    def __init__(self, plugin):
        self.plugin = plugin
        self.builder = gtk.Builder()
        self.builder.add_from_file("plugins/dmf_control_board/microdrop/glade/feedback_results.glade")
        self.window = self.builder.get_object("window")
        self.combobox_plot_type = self.builder.get_object("combobox_plot_type")
        self.window.set_title("Feedback Results")
        self.builder.connect_signals(self)
        menu_item = gtk.MenuItem("Feedback Results")
        plugin.app.main_window_controller.menu_view.append(menu_item)
        menu_item.connect("activate", self.on_window_show)
        menu_item.show()

        self.figure = Figure()   
        self.canvas = FigureCanvasGTK(self.figure)
        self.axis = self.figure.add_subplot(111)
        self.vbox = self.builder.get_object("vbox1")
        toolbar = NavigationToolbar(self.canvas, self.window)
        self.vbox.pack_start(self.canvas)
        self.vbox.pack_start(toolbar, False, False)
        plot_types = ["Impedance vs time",
                      "Impedance vs frequency",
                      "Impedance vs voltage"]
        combobox_set_model_from_list(self.combobox_plot_type, plot_types)
        self.combobox_plot_type.set_active(0)

    def on_window_show(self, widget, data=None):
        """
        Handler called when the user clicks on "Feedback Results" in the "View"
        menu.
        """
        self.window.show_all()

    def on_window_delete_event(self, widget, data=None):
        """
        Handler called when the user closes the "Feedback Results" window. 
        """
        self.window.hide()
        return True

    def on_combobox_plot_type_changed(self, widget, data=None):
        pass

    def on_experiment_log_selection_changed(self, data):
        """
        Handler called whenever the experiment log selection changes.

        Parameters:
            data : dictionary of experiment log data for the selected steps
        """
        self.axis.cla()
        self.axis.set_xlabel("time (ms)")
        self.axis.set_ylabel("|Z$_{device}$(f)| ($\Omega$)")
        self.axis.grid(True)
        self.axis.set_title("Impedance")
        legend = []
        for row in data:
            if row.keys().count("FeedbackResults"):
                results = loads(row["FeedbackResults"])
                results.plot(self.axis)
                legend.append("Step %d (%.3f s)" % (row["step"], row["time"]))
        if len(legend):
            self.axis.legend(legend)
        self.figure.subplots_adjust(left=0.17, bottom=0.15)
        self.canvas.draw()
