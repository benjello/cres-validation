#!/bin/bash

# Script pour réinitialiser la branche locale main à celle du repo d'origine sur GitHub
# Usage: ./reset-main.sh

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Vérification de la branche actuelle...${NC}"

# Vérifier qu'on est dans un repo git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Erreur: Ce répertoire n'est pas un dépôt Git${NC}"
    exit 1
fi

# Obtenir la branche actuelle
CURRENT_BRANCH=$(git branch --show-current)

if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${RED}Erreur: Vous n'êtes pas sur la branche 'main' (branche actuelle: ${CURRENT_BRANCH})${NC}"
    echo -e "${YELLOW}Pour réinitialiser une autre branche, modifiez le script ou utilisez git directement.${NC}"
    exit 1
fi

echo -e "${GREEN}Branche actuelle: main${NC}"

# Vérifier qu'il y a un remote 'origin'
if ! git remote get-url origin > /dev/null 2>&1; then
    echo -e "${RED}Erreur: Aucun remote 'origin' configuré${NC}"
    exit 1
fi

ORIGIN_URL=$(git remote get-url origin)
echo -e "${GREEN}Remote origin: ${ORIGIN_URL}${NC}"

# Vérifier s'il y a des modifications non commitées
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Attention: Vous avez des modifications non commitées${NC}"
    echo -e "${YELLOW}Voulez-vous continuer ? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Opération annulée${NC}"
        exit 0
    fi
fi

# Vérifier s'il y a des fichiers non trackés (optionnel, juste un avertissement)
if [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo -e "${YELLOW}Attention: Vous avez des fichiers non trackés (ils ne seront pas affectés)${NC}"
fi

echo -e "${YELLOW}Récupération des dernières modifications depuis origin...${NC}"
git fetch origin

# Vérifier que origin/main existe
if ! git rev-parse --verify origin/main > /dev/null 2>&1; then
    echo -e "${RED}Erreur: La branche 'origin/main' n'existe pas${NC}"
    exit 1
fi

echo -e "${YELLOW}Réinitialisation de la branche locale main à origin/main...${NC}"
git reset --hard origin/main

echo -e "${GREEN}✅ Branche main réinitialisée avec succès !${NC}"
echo -e "${GREEN}La branche locale main correspond maintenant exactement à origin/main${NC}"

# Afficher le dernier commit
echo -e "\n${YELLOW}Dernier commit:${NC}"
git log -1 --oneline
