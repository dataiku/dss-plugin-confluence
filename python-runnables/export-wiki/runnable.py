# -*- coding: utf-8 -*-

from dataiku.runnables import Runnable
from dataikuapi import DSSClient
from dataikuapi.dss.wiki import DSSWiki, DSSWikiSettings
from dataikuapi.utils import DataikuException
import dataiku
import time
import os
from atlassian import Confluence
from md2conf import convert_info_macros, convert_comment_block, convert_code_block, add_images, process_refs
import markdown
import requests
import re
from emoji import replace_emoji

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import locale
os.environ["PYTHONIOENCODING"] = "utf-8"

class DSSWikiConfluenceExporter(Runnable):
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
        self.username = self.config.get("username", None)
        self.password = self.config.get("password", None)
        self.url = self.format_url(self.config.get("server_type", None), self.config.get("url", None), self.config.get("orgname", None))
        self.confluence_space = self.config.get("confluence_space", None)
        self.client = dataiku.api_client()
        self.studio_external_url = self.client.get_general_settings().get_raw()['studioExternalUrl']
        self.wiki = DSSWiki(self.client, self.project_key)
        self.wiki_settings = self.wiki.get_settings()
        self.taxonomy = self.wiki_settings.get_taxonomy()
        self.articles = self.wiki.list_articles()
        self.confluence = Confluence(
            url=self.url,
            username=self.username,
            password=self.password
        )
        self.progress = 0

    def format_url(self, server_type, server_name, organization_name):
        if server_type == "local":
            return server_name
        else:
            assert re.match('^[a-zA-Z0-9]+$', organization_name)
            return "https://" + organization_name + ".atlassian.net/wiki"

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
        space = self.confluence.get_space(self.confluence_space)
        if "id" not in space:
            status = self.confluence.create_space(self.confluence_space, self.confluence_space)

        # todo: should the space home page be root for all tranfered docs ?
        self.recurse_taxonomy(self.taxonomy)
        return self.url + "/display/" + self.confluence_space

    def recurse_taxonomy(self, taxonomy, ancestor = None):
        for article in taxonomy:
            if len(article['children']) > 0:
                confluence_id = self.transfer_article(article['id'], ancestor)
                self.recurse_taxonomy(article['children'], confluence_id)
            else:
                confluence_id = self.transfer_article(article['id'], ancestor)

    def transfer_article(self, article_id, parent_id = None):
        article = self.wiki.get_article(article_id)
        page_name = article.get_data().get_name()
        dss_page_body = article.get_data().get_body()

        dss_page_body = self.develop_dss_links(dss_page_body)
        dss_page_body = self.develop_dsswiki_links(dss_page_body)
        confluence_page_body = self.convert(dss_page_body)

        status = self.confluence.get_page_by_title(self.confluence_space, page_name)
        print('ALX:first status={0}'.format(status)) # got None here
        if status != None and "id" in status:
            self.confluence.remove_page(status['id'])

        status = self.confluence.create_page(
            space=self.confluence_space,
            title=page_name,
            body=confluence_page_body,
            parent_id = parent_id
        )
        #{u'message': u'A page with this title already exists: A page already exists with the title Root in the space with key DEMO', u'data': {u'successful': False, u'errors': [], u'valid': True, u'allowedInReadOnlyMode': True, u'authorized': False}, u'reason': u'Bad Request', u'statusCode': 400}
        new_id = status['id'] # todo: confluence can send None, fix it 
        confluence_page_body = add_images(
            new_id,
            self.studio_external_url,
            self.url,
            confluence_page_body,
            self.username,
            self.password
        )
        myLocale=locale.setlocale(category=locale.LC_ALL, locale="en_GB.UTF-8")
        status = self.confluence.update_page(
            page_id = new_id,
            title = page_name,
            body=confluence_page_body
        )
        self.update_progress()
        return new_id

    def update_progress(self):
        self.progress = self.progress + 1
        self.progress_callback(self.progress)

    def convert(self, md_input):
        html = markdown.markdown(md_input, extensions=['markdown.extensions.tables',
                                                       'markdown.extensions.fenced_code',
                                                       'markdown.extensions.nl2br',
                                                       'markdown.extensions.extra'])
        html = '\n'.join(html.split('\n')[1:])
        html = convert_info_macros(html)
        html = convert_comment_block(html)
        html = convert_code_block(html)
        html = process_refs(html)
        return html

    def develop_dss_links(self, md):
        md = replace_emoji(md)
        md = re.sub(r'\(saved_model:(\d+)\)', '(' + self.studio_external_url + r'/projects/'+ self.project_key +r'/savedmodels/\1/versions/)',md)
        md = re.sub(r'saved_model:(\d+)', '<a href="' + self.studio_external_url + r'/projects/'+ self.project_key +r'/savedmodels/\1/versions/">Model</a>',md)
        md = re.sub(r'\(insight:(\d+)\)', '(' + self.studio_external_url + r'/projects/'+ self.project_key +r'/dashboards/insights/\1/view/)',md)
        md = re.sub(r'insight:(\d+)', '<a href="' + self.studio_external_url + r'/projects/'+ self.project_key +r'/dashboards/insights/\1/view/">Insight</a>',md)
        md = re.sub(r'\(project:([^\s]+)\)', '(' + self.studio_external_url + r'/projects/\1/)',md)
        md = re.sub(r'project:([^\s]+)', '<a href="' + self.studio_external_url + r'/projects/\1/">Project</a>',md)
        md = re.sub(r'\(dataset:([^\s]+)\)', '(' + self.studio_external_url + r'/projects/'+ self.project_key + r'/datasets/\1/explore/)',md)
        md = re.sub(r'dataset:([^\s]+)', '<a href="' + self.studio_external_url + r'/projects/'+ self.project_key + r'/datasets/\1/explore/">Dataset</a>',md)
        return md

    def develop_dsswiki_links(self, md):
        # this [[Title]] notation only works for wiki articles -> straight embeding in <a> tag
        md = re.sub(r'\[\[([a-zA-Z0-9_]+)\]\]', r'<a href="/display/'+ self.confluence_space + r'/\1">\1</a>',md)
        return md
