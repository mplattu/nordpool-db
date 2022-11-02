.PHONY: test install-libs update-requirements

clean:
	# virtualenv
	rm -fR bin/ lib/ local/ share/

install-libs:
	pip3 install -r requirements.txt

update-requirements:
	pip3 freeze >requirements.txt

test:
	PYTHONPATH=$(PWD)/nordpool_db/ python3 test/test.py
