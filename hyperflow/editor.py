#!/usr/bin/env python3
"""
HyperFlow Editor - GUI for creating and editing automation workflows
"""

import sys
import json
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QDialog, 
    QLineEdit, QFormLayout, QComboBox, QLabel, QCheckBox,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt


class RuleDialog(QDialog):
    """Dialog for creating/editing a rule"""
    
    # Define event types and their properties
    EVENT_PROPERTIES = {
        "openwindow": ["address", "workspace", "class", "title"],
        "closewindow": ["address", "workspace", "class", "title"],
        "activewindow": ["class", "title"],
        "activewindowv2": ["address"],
        "workspace": ["name"],
        "workspacev2": ["name", "id"],
        "destroyworkspacev2": ["name", "id"],
        "windowtitle": ["address"],
        "windowtitlev2": ["address", "title"],
        "activelayout": ["keyboard", "layout"],
        "urgent": ["address"]
    }
    
    def __init__(self, rule_data=None, parent=None):
        super().__init__(parent)
        self.rule_data = rule_data or {}
        self.conditions_widgets = []
        self.actions_widgets = []
        self.setup_ui()
        if self.rule_data:
            self.populate_data()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Edit Rule" if self.rule_data else "New Rule")
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Name
        self.name_edit = QLineEdit()
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_edit)
        
        # Enabled checkbox
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        layout.addWidget(self.enabled_check)
        
        # Trigger type
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems([
            "openwindow", "closewindow", "activewindow", "activewindowv2",
            "workspace", "workspacev2", "destroyworkspacev2", 
            "windowtitle", "windowtitlev2", "activelayout"
        ])
        self.trigger_combo.currentTextChanged.connect(self.on_trigger_changed)
        layout.addWidget(QLabel("Trigger Type:"))
        layout.addWidget(self.trigger_combo)
        
        # Trigger debounce
        self.debounce_edit = QLineEdit()
        self.debounce_edit.setPlaceholderText("Debounce (ms) - e.g. 200")
        layout.addWidget(QLabel("Debounce (optional):"))
        layout.addWidget(self.debounce_edit)
        
        # Conditions section
        layout.addWidget(QLabel("Conditions:"))
        self.conditions_layout = QVBoxLayout()
        conditions_widget = QWidget()
        conditions_widget.setLayout(self.conditions_layout)
        layout.addWidget(conditions_widget)
        
        self.add_condition_btn = QPushButton("Add Condition")
        self.add_condition_btn.clicked.connect(self.add_condition)
        layout.addWidget(self.add_condition_btn)
        
        # Actions section
        layout.addWidget(QLabel("Actions:"))
        self.actions_layout = QVBoxLayout()
        actions_widget = QWidget()
        actions_widget.setLayout(self.actions_layout)
        layout.addWidget(actions_widget)
        
        self.add_action_btn = QPushButton("Add Action")
        self.add_action_btn.clicked.connect(self.add_action)
        layout.addWidget(self.add_action_btn)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        layout.addLayout(buttons_layout)
    
    def on_trigger_changed(self, event_type):
        """Handle trigger type change to update condition property options"""
        # This could be extended to dynamically update property options in existing conditions
        pass
    
    def add_condition(self, condition_data=None):
        """Add a condition row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Property
        property_combo = QComboBox()
        current_event = self.trigger_combo.currentText()
        properties = self.EVENT_PROPERTIES.get(current_event, [])
        property_combo.addItems(properties)
        layout.addWidget(property_combo)
        
        # Operator
        operator_combo = QComboBox()
        operator_combo.addItems(["equals", "contains", "startswith", "endswith", "greater", "less"])
        layout.addWidget(operator_combo)
        
        # Value
        value_edit = QLineEdit()
        value_edit.setPlaceholderText("Value")
        layout.addWidget(value_edit)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_condition(widget))
        layout.addWidget(remove_btn)
        
        self.conditions_layout.addWidget(widget)
        self.conditions_widgets.append({
            'widget': widget,
            'property': property_combo,
            'operator': operator_combo,
            'value': value_edit
        })
        
        # Populate if editing existing condition
        if condition_data:
            property_index = property_combo.findText(condition_data.get('property', ''))
            if property_index >= 0:
                property_combo.setCurrentIndex(property_index)
                
            operator_index = operator_combo.findText(condition_data.get('operator', 'equals'))
            if operator_index >= 0:
                operator_combo.setCurrentIndex(operator_index)
                
            value_edit.setText(condition_data.get('value', ''))
    
    def remove_condition(self, widget):
        """Remove a condition row"""
        self.conditions_layout.removeWidget(widget)
        widget.deleteLater()
        self.conditions_widgets = [cw for cw in self.conditions_widgets if cw['widget'] != widget]
    
    def add_action(self, action_data=None):
        """Add an action row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Command
        command_edit = QLineEdit()
        command_edit.setPlaceholderText("Command (e.g. hyprctl dispatch movetoworkspace 5)")
        layout.addWidget(command_edit)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_action(widget))
        layout.addWidget(remove_btn)
        
        self.actions_layout.addWidget(widget)
        self.actions_widgets.append({
            'widget': widget,
            'command': command_edit
        })
        
        # Populate if editing existing action
        if action_data:
            command_edit.setText(action_data.get('command', ''))
    
    def remove_action(self, widget):
        """Remove an action row"""
        self.actions_layout.removeWidget(widget)
        widget.deleteLater()
        self.actions_widgets = [aw for aw in self.actions_widgets if aw['widget'] != widget]
    
    def populate_data(self):
        """Populate dialog with existing rule data"""
        self.name_edit.setText(self.rule_data.get('name', ''))
        self.enabled_check.setChecked(self.rule_data.get('enabled', True))
        
        trigger = self.rule_data.get('trigger', {})
        trigger_type = trigger.get('type', '')
        index = self.trigger_combo.findText(trigger_type)
        if index >= 0:
            self.trigger_combo.setCurrentIndex(index)
            
        debounce = trigger.get('debounce', '')
        if debounce:
            self.debounce_edit.setText(str(debounce))
        
        # Populate conditions
        conditions = self.rule_data.get('conditions', [])
        for condition in conditions:
            self.add_condition(condition)
        
        # Populate actions
        actions = self.rule_data.get('actions', [])
        for action in actions:
            self.add_action(action)
    
    def get_rule_data(self):
        """Get rule data from dialog inputs"""
        conditions = []
        for cw in self.conditions_widgets:
            prop = cw['property'].currentText()
            operator = cw['operator'].currentText()
            value = cw['value'].text()
            if prop and value:
                conditions.append({
                    'property': prop,
                    'operator': operator,
                    'value': value
                })
        
        actions = []
        for aw in self.actions_widgets:
            command = aw['command'].text()
            if command:
                actions.append({
                    'command': command
                })
        
        trigger_data = {
            'type': self.trigger_combo.currentText()
        }
        
        try:
            debounce = int(self.debounce_edit.text())
            if debounce > 0:
                trigger_data['debounce'] = debounce
        except ValueError:
            pass  # Ignore invalid debounce value
        
        return {
            'id': self.rule_data.get('id', os.urandom(4).hex()),
            'name': self.name_edit.text(),
            'enabled': self.enabled_check.isChecked(),
            'trigger': trigger_data,
            'conditions': conditions,
            'actions': actions
        }


