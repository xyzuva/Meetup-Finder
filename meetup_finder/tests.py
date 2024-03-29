import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Events


def db_add_event(organizer="Test Organizer", name="Test Event Name", comment="Test Event Details",
                        address="Test Address", geolocation="0,0", days=1):
    """
    Adds an event with the provided parameters to the DB that
    takes place `days` from now (negative for past event).
    (This event does not have going/not going/maybe data initialized.)
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Events.objects.create(organizer=organizer,
                                 name=name,
                                 comment=comment,  # event details
                                 address=address,
                                 geolocation=geolocation,
                                 event_date=time.date().isoformat(),
                                 event_time=time.time().isoformat())


def create_user_and_login(self, username, password):
    self.user = User.objects.create_user(username=username, password=password)
    self.client.login(username=username, password=password)
    return self.user


def login_and_add_event(self, organizer="Test Organizer", name="Test Event Name", comment="Test Event Details",
                        address="Test Address", geolocation="0,0", event_date="12/1/2100", event_time="1:00",
                        login=True, follow=True):
    if login:
        self.user = create_user_and_login(self, 'testuser', '12345')
    response = self.client.post(reverse('meetup_finder:events'), {
        'organizer': organizer,
        'name': name,
        'comment': comment,
        'address': address,
        'geolocation': geolocation,
        'event_date': event_date,
        'event_time': event_time,
    }, follow=follow)  # the list of events

    try:
        event = Events.objects.latest('pk')
    except Events.DoesNotExist:
        event = None
    return response, event


class EventsIndexViewTests(TestCase):
    def test_no_events(self):
        """
        If no events exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('meetup_finder:index'))  # the list of events
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No events are available.")
        self.assertQuerysetEqual(response.context['event_list'], [])  # the list of events

    def test_single_event(self):
        """
        An added event is displayed on the events page.
        """
        db_add_event()
        response = self.client.get(reverse('meetup_finder:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Organizer")
        self.assertContains(response, "Test Event Name")
        self.assertContains(response, "Test Event Details")
        self.assertContains(response, "Test Address")

    def test_past_event(self):
        """
        Past events are not displayed on the events page.
        """
        db_add_event(days=-7)
        response = self.client.get(reverse('meetup_finder:index'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Past Test Organizer")
        self.assertNotContains(response, "Past Test Event Name")
        self.assertNotContains(response, "Past Test Event Details")
        self.assertNotContains(response, "Past Test Address")

    def test_multiple_events(self):
        """
        A second added event is displayed on the events page.
        """
        db_add_event(organizer="Test Organizer",
                     name="Test Event Name",
                     comment="Test Event Details",  # event details
                     address="Test Address")
        db_add_event(organizer="Test Organizer 2",
                     name="Test Event Name 2",
                     comment="Test Event Details 2",  # event details
                     address="Test Address 2")
        response = self.client.get(reverse('meetup_finder:index'))
        self.assertContains(response, "Test Organizer 2")
        self.assertContains(response, "Test Event Name 2")
        self.assertContains(response, "Test Event Details 2")
        self.assertContains(response, "Test Address 2")


class EventsCreateViewTests(TestCase):
    def test_event_form(self):
        """
        Check that the create event form loads.
        """
        self.user = create_user_and_login(self, 'testuser', '12345')
        response = self.client.get(reverse('meetup_finder:events'))  # event creation
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Organizer")
        self.assertContains(response, "Event Name")
        self.assertContains(response, "Details")
        self.assertContains(response, "Address")
        self.assertContains(response, "Event date")
        self.assertContains(response, "Event time")

    def test_event_form_submit(self):
        """
        Check that submitting a valid create event form works.
        """
        response, _ = login_and_add_event(self)
        self.assertEqual(response.status_code, 200)  # after redirect
        self.assertContains(response, "Test Organizer")
        self.assertContains(response, "Test Event Name")
        self.assertContains(response, "Test Event Details")
        self.assertContains(response, "Test Address")
        self.assertContains(response, "Dec. 1, 2100")
        self.assertContains(response, "1 a.m.")

        response = self.client.get(reverse('meetup_finder:index'))  # check index page for event
        self.assertContains(response, "Test Organizer")
        self.assertContains(response, "Test Event Name")
        self.assertContains(response, "Test Event Details")
        self.assertContains(response, "Test Address")
        self.assertContains(response, "Dec. 1, 2100")

    def test_event_form_submit_invalid(self):
        """
        Check that submitting an invalid event fails. Any submitted data is sent back.
        """
        response, _ = login_and_add_event(self, comment="", address="", geolocation="", event_date="", event_time="")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Organizer")
        self.assertContains(response, "Test Event Name")
        self.assertContains(response, "This field is required.")

    def test_event_form_submit_past(self):
        """
        Check that submitting a past event fails. Any submitted data is sent back.
        """
        response, _ = login_and_add_event(self, event_date="1/1/1900")
        self.assertEqual(response.status_code, 200)  # after redirect
        self.assertContains(response, "Test Organizer")
        self.assertContains(response, "Test Event Name")
        self.assertContains(response, "Test Event Details")
        self.assertContains(response, "Test Address")
        self.assertContains(response, "1/1/1900")
        self.assertContains(response, "This event is in the past.")

    def test_response_vote_logout_get(self):
        """
        Check that logged-out users cannot access the submit event form.
        """
        self.user = create_user_and_login(self, 'testuser', '12345')
        self.client.logout()

        response = self.client.get(reverse('meetup_finder:events'))  # event creation
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_response_vote_logout_post(self):
        """
        Check that logged-out users cannot submit an event.
        """
        self.user = create_user_and_login(self, 'testuser', '12345')
        self.client.logout()

        response, _ = login_and_add_event(self, login=False, follow=False)
        self.assertEqual(response.status_code, 302)  # redirect to login

        response = self.client.get(reverse('meetup_finder:index'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test Organizer")
        self.assertNotContains(response, "Test Event Name")
        self.assertNotContains(response, "Test Event Details")
        self.assertNotContains(response, "Test Address")


class EventsDetailViewTests(TestCase):
    def test_event_details(self):
        """
        Detailed view displays correctly. Votes are initialized to 0.
        """
        _, event = login_and_add_event(self)

        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Organizer")
        self.assertContains(response, "Test Event Name")
        self.assertContains(response, "Test Event Details")
        self.assertContains(response, "Test Address")
        self.assertRegex(response.content, rb"Going.*0")
        self.assertRegex(response.content, rb"Not Going.*0")
        self.assertRegex(response.content, rb"Maybe.*0")
        self.assertContains(response, "Respond")
        self.assertContains(response, "Delete Event")  # authorized user
        self.assertNotContains(response,
                               "Log in to respond to the event, or delete the event if you are the event creator.")

    def test_event_details_noauth(self):
        """
        Detailed view displays correctly for non-authorized user
        """
        _, event = login_and_add_event(self)
        self.client.logout()
        self.user = create_user_and_login(self, 'differenttestuser', '12345')

        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Organizer")
        self.assertContains(response, "Test Event Name")
        self.assertContains(response, "Test Event Details")
        self.assertContains(response, "Test Address")
        self.assertRegex(response.content, rb"Going.*0")
        self.assertRegex(response.content, rb"Not Going.*0")
        self.assertRegex(response.content, rb"Maybe.*0")
        self.assertContains(response, "Respond")
        self.assertNotContains(response, "Delete Event")  # not authorized user
        self.assertNotContains(response,
                               "Log in to respond to the event, or delete the event if you are the event creator.")

    def test_event_details_logout(self):
        """
        Detailed view displays correctly for logged-out user
        """
        _, event = login_and_add_event(self)
        self.client.logout()

        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Organizer")
        self.assertContains(response, "Test Event Name")
        self.assertContains(response, "Test Event Details")
        self.assertContains(response, "Test Address")
        self.assertRegex(response.content, rb"Going.*0")
        self.assertRegex(response.content, rb"Not Going.*0")
        self.assertRegex(response.content, rb"Maybe.*0")
        self.assertNotContains(response, "Respond")  # not authorized user
        self.assertNotContains(response, "Delete Event")  # not authorized user
        self.assertContains(response,
                            "Log in to respond to the event, or delete the event if you are the event creator.")

    def test_event_details_past(self):
        """
        Detailed view displays notice for past event
        """
        event = db_add_event(days=-7)
        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Organizer")
        self.assertContains(response, "Test Event Name")
        self.assertContains(response, "Test Event Details")
        self.assertContains(response, "Test Address")
        self.assertContains(response, "This is a past event.")

    def test_event_details_no_event(self):
        """
        Check that an invalid/deleted event id is handled
        """
        _, event = login_and_add_event(self)
        self.client.post(reverse('meetup_finder:event_delete', args=[event.pk]), follow=True)
        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertEqual(response.status_code, 404)


class EventsResponseVoteTests(TestCase):
    def test_response_vote(self):
        """
        Check that Votes are added properly
        """
        _, event = login_and_add_event(self)
        self.client.logout()

        self.user = create_user_and_login(self, 'differenttestuser', '12345')
        r = event.response_set.get(response_text='Going')
        response = self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id}, follow=True)
        self.assertRegex(response.content, rb"Going.*1")
        self.assertRegex(response.content, rb"Not Going.*0")
        self.assertRegex(response.content, rb"Maybe.*0")
        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertRegex(response.content, rb"Going.*1")
        self.assertRegex(response.content, rb"Not Going.*0")
        self.assertRegex(response.content, rb"Maybe.*0")
        self.client.logout()

        self.user = create_user_and_login(self, 'anothertestuser', '12345')
        r = event.response_set.get(response_text='Not Going')
        response = self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id}, follow=True)
        self.assertRegex(response.content, rb"Going.*1")
        self.assertRegex(response.content, rb"Not Going.*1")
        self.assertRegex(response.content, rb"Maybe.*0")
        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertRegex(response.content, rb"Going.*1")
        self.assertRegex(response.content, rb"Not Going.*1")
        self.assertRegex(response.content, rb"Maybe.*0")
        self.client.logout()

        self.user = create_user_and_login(self, 'yetanothertestuser', '12345')
        r = event.response_set.get(response_text='Maybe')
        response = self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id}, follow=True)
        self.assertRegex(response.content, rb"Going.*1")
        self.assertRegex(response.content, rb"Not Going.*1")
        self.assertRegex(response.content, rb"Maybe.*1")
        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertRegex(response.content, rb"Going.*1")
        self.assertRegex(response.content, rb"Not Going.*1")
        self.assertRegex(response.content, rb"Maybe.*1")
        self.client.logout()

        self.user = create_user_and_login(self, 'thefinaltestuser', '12345')
        r = event.response_set.get(response_text='Going')
        response = self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id}, follow=True)
        self.assertRegex(response.content, rb"Going.*2")
        self.assertRegex(response.content, rb"Not Going.*1")
        self.assertRegex(response.content, rb"Maybe.*1")
        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertRegex(response.content, rb"Going.*2")
        self.assertRegex(response.content, rb"Not Going.*1")
        self.assertRegex(response.content, rb"Maybe.*1")
        self.client.logout()

        response = self.client.get(reverse('meetup_finder:detail', args=[event.pk]))
        self.assertRegex(response.content, rb"Going.*2")
        self.assertRegex(response.content, rb"Not Going.*1")
        self.assertRegex(response.content, rb"Maybe.*1")

    def test_response_vote_logout(self):
        """
        Check that logged-out users cannot vote.
        """
        _, event = login_and_add_event(self)
        self.client.logout()
        r = event.response_set.get(response_text='Going')
        response = self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id})
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_response_vote_invalid(self):
        """
        Check that not selecting a choice throws an error message and does not add a vote.
        """
        _, event = login_and_add_event(self)
        self.client.logout()

        self.user = create_user_and_login(self, 'differenttestuser', '12345')
        response = self.client.post(reverse('meetup_finder:vote', args=[event.id]), {}, follow=True)
        self.assertRegex(response.content, rb"Going.*0")
        self.assertRegex(response.content, rb"Not Going.*0")
        self.assertRegex(response.content, rb"Maybe.*0")
        self.assertContains(response, "You didn&#x27;t select a choice.")  # Django escapes the apostrophe

    # def test_response_vote_double(self):
    #     """
    #     Check that users cannot vote multiple times
    #     """
    #     _, event = login_and_add_event(self)
    #     self.client.logout()
    #
    #     self.user = create_user_and_login(self, 'differenttestuser', '12345')
    #     r = event.response_set.get(response_text='Going')
    #     self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id}, follow=True)
    #     response = self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id}, follow=True)
    #     self.assertRegex(response.content, rb"Going.*1")
    #     # self.assertContains(response, "You didn&#x27;t select a choice.")  # check for error once implemented

    # def test_response_vote_change(self):
    #     """
    #     Check that a different response changes the previous vote
    #     """
    #     _, event = login_and_add_event(self)
    #     self.client.logout()
    #
    #     self.user = create_user_and_login(self, 'differenttestuser', '12345')
    #     r = event.response_set.get(response_text='Going')
    #     self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id}, follow=True)
    #     r = event.response_set.get(response_text='Not Going')
    #     response = self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id}, follow=True)
    #     self.assertRegex(response.content, rb"Going.*0")
    #     self.assertRegex(response.content, rb"Not Going.*1")
    #     # self.assertContains(response, "You didn&#x27;t select a choice.")  # check for error once implemented

    def test_response_vote_no_event(self):
        """
        Check that an invalid/deleted event id is handled
        """
        _, event = login_and_add_event(self)
        r = event.response_set.get(response_text='Going')
        self.client.post(reverse('meetup_finder:event_delete', args=[event.pk]), follow=True)

        self.user = create_user_and_login(self, 'differenttestuser', '12345')
        response = self.client.post(reverse('meetup_finder:vote', args=[event.id]), {'response': r.id}, follow=True)
        self.assertEqual(response.status_code, 404)


