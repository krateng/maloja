convert ../../maloja/web/static/png/favicon_large.png -resize 256 icon256.png
convert ../../maloja/web/static/png/favicon_large.png -resize 128 icon128.png
convert ../../maloja/web/static/png/favicon_large.png -resize 48 icon48.png
convert ../../maloja/web/static/png/favicon_large.png -background none -resize 280 -gravity center -extent 440x280 -background "#232327" -flatten tile.png
rm ../maloja-scrobbler.zip
zip ../maloja-scrobbler.zip sites/* *.js *.json *.html icon*.png
