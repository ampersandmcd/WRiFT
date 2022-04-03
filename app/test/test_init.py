import unittest
from application import init_app


class InitTests(unittest.TestCase):

    def test_init(self):
        """
        Ensure app initializes and homepage loads correctly.
        Referenced https://flask.palletsprojects.com/en/2.0.x/testing/
        Referenced https://testdriven.io/blog/flask-pytest/
        Referenced https://martinfowler.com/bliki/GivenWhenThen.html

        GIVEN a Flask application configured for testing
        WHEN the '/' page is requested (GET)
        THEN check that the response is valid
        """
        flask_app = init_app()

        # create a test client using the Flask application configured for testing
        # follow standard syntax of (expected, actual)
        # https://stackoverflow.com/questions/2404978/why-are-assertequals-parameters-in-the-order-expected-actual
        with flask_app.test_client() as test_client:
            response = test_client.get('/')
            self.assertEqual(200, response.status_code)
            self.assertIn(b'<html', response.data)
            self.assertIn(b'</html>', response.data)
