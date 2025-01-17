from flask import Flask, render_template, request, jsonify
import sqlite3
import random

app = Flask(__name__)

#This my SQLite database, containing two tables directly relevant for my coursework. One that hosts data about films, which uploaded to DB Browser as a CSV and formatted to comply with my requirements. The other contains my user information for single user authentication.
DATABASE = 'HHActualTest.db'

# This is a function that I will use for the authentication of account. Website only requires single admin access in this form, as I am the only one who will be submitting and deleting films from the records. Takes 'username' and 'password' as the inputs.
def check_credentials(username, password):
    # Connection to database
    with sqlite3.connect(DATABASE) as conn:
        # Cursor to look through database and execute SQL queries
        cur = conn.cursor()
        # SQL execution to select password from my user table, where based on whether the inputted username exists in the table. Parameterised because for security purposes
        cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        # Looks at/fetches first row of data from the SQL query.
        user = cur.fetchone()
        # Check if username was found and whether password in the database matches the one that I inputted. If these conditions are met then outcome is 'true'. This will be used when trying to access my admin page. 
        return user and user[0] == password

# App route for the admin page. This route involves getting data from the database and sending data.
@app.route('/admin', methods=['GET', 'POST'])
# Function to make the page do things
def admin():
    # Variables initialised for later in the function
    error = None
    result_message = ""
    films = []

    # Checks if user is trying to access app route/page without having submitted something, i.e. having clicked on it from the navbar. This renders a login page.
    if request.method == 'GET':
        return render_template('login.html', error=error)

    # Checks whether the user has submitted a form. There are two forms that would be responsible for this
    if request.method == 'POST':
        # This checks if the user is trying to access the page because they clicked the log-in button on the log-in page.
        if 'login_button' in request.form:
            # This declares the username and password from the login page form as username and password variables
            username = request.form.get('username')
            password = request.form.get('password')
            # This requires that the username and password were not empty in the login form and that they match the records in the user database (just one entry). If those conditions are met, it moves onto the next part.
            if username and password and check_credentials(username, password):
                # Assigns the result of the fetch_films function (i.e. the full film list) and renders the admin page as it is intended in the HTML code. 
                films = fetch_films()
                return render_template('admin.html', result_message=result_message, films=films)
            # If the login details were wrong, then the login page is rendered again with an error message
            else:
                error = 'Incorrect Login Details'
                return render_template('login.html', error=error)
        #  Checks if the user has submitted a film submission form, i.e. is trying to re-enter the page after inputting a film from the admin area. If so, it takes the contents of the form and declares them as variables which can be passed through function that inserts films below.
        elif 'film_submit_button' in request.form:
            name = request.form.get('name')
            year = request.form.get('year')
            runtime = request.form.get('runtime')
            genre = request.form.get('genre')
            language = request.form.get('language')
            imdb_score = request.form.get('imdb_score')
            comment = request.form.get('comment')
            imdb_link = request.form.get('imdb_link')
        # If the form for inputting a name of a film was satisfied then the function that inserts films is executed, which takes the contents of the form as its inputs
            if name:
                result_message = insert_film(name, year, runtime, genre, language, imdb_score, comment, imdb_link)
                films = fetch_films()
    # Providing that the required conditions have been met, it renders the admin page
    return render_template('admin.html',result_message=result_message,films=films)

@app.route('/random_film')
def random_film():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM hhdata")
    films = cur.fetchall()
    if films:
        film = random.choice(films)
        film_data = {
            "title": film[1],
            "year": film[2],
            "runtime": film[3],
            "genre": film[4],
            "language": film[5],
            "imdb_score": film[6],
            "comment": film[7],
            "imdb_link": film[8]
        }
    else:
        film_data = None
    conn.close()
    return jsonify(film_data)