class HyperFlowEditor(QMainWindow):
    """Main editor window"""
    
    def __init__(self):
        super().__init__()
        self.config_path = Path.home() / ".config/hyperflow/workflows.json"
        self.rules = []
        self.setup_ui()
        self.load_rules()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("HyperFlow Editor")
        self.resize(600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Rules list
        self.rules_list = QListWidget()
        layout.addWidget(QLabel("Automation Rules:"))
        layout.addWidget(self.rules_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("New Rule")
        self.new_btn.clicked.connect(self.new_rule)
        buttons_layout.addWidget(self.new_btn)
        
        self.edit_btn = QPushButton("Edit Rule")
        self.edit_btn.clicked.connect(self.edit_rule)
        buttons_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Rule")
        self.delete_btn.clicked.connect(self.delete_rule)
        buttons_layout.addWidget(self.delete_btn)
        
        self.save_btn = QPushButton("Save Rules")
        self.save_btn.clicked.connect(self.save_rules)
        buttons_layout.addWidget(self.save_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_rules(self):
        """Load rules from config file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.rules = json.load(f)
                self.refresh_rules_list()
            else:
                self.rules = []
                self.refresh_rules_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load rules: {e}")
            self.rules = []
            self.refresh_rules_list()
    
    def refresh_rules_list(self):
        """Refresh the rules list display"""
        self.rules_list.clear()
        for rule in self.rules:
            item = QListWidgetItem(rule.get('name', 'Unnamed Rule'))
            item.setCheckState(Qt.Checked if rule.get('enabled', True) else Qt.Unchecked)
            item.setData(Qt.UserRole, rule)
            self.rules_list.addItem(item)
    
    def new_rule(self):
        """Create a new rule"""
        dialog = RuleDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            rule_data = dialog.get_rule_data()
            self.rules.append(rule_data)
            self.refresh_rules_list()
    
    def edit_rule(self):
        """Edit selected rule"""
        current_row = self.rules_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a rule to edit.")
            return
        
        item = self.rules_list.item(current_row)
        rule_data = item.data(Qt.UserRole)
        
        dialog = RuleDialog(rule_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_rule_data = dialog.get_rule_data()
            self.rules[current_row] = new_rule_data
            self.refresh_rules_list()
    
    def delete_rule(self):
        """Delete selected rule"""
        current_row = self.rules_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a rule to delete.")
            return
        
        reply = QMessageBox.question(self, "Confirm", "Are you sure you want to delete this rule?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.rules[current_row]
            self.refresh_rules_list()
    
    def save_rules(self):
        """Save rules to config file"""
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save rules
            with open(self.config_path, 'w') as f:
                json.dump(self.rules, f, indent=2)
            
            QMessageBox.information(self, "Success", f"Rules saved to {self.config_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save rules: {e}")


def main():
    app = QApplication(sys.argv)
    editor = HyperFlowEditor()
    editor.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()