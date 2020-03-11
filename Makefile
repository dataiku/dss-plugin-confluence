PLUGIN_VERSION=1.0.0
PLUGIN_ID=confluence

all:
	cat plugin.json|json_pp > /dev/null
	rm -rf dist
	mkdir dist
	zip -r dist/dss-plugin-${PLUGIN_ID}-${PLUGIN_VERSION}.zip code-env parameter-sets plugin.json python-lib python-runnables
