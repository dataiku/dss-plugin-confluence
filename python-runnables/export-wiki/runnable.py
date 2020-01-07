# -*- coding: utf-8 -*-

from dataiku.runnables import Runnable
from dataikuapi import DSSClient
from dataikuapi.dss.wiki import DSSWiki, DSSWikiSettings
from dataikuapi.utils import DataikuException
import dataiku
import os, re, logging
from atlassian import Confluence

from requests import HTTPError

from wikitransfer import WikiTransfer

import locale
os.environ["PYTHONIOENCODING"] = "utf-8"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='confluence plugin %(levelname)s - %(message)s')

class DSSWikiConfluenceExporter(Runnable, WikiTransfer):

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
        self.assert_confluence_username()
        self.confluence_password = self.config.get("confluence_password", None)
        self.assert_confluence_password()
        self.confluence_url = self.format_confluence_url(self.config.get("server_type", None), self.config.get("url", None), self.config.get("orgname", None))
        self.confluence_space_key = self.config.get("confluence_space_key", None)
        self.assert_space_key()
        self.confluence_space_name = self.config.get("confluence_space_name", None)
        if self.confluence_space_name == "":
            self.confluence_space_name = self.confluence_space_key
        self.check_space_key_format()
        self.client = dataiku.api_client()
        try:
            self.studio_external_url = self.client.get_general_settings().get_raw()['studioExternalUrl']
            assert(self.studio_external_url not in (None, ''))
        except Exception as err:
            logger.error("studioExternalUrl not set :{}".format(err))
            raise Exception("Please set the DSS location URL in Administration > Settings > Notifications & Integrations > DSS Location > DSS URL")
        self.wiki = DSSWiki(self.client, self.project_key)
        self.wiki_settings = self.wiki.get_settings()
        self.taxonomy = self.wiki_settings.get_taxonomy()
        self.articles = self.wiki.list_articles()
        self.space_homepage_id = None
        self.confluence = Confluence(
            url=self.confluence_url,
            username=self.confluence_username,
            password=self.confluence_password
        )
        self.assert_logged_in()
        self.progress = 0

    def get_progress_target(self):
        return (len(self.articles), 'FILES')

    def run(self, progress_callback):
        self.progress_callback = progress_callback

        space = self.confluence.get_space(self.confluence_space_key)
        if space is None:
            raise Exception('Empty answer from server. Please check the Confluence server address.')

        if "id" not in space:
            space = self.confluence.create_space(self.confluence_space_key, self.confluence_space_name)

        if space is None:
            space = self.confluence.get_space(self.confluence_space_key)
            if u'statusCode' in space and space[u'statusCode'] == 404:
                raise Exception('Could not create the "' + self.confluence_space_key + '" space. It probably exists but you don\'t have permission to view it, or the casing is wrong.')

        if space is not None and "homepage" in space:
            self.space_homepage_id = space['homepage']['id']
        else:
            self.space_homepage_id = None

        self.recurse_taxonomy(self.taxonomy, self.space_homepage_id)

        if self.space_homepage_id is not None:
            self.update_landing_page(self.space_homepage_id)
        
        return self.confluence_url + "/display/" + self.confluence_space_key

    def assert_logged_in(self):
        try:
            user_details = self.confluence.get_user_details_by_userkey(self.confluence_username)
        except Exception as err:
            logger.error("get_user_details_by_userkey failed:{}".format(err))
            raise Exception('Could not connect to Confluence server. Please check the connection details')
        if user_details is None:
            raise Exception('No answer from the server. Please check the connection details to the Confluence server.')
        if "HTTP Status 401 – Unauthorized" in user_details:
            raise Exception('No valid Confluence credentials, please check login and password')

    def assert_space_key(self):
        space_name_format = re.compile(r'^[a-zA-Z0-9]+$')
        if self.confluence_space_key is None or space_name_format.match(self.confluence_space_key) is None:
            raise Exception('The space key does not match Confluence requirements ([a-z], [A-Z], [0-9], not space)')

    def assert_confluence_username(self):
        username_format = re.compile(r'^[a-z0-9-.@]+$')
        if self.confluence_username is None or username_format.match(self.confluence_username) is None:
            raise Exception('The Confluence user name is not valid')

    def assert_confluence_password(self):
        if self.confluence_password is None or self.confluence_password == "":
            raise Exception('Please set your Confluence login password')