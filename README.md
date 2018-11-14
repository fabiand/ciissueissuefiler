# Goal

Automatically discover often reoccurring failing testcases in our Ci and automatically file them if they are not already filed.

# Usage

Finding:
```
$ make
rm -v *found-issue*
'all-found-issues' wurde entfernt
python3 getfailures.py > all-found-issues
csplit -z -f found-issue- all-found-issues "/^---/" "{*}"
3152
3087
1629
1734
$ export GITHUB_TOKEN=<your-token>
```

Filing:
```
$ make file
for ISSUE in $(ls -1 found-issue*); do grep -q filed-as $ISSUE && ( echo -n "$ISSUE " ; grep filed-as $ISSUE ) || hub issue create -F $ISSUE ; done
found-issue-00 filed-as: ['https://api.github.com/repos/kubevirt/kubevirt/issues/1703']
Aborted: the origin remote doesn't point to a GitHub repository.
found-issue-02 filed-as: ['https://api.github.com/repos/kubevirt/kubevirt/issues/1689']
found-issue-03 filed-as: ['https://api.github.com/repos/kubevirt/kubevirt/issues/1701']

```

This fails. You need to do this from the kubevirt repository.
