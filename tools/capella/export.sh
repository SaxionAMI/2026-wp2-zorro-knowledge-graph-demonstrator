#!/bin/sh
set -eu
mkdir -p /tmp/model/FischertechnikFactory /output
cp /model/FischertechnikFactory.capella /model/FischertechnikFactory.aird /model/FischertechnikFactory.afm /tmp/model/FischertechnikFactory/
cat > /tmp/model/FischertechnikFactory/.project <<'PROJECT'
<?xml version="1.0" encoding="UTF-8"?>
<projectDescription><name>FischertechnikFactory</name><comment></comment><projects></projects><buildSpec></buildSpec><natures><nature>org.polarsys.capella.project.nature</nature></natures></projectDescription>
PROJECT
xvfb-run -a -s '-screen 0 1920x1080x24' capella -nosplash -consoleLog \
  -application org.polarsys.capella.core.commandline.core \
  -appid org.polarsys.kitalpha.doc.gen.business.capella.commandline \
  -data /tmp/workspace -import /tmp/model/FischertechnikFactory \
  -input /FischertechnikFactory/FischertechnikFactory.aird \
  -outputfolder /FischertechnikFactory/html -forceoutputfoldercreation \
  -logfile /tmp/export-log.html
if [ ! -d /tmp/model/FischertechnikFactory/html ]; then
  echo 'Capella did not generate documentation.' >&2
  exit 1
fi
# Native vector export avoids SWT's raster size limit for large hierarchies.
xvfb-run -a -s '-screen 0 1920x1080x24' capella -nosplash -consoleLog \
  -application org.polarsys.capella.core.commandline.core \
  -appid org.polarsys.capella.exportRepresentations \
  -data /tmp/workspace -input /FischertechnikFactory/FischertechnikFactory.aird \
  -outputfolder /FischertechnikFactory/native-svg -forceoutputfoldercreation \
  -imageFormat SVG -logfile /tmp/svg-export-log.html
cp -R /tmp/model/FischertechnikFactory/html/. /output/
mkdir -p /output/native-svg
cp -R /tmp/model/FischertechnikFactory/native-svg/. /output/native-svg/
