from app import init_app


app = init_app()

if __name__ == "__main__":
    # follows standard design pattern from https://hackersandslackers.com/flask-application-factory/.
    app.run(host="127.0.0.1")
