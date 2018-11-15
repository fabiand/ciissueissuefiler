all: clean find

find:
	python3 getfailures.py | tee all-found-issues
	csplit -z -f found-issue- all-found-issues "/^---/" "{*}"
	sed -i "/^---/ d" found-issue-*

file:
	for ISSUE in $$(ls -1 found-issue*); do echo $$ISSUE ; grep -q filed-as $$ISSUE && grep filed-as $$ISSUE || echo hub issue create -F $$PWD/$$ISSUE ; done

clean:
	-rm -v *found-issue*
