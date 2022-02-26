ICON_DIR=./maloja/web/static/png;
SCROBBLER_DIR=./auxiliary/chromium_scrobbler;

convert $ICON_DIR/favicon_large.png -resize 256 $SCROBBLER_DIR/maloja-scrobbler/icon256.png
convert $ICON_DIR/favicon_large.png -resize 128 $SCROBBLER_DIR/maloja-scrobbler/icon128.png
convert $ICON_DIR/favicon_large.png -resize 48 $SCROBBLER_DIR/maloja-scrobbler/icon48.png
convert $ICON_DIR/favicon_large.png -background none -resize 280 -gravity center -extent 440x280 -background "#232327" -flatten $SCROBBLER_DIR/tile.png
rm $SCROBBLER_DIR/maloja-scrobbler.zip
zip $SCROBBLER_DIR/maloja-scrobbler.zip $SCROBBLER_DIR/maloja-scrobbler/* $SCROBBLER_DIR/maloja-scrobbler/*/*
