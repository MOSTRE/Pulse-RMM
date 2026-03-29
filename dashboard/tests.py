from django.test import SimpleTestCase


class DashboardTests(SimpleTestCase):
    def test_home(self):
        self.assertEqual(self.client.get("/").status_code, 200)
