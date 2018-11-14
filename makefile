all: clean find

find:
	python3 getfailures.py | tee all-found-issues
	csplit --suppress-matched -z -f found-issue- all-found-issues "/^---/" "{*}"

file:
	for ISSUE in $$(ls -1 found-issue*); do echo $$ISSUE ; grep -q filed-as $$ISSUE && grep filed-as $$ISSUE || echo hub issue create -F $$(realpath $$ISSUE) ; done

clean:
	-rm -v *found-issue*
