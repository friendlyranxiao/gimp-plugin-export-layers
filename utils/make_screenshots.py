#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Export Layers.
#
# Copyright (C) 2013-2018 khalim19 <khalim19@gmail.com>
#
# Export Layers is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Export Layers is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Export Layers.  If not, see <https://www.gnu.org/licenses/>.

"""
This script automatically takes and processes screenshots of the plug-in dialog
for documentation purposes.
"""

from __future__ import absolute_import, division, print_function, unicode_literals
from export_layers import pygimplib
from future.builtins import *

import os
import time

import pygtk
pygtk.require("2.0")
import gtk

import gimp
from gimp import pdb

from export_layers.pygimplib import pgitemtree
from export_layers.pygimplib import pgutils

import export_layers.config
export_layers.config.init()

from export_layers import builtin_procedures
from export_layers import builtin_constraints
from export_layers import settings_plugin
from export_layers.gui import gui_plugin

pygimplib.init()


PLUGINS_DIRPATH = os.path.dirname(os.path.dirname(pgutils.get_current_module_filepath()))

TEST_IMAGES_DIRPATH = os.path.join(
  pygimplib.config.PLUGIN_SUBDIRPATH, "tests", "test_images")
TEST_IMAGES_FILEPATH = os.path.join(
  TEST_IMAGES_DIRPATH, "test_export_layers_contents.xcf")
OUTPUT_DIRPATH = os.path.join(gimp.user_directory(4), "Loading Screens", "Components")

SCREENSHOTS_DIRPATH = os.path.join(PLUGINS_DIRPATH, "docs", "images")
SCREENSHOT_DIALOG_BASIC_USAGE_FILENAME = "screenshot_dialog_basic_usage.png"
SCREENSHOT_DIALOG_ADVANCED_USAGE_FILENAME = "screenshot_dialog_advanced_usage.png"


def take_screenshots(gui, dialog, settings):
  settings["main/layer_groups_as_folders"].set_value(True)
  settings["gui_session/current_directory"].set_value(OUTPUT_DIRPATH)
  settings["gui/show_more_settings"].set_value(False)
  
  decoration_offsets = move_dialog_to_corner(dialog, settings)
  
  while gtk.events_pending():
    gtk.main_iteration()
  
  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_BASIC_USAGE_FILENAME,
    settings,
    decoration_offsets)
  
  settings["main/use_image_size"].set_value(True)
  settings["gui/show_more_settings"].set_value(True)
  
  #HACK: Accessing private members
  
  gui._box_procedures.clear()
  gui._box_constraints.clear()
  
  gui._box_procedures.add_item(
    builtin_procedures.BUILTIN_PROCEDURES["insert_background_layers"])
  gui._box_constraints.add_item(
    builtin_constraints.BUILTIN_CONSTRAINTS["include_layers"])
  gui._box_constraints.add_item(
    builtin_constraints.BUILTIN_CONSTRAINTS["only_layers_without_tags"])
  settings["main/constraints/added/only_layers_without_tags/enabled"].set_value(False)
  
  gui._export_name_preview.set_selected_items(set([
    gui._export_name_preview._layer_exporter.layer_tree["bottom-frame"].item.ID]))
  gui._export_name_preview.on_selection_changed()
  
  dialog.set_focus(gui._export_name_preview.tree_view)
  
  while gtk.events_pending():
    gtk.main_iteration()
  
  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_ADVANCED_USAGE_FILENAME,
    settings,
    decoration_offsets)
  
  gtk.main_quit()
  

def take_and_process_screenshot(
      screenshots_dirpath, filename, settings, decoration_offsets):
  #HACK: Wait a while until the window is fully shown.
  time.sleep(1)
  
  screenshot_image = take_screenshot()
  
  crop_to_dialog(screenshot_image, settings, decoration_offsets)
  
  pdb.gimp_file_save(
    screenshot_image,
    screenshot_image.active_layer,
    os.path.join(screenshots_dirpath, filename),
    filename)
  
  pdb.gimp_image_delete(screenshot_image)
  

def take_screenshot():
  return pdb.plug_in_screenshot(1, -1, 0, 0, 0, 0)


def move_dialog_to_corner(dialog, settings):
  settings["gui/dialog_position"].set_value((0, 0))
  dialog.set_gravity(gtk.gdk.GRAVITY_STATIC)
  decoration_offset_x, decoration_offset_y = dialog.get_position()
  dialog.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)
  settings["gui/dialog_position"].set_value((-decoration_offset_x, 0))
  
  return decoration_offset_x, decoration_offset_y


def crop_to_dialog(image, settings, decoration_offsets):
  settings["gui/dialog_size"].gui.update_setting_value()
  
  pdb.gimp_image_crop(
    image,
    settings["gui/dialog_size"].value[0],
    settings["gui/dialog_size"].value[1] + decoration_offsets[1],
    0,
    0)
  
  pdb.plug_in_autocrop(image, image.active_layer)


#===============================================================================


def main(settings=None):
  if not settings:
    settings = settings_plugin.create_settings()
  
  image = pdb.gimp_file_load(TEST_IMAGES_FILEPATH, os.path.basename(TEST_IMAGES_FILEPATH))
  
  layer_tree = pgitemtree.LayerTree(
    image, name=pygimplib.config.SOURCE_PERSISTENT_NAME, is_filtered=True)
  
  settings["special/image"].set_value(image)
  
  gui_plugin.ExportLayersGui(layer_tree, settings, run_gui_func=take_screenshots)
  
  pdb.gimp_image_delete(image)
