# coding=utf-8
"""
Cadasta project - **Questionnaires api.**

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

from cadasta.api.base_api import BaseApi
from cadasta.common.setting import (
    get_url_instance
)

__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__revision__ = '$Format:%H$'
__date__ = '18/01/17'
__copyright__ = 'Copyright 2016, Cadasta'


class GetQuestionnaire(BaseApi):
    """Class to get and put data of questionnaire."""

    api_url = '/api/v1/organizations/%{organization_slug}s/projects/%{project_slug}s/questionnaire/'

    def __init__(self, organization_slug, project_slug, on_finished=None):
        """Constructor.

        It will get Questionnaire from organization_slug and project_slug

        :param organization_slug: Organization slug for Questionnaire
        :type organization_slug: Str

        :param project_slug: Project slug for Questionnaire
        :type project_slug: Str

        :param on_finished: (optional) function that catch result request
        :type on_finished: Function
        """
        self.request_url = get_url_instance() + self.api_url
        super(GetQuestionnaire, self).__init__(on_finished)
        self.on_finished = on_finished
        self.request_url = self.request_url % {
            'organization_slug': organization_slug,
            'project_slug': project_slug
        }
        self.connect_get()

    def connection_finished(self):
        """On finished function when tools request is finished."""
        # extract result
        if self.error:
            self.on_finished(
                (False, self.error)
            )
        else:
            result = self.get_json_results()
            if self.on_finished and callable(self.on_finished):
                self.on_finished(
                    (True, result)
                )
