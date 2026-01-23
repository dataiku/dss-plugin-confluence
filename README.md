# Confluence Exporter

This plugin provides a export connector to push your Dataiku DSS projects wiki in Confluence.

## How to set up

- One installed, the login credentials to the Confluence service need to be set up. As a DSS administrator, go to **Plugins > Installed > Confluence wiki > Settings > Confluence login** and add a preset. There, fill in the connection details and make the preset available to the relevant DSS user / group.
- For online Confluence instances, you will need to first create an API token. To do so, go to your **Profile > Manage your account > Security > Create and manage API tokens > Create API token**. Copy the created token and paste it into the API token box of your DSS preset.
- A space needs to exist on the Confluence server. On Confluence, use the **Spaces > Create Space** menu, choose a space name and copy the space key. Then paste it in the **Confluence Space key** box of your DSS preset.
- The DSS URL needs to be filled in. Go to **Administration > Settings > Notifications & Integrations > DSS Location** and make sure that the DSS URL is set up.

## How to use

Once the plugin is set up, navigate to the DSS project containing the wiki pages to push to Confluence. Once in the project, click on **Macro > Wiki Confluence export**. Select the preset corresponding to the Confluence Space you are targeting, and press **Run Macro**.

## Known Issues

- All code must be inside a code block. Any html tag present outside a code block is likely to make the page’s transfer fail.
- Compliance to HTML and Markdown standards is more stringent on Confluence than on DSS Wiki. Some HTML code might result in a functional wiki page on DSS but may be refused on Confluence. If that’s the case, an error message will appear in place of the wiki page. It’s up to you to go back to the DSS wiki page and fix the issue there before attempting another transfer.
- Discrepancies between the DSS Wiki and the uploaded Confluence version can appear when blocks are not properly separated by a line.
- URLs are directly clickable in the DSS wiki, but are not with Confluence, unless they were properly tagged in markdown using the `[title](url)` scheme.
