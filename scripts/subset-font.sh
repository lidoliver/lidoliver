#!/usr/bin/env bash
# Re-subset the embedded font. Only needed when config.py gains a new icon or symbol.
# Needs fonttools + brotli:  python3 -m venv .venv && .venv/bin/pip install fonttools brotli
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python3}
SRC=${SRC:-/usr/share/fonts/TTF}
ICONS=$($PY -c 'import config; print(",".join(f"U+{c:X}" for c in config.icons()))')
UNI="U+0020-007E,U+00B7,U+00C5,U+00C6,U+00D8,U+00E5,U+00E6,U+00F8,U+2014,U+2022,U+2026,U+203A,U+2192,U+258C,$ICONS"
for w in Regular Bold; do
  $PY -m fontTools.subset "$SRC/JetBrainsMonoNerdFont-$w.ttf" --unicodes="$UNI" \
    --layout-features='' --flavor=woff2 --output-file="assets/jbm-${w,,}.woff2"
done
ls -l assets/*.woff2
