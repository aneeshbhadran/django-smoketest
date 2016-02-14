test:
	virtualenv ve
	./ve/bin/pip install .
	./ve/bin/pip install flake8
	./ve/bin/flake8 smoketest --max-complexity=9
	cd testapp && ../ve/bin/python manage.py test

clean:
	rm -rf ve
	find . -name '*.pyc' -exec rm {} \;
