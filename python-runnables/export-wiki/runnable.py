# -*- coding: utf-8 -*-

from dataiku.runnables import Runnable
from dataikuapi import DSSClient
from dataikuapi.dss.wiki import DSSWiki, DSSWikiSettings
from dataikuapi.utils import DataikuException
import dataiku
import os
from atlassian import Confluence

import requests

from wikitransfer import WikiTransfer

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import locale
os.environ["PYTHONIOENCODING"] = "utf-8"

class DSSWikiConfluenceExporter(Runnable, WikiTransfer):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        self.confluence_username = self.config.get("confluence_username", None)
        self.confluence_password = self.config.get("confluence_password", None)
        self.confluence_url = self.format_confluence_url(self.config.get("server_type", None), self.config.get("url", None), self.config.get("orgname", None))
        self.confluence_space_key = self.config.get("confluence_space_key", None)#.upper()
        self.confluence_space_name = self.config.get("confluence_space_name", None)
        if self.confluence_space_name == "":
            self.confluence_space_name = self.confluence_space_key
        self.check_space_key_format()
        self.client = dataiku.api_client()
        self.studio_external_url = self.client.get_general_settings().get_raw()['studioExternalUrl']
        self.wiki = DSSWiki(self.client, self.project_key)
        self.wiki_settings = self.wiki.get_settings()
        self.taxonomy = self.wiki_settings.get_taxonomy()
        self.articles = self.wiki.list_articles()
        self.confluence = Confluence(
            url=self.confluence_url,
            username=self.confluence_username,
            password=self.confluence_password
        )
        self.progress = 0

    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return (len(self.articles), 'FILES')

    def run(self, progress_callback):
        """
        Do stuff here. Can return a string or raise an exception.
        The progress_callback is a function expecting 1 value: current progress
        """
        self.progress_callback = progress_callback
        space = self.confluence.get_space(self.confluence_space_key)

        if "id" not in space:
            space = self.confluence.create_space(self.confluence_space_key, self.confluence_space_name)
        if space is None:
            space = self.confluence.get_space(self.confluence_space_key)
        if space is not None and "homepage" in space:
            ancestor_id = space['homepage']['id']
        else:
            ancestor_id = None

        self.recurse_taxonomy(self.taxonomy, ancestor_id)
        
        return self.confluence_url + "/display/" + self.confluence_space_key