.PHONY: help git-health frontend-test frontend-build backend-test backend-check fiorellia-preflight eval-help smoke

help:
	@echo "Local smoke-check commands:"
	@echo "  make git-health          Inspect Git status, refs, and locks"
	@echo "  make frontend-test       Run frontend tests"
	@echo "  make frontend-build      Build frontend"
	@echo "  make backend-test        Run backend tests"
	@echo "  make backend-check       Compile key backend Python modules"
	@echo "  make fiorellia-preflight Run Fiorell.IA training preflight"
	@echo "  make eval-help           Show backend eval command help"
	@echo "  make smoke               Run core local checks"

git-health:
	git status -sb
	git fetch --prune origin
	git fsck --full
	find .git -name '*.lock' -print

frontend-test:
	npm run test

frontend-build:
	npm run build

backend-test:
	cd backend && if [ -x .venv/bin/python ]; then ./.venv/bin/python -m pytest; else python3 -m pytest; fi

backend-check:
	python3 -m py_compile backend/api.py backend/genisia_rag_engine.py backend/config.py backend/schemas.py

fiorellia-preflight:
	python3 fiorellia/training/preflight_check_training.py

eval-help:
	cd backend && python3 eval/run_benchmark.py --help

smoke: frontend-test frontend-build backend-test backend-check
