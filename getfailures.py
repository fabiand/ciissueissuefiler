#!/usr/bin/python3

from lxml import etree
import requests
from pprint import pprint
from multiprocessing.dummy import Pool

failures = {}

num_evaled = 42
top_count = 2

def recentJobs(n):
    URL="https://jenkins.ovirt.org/job/kubevirt_kubevirt_standard-check-pr/api/xml"
    xml = requests.get(URL).text
    tree = etree.fromstring(xml)
    fragments = tree.xpath("//number")
    return sorted([f.text for f in fragments[0:n]])

def failuresOfJob(jobid):
    URL="https://jenkins.ovirt.org/job/kubevirt_kubevirt_standard-check-pr/%s/testReport/api/xml" % jobid
    
    xml = requests.get(URL).text
    
    tree = etree.fromstring(xml)
    
    fragments = tree.xpath("//case[status='FAILED' or status='REGRESSION']")
    
    return [(f.find("name").text,
            (f.find("stdout").text if f.find("stdout") is not None else "N/A"),
            f.find("errorStackTrace").text) for f in fragments]

def appendFailures(jobid):
    for (name, stdout, trace) in failuresOfJob(jobid):
       if name is not None:
            failures.setdefault((name, stdout, trace), []).append(jobid)

def createIssue(namedetails, jobids, top_count, num_evaled):
    name, stdout, trace = namedetails
    num_failures = len(jobids)
    failed_job_urls = "\n".join(["- https://jenkins.ovirt.org/job/kubevirt_kubevirt_standard-check-pr/%s/testReport/" % j for j in jobids])

    return """
"{name}" failed {num_failures} times

/kind bug

What happened:
This test failed {num_failures} times in the most recent {num_evaled} jobs with:

STDOUT:
```
{stdout}
```

TRACE:
```
{trace}
```

What you expected to happen:
Test passes

How to reproduce it (as minimally and precisely as possible):
Take a look at the failures in:
{failed_job_urls}

Anything else we need to know?:
This was automatically filed, because it was one of the TOP {top_count} failing tests.
""".format(name=name, stdout=stdout, trace=trace, num_failures=num_failures, failed_job_urls=failed_job_urls, top_count=top_count, num_evaled=num_evaled)

def isAlreadyAnIssue(name):
    URL="https://api.github.com/search/issues"
    data = {"q": "repo=kubevirt/kubevirt in:title is:open '%s'" % name}
    return (requests.get(URL, data).json()["total_count"] > 0)

if __name__ == "__main__":
    jobids = list(recentJobs(num_evaled))
    list(Pool(16).map(lambda i: appendFailures(i), jobids))
    sortedFailures = list(reversed(sorted(failures.items(), key=lambda item: len(item[1]))))
    topFailures = sortedFailures[0:top_count]
    print("---\n".join(createIssue(failure, jobids, top_count, num_evaled)
                       for (failure, jobids) in topFailures
                       if not isAlreadyAnIssue(failure[0])))
