# dss-plugin-confluence
Push your DSS wiki contents to [Confluence](https://www.atlassian.com/software/confluence)

## Install in DSS
To install **Plugin: dss-plugin-confluence** in DSS, go to *Administration > Plugins > Store* and search for the plugin name.

Alternatively, [Download it]() (for DSS 6+) and follow our [installation instructions](https://doc.dataiku.com/dss/latest/plugins/installing.html)

## Plugin information

|   |   |
|---|---|
| Version  | 1.0.0 |
| Author  | Dataiku |
| Released  | 2019-09 |
| Last updated  | 2019-09 |
| License  | Apache Software License |
| Source code  | [Github](https://github.com/dataiku/dataiku-contrib/tree/master/confluence) |
| Reporting issues  | [Github](https://github.com/dataiku/dataiku-contrib/issues) |

## How to use

You need to install the plugin in Dataiku DSS. Go to the *Administration > Plugins* page. The plugin requires the installation of a code environment.

Once the plugin, navigate to the DSS project containing the wiki pages to push to Confluence. Once in the project, click on *Macro > Wiki Confluence export*

Fill in the following details:
- Your login / password for Confluence
- The space name in which the DSS wiki will be pushed
- The type of server, either on premises or cloud instance
- The url of your on premises confluence server, or
- The organization name pointing to your Confluence cloud space

![](images/macro_setup.png)
