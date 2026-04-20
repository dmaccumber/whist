.PHONY: install play test simulate report clean

install:
	python3 -m pip install -e ".[dev]"

play:
	python3 -m whist

play-easy:
	python3 -m whist --difficulty easy

play-hard:
	python3 -m whist --difficulty hard

test:
	python3 -m pytest tests/ -v

simulate:
	python3 -m whist --simulate 1000

report:
	cd report && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex

clean:
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/
	find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
