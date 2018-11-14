all: clean find

find:
	python3 getfailures.py > all-found-issues
	csplit -z -f found-issue- all-found-issues "/^---/" "{*}"

file:
	for ISSUE in $$(ls -1 found-issue*); do grep -q filed-as $$ISSUE && ( echo -n "$$ISSUE " ; grep filed-as $$ISSUE ) || hub issue create -F $$ISSUE ; done

clean:
	-rm -v *found-issue*