# Function that is called when a new film is being inserted by the admin from the admin page. It takes form criteria about a film from the admin page as its inputs.
def insert_film(name, year, runtime, genre, language, imdb_score, comment):
    # Try used in case of exceptions, with "except" code occuring if error occurs
    try:
        # Connects to database
        conn = sqlite3.connect(DATABASE)
        # Cursor to look through database and execute SQL queries
        cur = conn.cursor()
        # First prepares the SQL query using a parameterised query. I split it up because it became very complex and hard to read when the cur execution occured with the query written out in the same line.
        query = "INSERT INTO hhdata (Name, Year, Runtime, Genre, Language, IMDBScore, Comment) VALUES (?, ?, ?, ?, ?, ?, ?)"
        # SQL exection that inserts the form data into the database table in the relevant columns
        cur.execute(query, (name, year, runtime, genre, language, imdb_score, comment))
        # This insertion is committed to the database
        conn.commit()
        # Success message! showing that the film insertion was successfull
        msg = "Film added successfully!"
    # If a mistake was made along the way for this film insertion function...
    except:
        # This prevents anything from being added to the database and takes it back to a state before the function was called
        conn.rollback()
        msg = "Error while inserting a film!"
    finally:
        # Database connection closed
        conn.close()
        # Either the message for the successful film addition or for the error is shown
        return msg

# Function for retrieving films from the database, with opportunity to create custom parameter queries to the database using the filter form, as well as also fetching the full film list.
def fetch_films(decade=None, genre=None, runtime=None, language=None, imdb_score=None):
    try:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        query = "SELECT * FROM hhdata WHERE 1=1"
        film_parameters = []

        if decade and decade != 'any':
            start_year = int(decade[:-1])
            end_year = start_year + 9
            query += " AND Year >= ? AND Year <= ?"
            film_parameters.extend([start_year, end_year])

        if runtime == "under_90":
            query += " AND Runtime < 90"
        elif runtime == "90_to_101":
            query += " AND Runtime BETWEEN 90 AND 101"

        if genre and genre != 'any' and genre.strip():
            query += " AND Genre LIKE ?"
            film_parameters.append(f"%{genre.strip()}%")

        if language and language != 'any' and language.strip():
            query += " AND Language LIKE ?"
            film_parameters.append(f"%{language.strip()}%")

        if imdb_score and imdb_score != 'any':
            query += " AND IMDBScore >= ?"
            film_parameters.append(float(imdb_score))

        cur.execute(query, tuple(film_parameters))
        films = cur.fetchall()
    except Exception as e:
        films = []
        print(f"Error during your search: {str(e)}")
    finally:
        conn.close()
        return films




# App route for deleting a film, after clicking on a delete film button in the database
@app.route('/delete_film', methods=['POST'])
# Function for deleting a film
def delete_film():
    # Declares variable that represents the ID for the film that I want to delete
    film_id = request.form.get('film_id')
# Try used in case of exceptions, with "except" code occuring if error occurs
    try:
        # Connects to database
        with sqlite3.connect(DATABASE) as conn:
        # Cursor to look through database and execute SQL queries
            cur = conn.cursor()
        # SQL query to delete a film from the database based on the ID
        query = "DELETE FROM hhdata WHERE ID = ?"
        # Query is executed where the film ID replaces the ?
        cur.execute(query, (film_id,))

        # Execution is actioned to the database
        conn.commit()
    # Way to handle exceptions where there was an issue with the deletion, where it prints the error to the console and does not display any films
    except Exception as e:
        conn.rollback()
        print(f"Error deleting film: {str(e)}")
    finally:
        # Close database connection
        conn.close()
        # Renders the deleted_film page with confirmation
        return render_template('deleted_film.html')

# Index route that renders the index homepage
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

# App route for displaying the list of films https://www.digitalocean.com/community/tutorials/processing-incoming-request-data-in-flask
@app.route('/film_list')
# Function for displaying films. It uses requests.args.get to retrieve the query parameters from the URL/form filter request and declares them as variables that can be used to then fetch the films
def film_list():
    decade = request.args.get('decade', 'any')
    genre = request.args.get('genre', 'any')
    runtime = request.args.get('runtime', 'any')
    language = request.args.get('language', 'any')
    imdb_score = request.args.get('imdb_score', 'any')

# Fetch_films function called, to then retrieve the films that meet the criteria from the database.
    films = fetch_films(decade=decade,genre=genre, runtime=runtime,language=language,imdb_score=imdb_score)

# Film list template is rendered with the films on the page
    return render_template('film_list.html', films=films, decade=decade,genre=genre, runtime=runtime,language=language,imdb_score=imdb_score)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
