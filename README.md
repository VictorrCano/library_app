# Library App

This is my Project 1: Books for the course Web Programming with Python and JavaScript.

application.py is where the flask app is written

index.html is the welcome page, allows you to navigate to register or login page depending on new or returning user

login.html page prompts you to enter username and password to existing books account, takes user to search page

register.html allows new user to create new account, takes new user to submit page once completed

submit.html page welcomes new user, allows user to navigate to login page and begin session

search.html prompts user to search for book using Title, Author name, or ISBN, then redirects to books page

books.html loops through all books matching entry from search page, displaying Title, Author, and ISBN, allows user to navigate to binfo page of each book

binfo.html is book info page which contains additional details about specific books including average rating, and the option for users to submit their own review

searching /api/(isbn) route will return json file with info of book with matching isbn code 

https://www.youtube.com/watch?v=iqOleiXwvqA&feature=youtu.be





