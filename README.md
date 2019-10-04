# dss-plugin-confluence
Push your DSS wiki contents to [Confluence](https://www.atlassian.com/software/confluence)

## How to use

Once the plugin installed, navigate to the DSS project containing the wiki pages to push to Confluence. Once in the project, click on *Macro > Wiki Confluence export*

Fill in the following details:

- Your login / password for Confluence
- The space name, if the space has not been created yet
- The space key in which the DSS wiki will be pushed
- The type of server, either on premises or cloud instance
- The url of your on premises confluence server, or
- The organization name pointing to your Confluence cloud space

![](images/macro_setup.png)

## Known issues

- All code must be inside a code block. Any html tag present outside a code block is likely to make the page's transfer fail.
- URLs are directly clickable in the DSS wiki, but are not with Confluence, unless they where properly taged in markdown using the `[title](url)` scheme.
- Discrepancies between the DSS Wiki and the uploaded Confluence version can appear when blocks are not properly separated by a line.
