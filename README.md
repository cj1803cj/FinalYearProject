# FinalYearProject
Submission for my FYP, a website that recommends similar projects and users

### Installation
Create a new conda environment using the instructions given in the requirements.txt file.
This will create an environment with the dependencies installed in order for the application to run.

### Usage
Open a command prompt inside the root directory of the project and run the following:

$ export FLASK_APP=recommendev.py ($ set FLASK_APP=recommendev.py on Windows)  
$ flask run

### Email Server
If you would like to test email functionality (testing, reset password requests) then you will need to run an email server:

In window 1:  
$ python -m smtpd -n -c DebuggingServer localhost:8025  

In window 2:
$ export FLASK_APP=recommendev.py  
$ export FLASK_DEBUG=1  
$ export MAIL_SERVER=localhost  
$ export MAIL_PORT=8025  
$ flask run  

Again, make sure to use set instead of export on Windows.