all: clean find

find:
	python3 getfailures.py | tee all-found-issues
	sed -i "/^# / d" all-found-issues
	csplit -z -f found-issue- all-found-issues "/^---/" "{*}"
	sed -i "/^---/ d" found-issue-*

find-unfiled:
	@for ISSUE in $$(ls -1 found-issue*); do grep -q filed-as $$ISSUE && true || echo $$ISSUE ; done

file:
	make find-unfiled | xargs -P 1 echo hub issue create -F

clean:
	-rm -v *found-issue*
