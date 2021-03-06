from django.test import TestCase, Client
from django.urls import reverse
from django.test.utils import setup_test_environment

from bs4 import BeautifulSoup
import re
import time

from website.models import *
from website.forms import *

client = Client()

# length of base template, used to test for empty pages
LEN_BASE = 2600


class BaseWebsiteLoadTestCase(TestCase):
    def setUp(self):
        super()

    def test_homepage_load(self):
        url = reverse("website:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), LEN_BASE)

    def test_project_list_load(self):
        url = reverse("website:projects_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), LEN_BASE)

    def test_project_students_load(self):
        url = reverse("website:students")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), LEN_BASE)

    def test_project_educators_load(self):
        url = reverse("website:educators")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), LEN_BASE)

    def test_project_leaders_load(self):
        url = reverse("website:leaders")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), LEN_BASE)


VERBOSE = False


class TraverseLinksTest(TestCase):

    def setUp(self):
        # By default, login as superuser
        um = OpenSUTDUserManager()
        um.create_user("tom", display_name="Tom Magnanti",
                       display_picture="https://via.placeholder.com/150",
                       graduation_year=2018, pillar="ISTD",
                       password="tompassword")

        self.client = Client()
        self.superuser = User.objects.get(username="tom")
        self.client.login(username="tom", password="tompassword")

    @classmethod
    def setUpTestData(cls):
        pm = OpenSUTDProjectManager()
        um = OpenSUTDUserManager()

        pm.create_project(project_uid="ACAD_00001",
                          title="OpenSUTD Web Platform",
                          caption="Sample project 1",
                          category="ACAD",
                          url="https://github.com/OpenSUTD/web-platform-prototype",
                          poster_url="https://via.placeholder.com/150",
                          featured_image="https://via.placeholder.com/150")

        um.create_user("dick", display_name="Dick Tan",
                       display_picture="https://via.placeholder.com/150",
                       graduation_year=2019, pillar="ISTD")

        um.create_user("jane", display_name="Jane Tan",
                       display_picture="https://via.placeholder.com/150",
                       graduation_year=2021, pillar="ESD")

        pm.create_project(project_uid="ACAD_00002",
                          title="RandomZZZZZ",
                          caption="Sample project 2",
                          category="ACAD",
                          url="https://github.com/OpenSUTD/web-platform-prototype",
                          poster_url="https://via.placeholder.com/150",
                          featured_image="https://via.placeholder.com/150")

        pm.set_project_status("ACAD_00001", "DISPLAY")
        pm.add_user_to_project("ACAD_00001", "dick")
        pm.add_user_to_project("ACAD_00001", "jane")
        pm.add_tag_to_project(
            "ACAD_00001", "rand1,rand2,education,student,policy")

        pm.add_user_to_project("ACAD_00002", "jane")
        pm.add_tag_to_project(
            "ACAD_00002", "rand1,rand2,education,student,policy")

    def test_traverse_urls(self):
        # Fill these lists as needed with your site specific URLs to check and to avoid
        to_traverse_list = ["/", "/projects/",
                            "/students/", "/educators/", "/leaders/"]
        to_avoid_list = ["javascript:history\.back()", "https://*",
                         "javascript:history\.go\(-1\)", "^mailto:.*"]

        done_list = []
        error_list = []
        source_of_link = dict()
        for link in to_traverse_list:
            source_of_link[link] = "initial"

        (to_traverse_list, to_avoid_list, done_list, error_list, source_of_link) = \
            self.recurse_into_path(
                to_traverse_list, to_avoid_list, done_list, error_list, source_of_link)

        print("END REACHED\nStats:")
        if VERBOSE:
            print("\nto_traverse_list = " + str(to_traverse_list))
        if VERBOSE:
            print("\nto_avoid_list = " + str(to_avoid_list))
        if VERBOSE:
            print("\nsource_of_link = " + str(source_of_link))
        if VERBOSE:
            print("\ndone_list = " + str(done_list))
        print("Followed " + str(len(done_list)) + " links successfully")
        print("Avoided " + str(len(to_avoid_list)) + " links")

        if error_list:
            print("!! " + str(len(error_list)) + " error(s) : ")
            for error in error_list:
                print(str(error) + " found in page " +
                      source_of_link[error[0]])

            print("Errors found traversing links")
            assert False
        else:
            print("No errors")

    def recurse_into_path(self, to_traverse_list, to_avoid_list, done_list, error_list, source_of_link):
        """ Dives into first item of to_traverse_list
            Returns: (to_traverse_list, to_avoid_list, done_list, source_of_link)
        """

        if to_traverse_list:
            url = to_traverse_list.pop()

            if not match_any(url, to_avoid_list):
                print("\nSurfing to " + str(url) +
                      ", discovered in " + str(source_of_link[url]))
                response = self.client.get(url, follow=True)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")

                    text = soup.get_text()

                    for link in soup.find_all("a"):
                        new_link = link.get("href")
                        if VERBOSE:
                            print("  Found link: " + str(new_link))
                        if match_any(new_link, to_avoid_list):
                            if VERBOSE:
                                print("    Avoiding it")
                        elif new_link in done_list:
                            if VERBOSE:
                                print("    Already done, ignoring")
                        elif new_link in to_traverse_list:
                            if VERBOSE:
                                print("    Already in to traverse list, ignoring")
                        else:
                            if VERBOSE:
                                print(
                                    "    New, unknown link: Storing it to traverse later")
                            source_of_link[new_link] = url
                            to_traverse_list.append(new_link)

                    done_list.append(url)
                    if VERBOSE:
                        print("Done")
                else:
                    error_list.append((url, response.status_code))
                    to_avoid_list.append(url)

            if VERBOSE:
                print("Diving into next level")
            return self.recurse_into_path(to_traverse_list, to_avoid_list, done_list, error_list, source_of_link)

        else:
            # Nothing to traverse
            if VERBOSE:
                print("Returning to upper level")
            return to_traverse_list, to_avoid_list, done_list, error_list, source_of_link


