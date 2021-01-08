export VENV := ./venv

.PHONY: install
install: python

.PHONY: python
python: python_dev python_vvuq

.PHONY: python_dev python_vvuq
python_dev python_vvuq: venv
	. $(VENV)/bin/activate && pip install -e .[$(subst python_,,$@)]

venv:
	test -d $(VENV) || python3 -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip setuptools wheel

.PHONY: test
test:
	tox 

.PHONY: distclean
distclean:
	rm -rf $(VENV)/
	rm -rf .tox/
	rm -rf isct.egg-info/
	rm -rf cov_html/
