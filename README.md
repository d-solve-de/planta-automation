# Simple Automation App

This simple python script automates the use of planta.
This allows the user to focus on his actual work and waste less time with organisational overhead.
The app provides a full man page that describes its behaviour and is directly usable via terminal.
The app has no UI to automate the use of planta in the most efficient way.

# How to use it



- TODO: add input validation (excessive one)
add a test of all inputs if they are in range
especially the exclude values
the weekdays 
if the delays are between 0 and 100
if the default reference file is of type csv
if the strategy is one of the allowed values
- TODO: all selectors of planta should be defined in an extra file so they can be changed easily and are not hard coded in the code
- TODO: add another strategy where a post processing is applied to the values that adds random noise to the values so it is not seen directly that they were entered via a program
- TODO: delete doc in python file
- TODO: make man page in extra file and with native tool
- TODO: add the functionality that the defaul_reference is changed depending on the actual number of rows - create file if not existant
- TODO: add functionality to specify week of use
- TODO: add functionality to apply many filter like - fill week with standard way, then wednesday with other functionality but in a simple to use way via terminal
- TODO: add doc here
- TODO: rewrite README
- TODO: publish project online

# User stories

## Daily Flow
The user opens the app, the app goes to planta and loads the standard setup of a user. If the user loads the app the first time default values are applied automatically.
If the user just hits ENTER the standard setup is applied and planta is filled according to the stored strategies or Defaults
If the user changes the configuration, the new configuration is applied to the filling of planta

The user can choose the following parameters:
- override vs. fill blanks only (drop down) (default = fill blanks only)
- the user can define cells to be excluded by the filling (define in an extra array showing the columns) (default= none) --> TODO: add this functionality
- the user can choose a fill strategy (uniform, random, like_latest_day, like_reference_day) (default = like_latest_day)
- the user can define on which time range the strategy should apply (today, this week, until column is completely filled) (drop down) (default = today) TODO: implement this functionality

The user can store different reference_days that are automatically shown in an additional drop down menu if copy_reference is used.
For reference days, all rows have to have a value defined to be filled. While filling the cells the copy_reference strategy automatically scales the values so the values sum up to total_hours worked on that day.

There are pre-defined days already hard coded by the program. For example PI Planning weeks or workshop days or educational days. 
Reference days should be able to be edited, added or deleted.

If the number of rows or their name changes over time, the reference days do not fit anymore. Therefore the program always loads the newest version of the website and when reference_days is chosen as strategy it has to be tested if everything worked.

After a strategy was applied a message is shown to the user showing which days where changed in which way.

The url to planta should be configurable as well.  (current = ...)
The precision should be configurable (default = 2 decimals after comma)
The variance for the random strategy should be configurable. (default = 0.7)
The number of retries in the random strategy as well (default =5)