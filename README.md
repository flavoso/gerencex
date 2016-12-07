# gerencex
Python/Django small project to manage hours bank and productivity of public employees. It's really small and fitted just to solve a problem of mine, as a manager who struggles to keep controlling the hours bank of my team members at a brazilian public agency.

The intention is to control the hours bank in an automatic way. Each worker will click at a button to register the check in and check out at work. At the initial page, the workers will get informed about the credit or debit of hours they have, as well as the balance of their co-workers.

The manager can setup parameters like:

* the maximum amount of work hours per day;
* the maximum amount of extra hours of work per day;
* the minimum check in and maximum check out time;
* the maximum monthly hours balance;
* tolerance time for check in and check out.

It's also possible to register the workers absences, like vacations, jobs out, etc.

I'm working on the hours bank app for now. Afterwards, the productivity app will be developed.

## Setting up

The python-decouple and dj-database-url packages are used, so that the same code may be  used for development and production.

In the production host, create a '.env' file at project's root, with the following lines:

DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
ALLOWED_HOSTS=your-allowed-hosts
COMPANY_SITE=the-url-of-your-company-site

DATABASE_URL is an url like this:

mysql://myuser:mypassword@myhost/mydatabase$myoptions

The COMPANY_SITE parameter is used to check if the workers are checking in and out at work. Otherwise, they could make fake check ins.

For development, you can add a DEVELOPER_HOSTNAME parameter to .env. This way, the system will accept check ins and checkouts made from your workstation.

## Requirements

The requirements.txt lists the packages gunicorn and psycopg2, which are used for heroku deployment. If you are not going to deploy at heroku, you can safely remove both packages.
