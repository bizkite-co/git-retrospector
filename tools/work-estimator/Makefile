# Makefile for the Git Work Estimate Tool

# Default variables
days ?= 30
session_gap ?= 1
full_credit ?= 1
zero_credit ?= 5
change_baseline ?= 100
change_max_score ?= 500
max_bonus ?= 5

.PHONY: analyze clean help

help:
	@echo "Available commands:"
	@echo "  make analyze [days=N] [zero_credit=N] [max_bonus=N] ..."
	@echo "    - Run the work analysis.
	@echo "  make clean              - Remove generated analysis files."
	@echo "  make help               - Show this help message."

analyze:
	@echo "Running work analysis for the last $(days) days..."
	python src/analyze_work.py .. --days $(days) --session-gap $(session_gap) --full-credit $(full_credit) --zero-credit $(zero_credit) --change-baseline $(change_baseline) --change-max-score $(change_max_score) --max-bonus-hours $(max_bonus)

clean:
	@echo "Removing generated files..."
	rm -f work_analysis.json llm_prompt.txt
