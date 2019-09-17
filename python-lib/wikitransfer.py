# -*- coding: utf-8 -*-

from md2conf import convert_info_macros, convert_comment_block, convert_code_block, add_images, process_refs
import markdown
from emoji import replace_emoji
import re

class WikiTransfer():

    def recurse_taxonomy(self, taxonomy, ancestor = None):
        for article in taxonomy:
            if len(article['children']) > 0:
                confluence_id = self.transfer_article(article['id'], ancestor)
                self.recurse_taxonomy(article['children'], confluence_id)
            else:
                confluence_id = self.transfer_article(article['id'], ancestor)

    def transfer_article(self, article_id, parent_id = None):
        article_data = self.wiki.get_article(article_id).get_data()
        dss_page_name = article_data.get_name()
        dss_page_body = article_data.get_body()

        confluence_page_body = self.convert(dss_page_body)

        status = self.confluence.get_page_by_title(self.confluence_space, dss_page_name)
        print('ALX:first status={0}'.format(status)) # got None here
        if status != None and "id" in status:
            self.confluence.remove_page(status['id'])

        status = self.confluence.create_page(
            space=self.confluence_space,
            title=dss_page_name,
            body=confluence_page_body,
            parent_id = parent_id
        )
        if status is None:
            status = self.confluence.get_page_by_title(
                self.confluence_space, 
                dss_page_name
            )
        #{u'message': u'A page with this title already exists: A page already exists with the title Root in the space with key DEMO', u'data': {u'successful': False, u'errors': [], u'valid': True, u'allowedInReadOnlyMode': True, u'authorized': False}, u'reason': u'Bad Request', u'statusCode': 400}
        new_id = status['id'] # todo: confluence can send None, fix it 
        confluence_page_body = add_images(
            new_id,
            self.studio_external_url,
            self.confluence_url,
            confluence_page_body,
            self.confluence_username,
            self.confluence_password
        )
        
        status = self.confluence.update_page(
            page_id = new_id,
            title = dss_page_name,
            body=confluence_page_body
        )
        self.update_progress()
        return new_id

    def convert(self, md_input):
        md = self.develop_dss_links(md_input)
        md = self.develop_dsswiki_links(md)
        html = markdown.markdown(md, extensions=['markdown.extensions.tables',
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

    def format_url(self, server_type, server_name, organization_name):
        if server_type == "local":
            return server_name
        else:
            assert re.match('^[a-zA-Z0-9]+$', organization_name)
            return "https://" + organization_name + ".atlassian.net/wiki"

    def develop_dsswiki_links(self, md):
        # this [[Title]] notation only works for wiki articles -> straight embeding in <a> tag
        md = re.sub(r'\[\[([a-zA-Z0-9_]+)\]\]', r'<a href="/display/'+ self.confluence_space + r'/\1">\1</a>',md)
        return md

    def update_progress(self):
        self.progress = self.progress + 1
        self.progress_callback(self.progress)