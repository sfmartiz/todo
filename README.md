# To-do assistant
A lightweight app for keeping track of periodical repeating tasks, always sorted by order of deadline. Available periods to use are:
- Every day at fixed hour and minute
- Every week at fixed day, hour and minute
- Every week at specific days of week (e.g Monday and Tuesday) and fixed hour and minute
- Every month at fixed day, hour and minute
- Custom period
- Non-repeatable task with a fixed deadline

### Requirements
- SQLAlchemy
- Python 3.10 - Due to implementation of the ```match case``` syntax