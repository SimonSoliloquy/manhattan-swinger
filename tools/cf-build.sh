#!/bin/sh
# Build the folder Cloudflare serves at https://simonsoliloquy.com/manhattan-swinger/ (see wrangler.jsonc).
# Cloudflare's GitHub build runs this and then `npx wrangler deploy` on every push to main.
# By hand: sh tools/cf-build.sh && npx wrangler@4.40.0 deploy
set -e
cd "$(dirname "$0")/.."
rm -rf .cf && mkdir -p .cf/manhattan-swinger/data
cp index.html .cf/manhattan-swinger/
cp data/manhattan.bin data/manhattan.json data/streets.json .cf/manhattan-swinger/data/
