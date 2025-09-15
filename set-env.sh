#\!/bin/bash
export CARTRITA_SECRET=cartrita_main_secret_key_2025_change_this_in_production
export $(grep -v "^#" .env | xargs)
echo "Environment variables loaded from .env"
echo "CARTRITA_SECRET is set to: $CARTRITA_SECRET"
