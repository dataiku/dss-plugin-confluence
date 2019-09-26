# -*- coding: utf-8 -*-

from md2conf import convert_info_macros, convert_comment_block, convert_code_block, add_images, process_refs, upload_attachment
import markdown, re, urllib
from emoji import replace_emoji
from dataikuapi.dss.wiki import DSSWiki

from wikilinks import WikiLinkExtension
from attachmenttable import AttachmentTable


class WikiTransfer(AttachmentTable):
    attachment_table = AttachmentTable()
    
    def recurse_taxonomy(self, taxonomy, ancestor = None):
        for article in taxonomy:
            if len(article['children']) > 0:
                confluence_id = self.transfer_article(article['id'], ancestor)
                self.recurse_taxonomy(article['children'], confluence_id)
            else:
                confluence_id = self.transfer_article(article['id'], ancestor)

    def transfer_article(self, article_id, parent_id = None):
        self.attachment_table.reset()
        article_data = self.wiki.get_article(article_id).get_data()
        dss_page_name = article_data.get_name()
        dss_page_body = article_data.get_body()

        status = self.confluence.get_page_by_title(self.confluence_space, dss_page_name)

        if status != None and "id" in status:
            self.confluence.remove_page(status['id'])

        #change : uploading empty page first
        status = self.confluence.create_page(
            space=self.confluence_space,
            title=dss_page_name,
            body="",
            parent_id = parent_id
        )

        if status is None:
            status = self.confluence.get_page_by_title(
                self.confluence_space, 
                dss_page_name
            )

        #{u'message': u'A page with this title already exists: A page already exists with the title Root in the space with key DEMO', u'data': {u'successful': False, u'errors': [], u'valid': True, u'allowedInReadOnlyMode': True, u'authorized': False}, u'reason': u'Bad Request', u'statusCode': 400}
        new_id = status['id'] # todo: confluence can send None, fix it 

        if len(article_data.article_data['article']['attachments']) > 0:
            self.process_attachments(new_id, article_data)

        confluence_page_body = self.convert(dss_page_body, article_id, new_id)

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

    def convert(self, md_input, article_id, new_id):
        md = replace_emoji(md_input)
        md = self.process_attached_images(md, article_id, new_id)
        md = md + '\n' + self.attachment_table.to_md()
        md = self.develop_dss_links(md)
        html = markdown.markdown(md, extensions=['markdown.extensions.tables',
                                                       'markdown.extensions.fenced_code',
                                                       'markdown.extensions.nl2br',
                                                       'markdown.extensions.extra',
                                                       WikiLinkExtension()])
        html = convert_info_macros(html)
        html = convert_comment_block(html)
        html = convert_code_block(html)
        html = process_refs(html)
        return html

    def develop_dss_links(self, md):
        links = self.find_dss_links(md)
        for link in links:
            object_type = link[0]
            project_key = self.project_key if link[2] == '' and link[0].lower() != 'project' else link[1]
            object_id = link[1] if link[2] == '' else link[2]
            initial_id = object_id if link[2] == '' else project_key + '.' + object_id
            object_path = self.build_dss_path(object_type, project_key, object_id)

            md = re.sub(r'\(' + object_type + r':' + initial_id + r'\)', '(' + object_path + ')',  md, flags=re.IGNORECASE)
            md = re.sub( object_type + r':' + initial_id, self.build_dss_url(object_type, object_path),  md, flags=re.IGNORECASE)
        return md
    
    def find_dss_links(self, md):
        dss_links_regexp = re.compile(r'(\bsaved_model\b|\binsight\b|\bproject\b|\bdataset\b):([a-zA-Z0-9_]+)\.?([a-zA-Z0-9_]+)?',flags=re.I | re.X)
        return dss_links_regexp.findall(md)

    def build_dss_path(self, object_type, project_key, object_id):
        path_type = {
            'saved_model': '/savedmodels/' + object_id + '/versions/',
            'insight': '/dashboards/insights/' + object_id + '/view/',
            'project': '/',
            'dataset': '/datasets/'+ object_id + '/explore/'
        }
        return self.studio_external_url + '/projects/' + project_key + path_type[object_type.lower()]

    def build_dss_url(self, object_type, object_path):
        return '<a href="' + object_path + '">' + object_type + '</a>'

    def process_attached_images(self, md, article_id, new_id):
        links = re.findall(r'\[([^\s]+)\]\(([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\)', md)
        links = self.remove_duplicate_links(links)
        for link in links:
            article = self.wiki.get_article(article_id)
            try:
                image = self.get_uploaded_file(article, link[1], link[2])
                if link[0] == "":
                    file_name = link[1] + '.' + link[2]
                else:
                    file_name = link[0]
                upload_attachment(new_id, file_name, "", self.confluence_url, self.confluence_username, self.confluence_password, raw = image)
                md = re.sub(r'!?\[[^\s]+\]\(' + link[1] + r'\.' + link[2] + r'\)', '<ac:image ac:thumbnail="true"><ri:attachment ri:filename="'+ file_name +'" /></ac:image>', md)
            except:
                md = re.sub(r'!?\[[^\s]+\]\(' + link[1] + r'\.' + link[2] + r'\)', '*Image could not be transfered*', md)
                pass
        return md

    def get_uploaded_file(self, article, project_key, upload_id):
        if project_key == self.project_key:
            return article.get_uploaded_file(project_key, upload_id)
        else:
            wiki = DSSWiki(self.client, project_key)
            list_articles = wiki.list_articles()
            return list_articles[0].get_uploaded_file(project_key, upload_id)

    def remove_duplicate_links(self, links):
        # todo
        return links

    def format_url(self, server_type, server_name, organization_name):
        if server_type == "local":
            return server_name
        else:
            assert re.match('^[a-zA-Z0-9]+$', organization_name)
            return "https://" + organization_name + ".atlassian.net/wiki"

    def update_progress(self):
        self.progress = self.progress + 1
        self.progress_callback(self.progress)

    def process_attachments(self, article_id, article):
        for attachment in article.article_data['article']['attachments']:
            if attachment[u'attachmentType'] == 'FILE':
                attachment_name = attachment['details']['objectDisplayName']
                article = self.wiki.get_article(article.article_id)
                try:
                    file = article.get_uploaded_file(attachment_name, attachment['smartId'])
                    upload_attachment(article_id, attachment_name, "", self.confluence_url, self.confluence_username, self.confluence_password, raw = file)
                except Exception as err:
                    # get_uploaded_file not implemented yet on backend, older version of DSS
                    pass
            elif attachment[u'attachmentType'] == 'DSS_OBJECT':
                self.attachment_table.add(attachment)
                '''
                {
                u 'attachedOn': 1568715909029, u 'attachmentType': u 'FILE', u 'smartId': u 'E3VrvT9ZouZc', u 'details': {
                        u 'mimeType': u 'image/png',
                        u 'objectDisplayName': u 'Screen Shot 2019-09-13 at 09.39.11.png',
                        u 'size': 53791
                    }, u 'attachedBy': u 'admin'
                }
                '''