def match_any(my_string, regexp_list):
    if my_string:
        combined = "(" + ")|(".join(regexp_list) + ")"
        return re.match(combined, my_string)
    else:
        # "None" as string always matches
        return True


class SecuredPageTestCase(TestCase):
    def setUp(self):
        pm = OpenSUTDProjectManager()
        pm.create_project(project_uid="ACAD_00001",
                          title="OpenSUTD Web Platform",
                          caption="Sample project 1",
                          category="ACAD",
                          url="https://github.com/OpenSUTD/web-platform-prototype",
                          poster_url="https://via.placeholder.com/150",
                          featured_image="https://via.placeholder.com/150")

        um = OpenSUTDUserManager()
        um.create_user("tom", display_name="Tom Magnanti",
                       display_picture="https://via.placeholder.com/150",
                       graduation_year=2018, pillar="ISTD")

    def test_auth_approval_view(self):
        url = reverse("website:approve_project", args=("ACAD_00001",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_auth_submit_view(self):
        url = reverse("website:submit_project")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_auth_submit_reject(self):
        url = reverse("website:hide_project", args=("ACAD_00001",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_auth_submit_approve(self):
        url = reverse("website:approve_project", args=("ACAD_00001",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_auth_user_edit(self):
        url = reverse("website:user_edit", args=("tom",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_auth_project_edit(self):
        url = reverse("website:project_edit", args=("ACAD_00001",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_auth_project_bypass(self):
        url = reverse("website:project_view_bypass", args=("ACAD_00001",))
        response = self.client.get(url)
        # actually a custom 404 page
        self.assertEqual(response.status_code, 302)

class LogintoSecuredPageTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        um = OpenSUTDUserManager()
        um.create_user("tom", display_name="Tom Magnanti",
                       display_picture="https://via.placeholder.com/150",
                       graduation_year=2018, pillar="ISTD",
                       password="tompassword")
        pm = OpenSUTDProjectManager()
        pm.create_project(project_uid="ACAD_00001",
                          title="OpenSUTD Web Platform",
                          caption="Sample project 1",
                          category="ACAD",
                          url="https://github.com/OpenSUTD/web-platform-prototype",
                          poster_url="https://via.placeholder.com/150",
                          featured_image="https://via.placeholder.com/150")

        self.client.login(username="tom", password="tompassword")

    def test_login_approval_view(self):
        response = self.client.get(reverse("website:projects_admin"))
        self.assertEqual(response.status_code, 200)

    def test_login_submission_view(self):
        response = self.client.get(reverse("website:submit_project"))
        self.assertEqual(response.status_code, 200)

    def test_login_user_edit(self):
        url = reverse("website:user_edit", args=("tom",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_login_project_edit(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        url = reverse("website:project_edit", args=("ACAD_00001",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class UserTestCase(TestCase):
    def setUp(self):
        um = OpenSUTDUserManager()
        um.create_user("tom", display_name="Tom Magnanti",
                       display_picture="https://via.placeholder.com/150",
                       graduation_year=2018, pillar="ISTD")

        um.create_user("jane", display_name="Jane Tan",
                       display_picture="https://via.placeholder.com/150",
                       graduation_year=2021, pillar="ESD")

    def test_user_get_name(self):
        tom = User.objects.get(username="tom")
        self.assertEqual(tom.display_name, "Tom Magnanti")

        jane = User.objects.get(username="jane")
        self.assertEqual(jane.display_name, "Jane Tan")

    def test_user_get_year(self):
        tom = User.objects.get(username="tom")
        self.assertEqual(tom.graduation_year, 2018)

        jane = User.objects.get(username="jane")
        self.assertEqual(jane.graduation_year, 2021)

    def test_user_get_pillar(self):
        tom = User.objects.get(username="tom")
        self.assertEqual(tom.pillar, "ISTD")

        jane = User.objects.get(username="jane")
        self.assertEqual(jane.pillar, "ESD")

    # test user profile page contents

    def test_user_page_load(self):
        url = reverse("website:user_profile", args=("tom",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse("website:user_profile", args=("jane",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse("website:user_profile", args=("tom",))
        response = self.client.get(url)
        self.assertGreater(len(response.content), LEN_BASE)

        url = reverse("website:user_profile", args=("jane",))
        response = self.client.get(url)
        self.assertGreater(len(response.content), LEN_BASE)

    def test_user_page_contents(self):
        url = reverse("website:user_profile", args=("tom",))
        response = str(self.client.get(url).content)
        self.assertEqual("Tom Magnanti" in response, True)

        url = reverse("website:user_profile", args=("jane",))
        response = str(self.client.get(url).content)
        self.assertEqual("Jane Tan" in response, True)

        url = reverse("website:user_profile", args=("tom",))
        response = str(self.client.get(url).content)
        self.assertEqual("2018" in response, True)

        url = reverse("website:user_profile", args=("jane",))
        response = str(self.client.get(url).content)
        self.assertEqual("2021" in response, True)

        url = reverse("website:user_profile", args=("tom",))
        response = str(self.client.get(url).content)
        self.assertEqual("ISTD" in response, True)

        url = reverse("website:user_profile", args=("jane",))
        response = str(self.client.get(url).content)
        self.assertEqual("ESD" in response, True)

class ProjectShowcaseTestCase(TestCase):
    def setUp(self):
        pm = OpenSUTDProjectManager()

        pm.create_project(project_uid="ACAD_00001",
                          title="OpenSUTD Web Platform",
                          caption="Sample project 1",
                          category="ACAD",
                          url="https://github.com/OpenSUTD/web-platform-prototype",
                          poster_url="https://via.placeholder.com/150",
                          featured_image="https://via.placeholder.com/150")

        um = OpenSUTDUserManager()

        um.create_user("tom", display_name="Tom Magnanti",
                       display_picture="https://via.placeholder.com/150",
                       graduation_year=2018, pillar="ISTD")

        um.create_user("jane", display_name="Jane Tan",
                       display_picture="https://via.placeholder.com/150",
                       graduation_year=2021, pillar="ESD")

    def test_project_properties(self):
        proj = Project.objects.get(project_uid="ACAD_00001")
        self.assertEqual(proj.title, "OpenSUTD Web Platform")

    def test_add_user_project(self):
        pm = OpenSUTDProjectManager()
        pm.add_user_to_project("ACAD_00001", "tom")
        proj = Project.objects.get(project_uid="ACAD_00001")
        self.assertEqual(len(proj.users.all()), 1)
        pm.add_user_to_project("ACAD_00001", "jane")
        self.assertEqual(len(proj.users.all()), 2)

    def test_add_tag_project(self):
        pm = OpenSUTDProjectManager()
        pm.add_tag_to_project("ACAD_00001", "rand1,rand2")
        proj = Project.objects.get(project_uid="ACAD_00001")
        self.assertEqual(len(proj.tags.all()), 2)

    def test_add_del_user_project(self):
        tom = User.objects.get(username="tom")
        jane = User.objects.get(username="jane")
        proj = Project.objects.get(project_uid="ACAD_00001")
        proj.users.add(tom)
        proj.users.add(jane)
        proj.users.remove(jane)
        self.assertEqual(len(proj.users.all()), 1)

    def test_project_page_not_approved(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "REJECT")
        url = reverse("website:project_view", args=("ACAD_00001",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual("Error 404: Page Not Found!" in str(
            response.content), True)
        self.assertGreater(len(response.content), LEN_BASE)

    def test_project_page_approved(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        url = reverse("website:project_view", args=("ACAD_00001",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), LEN_BASE)

    def test_project_page_name(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        url = reverse("website:project_view", args=("ACAD_00001",))
        response = str(self.client.get(url).content)
        self.assertEqual("OpenSUTD Web Platform" in response, True)

    def test_project_tag(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        pm.add_tag_to_project("ACAD_00001", "tag1,tag2")
        url = reverse("website:project_view", args=("ACAD_00001",))
        response = str(self.client.get(url).content)
        self.assertEqual("tag1" in response, True)
        self.assertEqual("tag2" in response, True)

    def test_project_page_contents(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        url = reverse("website:project_view", args=("ACAD_00001",))
        response = str(self.client.get(url).content)
        # print(response)
        # test top and bottom of contents
        # this does not pass on Travis for Pull Request builds
        # due to them disabling env variables for security reasons
        #self.assertEqual("Prototype for the Eventual OpenSUTD Web Platform" in response, True)
        #self.assertEqual("Data Model" in response, True)
        self.assertGreater(len(response), LEN_BASE)

    def test_project_page_load(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        url = reverse("website:project_view", args=("ACAD_00001",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_project_page_not_empty(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        url = reverse("website:project_view", args=("ACAD_00001",))
        response = str(self.client.get(url).content)
        self.assertGreater(len(response), LEN_BASE)

    def test_project_author_name(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        pm.add_user_to_project("ACAD_00001", "tom")
        url = reverse("website:project_view", args=("ACAD_00001",))
        response = str(self.client.get(url).content)
        self.assertEqual("Tom Magnanti" in response, True)

    def test_project_author_pillar(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        pm.add_user_to_project("ACAD_00001", "tom")
        url = reverse("website:project_view", args=("ACAD_00001",))
        response = str(self.client.get(url).content)
        self.assertEqual("ISTD" in response, True)

    def test_project_list_page(self):
        pm = OpenSUTDProjectManager()
        pm.set_project_status("ACAD_00001", "DISPLAY")
        url = reverse("website:projects_list")
        response = str(self.client.get(url).content)
        self.assertEqual("OpenSUTD Web Platform" in response, True)
        self.assertEqual("Sample project 1" in response, True)
