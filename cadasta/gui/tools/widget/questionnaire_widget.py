# coding=utf-8
"""
Cadasta Questionnaire -**Cadasta Widget**

This module provides: Project Questionnaire update
Organisation selection, Generate new questionnairre


.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
import json
import logging
import re

from qgis.gui import QgsMessageBar
from cadasta.gui.tools.widget.widget_base import (
    get_widget_step_ui_class,
    WidgetBase
)
from cadasta.api.questionnaire import GetQuestionnaire, UpdateQuestionnaire
from cadasta.utilities.i18n import tr
from cadasta.utilities.resources import resources_path

__copyright__ = "Copyright 2016, Cadasta"
__license__ = "GPL version 3"
__email__ = "info@kartoza.org"
__revision__ = '$Format:%H$'

FORM_CLASS = get_widget_step_ui_class(__file__)

LOGGER = logging.getLogger('CadastaQGISPlugin')

mapping_type = {
    'String': 'TX',
    'Integer': 'IN',
    'Double': 'DE',
    'Date': 'DA',
    'DateTime': 'DT'
}


class QuestionnaireWidget(WidgetBase, FORM_CLASS):
    """Questionnaire widget."""

    def __init__(self, parent=None):
        """Constructor

        :param parent: parent - widget to use as parent.
        :type parent: QWidget
        """
        super(QuestionnaireWidget, self).__init__(parent)
        self.set_widgets()
        self.qgis_layer_box_changed()

    def set_widgets(self):
        """Set all widgets."""
        self.update_button.clicked.connect(
            self.update_questionnaire)
        self.generate_questionnaire_button.clicked.connect(
            self.generate_new_questionnaire)
        self.qgis_layer_box.currentIndexChanged.connect(
            self.qgis_layer_box_changed)

    def selected_layer(self):
        """Get selected layer from combo box.

        :returns: Layer data
        :rtype: QgsVectorLayer
        """
        layer_data = self.qgis_layer_box.currentLayer()
        return layer_data

    def qgis_layer_box_changed(self):
        """Update description when combo box changed."""
        # Get extent
        layer = self.selected_layer()
        self.reset_button()
        if layer:
            names = layer.name().split('/')
            try:
                self.current_organization_slug = names[0]
                self.current_project_slug = names[1]
                self.get_questionnaire_project(
                    names[0],
                    names[1]
                )
            except IndexError:
                self.current_organization_slug = ''
                self.current_project_slug = ''
                self.get_questionnaire_project('', '')

    def reset_button(self):
        """Function to reset button."""
        self.update_button.setEnabled(False)
        self.generate_questionnaire_button.setEnabled(False)
        self.update_button.setText(
            tr('Update')
        )

    def get_questionnaire_project(self, organization_slug, project_slug):
        """Get questionnaire for project.

        :param organization_slug: Organization slug for Questionnaire
        :type organization_slug: Str

        :param project_slug: Project slug for Questionnaire
        :type project_slug: Str

        """
        self.questionnaire_text_edit.setText(tr('Loading'))
        self.get_questionnaire_api = GetQuestionnaire(
            organization_slug=organization_slug,
            project_slug=project_slug,
            on_finished=self.get_questionnaire_project_finished
        )

    def get_questionnaire_project_finished(self, result):
        """Function when Questionnaire Api finished.

        :param result: result of request
        :type result: (bool, list/dict/str, str, str)
        """
        self.generate_questionnaire_button.setEnabled(True)
        self.update_button.setEnabled(True)

        organization_slug = self.current_organization_slug
        project_slug = self.current_project_slug
        if result[2] == organization_slug and result[3] == project_slug:
            if result[0]:
                self.questionnaire_text_edit.setText(
                    json.dumps(result[1], indent=4))
            else:
                if 'Error code:404' == result[1]:
                    self.questionnaire_text_edit.setText(
                        tr('Questionnaire is not found'))
                else:
                    self.questionnaire_text_edit.setText(
                        tr('Failed to load Questionnaire'))

    def update_questionnaire(self):
        """Update questionnaire of selected project."""
        self.update_button.setEnabled(False)
        self.update_button.setText(
            tr('Updating')
        )

        organization_slug = self.current_organization_slug
        project_slug = self.current_project_slug
        self.update_questionnaire_api = UpdateQuestionnaire(
            organization_slug=organization_slug,
            project_slug=project_slug,
            new_questionnaire=self.questionnaire_text_edit.toPlainText(),
            on_finished=self.update_questionnaire_finished
        )

    def update_questionnaire_finished(self, result):
        """Update questionnaire of selected project is finished.

        :param result: result of request
        :type result: (bool, list/dict/str, str, str)
        """
        self.update_button.setEnabled(True)
        if result[0]:
            self.update_button.setText(tr('Updated'))
        else:
            self.update_button.setText(tr('Failed'))
            if 'Error code:500' == result[1]:
                self.message_bar = QgsMessageBar()
                self.message_bar.pushWarning(
                    self.tr('Error'),
                    self.tr('There was something wrong when update,'
                            'please contact administration')
                )
            elif 'Error code:400' == result[1]:
                self.message_bar = QgsMessageBar()
                self.message_bar.pushWarning(
                    self.tr('Error'),
                    self.tr(
                        'Can not update questionnaire for this project.'
                    )
                )
            else:
                self.message_bar = QgsMessageBar()
                self.message_bar.pushWarning(
                    self.tr('Error'),
                    self.tr(
                        'There was something wrong when update,'
                        'please update it later'
                    )
                )

    def generate_new_questionnaire(self):
        """Generate new questionnaire.

        Thiw will get current questionnaire of create from default
        questionnaire. Updating it by looking of attributes.
        """
        current_layer = self.selected_layer()
        current_questionnaire = self.questionnaire_text_edit.toPlainText()
        questionnaire_path = resources_path('questionnaire.json')
        # get default questionnaire
        with open(questionnaire_path) as data_file:
            default_questionnaire = json.load(data_file)

        try:
            current_questionnaire = json.dumps(
                json.loads(current_questionnaire)
            )
            current_questionnaire = re.sub(
                r'"id":[ ]?"(.*?)"', "",
                current_questionnaire
            )
            current_questionnaire = re.sub(
                r',[ ]?}', '}',
                current_questionnaire
            )
            current_questionnaire = re.sub(
                r',[ ]?,', ',',
                current_questionnaire
            )
            questionnaire = json.loads(current_questionnaire)
            questionnaire.pop('version', None)
            questionnaire.pop('id_string', None)
            questionnaire.pop('md5_hash', None)
            questionnaire.pop('xls_form', None)
        except ValueError as e:
            LOGGER.debug(e)
            default_questionnaire['filename'] = current_layer.name()
            default_questionnaire['title'] = current_layer.name()
            default_questionnaire['id_string'] = current_layer.name()
            questionnaire = default_questionnaire

        # Get current fields
        for field in current_layer.fields():
            found = False
            for question in questionnaire["questions"]:
                if question["name"] == field.name():
                    found = True
            if not found:
                questionnaire["questions"].append(
                    {
                        "name": field.name(),
                        "label": field.name(),
                        "type": mapping_type[field.typeName()],
                        "required": False,
                        "constraint": 'null',
                        "default": 'null',
                        "hint": 'null',
                        "relevant": 'null'
                    }
                )

        self.questionnaire_text_edit.setText(
            json.dumps(questionnaire, indent=4))
        self.update_button.setText(tr('Update'))
