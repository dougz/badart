#!/bin/bash

"${HUNT2020_BASE}/snellen/external/closure/bin/calcdeps.py" \
    -i "badart.js" \
    -p "${HUNT2020_BASE}/snellen/external/closure/" \
    --output_file "badart-compiled.js" \
    -o compiled \
    -c "${HUNT2020_BASE}/snellen/external/closure-compiler.jar" \
    -f '--compilation_level' -f 'ADVANCED_OPTIMIZATIONS' \
    -f '--externs' -f "externs.js" \
    -f '--rename_variable_prefix' -f 'S'
