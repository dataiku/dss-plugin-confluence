# -*- coding: utf-8 -*-

import re, arrow

class AttachmentTable():
    def __init__(self):
        self.attachment_list = []

    def add(self, attachment):
        self.attachment_list.append(attachment)

    def reset(self):
        self.attachment_list = []

    def to_md(self):
        if len(self.attachment_list) == 0:
            return ''
        table = '|'.join(["", "DSS attachment", "Project", "Type", "Size", "Added", ""]) + '\n'
        table = table + '|'.join(["", "---", "---", "---", "---", "---", ""])
        for attachment in self.attachment_list:
            item = '[' + attachment['details']['objectDisplayName'] + ']' + '(' + attachment['taggableType'].lower() + ':' + attachment['smartId'] + ')'
            project = re.search('([a-zA-Z0-9_]+)\.?', attachment['smartId']).group(1)
            added = arrow.get(float(attachment['attachedOn']) / 1000.).humanize() + ' by ' + attachment['details']['userDisplayName']
            item_type = self.project_type(attachment)
            line = '|'.join(["", item, project, item_type, "-", added, ""])
            table = table + '\n' + line
        return table

    def project_type(self, attachment):
        return attachment['taggableType'].title()
