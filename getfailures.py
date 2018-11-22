#!/usr/bin/python3

from lxml import etree
import requests
from pprint import pprint
from multiprocessing.dummy import Pool
import json
import os
import datetime

failures = {}

num_evaled = 8
top_count = 8

def log(msg):
    print ("# %s" % msg)

GITHUB_TOKEN=os.environ.get("GITHUB_TOKEN", "")
GITHUB_USER=os.environ.get("GITHUB_USER", "")
if GITHUB_TOKEN and GITHUB_USER:
    log("Using github auth")
    auth=(GITHUB_USER, GITHUB_TOKEN)
else:
    auth=None

def recentJobsALL(n):
    URL="https://jenkins.ovirt.org/job/kubevirt_kubevirt_standard-check-pr/api/xml"
    xml = requests.get(URL, auth=auth).text
    tree = etree.fromstring(xml)
    fragments = tree.xpath("//number")
    return sorted([f.text for f in fragments[0:n]])

def recentJobsMERGED(n, ref="master"):
    log("Checking most recent {n} jobs on ref {ref}".format(n=n, ref=ref))

    RECENT_PR_MERGED_URL="https://api.github.com/repos/kubevirt/kubevirt/pulls?state=closed&base={ref}&sort=updated&direction=desc".format(ref=ref)

    statuses_urls = []
    for PR in requests.get(RECENT_PR_MERGED_URL, auth=auth).json():
      statuses_urls.append(PR["statuses_url"])

    jobids = []
    for statuses_url in statuses_urls:
        log ("  Getting status on %s" % statuses_url)
        status_list = requests.get(statuses_url, auth=auth).json()
        for status in status_list:
            if status["state"] != "pending" and status["context"] == "standard-ci":
                jobids.append(status["target_url"].split("/")[-2])
        #jobid=list(filter(lambda v: v["state"] != "pending" and v["context"] == "standard-ci", obj))[0]["target_url"].split("/")[-2]
        if len(jobids) >= n:
            break
    log("  Found jobs: %s" % jobids)

    return jobids

recentJobs = recentJobsMERGED

def failuresOfJob(jobid):
    URL="https://jenkins.ovirt.org/job/kubevirt_kubevirt_standard-check-pr/%s/testReport/api/xml" % jobid
    
    try:
      xml = requests.get(URL).text
      tree = etree.fromstring(xml)
    except Exception as e:
      log("Failed to parse job %s. It was probably aborted" % jobid)
      return [(None, URL, "N/A")]
    
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
    failed_job_urls = "\n".join(["- https://jenkins.ovirt.org/job/kubevirt_kubevirt_standard-check-pr/{job}/testReport/ [Console output](https://jenkins.ovirt.org/job/kubevirt_kubevirt_standard-check-pr/{job}/consoleText)".format(job=j) for j in jobids])
    issues = findExistingIssues(name)
    closedissues = findExistingClosedIssues(name)
    if issues:
        cond_filed_as = "filed-as: %s" % issues
    elif closedissues:
        cond_filed_as = "filed-as-closed: %s" % closedissues
    else:
        cond_filed_as = ""

    return """{cond_filed_as}
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
""".format(name=name, stdout=stdout, trace=trace, num_failures=num_failures, failed_job_urls=failed_job_urls, top_count=top_count, num_evaled=num_evaled, cond_filed_as=cond_filed_as)

def findExistingIssues(name):
    URL="https://api.github.com/search/issues"
    params = {"q": "user:kubevirt repo:kubevirt in:title is:open '%s'" % name}
    resp = requests.get(URL, auth=auth, params=params)
    openissues = [(i["url"], i["assignee"]["login"] if i["assignee"] is not None else None) for i in resp.json()["items"]]
    return openissues

def findExistingClosedIssues(name):
    URL="https://api.github.com/search/issues"
    last_week = (datetime.date.today() - datetime.timedelta(7))
    params = {"q": "user:kubevirt repo:kubevirt in:title closed:>%s '%s'" % (last_week, name)}
    resp = requests.get(URL, auth=auth, params=params)
    closedissues = [(i["url"], i["assignee"]["login"] if i["assignee"] is not None else None) for i in resp.json()["items"]]
    return closedissues

if __name__ == "__main__":
    jobids = list(recentJobs(num_evaled))
    list(Pool(8).map(lambda i: appendFailures(i), jobids))
    sortedFailures = list(reversed(sorted(failures.items(), key=lambda item: len(item[1]))))
    topFailures = sortedFailures[0:top_count]
    print("---\n".join(createIssue(failure, jobids, top_count, num_evaled)
                       for (failure, jobids) in topFailures))
