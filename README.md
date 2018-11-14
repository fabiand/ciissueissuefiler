[![Build Status](https://travis-ci.com/fabiand/ciissueissuefiler.svg?branch=master)](https://travis-ci.com/fabiand/ciissueissuefiler)

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
```

Finding what to file:
```
$ make file
for ISSUE in $(ls -1 found-issue*); do echo $ISSUE ; grep -q filed-as $ISSUE && grep filed-as $ISSUE || echo hub issue create -F $ISSUE ; done
found-issue-00
filed-as: ['https://api.github.com/repos/kubevirt/kubevirt/issues/1703']
found-issue-01
hub issue create -F found-issue-01
found-issue-02
filed-as: ['https://api.github.com/repos/kubevirt/kubevirt/issues/1689']
found-issue-03
filed-as: ['https://api.github.com/repos/kubevirt/kubevirt/issues/1701']
```

This fails. You need to do this from the kubevirt repository.

Filing:
```
$ cd <to-your.kubevirt-checkout>
$ export GITHUB_TOKEN=<your-token>  # Or not, then you can login with username/password
$ hub issue create -F /home/fabiand/kubevirt/ciissueissuefiler/found-issue-01
https://github.com/kubevirt/kubevirt/issues/1708
```
