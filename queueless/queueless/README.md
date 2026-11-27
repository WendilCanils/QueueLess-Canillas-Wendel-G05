# QueueLess

Digital queue management system for school offices. Students get digital queue tickets, and office staff call and process them. Built with Django and Supabase PostgreSQL.

## Roles
- **Student**: browse offices, take a ticket, track position, edit, cancel or delete tickets.
- **Office Staff**: call the next student, complete or mark no-show, manage services, view records.

## Setup
1. Clone the repo and create a virtual environment.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set your Supabase `DATABASE_URL`.
4. `python manage.py migrate`
5. `python manage.py createsuperuser`
6. `python manage.py runserver`

## Test data
In `/admin/`, create an Office and Services, then set a user's Profile role to Office Staff and assign the office.

## Branching
`main` (stable) <- `develop` <- `feature/*` via pull requests.