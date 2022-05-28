# Confluence-Task-Reporting
Reporting for Tasks (overdue, due soon, etc.) from a confluence on prem server

Confluence built-in task viewer is great for a single person. Once you have 1000s of Users working in 100s of spaces it 
becomes tedious to keep track of overdue tasks.

This little script is here to help. Most probably there exist paid plugins/add-ons for Confluence out there, but usually
they come at some steep license costs. On the other hand they are natively integrated into Confluence and would provide
much faster results. Also on the other hand: When people anyway don't deal with their tasks then why would you need
real-time reporting on overdue tasks?

## Important notice
This tool will access only the information that the user stated in the <code>.env</code>-File is authorized to view!
If this user doesn't have rights to call Confluence-APIs the result will be 0 entries.

## How we do it
Powered by a little local database we scan the users of the Confluence instance. Then we scan all their open tasks.
Having gathered all the needed information we can create beautiful, customized reports. Those reports can be sent via
E-Mail as PDF or stored in a Confluence-Page.

## Crawler
* <code>user_crawler.py</code> reads users from Confluence-Instance
* <code>user_task_crawler.py</code> reads tasks for Users

## Reports
* Average overdue age distribution (graph)

## Distribution
* Via E-Mail as PDF
* Write result als Confluence page
