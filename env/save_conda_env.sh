#!/bin/bash
ENV_FILE="environment.yml"
TMP_FILE="$ENV_FILE.tmp"

# Export the current Conda environment
conda env export --no-builds > "$TMP_FILE" || exit 1

# Compare with existing environment.yml
if ! cmp -s "$TMP_FILE" "$ENV_FILE"; then
    echo "Conda environment has changed. Updating $ENV_FILE."
    mv "$TMP_FILE" "$ENV_FILE"
    git add "$ENV_FILE"
else
    rm "$TMP_FILE"
fi
