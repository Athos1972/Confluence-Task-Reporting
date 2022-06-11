# Confluence-Task-Reporting
Reporting for Tasks (overdue, due soon, etc.) from a confluence on prem server

Confluence built-in task viewer is great for a single person. Once you have 1000s of Users working in 100s of spaces it 
becomes tedious to keep track of overdue tasks or low-quality tasks.

This little script is here to help. Most probably there exist paid plugins/add-ons for Confluence out there, but usually
they come at some steep license costs. On the other hand they are natively integrated into Confluence and would provide
much faster and more acurate results - so if you can spend the bucks for such plugins: Go ahead. 

Also on the other hand: When people anyway don't deal with their tasks then why would you need
real-time reporting on overdue tasks?

## Important notice
This tool will access only the information that the user stated in the <code>.env</code>-File is authorized to view!
If this user doesn't have rights to call Confluence-APIs the result will be 0 entries.

From the various API-Calls we'll always only receive pages that the user would anyway be allowed to see. So this tool 
does not help (nor support) doing things that you couldn't do manually anyways

## How does it work?
Powered by a little local database we scan the users of the Confluence instance. Then we scan all their open tasks.
Having gathered all the needed information we can create beautiful, customized reports. Those reports can be sent via
E-Mail as PDF or stored in a Confluence-Page.

Another option to consume the results is via a nice little dashboard. 

# How to start?
## Check prerequisits
* Python > 3.6 on your computer. To check: <code>python -V</code>

## Install
* Hopefully you're comfortable with using the console or command prompt. Otherwise you won't make it. Sorry.
* Get the repository <code>git clone https://github.com/Athos1972/Confluence-Task-Reporting </code>  
* Create a file named exactly <code>.env</code> in the root of the downloaded repository.
* Enter <code>CONF_USER=<your_user_name></code>, <CONF_PWD=<your_password_for_confluence> into the file
* Enter <code>CONF_BASE_URL="https://<path_to_your_confluence_instance>"</code> into the <code>.env</code> file
* Create a virtual environment (e.g. <code>virutalenv venv</code>)
  * then activate it by typing <code>venv/bin/activate</code> on Linux/Mac or <code>/venv/scripts/activate</code> 
    on Windows
  * Install the needed dependencies: <code>pip install -r requirements.txt</code>  
  
## First steps
* Start <code>python user_crawler.py</code>. This will do quite some stuff. It will initialize the database, connect to
your Confluence instance and read all users (that your User is authorized to read). It may take some time depending on 
the size of your installation.
* Start <code>python user_task_crawler.py</code>. This will run even longer. For all the users that were loaded in the
previous step we'll search for their tasks. We'll also scan the pages, that those tasks are included and will derive
due-date of the tasks as well as the space name.
  * <b>TIPP</b>: For permanent crawling it might be good if you set command line parameter OUWT (Only Users With Tasks)
  by calling <code>python user_task_crawler.py -OUWT=1</code>. This will - you guessed it - just crawl for users who
  anyway had already some tasks.
  * <b>TIPP</b>: If you don't want to consume too much bandwidth you might consider setting 
    <code>sleep_between_crawl_tasks</code> in <code>config.toml</code> to a value around 2-5 seconds. This would also  
    seem less suspicious for people analyzing network traffic.
* Start the dashboard: <code>python dashboard.py</code>. Navigate to URL http://127.0.0.1:8050/ and see the results

## Additional crawlers
* <code>tasks_recrawl_by_page.py</code> recrawls tasks from previously crawled pages.
* <code>task_recrawl_by_duedate.py</code> goes through all tasks in the database sorted by last crawl date and.
analyses those tasks again.
## Reports
* Average overdue age distribution (graph)

## Distribution
* Via E-Mail as PDF
* Write result als Confluence page