class EventsResponseDeleteTests(TestCase):
    def test_delete_event_auth(self):
        """
        Check that authorized user can delete event
        """
        _, event = login_and_add_event(self)

        response = self.client.post(reverse('meetup_finder:event_delete', args=[event.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test Organizer")
        self.assertNotContains(response, "Test Event Name")
        self.assertNotContains(response, "Test Event Details")
        self.assertNotContains(response, "Test Address")
        self.assertNotContains(response, "Dec. 1, 2100")

    def test_delete_event_no_auth(self):
        """
        Check that non-authorized user cannot delete event
        """
        _, event = login_and_add_event(self)
        self.client.logout()
        self.user = create_user_and_login(self, 'differenttestuser', '12345')

        response = self.client.post(reverse('meetup_finder:event_delete', args=[event.pk]))
        self.assertEqual(response.status_code, 403)

    def test_delete_event_logout(self):
        """
        Check that logged-out user cannot delete event
        """
        _, event = login_and_add_event(self)
        self.client.logout()

        response = self.client.post(reverse('meetup_finder:event_delete', args=[event.pk]))
        self.assertEqual(response.status_code, 302)  # redirect to login


class ProfileTests(TestCase):
    def test_profile(self):
        """
        Check that profile loads
        """
        self.user = create_user_and_login(self, 'testuser', '12345')
        response = self.client.get(reverse('meetup_finder:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Name')
        self.assertContains(response, 'Email')
        self.assertContains(response, 'Update')

    def test_profile_submit(self):
        """
        Check that submitting a valid profile update form works.
        """
        self.user = create_user_and_login(self, 'testuser', '12345')
        response = self.client.post(reverse('meetup_finder:profile'),
                                    {
                                        'full_name': "Test User",
                                        'bio': "I am a user from Testlandia.",
                                        'birthday': "01/01/1970"
                                    },
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'I am a user from Testlandia.')
        self.assertContains(response, 'Jan. 1, 1970')

    def test_profile_invalid(self):
        """
        Check that submitting an invalid profile update form fails. Any submitted data is sent back.
        """
        self.user = create_user_and_login(self, 'testuser', '12345')
        self.client.post(reverse('meetup_finder:profile'),
                         {
                             'full_name': "Test User",
                             'bio': "I am a user from Testlandia.",
                             'birthday': "01/01/1970",
                         })

        response = self.client.post(reverse('meetup_finder:profile'),
                                    {
                                        'full_name': "",
                                        'bio': "I am a user from Testlandshire.",
                                        'birthday': "Not a Date",
                                    },
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'I am a user from Testlandia.')
        self.assertContains(response, 'Jan. 1, 1970')

        self.assertContains(response, "This field is required.")
        self.assertContains(response, 'I am a user from Testlandshire.')
        self.assertContains(response, 'Not a Date')
        self.assertContains(response, 'Enter a valid date.')

    def test_profile_logout(self):
        """
        Check that logged-out user viewing profile is redirected
        """
        self.user = create_user_and_login(self, 'testuser', '12345')
        self.client.logout()

        response = self.client.get(reverse('meetup_finder:profile'))
        self.assertEqual(response.status_code, 302)  # redirect to login


class ThirdPartyTests(TestCase):
    """
    Tests to ensure none of the third-party libraries break due to any changes in settings.py, the DB, etc.
    """
    def test_root(self):
        """
        Check that the root page loads
        """
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_allauth(self):
        """
        Check that allauth pages load
        """
        _, event = login_and_add_event(self)

        response = self.client.get(reverse('account_logout'), follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('account_logout'), follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('account_login'), follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('account_signup'), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_admin_login(self):
        """
        Check that the admin login page loads
        """
        response = self.client.get(reverse('admin:index'), follow=True)
        self.assertEqual(response.status_code, 200)
