#!/usr/bin/env bash
# End-to-end verification driver for ReceptionFlow crews.
#   scripts/verify_all_crews.sh            # all flows, cheap -> expensive
#   scripts/verify_all_crews.sh COOKING    # a single flow by category label
# Requires Task 1 (EPIC_NEWS_REQUEST override) to be in place.
set -uo pipefail
cd "$(dirname "$0")/.."

export MAIL="fred.jacquet@gmail.com"

# "CATEGORY|routing request" — cheap -> expensive (POEM excluded; holiday already green)
FLOWS=(
  "SAINT|Donne moi le saint du jour en français"
  "COOKING|Get me the recipe for Salade César"
  "SHOPPING|Donne moi un conseil d'achat pour remplacer mon sodastream par une marque plus éthique"
  "BOOK_SUMMARY|tell me all about the book: Clamser à Tataouine de Raphaël Quenard"
  "NEWSDAILY|get the daily news report"
  "FINDAILY|get the financial daily report"
  "COMPANY_NEWS|get me all news for company JT International SA"
  "RSS|get the rss weekly report"
  "MENU|Generate a complete weekly menu planner with 30 recipes and shopping list for a family of 3 in French"
  "MEETING_PREP|Meeting preparation for JT International SA with the CTO to discuss PowerFlex deployment in Switzerland"
  "PESTEL|Fais moi un rapport PESTEL à propos de la société Pictet aujourd'hui en français"
  "SALES_PROSPECTING|let's find a sales prospect at Temenos to sell our product: Dell PowerFlex"
  "DEEPRESEARCH|conduct a deep research study on the progress of quantum computing and applications in cryptography"
  "OPEN_SOURCE_INTELLIGENCE|Complete OSINT analysis of Mistral.AI"
)

run_one() {
  local label="$1" request="$2"
  echo "================ $label ================"
  : > logs/epic_news_error.log 2>/dev/null || true
  EPIC_NEWS_REQUEST="$request" crewai flow kickoff
  local code=$?
  local errbytes
  errbytes=$(wc -c < logs/epic_news_error.log 2>/dev/null | tr -d ' ')
  local delivered="no"
  grep -q "Email delivered to fred.jacquet@gmail.com" logs/epic_news.log 2>/dev/null \
    && delivered="yes"
  echo "RESULT $label: exit=$code error_log_bytes=${errbytes:-?} email_delivered=$delivered"
  echo "---- last 8 log lines ----"
  tail -n 8 logs/epic_news.log 2>/dev/null || true
}

only="${1:-}"
for entry in "${FLOWS[@]}"; do
  label="${entry%%|*}"; request="${entry#*|}"
  [ -n "$only" ] && [ "$only" != "$label" ] && continue
  run_one "$label" "$request"
done
