#!/usr/bin/env bash
set -euo pipefail

mkdir -p ./data
chmod -R 777 ./data
echo "Diretorio ./data preparado com permissoes 777 para o container SQL Server (uid 10001)."
