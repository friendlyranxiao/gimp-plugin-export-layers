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
This module provides a class to interconnect the widgets displaying previews of
layer names and images to be exported.
"""

from __future__ import absolute_import, division, print_function, unicode_literals
from future.builtins import *

from export_layers.pygimplib import pginvocation

from .. import operations


class ExportPreviewsController(object):
  
  _DELAY_PREVIEWS_SETTINGS_UPDATE_MILLISECONDS = 50
  _DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS = 500
  
  def __init__(self, export_name_preview, export_image_preview, settings, image):
    self._export_name_preview = export_name_preview
    self._export_image_preview = export_image_preview
    self._settings = settings
    self._image = image
    
    self._paned_outside_previews_previous_position = (
      self._settings["gui/paned_outside_previews_position"].value)
    self._paned_between_previews_previous_position = (
      self._settings["gui/paned_between_previews_position"].value)
  
  def init_previews(self):
    self._export_name_preview.update()
    self._export_image_preview.update()
  
  def connect_setting_changes_to_previews(self):
    self._connect_settings_changed()
    self._connect_setting_after_reset_collapsed_layers_in_name_preview()
    self._connect_setting_after_reset_selected_layers_in_name_preview()
    self._connect_setting_after_reset_displayed_layers_in_image_preview()
  
  def _connect_settings_changed(self):
    self._connect_basic_settings()
    
    self._connect_already_added_operations(self._settings["main/procedures"])
    self._prepare_to_connect_subsequent_operations(self._settings["main/procedures"])
    
    self._connect_already_added_operations(self._settings["main/constraints"])
    self._prepare_to_connect_subsequent_operations(self._settings["main/constraints"])
  
  def _connect_basic_settings(self):
    basic_setting_names = [
      "layer_groups_as_folders",
      "use_image_size",
      "only_visible_layers"
    ]
    
    for setting_name in basic_setting_names:
      self._settings["main"][setting_name].connect_event(
        "value-changed", self._update_previews_on_setting_change)
  
  def _connect_already_added_operations(self, operations_group):
    for setting in operations.walk(operations_group, setting_name="enabled"):
      setting.connect_event("value-changed", self._update_previews_on_setting_change)
  
  def _prepare_to_connect_subsequent_operations(self, operations_group):
    def _on_after_add_operation(operations_, operation, *args, **kwargs):
      if operation["enabled"].value:
        self._update_previews_on_setting_change(operation["enabled"])
      operation["enabled"].connect_event(
        "value-changed", self._update_previews_on_setting_change)
    
    def _on_after_reorder_operation(operations_, operation, *args, **kwargs):
      if operation["enabled"].value:
        self._update_previews_on_setting_change(operation["enabled"])
    
    def _on_before_remove_operation(operations_, operation, *args, **kwargs):
      if operation["enabled"].value:
        # Changing the enabled state triggers the "value-changed" event and thus
        # properly keeps the previews in sync after operation removal.
        operation["enabled"].set_value(False)
    
    operations_group.connect_event("after-add-operation", _on_after_add_operation)
    operations_group.connect_event("after-reorder-operation", _on_after_reorder_operation)
    operations_group.connect_event("before-remove-operation", _on_before_remove_operation)
  
  def _update_previews_on_setting_change(self, setting):
    pginvocation.timeout_add_strict(
      self._DELAY_PREVIEWS_SETTINGS_UPDATE_MILLISECONDS,
      self._export_name_preview.update)
    pginvocation.timeout_add_strict(
      self._DELAY_PREVIEWS_SETTINGS_UPDATE_MILLISECONDS,
      self._export_image_preview.update)
  
  def _connect_setting_after_reset_collapsed_layers_in_name_preview(self):
    self._settings[
      "gui_session/export_name_preview_layers_collapsed_state"].connect_event(
        "after-reset",
        lambda setting: self._export_name_preview.set_collapsed_items(
          setting.value[self._image.ID]))
  
  def _connect_setting_after_reset_selected_layers_in_name_preview(self):
    self._settings["main/selected_layers"].connect_event(
      "after-reset",
      lambda setting: self._export_name_preview.set_selected_items(
        setting.value[self._image.ID]))
  
  def _connect_setting_after_reset_displayed_layers_in_image_preview(self):
    def _clear_image_preview(setting):
      self._export_image_preview.clear()
    
    self._settings["gui_session/export_image_preview_displayed_layers"].connect_event(
      "after-reset", _clear_image_preview)
  
  def connect_visible_changed_to_previews(self):
    def _connect_visible_changed(preview, setting):
      preview.widget.connect("notify::visible", self._on_preview_visible_changed, preview)
      if not setting.value:
        preview.lock_update(True, "previews_sensitive")
    
    _connect_visible_changed(
      self._export_name_preview, self._settings["gui/export_name_preview_sensitive"])
    _connect_visible_changed(
      self._export_image_preview, self._settings["gui/export_image_preview_sensitive"])
  
  def _on_preview_visible_changed(self, widget, property_spec, preview):
    preview_visible = preview.widget.get_visible()
    preview.lock_update(not preview_visible, "preview_visible")
    if preview_visible:
      preview.update()
  
  def on_dialog_is_active_changed(self, dialog, property_spec, is_exporting_func):
    if dialog.is_active() and not is_exporting_func():
      self._export_name_preview.update(reset_items=True)
      self._export_image_preview.update()
  
  def on_paned_outside_previews_position_changed(self, paned, property_spec):
    current_position = paned.get_position()
    max_position = paned.get_property("max-position")
    
    if (current_position == max_position
        and self._paned_outside_previews_previous_position != max_position):
      self._disable_preview_on_paned_drag(
        self._export_name_preview, self._settings["gui/export_name_preview_sensitive"],
        "previews_sensitive")
      self._disable_preview_on_paned_drag(
        self._export_image_preview, self._settings["gui/export_image_preview_sensitive"],
        "previews_sensitive")
    elif (current_position != max_position
          and self._paned_outside_previews_previous_position == max_position):
      self._enable_preview_on_paned_drag(
        self._export_name_preview, self._settings["gui/export_name_preview_sensitive"],
        "previews_sensitive")
      self._enable_preview_on_paned_drag(
        self._export_image_preview, self._settings["gui/export_image_preview_sensitive"],
        "previews_sensitive")
    elif current_position != self._paned_outside_previews_previous_position:
      if self._export_image_preview.is_larger_than_image():
        pginvocation.timeout_add_strict(
          self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS,
          self._export_image_preview.update)
      else:
        pginvocation.timeout_remove_strict(self._export_image_preview.update)
        self._export_image_preview.resize()
    
    self._paned_outside_previews_previous_position = current_position
  
  def on_paned_between_previews_position_changed(self, paned, property_spec):
    current_position = paned.get_position()
    max_position = paned.get_property("max-position")
    min_position = paned.get_property("min-position")
    
    if (current_position == max_position
        and self._paned_between_previews_previous_position != max_position):
      self._disable_preview_on_paned_drag(
        self._export_image_preview, self._settings["gui/export_image_preview_sensitive"],
        "vpaned_preview_sensitive")
    elif (current_position != max_position
          and self._paned_between_previews_previous_position == max_position):
      self._enable_preview_on_paned_drag(
        self._export_image_preview, self._settings["gui/export_image_preview_sensitive"],
        "vpaned_preview_sensitive")
    elif (current_position == min_position
          and self._paned_between_previews_previous_position != min_position):
      self._disable_preview_on_paned_drag(
        self._export_name_preview, self._settings["gui/export_name_preview_sensitive"],
        "vpaned_preview_sensitive")
    elif (current_position != min_position
          and self._paned_between_previews_previous_position == min_position):
      self._enable_preview_on_paned_drag(
        self._export_name_preview, self._settings["gui/export_name_preview_sensitive"],
        "vpaned_preview_sensitive")
    elif current_position != self._paned_between_previews_previous_position:
      if self._export_image_preview.is_larger_than_image():
        pginvocation.timeout_add_strict(
          self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS,
          self._export_image_preview.update)
      else:
        pginvocation.timeout_remove_strict(self._export_image_preview.update)
        self._export_image_preview.resize()
    
    self._paned_between_previews_previous_position = current_position
  
  def _enable_preview_on_paned_drag(
        self, preview, preview_sensitive_setting, update_lock_key):
    preview.lock_update(False, update_lock_key)
    preview.add_function_at_update(preview.set_sensitive, True)
    # In case the image preview gets resized, the update would be canceled,
    # hence update always.
    pginvocation.timeout_add(
      self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS, preview.update)
    preview_sensitive_setting.set_value(True)
  
  def _disable_preview_on_paned_drag(
        self, preview, preview_sensitive_setting, update_lock_key):
    preview.lock_update(True, update_lock_key)
    preview.set_sensitive(False)
    preview_sensitive_setting.set_value(False)
  
  def on_name_preview_selection_changed(self):
    layer_elem_from_cursor = self._export_name_preview.get_layer_elem_from_cursor()
    if layer_elem_from_cursor is not None:
      if (self._export_image_preview.layer_elem is None
          or (layer_elem_from_cursor.item.ID
              != self._export_image_preview.layer_elem.item.ID)):
        self._export_image_preview.layer_elem = layer_elem_from_cursor
        self._export_image_preview.update()
    else:
      layer_elems_from_selected_rows = (
        self._export_name_preview.get_layer_elems_from_selected_rows())
      if layer_elems_from_selected_rows:
        self._export_image_preview.layer_elem = layer_elems_from_selected_rows[0]
        self._export_image_preview.update()
      else:
        self._export_image_preview.clear()
  
  def on_name_preview_after_update(self):
    self._export_image_preview.update_layer_elem()
  
  def on_name_preview_after_edit_tags(self):
    self.on_name_preview_selection_changed()
